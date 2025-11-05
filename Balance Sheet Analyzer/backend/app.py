from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import sqlite3
import os
import pandas as pd
import numpy as np
import json
import requests
from datetime import datetime, timedelta
import uuid
import shutil
from pathlib import Path
from fuzzywuzzy import process

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
CORS(app)
jwt = JWTManager(app)

# Initialize database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            company_id TEXT NOT NULL,
            approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Admin users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Pending approvals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT UNIQUE NOT NULL,
            requested_by TEXT NOT NULL,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default admin user
    try:
        c.execute("INSERT INTO admin_users (username, password) VALUES (?, ?)", 
                 ('admin', 'admin123'))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

init_db()

# Helper functions

    


def create_company_folder(company_id):
    """Create company folder and copy scraped data if available"""
    # Convert relative path to absolute path
    template_dir = Path('../../../finance-scrape/output/mod_companies').resolve()
    
    folder_path = f'company_data/{company_id}'
    os.makedirs(folder_path, exist_ok=True)
    
    # Check if template folder exists
    template_folder_path = template_dir / company_id
    
    if template_folder_path.exists() and template_folder_path.is_dir():
        try:
            # Copy all contents if exact match exists
            shutil.copytree(template_folder_path, folder_path, dirs_exist_ok=True)
            print(f"Copied template contents from '{template_folder_path}' to '{folder_path}'")
        except Exception as e:
            print(f"Error copying template contents: {e}")
    else:
        # Fuzzy matching fallback
        print(f"No exact match found for '{company_id}', searching for nearest match...")
        
        # Get all available folders in template directory
        available_folders = []
        if template_dir.exists() and template_dir.is_dir():
            available_folders = [f.name for f in template_dir.iterdir() if f.is_dir()]
        
        if available_folders:
            # Find the best match using fuzzy matching
            best_match, score = process.extractOne(company_id, available_folders)
            
            if score >= 75:  # threshold
                best_match_path = template_dir / best_match
                try:
                    shutil.copytree(best_match_path, folder_path, dirs_exist_ok=True)
                    print(f"Copied from nearest match '{best_match}' (score: {score}) to '{folder_path}'")
                except Exception as e:
                    print(f"Error copying from nearest match: {e}")
            else:
                print(f"No suitable match found. Best match was '{best_match}' with score {score} (below threshold 80)")
        else:
            print(f"No template folders found in '{template_dir}'")
        
    # Create dynamic system prompt for LLM
    system_prompt = generate_dynamic_system_prompt(company_id)
    
    with open(f'{folder_path}/system_prompt.txt', 'w') as f:
        f.write(system_prompt)

def get_user_company_files(company_id):
    """Get list of visible CSV files for a company"""
    folder_path = f'company_data/{company_id}'
    if not os.path.exists(folder_path):
        return []
    
    files = os.listdir(folder_path)
    visible_files = [f for f in files if f.endswith('.csv') and f != 'internal_data.csv']
    return visible_files


def transform_plot_data(file_path):
    """
    Optimized version using pandas operations
    """
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Step 1: Filter out invalid columns
        def is_valid_column(column_data, column_name):
            # Skip if column name is "--"
            if column_name == "--":
                return False
            
            # Skip if all values are "--", "NA", or empty
            valid_count = sum(1 for val in column_data 
                            if pd.notna(val) and str(val).strip() not in ["--", "NA", ""])
            return valid_count > 0
        
        valid_columns = [col for col in df.columns if is_valid_column(df[col], col)]
        df = df[valid_columns]
        
        # Step 2: Transform from row-major to column-major
        label_col = df.columns[0]
        time_periods = df.columns[1:]
        
        # Reverse time periods for chronological order
        time_periods_reversed = list(reversed(time_periods))
        
        # Melt the dataframe to transform to column-major format
        melted_df = df.melt(id_vars=[label_col], value_vars=time_periods_reversed, 
                          var_name='period', value_name='value')
        
        # Pivot to get the desired structure
        pivoted_df = melted_df.pivot(index='period', columns=label_col, values='value')
        
        # Reset index to make period a column
        pivoted_df = pivoted_df.reset_index()
        
        # Convert values to appropriate types
        for column in pivoted_df.columns:
            if column != 'period':
                pivoted_df[column] = pivoted_df[column].apply(convert_value)
        
        # Convert to list of dictionaries for JSON response
        result_data = pivoted_df.to_dict('records')
        
        return {
            "success": True,
            "data": result_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }
        
        
