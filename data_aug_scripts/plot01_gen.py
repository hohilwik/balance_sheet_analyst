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

def process_bs_files(root_directory):
    """Process all BS.csv files in the directory structure"""
    
    # Target labels we're looking for
    target_labels = [
        "Total Current Liabilities",
        "Total Non-Current Liabilities", 
        "Total Current Assets",
        "Total Non-Current Assets"
    ]
    
    # Walk through all directories
    for foldername, subfolders, filenames in os.walk(root_directory):
        bs_files = [f for f in filenames if f.endswith('BS.csv')]
        
        if not bs_files:
            continue
            
        print(f"Processing folder: {foldername}")
        
        for bs_file in bs_files:
            file_path = os.path.join(foldername, bs_file)
            print(f"  Processing file: {bs_file}")
            
            try:
                # Read CSV file
                df = pd.read_csv(file_path)
                
                # Check if the file has the expected structure
                if df.empty or len(df.columns) < 2:
                    print(f"    Warning: File {bs_file} appears to be empty or malformed")
                    continue
                
                # Get all available labels from first column
                label_column = df.columns[0]
                available_labels = df[label_column].astype(str).tolist()
                
                # Prepare output data
                output_data = []
                headers = df.columns.tolist()
                
                # Find matches for each target label
                for target_label in target_labels:
                    matched_label = find_best_match(target_label, available_labels)
                    
                    if matched_label:
                        # Extract the row for the matched label
                        matched_row = df[df[label_column] == matched_label].iloc[0].tolist()
                        output_data.append(matched_row)
                        print(f"    Found: '{matched_label}' for '{target_label}'")
                    else:
                        # Create a row with "NA" values
                        na_row = [target_label] + ["NA"] * (len(headers) - 1)
                        output_data.append(na_row)
                        print(f"    Warning: Could not find match for '{target_label}'")
                
                # Create output DataFrame
                output_df = pd.DataFrame(output_data, columns=headers)
                
                # Create plots directory if it doesn't exist
                plots_dir = os.path.join(foldername, "plots")
                os.makedirs(plots_dir, exist_ok=True)
                
                # Save the extracted data
                output_file = os.path.join(plots_dir, "01_plot_AandL.csv")
                output_df.to_csv(output_file, index=False)
                print(f"    Saved extracted data to: {output_file}")
                
            except Exception as e:
                print(f"    Error processing {bs_file}: {str(e)}")
        
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
    
    process_bs_files(root_directory)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()