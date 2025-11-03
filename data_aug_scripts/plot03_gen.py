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

def find_exceptional_items(available_labels):
    """Find Exceptional Items, fall back to Extraordinary Items if not found"""
    exceptional_match = find_best_match("Exceptional Items", available_labels)
    if exceptional_match:
        return exceptional_match, "Exceptional Items"
    
    extraordinary_match = find_best_match("Extraordinary Items", available_labels)
    if extraordinary_match:
        return extraordinary_match, "Exceptional Items"  # Standardize to Exceptional Items
    
    return None, "Exceptional Items"

def process_expenses_files(root_directory):
    """Process all PL.csv files to extract expenses data"""
    
    # Additional target labels we're looking for
    additional_labels = [
        "Total Tax Expenses"
    ]
    
    # Walk through all directories
    for foldername, subfolders, filenames in os.walk(root_directory):
        pl_files = [f for f in filenames if f.endswith('-PL.csv')]
        
        if not pl_files:
            continue
            
        print(f"Processing folder: {foldername}")
        
        for pl_file in pl_files:
            file_path = os.path.join(foldername, pl_file)
            print(f"  Processing file: {pl_file}")
            
            try:
                # Read the entire CSV file to preserve original structure
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) < 2:
                    print(f"    Warning: File {pl_file} appears to be empty or malformed")
                    continue
                
                # Extract headers (first line) and data
                headers = lines[0].strip().split(',')
                # Remove the first header (top-left cell) but keep the rest
                cleaned_headers = [''] + headers[1:]
                
                # Extract all labels from first column and their row indices
                available_labels = []
                data_rows = []
                for i, line in enumerate(lines[1:]):
                    row = line.strip().split(',')
                    if row and row[0]:  # if row is not empty and first column is not empty
                        available_labels.append(row[0])
                        data_rows.append((i + 1, row))  # Store row index and data
                
                # Prepare output data
                output_rows = []
                
                # Find EXPENSES and Total Expenses for block extraction
                expenses_start_label = find_best_match("EXPENSES", available_labels)
                total_expenses_label = find_best_match("Total Expenses", available_labels)
                
                # Extract block from after EXPENSES to before Total Expenses
                if expenses_start_label and total_expenses_label:
                    print(f"    Found EXPENSES block: '{expenses_start_label}' to '{total_expenses_label}'")
                    
                    # Find the indices of the start and end markers
                    start_index = None
                    end_index = None
                    
                    for i, (row_idx, row) in enumerate(data_rows):
                        if row[0] == expenses_start_label:
                            start_index = i
                        if row[0] == total_expenses_label:
                            end_index = i
                    
                    if start_index is not None and end_index is not None and start_index < end_index:
                        # Extract rows from start_index+1 to end_index-1 (excluding Total Expenses)
                        for i in range(start_index + 1, end_index):
                            row_idx, row_data = data_rows[i]
                            output_rows.append(row_data)
                            print(f"      Included: '{row_data[0]}'")
                        print(f"      Excluded 'Total Expenses' row")
                    else:
                        print(f"    Warning: Could not extract EXPENSES block (invalid indices)")
                else:
                    if not expenses_start_label:
                        print(f"    Warning: Could not find 'EXPENSES' label")
                    if not total_expenses_label:
                        print(f"    Warning: Could not find 'Total Expenses' label")
                
                # Find and include additional labels
                for target_label in additional_labels:
                    matched_label = find_best_match(target_label, available_labels)
                    
                    if matched_label:
                        # Find the row with the matched label
                        for row_idx, row_data in data_rows:
                            if row_data[0] == matched_label:
                                output_rows.append(row_data)
                                print(f"    Included additional: '{matched_label}' for '{target_label}'")
                                break
                    else:
                        # Create a row with "NA" values
                        na_row = [target_label] + ["NA"] * (len(cleaned_headers) - 1)
                        output_rows.append(na_row)
                        print(f"    Warning: Could not find match for '{target_label}'")
                
                # Find and include Exceptional/Extraordinary Items
                exceptional_label, display_label = find_exceptional_items(available_labels)
                if exceptional_label:
                    # Find the row with the matched label
                    for row_idx, row_data in data_rows:
                        if row_data[0] == exceptional_label:
                            # Use standardized label
                            standardized_row = [display_label] + row_data[1:]
                            output_rows.append(standardized_row)
                            print(f"    Included: '{exceptional_label}' as '{display_label}'")
                            break
                else:
                    # Create a row with "NA" values
                    na_row = [display_label] + ["NA"] * (len(cleaned_headers) - 1)
                    output_rows.append(na_row)
                    print(f"    Warning: Could not find match for 'Exceptional Items' or 'Extraordinary Items'")
                
                # Create plots directory if it doesn't exist
                plots_dir = os.path.join(foldername, "plots")
                os.makedirs(plots_dir, exist_ok=True)
                
                # Write output file
                output_file = os.path.join(plots_dir, "03_plot_expenses.csv")
                with open(output_file, 'w', encoding='utf-8') as f:
                    # Write headers (with empty first cell)
                    f.write(','.join(cleaned_headers) + '\n')
                    # Write data rows
                    for row in output_rows:
                        f.write(','.join(row) + '\n')
                
                print(f"    Saved {len(output_rows)} expense rows to: {output_file}")
                
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        lines = f.readlines()
                    
                    if len(lines) < 2:
                        print(f"    Warning: File {pl_file} appears to be empty or malformed")
                        continue
                    
                    # Extract headers (first line) and data
                    headers = lines[0].strip().split(',')
                    cleaned_headers = [''] + headers[1:]
                    
                    available_labels = []
                    data_rows = []
                    for i, line in enumerate(lines[1:]):
                        row = line.strip().split(',')
                        if row and row[0]:
                            available_labels.append(row[0])
                            data_rows.append((i + 1, row))
                    
                    output_rows = []
                    
                    # Find EXPENSES and Total Expenses for block extraction
                    expenses_start_label = find_best_match("EXPENSES", available_labels)
                    total_expenses_label = find_best_match("Total Expenses", available_labels)
                    
                    if expenses_start_label and total_expenses_label:
                        print(f"    Found EXPENSES block: '{expenses_start_label}' to '{total_expenses_label}'")
                        
                        start_index = None
                        end_index = None
                        
                        for i, (row_idx, row) in enumerate(data_rows):
                            if row[0] == expenses_start_label:
                                start_index = i
                            if row[0] == total_expenses_label:
                                end_index = i
                        
                        if start_index is not None and end_index is not None and start_index < end_index:
                            # Extract rows from start_index+1 to end_index-1 (excluding Total Expenses)
                            for i in range(start_index + 1, end_index):
                                row_idx, row_data = data_rows[i]
                                output_rows.append(row_data)
                                print(f"      Included: '{row_data[0]}'")
                            print(f"      Excluded 'Total Expenses' row")
                        else:
                            print(f"    Warning: Could not extract EXPENSES block (invalid indices)")
                    else:
                        if not expenses_start_label:
                            print(f"    Warning: Could not find 'EXPENSES' label")
                        if not total_expenses_label:
                            print(f"    Warning: Could not find 'Total Expenses' label")
                    
                    # Additional labels
                    for target_label in additional_labels:
                        matched_label = find_best_match(target_label, available_labels)
                        
                        if matched_label:
                            for row_idx, row_data in data_rows:
                                if row_data[0] == matched_label:
                                    output_rows.append(row_data)
                                    print(f"    Included additional: '{matched_label}' for '{target_label}'")
                                    break
                        else:
                            na_row = [target_label] + ["NA"] * (len(cleaned_headers) - 1)
                            output_rows.append(na_row)
                            print(f"    Warning: Could not find match for '{target_label}'")
                    
                    # Exceptional Items
                    exceptional_label, display_label = find_exceptional_items(available_labels)
                    if exceptional_label:
                        for row_idx, row_data in data_rows:
                            if row_data[0] == exceptional_label:
                                standardized_row = [display_label] + row_data[1:]
                                output_rows.append(standardized_row)
                                print(f"    Included: '{exceptional_label}' as '{display_label}'")
                                break
                    else:
                        na_row = [display_label] + ["NA"] * (len(cleaned_headers) - 1)
                        output_rows.append(na_row)
                        print(f"    Warning: Could not find match for 'Exceptional Items' or 'Extraordinary Items'")
                    
                    plots_dir = os.path.join(foldername, "plots")
                    os.makedirs(plots_dir, exist_ok=True)
                    
                    output_file = os.path.join(plots_dir, "03_plot_expenses.csv")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(','.join(cleaned_headers) + '\n')
                        for row in output_rows:
                            f.write(','.join(row) + '\n')
                    
                    print(f"    Saved {len(output_rows)} expense rows to: {output_file}")
                    
                except Exception as e:
                    print(f"    Error processing {pl_file} with latin-1 encoding: {str(e)}")
                
            except Exception as e:
                print(f"    Error processing {pl_file}: {str(e)}")
        
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
    
    process_expenses_files(root_directory)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()