import json
import os
import argparse

def add_content_id(data, counter):
    if isinstance(data, dict):
        # Check if the object has a "type" attribute
        if 'type' in data or 'col_header' in data:
            # Assign a numeric content_id based on the counter
            data['content_id'] = f"{counter[0]}"
            counter[0] += 1  # Increment the counter
        
        # Recursively process all values in the dictionary
        for key, value in data.items():
            add_content_id(value, counter)
    
    elif isinstance(data, list):
        # Recursively process each item in the list
        for item in data:
            add_content_id(item, counter)

def main(input_file):
    # Load the JSON data from the specified file
    with open(input_file, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    # Initialize a counter as a list to allow mutation
    counter = [1]

    # Add content_id to the JSON data
    add_content_id(json_data, counter)

    # Create the output file path
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_withIds{ext}"

    # Save the modified JSON data to a new file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)

    print(f"Modified JSON saved to: {output_file}")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Add content IDs to JSON objects with a 'type' attribute.")
    parser.add_argument("input_file", type=str, help="Path to the input JSON file (content_doc.json).")

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with the provided input file
    main(args.input_file)