def generate_dynamic_system_prompt(company_id):
    """Generate dynamic system prompt"""
    
    base_prompt_path = 'base_system_prompt.txt'
    try:
        with open(base_prompt_path, 'r') as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        system_prompt = "You are an experienced financial analyst briefing the company C-suite about the company's financials, income sources, expense streams, and future growth/profit prospects, while keeping in mind risk assessment of the state of the financials. Be respectful and professional. Do not use any emoji. Do not lecture the user. Concisely debrief the C-suite on the finances of the company"
    
    # Get all user files
    all_files = get_user_company_files(company_id)
    
    # Filter for specific financial report files
    financial_files = []
    for filename in all_files:
        if any([
            filename.endswith('_quarterly results.csv'),
            filename.endswith('_cash-flow.csv'), 
            filename.endswith('_annual_results.csv'),
            filename.endswith('-BS.csv'),
            filename.endswith('-PL.csv'),
            filename.endswith('ratios.csv')
        ]):
            financial_files.append(filename)
    
    file_contents = ""
    
    for filename in financial_files:
        file_path = f'company_data/{company_id}/{filename}'
        try:
            # Read the entire CSV file
            df = pd.read_csv(file_path)
            file_contents += df.to_string(index=False)  # Convert entire DataFrame to string
            file_contents += "\n"  # Add newline separation between files
            
        except Exception as e:
            file_contents += f"\n=== File: {filename} ===\nError reading file: {str(e)}\n"
    
    
    full_prompt = system_prompt + "\n" + file_contents
    
    return full_prompt


def convert_value(value):
    """Convert value to appropriate type, preserving nulls for invalid values"""
    if pd.isna(value) or str(value).strip() in ["--", "NA", ""]:
        return None
    try:
        if isinstance(value, str):
            clean_value = value.replace(',', '')
            return float(clean_value)
        return float(value)
    except (ValueError, TypeError):
        return value

# Authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    company_id = data.get('company_id')
    
    if not username or not password or not company_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (username, password, company_id) VALUES (?, ?, ?)",
                 (username, password, company_id))
        c.execute("INSERT OR IGNORE INTO pending_approvals (company_id, requested_by) VALUES (?, ?)",
                 (company_id, username))
        conn.commit()
        
        # Create company folder
        create_company_folder(company_id)
        
        return jsonify({'message': 'Registration successful. Waiting for admin approval.'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user and user[4]:  # Check if approved
        access_token = create_access_token(identity=username)
        return jsonify({
            'access_token': access_token,
            'username': username,
            'company_id': user[3]
        })
    elif user and not user[4]:
        return jsonify({'error': 'Account pending admin approval'}), 401
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# Admin routes
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM admin_users WHERE username = ? AND password = ?", (username, password))
    admin = c.fetchone()
    conn.close()
    
    if admin:
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token, 'username': username})
    else:
        return jsonify({'error': 'Invalid admin credentials'}), 401

