import os
import pandas as pd
import re
from fuzzywuzzy import fuzz, process

def normalize_text(text):
    """Normalize text for fuzzy matching by removing punctuation and standardizing spaces"""
    if pd.isna(text):
        return ""
    # Convert to string, lowercase, remove punctuation, and normalize spaces
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)     # Normalize spaces
    return text.strip()

def find_best_match(target, candidates, threshold=85):
    """Find the best fuzzy match for a target string among candidates"""
    # Try exact match first (case insensitive)
    normalized_target = normalize_text(target)
    for candidate in candidates:
        if normalize_text(candidate) == normalized_target:
            return candidate
    
    # If no exact match, use fuzzy matching
    best_match, score = process.extractOne(target, candidates, scorer=fuzz.token_sort_ratio)
    if score >= threshold:
        return best_match
    return None

def should_exclude_row(row, exclude_labels):
    """Check if a row should be excluded based on label or content"""
    if not row or len(row) == 0:
        return True  # Exclude empty rows
    
    # Check the label (first column)
    label = str(row[0]) if row[0] else ""
    
    # Exclude if label is empty or "--"
    if label.strip() == "" or label.strip() == "--":
        return True
    
    # Check if label matches any exclude labels
    for exclude_label in exclude_labels:
        if find_best_match(exclude_label, [label]):
            return True
    
    # Check if any cell in the row contains "12 mths" (case insensitive)
    for cell in row:
        cell_str = str(cell).lower() if cell else ""
        if "12 mths" in cell_str:
            return True
    
    return False

def process_cash_flow_files(root_directory):
    """Process all cash-flow.csv files to extract data excluding specific rows"""
    
    # Labels to exclude (using fuzzy matching)
    exclude_labels = [
        "Cash And Cash Equivalents Begin of Year",
        "Cash And Cash Equivalents End Of Year"
    ]
    
    # Walk through all directories
    for foldername, subfolders, filenames in os.walk(root_directory):
        cash_flow_files = [f for f in filenames if f.endswith('cash-flow.csv')]
        
        if not cash_flow_files:
            continue
            
        print(f"Processing folder: {foldername}")
        
        for cash_flow_file in cash_flow_files:
            file_path = os.path.join(foldername, cash_flow_file)
            print(f"  Processing file: {cash_flow_file}")
            
            try:
                # Read the entire CSV file to preserve original structure
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) < 2:
                    print(f"    Warning: File {cash_flow_file} appears to be empty or malformed")
                    continue
                
                # Extract headers (first line)
                headers = lines[0].strip().split(',')
                # Remove the first header (top-left cell) but keep the rest
                cleaned_headers = [''] + headers[1:]
                
                # Process data rows
                output_rows = []
                excluded_count = 0
                
                for i, line in enumerate(lines[1:]):
                    row = line.strip().split(',')
                    if not row:  # Skip completely empty rows
                        continue
                    
                    # Check if this row should be excluded
                    if should_exclude_row(row, exclude_labels):
                        excluded_count += 1
                        label = row[0] if row and len(row) > 0 else "Empty/Invalid"
                        print(f"    Excluded: '{label}'")
                        continue
                    
                    # Keep the row
                    output_rows.append(row)
                
                print(f"    Kept {len(output_rows)} rows, excluded {excluded_count} rows")
                
                # Create plots directory if it doesn't exist
                plots_dir = os.path.join(foldername, "plots")
                os.makedirs(plots_dir, exist_ok=True)
                
                # Write output file
                output_file = os.path.join(plots_dir, "04_plot_cashflow.csv")
                with open(output_file, 'w', encoding='utf-8') as f:
                    # Write headers (with empty first cell)
                    f.write(','.join(cleaned_headers) + '\n')
                    # Write data rows
                    for row in output_rows:
                        f.write(','.join(row) + '\n')
                
                print(f"    Saved filtered data to: {output_file}")
                
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        lines = f.readlines()
                    
                    if len(lines) < 2:
                        print(f"    Warning: File {cash_flow_file} appears to be empty or malformed")
                        continue
                    
                    # Extract headers (first line)
                    headers = lines[0].strip().split(',')
                    cleaned_headers = [''] + headers[1:]
                    
                    # Process data rows
                    output_rows = []
                    excluded_count = 0
                    
                    for i, line in enumerate(lines[1:]):
                        row = line.strip().split(',')
                        if not row:
                            continue
                        
                        if should_exclude_row(row, exclude_labels):
                            excluded_count += 1
                            label = row[0] if row and len(row) > 0 else "Empty/Invalid"
                            print(f"    Excluded: '{label}'")
                            continue
                        
                        output_rows.append(row)
                    
                    print(f"    Kept {len(output_rows)} rows, excluded {excluded_count} rows")
                    
                    plots_dir = os.path.join(foldername, "plots")
                    os.makedirs(plots_dir, exist_ok=True)
                    
                    output_file = os.path.join(plots_dir, "04_plot_cashflow.csv")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(','.join(cleaned_headers) + '\n')
                        for row in output_rows:
                            f.write(','.join(row) + '\n')
                    
                    print(f"    Saved filtered data to: {output_file}")
                    
                except Exception as e:
                    print(f"    Error processing {cash_flow_file} with latin-1 encoding: {str(e)}")
                
            except Exception as e:
                print(f"    Error processing {cash_flow_file}: {str(e)}")
        
        print()  # Empty line for readability

def main():
    # Get the root directory (you can modify this path as needed)
    root_directory = input("Enter the root directory path: ").strip()
    
    # Validate directory exists
    if not os.path.exists(root_directory):
        print(f"Error: Directory '{root_directory}' does not exist")
        return
    
    print(f"Starting processing of directory: {root_directory}")
    print("=" * 60)
    
    process_cash_flow_files(root_directory)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()