from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import sqlite3
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import uuid

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
    """Create company folder with sample CSV files"""
    folder_path = f'company_data/{company_id}'
    os.makedirs(folder_path, exist_ok=True)
    
    # Create sample CSV files
    sample_data = {
        'sales_data.csv': ['Date', 'Product', 'Quantity', 'Revenue'],
        'customer_data.csv': ['CustomerID', 'Name', 'Email', 'Region'],
        'inventory.csv': ['ProductID', 'ProductName', 'Stock', 'Price'],
        'employee_data.csv': ['EmployeeID', 'Name', 'Department', 'Salary'],
        'financials.csv': ['Month', 'Revenue', 'Expenses', 'Profit'],
        'marketing.csv': ['Campaign', 'Impressions', 'Clicks', 'Conversions'],
        'operations.csv': ['Metric', 'Value', 'Target', 'Variance'],
        'internal_data.csv': ['InternalID', 'ConfidentialData', 'Score']  # Hidden file
    }
    
    for filename, headers in sample_data.items():
        df = pd.DataFrame(columns=headers)
        # Add some sample rows
        for i in range(5):
            if filename == 'sales_data.csv':
                df.loc[i] = [f'2024-01-{i+1}', f'Product {i+1}', i*10, i*1000]
            elif filename == 'customer_data.csv':
                df.loc[i] = [f'CUST{i+1}', f'Customer {i+1}', f'customer{i+1}@email.com', f'Region {i%3+1}']
            # Add more sample data for other files...
        
        df.to_csv(f'{folder_path}/{filename}', index=False)
    
    # Create dynamic system prompt for LLM
    system_prompt = f"""
    You are an assistant for company: {company_id}.
    The user has access to various business data including sales, customers, inventory, etc.
    Help them analyze their data and answer business-related questions.
    Current date: {datetime.now().strftime('%Y-%m-%d')}
    """
    
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
    
import pandas as pd
import numpy as np

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
    system_prompt = "You are a helpful assistant."
    if os.path.exists(system_prompt_path):
        with open(system_prompt_path, 'r') as f:
            system_prompt = f.read()
    
    # LLM Integration - Choose one method:
    
    # Method 1: DeepSeek API
    # import requests
    # response = requests.post('https://api.deepseek.com/chat/completions', 
    #     headers={'Authorization': 'Bearer YOUR_DEEPSEEK_API_KEY'},
    #     json={
    #         'model': 'deepseek-chat',
    #         'messages': [
    #             {'role': 'system', 'content': system_prompt},
    #             {'role': 'user', 'content': message}
    #         ]
    #     })
    # llm_response = response.json()['choices'][0]['message']['content']
    
    # Method 2: Local LLM (replace with your implementation)
    # For now, we'll return a mock response
    llm_response = f"Mock response for: {message}. Company: {company_id}. System context loaded."
    
    return jsonify({'response': llm_response})

if __name__ == '__main__':
    app.run(debug=True, port=5000)