@app.route('/api/admin/pending-approvals', methods=['GET'])
@jwt_required()
def get_pending_approvals():
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT pa.company_id, pa.requested_by, pa.requested_at, u.id 
                 FROM pending_approvals pa 
                 JOIN users u ON pa.company_id = u.company_id''')
    approvals = c.fetchall()
    conn.close()
    
    result = []
    for approval in approvals:
        result.append({
            'company_id': approval[0],
            'requested_by': approval[1],
            'requested_at': approval[2],
            'user_id': approval[3]
        })
    
    return jsonify(result)

@app.route('/api/admin/approve-company/<company_id>', methods=['POST'])
@jwt_required()
def approve_company(company_id):
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET approved = TRUE WHERE company_id = ?", (company_id,))
    c.execute("DELETE FROM pending_approvals WHERE company_id = ?", (company_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Company approved successfully'})

# Data routes
@app.route('/api/user/files', methods=['GET'])
@jwt_required()
def get_user_files():
    current_user = get_jwt_identity()
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT company_id FROM users WHERE username = ?", (current_user,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    company_id = user[0]
    files = get_user_company_files(company_id)
    return jsonify(files)

@app.route('/api/user/file/<filename>', methods=['GET'])
@jwt_required()
def get_file_data(filename):
    current_user = get_jwt_identity()
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT company_id FROM users WHERE username = ?", (current_user,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    company_id = user[0]
    file_path = f'company_data/{company_id}/{filename}'
    
    if not os.path.exists(file_path) or filename == 'internal_data.csv':
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Read CSV with proper encoding and header handling
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # If the CSV has no headers, create generic ones
        if df.columns.dtype == 'object' and all(str(col).startswith('Unnamed:') for col in df.columns):
            df.columns = [f'Column_{i+1}' for i in range(len(df.columns))]
        
        # Convert NaN values to empty strings
        df = df.fillna('')
        
        # Convert all data to strings to avoid serialization issues
        df = df.astype(str)
        
        return jsonify({
            'columns': df.columns.tolist(),
            'data': df.values.tolist()
        })
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        try:
            df = pd.read_csv(file_path, encoding='latin-1')
            df = df.fillna('')
            df = df.astype(str)
            
            return jsonify({
                'columns': df.columns.tolist(),
                'data': df.values.tolist()
            })
        except Exception as e:
            return jsonify({'error': f'Failed to read file: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500
        
@app.route('/api/user/plot/<plot_name>', methods=['GET'])
@jwt_required()
def get_plot_data(plot_name):
    current_user = get_jwt_identity()
    
    # Get user's company_id
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT company_id FROM users WHERE username = ?", (current_user,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    company_id = user[0]
    file_path = f'company_data/{company_id}/plots/{plot_name}.csv'
    
    # If plot file doesn't exist, return empty data (frontend will use dummy data)
    if not os.path.exists(file_path):
        return jsonify({
            'data': [],
            'message': 'Plot data file not found, using sample data'
        })
    
    result = transform_plot_data(file_path)
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": result["data"]
        })
    else:
        return jsonify({
            "success": False,
            "error": result["error"],
            "data": []
        }), 500

# LLM Chat route
@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat_with_llm():
    current_user = get_jwt_identity()
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Get user's company_id
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT company_id FROM users WHERE username = ?", (current_user,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    company_id = user[0]
    system_prompt_path = f'company_data/{company_id}/system_prompt.txt'
    
    # Read system prompt
    system_prompt = "You are an experienced financial analyst briefing the company C-suite about the company's financials, income sources, expense streams, and future growth/profit prospects, while keeping in mind risk assessment of the state of the financials. Be respectful and professional. Do not use any emoji. Do not lecture the user. Concisely debrief the C-suite on the finances of the company."
    
    system_prompt = generate_dynamic_system_prompt(company_id)
    
    if os.path.exists(system_prompt_path):
        with open(system_prompt_path, 'r') as f:
            system_prompt = f.read()
    
    # Read API key
    api_key = ""
    api_path = "../../../api_deepseek.txt"
    
    # Try multiple possible paths for the API key
    possible_paths = [
        api_path
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    api_key = f.read()
                break
            except Exception as e:
                print(f"Error reading API key from {path}: {e}")
    
    if not api_key:
        return jsonify({'error': 'DeepSeek API key not found. Please ensure api_deepseek.txt exists with your API key.'}), 600
    
    # DeepSeek API call
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'deepseek-reasoner',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': message}
            ],
            'stream': False,
            'max_tokens': 32000
        }
        
        response = requests.post(
            'https://api.deepseek.com/chat/completions',
            headers=headers,
            json=payload,
            timeout=120  # 120 second timeout
        )
        
        if response.status_code == 200:
            response_data = response.json()
            llm_response = response_data['choices'][0]['message']['content']
            
            return jsonify({
                'response': llm_response,
                'usage': response_data.get('usage', {}),
                'model': response_data.get('model', 'deepseek-reasoner')
            })
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get('error', {}).get('message', error_detail)
            except:
                pass
                
            return jsonify({
                'error': f'DeepSeek API error: {response.status_code}',
                'detail': error_detail
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'DeepSeek API request timed out'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Failed to connect to DeepSeek API'}), 503
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)