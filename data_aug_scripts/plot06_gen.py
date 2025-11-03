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

def process_leverage_ratios_files(root_directory):
    """Process all ratios.csv files to extract leverage and liquidity ratios"""
    
    # Target labels we're looking for
    target_labels = [
        "Current Ratio (X)",
        "Quick Ratio (X)", 
        "Total Debt/Equity (X)"
    ]
    
    # Walk through all directories
    for foldername, subfolders, filenames in os.walk(root_directory):
        ratios_files = [f for f in filenames if f.endswith('ratios.csv')]
        
        if not ratios_files:
            continue
            
        print(f"Processing folder: {foldername}")
        
        for ratios_file in ratios_files:
            file_path = os.path.join(foldername, ratios_file)
            print(f"  Processing file: {ratios_file}")
            
            try:
                # Read the entire CSV file to preserve original structure
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) < 2:
                    print(f"    Warning: File {ratios_file} appears to be empty or malformed")
                    continue
                
                # Extract headers (first line) and data
                headers = lines[0].strip().split(',')
                # Remove the first header (top-left cell) but keep the rest
                cleaned_headers = [''] + headers[1:]
                
                # Extract all labels from first column
                available_labels = []
                data_rows = []
                for line in lines[1:]:
                    row = line.strip().split(',')
                    if row and row[0]:  # if row is not empty and first column is not empty
                        available_labels.append(row[0])
                        data_rows.append(row)
                
                # Prepare output data
                output_rows = []
                
                # Find matches for each target label
                for target_label in target_labels:
                    matched_label = find_best_match(target_label, available_labels)
                    
                    if matched_label:
                        # Find the row with the matched label
                        for row in data_rows:
                            if row[0] == matched_label:
                                # Use the original target label, not the matched one
                                output_row = [target_label] + row[1:]
                                output_rows.append(output_row)
                                print(f"    Found: '{matched_label}' for '{target_label}'")
                                break
                    else:
                        # Create a row with "NA" values
                        na_row = [target_label] + ["NA"] * (len(cleaned_headers) - 1)
                        output_rows.append(na_row)
                        print(f"    Warning: Could not find match for '{target_label}'")
                
                # Create plots directory if it doesn't exist
                plots_dir = os.path.join(foldername, "plots")
                os.makedirs(plots_dir, exist_ok=True)
                
                # Write output file
                output_file = os.path.join(plots_dir, "06_plot_leverage.csv")
                with open(output_file, 'w', encoding='utf-8') as f:
                    # Write headers (with empty first cell)
                    f.write(','.join(cleaned_headers) + '\n')
                    # Write data rows
                    for row in output_rows:
                        f.write(','.join(row) + '\n')
                
                print(f"    Saved extracted data to: {output_file}")
                
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        lines = f.readlines()
                    
                    if len(lines) < 2:
                        print(f"    Warning: File {ratios_file} appears to be empty or malformed")
                        continue
                    
                    # Extract headers (first line) and data
                    headers = lines[0].strip().split(',')
                    cleaned_headers = [''] + headers[1:]
                    
                    available_labels = []
                    data_rows = []
                    for line in lines[1:]:
                        row = line.strip().split(',')
                        if row and row[0]:
                            available_labels.append(row[0])
                            data_rows.append(row)
                    
                    output_rows = []
                    
                    # Find matches for each target label
                    for target_label in target_labels:
                        matched_label = find_best_match(target_label, available_labels)
                        
                        if matched_label:
                            for row in data_rows:
                                if row[0] == matched_label:
                                    output_row = [target_label] + row[1:]
                                    output_rows.append(output_row)
                                    print(f"    Found: '{matched_label}' for '{target_label}'")
                                    break
                        else:
                            na_row = [target_label] + ["NA"] * (len(cleaned_headers) - 1)
                            output_rows.append(na_row)
                            print(f"    Warning: Could not find match for '{target_label}'")
                    
                    plots_dir = os.path.join(foldername, "plots")
                    os.makedirs(plots_dir, exist_ok=True)
                    
                    output_file = os.path.join(plots_dir, "06_plot_leverage.csv")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(','.join(cleaned_headers) + '\n')
                        for row in output_rows:
                            f.write(','.join(row) + '\n')
                    
                    print(f"    Saved extracted data to: {output_file}")
                    
                except Exception as e:
                    print(f"    Error processing {ratios_file} with latin-1 encoding: {str(e)}")
                
            except Exception as e:
                print(f"    Error processing {ratios_file}: {str(e)}")
        
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
    
    process_leverage_ratios_files(root_directory)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()