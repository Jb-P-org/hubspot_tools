import requests
import csv
import os
import glob
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from termcolor import colored
import sys
from tqdm import tqdm

print(r"""
  _    _       _                     _     _______          _     
 | |  | |     | |                   | |   |__   __|        | |    
 | |__| |_   _| |__  ___ _ __   ___ | |_     | | ___   ___ | |___ 
 |  __  | | | | '_ \/ __| '_ \ / _ \| __|    | |/ _ \ / _ \| / __|
 | |  | | |_| | |_) \__ \ |_) | (_) | |_     | | (_) | (_) | \__ \
 |_|  |_|\__,_|_.__/|___/ .__/ \___/ \__|    |_|\___/ \___/|_|___/
                        | |                                       
                        |_|                                                   
    """)

print(colored("Par Jb-P https://jb-p.fr - Jean-Baptiste Ronssin - @jbronssin", "blue"))
print(colored("https://github.com/Jb-P-org/hubspot_tools", "blue"))
print("###############################################")
print(colored("You can interrupt the script when you want by pressing Ctrl+C", "red"))
print("###############################################")
print(colored("This script will create a folder named 'extract' in the same folder as the script", "yellow"))
print("###############################################")

# Load environment variables
load_dotenv()
TOKEN = os.getenv("HUBSPOT_TOKEN")

# HubSpot API base URLs
BASE_URL = "https://api.hubapi.com"
def get_delete_url(object_type):
    return f"{BASE_URL}/crm/v3/objects/{object_type}/batch/archive"

def get_hubspot_objects():
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    # Liste des objets standard connus
    standard_objects = ['contacts', 'companies', 'deals', 'tickets', 'products', 'line_items', 'quotes']
    
    # Get custom objects
    custom_url = f"{BASE_URL}/crm/v3/schemas"
    custom_response = requests.get(custom_url, headers=headers)
    
    if custom_response.status_code != 200:
        print(f'Error: {custom_response.status_code}')
        print("Error fetching custom objects from HubSpot")
        return None
    
    custom_objects = [obj['name'] for obj in custom_response.json().get('results', [])]
    
    return standard_objects + custom_objects

def get_object_fields(object_name):
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/crm/v3/properties/{object_name}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching fields for {object_name}")
        return None
    return response.json()

def extract_fields_to_csv(object_name, fields, output_file):
    field_data = [(field['name'], field.get('label', field['name']), field['type'], field.get('fieldType', 'N/A')) for field in fields['results']]

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['API Name', 'Field Name', 'Data Type', 'Field Type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for name, label, data_type, field_type in field_data:
            writer.writerow({
                'API Name': name,
                'Field Name': label,
                'Data Type': data_type,
                'Field Type': field_type
            })

def list_objects_and_fields():
    objects = get_hubspot_objects()
    if not objects:
        return

    print(colored("Available HubSpot Objects:", "yellow"))
    for i, obj in enumerate(objects, 1):
        print(colored(f"{i}. {obj}", "cyan"))

    while True:
        try:
            selection = int(input(colored("Enter the number of the object to extract fields: ", "green"))) - 1
            if 0 <= selection < len(objects):
                selected_object = objects[selection]
                break
            else:
                print(colored("Invalid selection. Please try again.", "red"))
        except ValueError:
            print(colored("Please enter a valid number.", "red"))

    fields = get_object_fields(selected_object)
    if not fields:
        return

    output_file = f'extract/{selected_object}_fields.csv'
    extract_fields_to_csv(selected_object, fields, output_file)

    print(colored(f"Fields for {selected_object} saved in {output_file}", "green"))

def extract_all_objects_fields():
    objects = get_hubspot_objects()
    if not objects:
        return

    for obj in tqdm(objects, desc="Extracting fields for all objects"):
        fields = get_object_fields(obj)
        if not fields:
            print(colored(f"Skipping {obj} due to error fetching fields", "yellow"))
            continue

        output_file = f'extract/{obj}_fields.csv'
        extract_fields_to_csv(obj, fields, output_file)

    print(colored("Fields for all objects saved in the 'extract' folder", "green"))

def delete_records_batch(object_type, record_ids):
    """Delete a batch of records from HubSpot."""
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "inputs": [{"id": id} for id in record_ids]
    }
    url = get_delete_url(object_type)
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 204, response.status_code, response.text

def get_object_type_from_filename(filename):
    base_name = os.path.splitext(filename)[0].lower()
    # Dictionary to map both singular and plural forms to the correct object type
    object_types = {
        'contact': 'contacts',
        'contacts': 'contacts',
        'company': 'companies',
        'companies': 'companies',
        'deal': 'deals',
        'deals': 'deals',
        'ticket': 'tickets',
        'tickets': 'tickets',
        'product': 'products',
        'products': 'products',
        'line_item': 'line_items',
        'line_items': 'line_items',
        'quote': 'quotes',
        'quotes': 'quotes'
    }
    return object_types.get(base_name, base_name)

def delete_records():
    delete_folder = "delete"
    if not os.path.exists(delete_folder):
        print(colored(f"Error: The '{delete_folder}' folder does not exist.", "red"))
        return

    csv_files = glob.glob(os.path.join(delete_folder, "*.csv"))
    if not csv_files:
        print(colored(f"Error: No CSV files found in the '{delete_folder}' folder. You must have at least one file named exactly after the object you want to delete records id. For example contact.csv", "red"))
        return

    print(colored("Available CSV files for deletion:", "yellow"))
    for i, file in enumerate(csv_files, 1):
        print(colored(f"{i}. {os.path.basename(file)}", "cyan"))

    while True:
        try:
            selection = int(input(colored("Enter the number of the file to process: ", "green"))) - 1
            if 0 <= selection < len(csv_files):
                selected_file = csv_files[selection]
                break
            else:
                print(colored("Invalid selection. Please try again.", "red"))
        except ValueError:
            print(colored("Please enter a valid number.", "red"))

    object_type = get_object_type_from_filename(os.path.basename(selected_file))
    record_ids = []
    with open(selected_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record_id_key = next((k for k in row.keys() if k.lower() == 'record id'), None)
            if record_id_key:
                record_ids.append(row[record_id_key])
            else:
                print(colored("Error: 'Record ID' column not found in the CSV.", "red"))
                return

    total_records = len(record_ids)
    print(colored(f"Number of records to delete: {total_records}", "yellow"))
    confirmation = input(colored(f"Are you sure you want to delete these {object_type}? (yes/no): ", "green"))

    if confirmation.lower() != 'yes':
        print(colored("Operation cancelled.", "red"))
        return

    batch_size = 100
    success_count = 0
    errors = []

    with tqdm(total=total_records, desc=f"Deleting {object_type}") as pbar:
        for i in range(0, total_records, batch_size):
            batch = record_ids[i:i+batch_size]
            success, status_code, response_text = delete_records_batch(object_type, batch)
            if success:
                success_count += len(batch)
            else:
                errors.append({
                    'Batch': f"{i}-{i+len(batch)}",
                    'Status Code': status_code,
                    'Error Message': response_text
                })
            pbar.update(len(batch))

    print(colored(f"\nOperation completed. {success_count}/{total_records} {object_type} successfully deleted.", "green"))

    if errors:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = os.path.join("errors", f"deletion_errors_{timestamp}.csv")
        with open(error_file, 'w', newline='') as csvfile:
            fieldnames = ['Batch', 'Status Code', 'Error Message']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for error in errors:
                writer.writerow(error)
        print(colored(f"Errors have been recorded in the file '{error_file}'.", "yellow"))

def main():
    # Create Folders if they don't exist
    for folder in ["extract", "delete", "errors"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(colored(f"Created '{folder}' folder", "yellow"))

    # Check if the .env file is present and the API key is set
    if not TOKEN:
        print("\n\n###############################################\n")
        print("¯\_(ツ)_/¯\n")
        print(colored("It seems you have not set your Hubspot API key in the .env file or the .env file is missing.", "red", attrs=["blink"]))
        print(colored("Please read the README and follow the process to set up your Hubspot API key.", "blue"))
        sys.exit(0)

    # Make the user choose the action to perform
    print(colored("What do you want to do today?", "yellow"))
    print(colored("1. Extract all the fields name from an object", "blue"))
    print(colored("2. Extract all the fields name from all the objects", "blue"))
    print(colored("3. Extract a data sample from an object", "blue"))
    print(colored("4. Extract a data sample from all the objects", "blue"))
    print(colored("5. Delete records from a CSV file", "blue"))

    action = input(colored("Enter the number of the action you want to perform: ", "green"))

    if action == '1':
        list_objects_and_fields()
    elif action == '2':
        extract_all_objects_fields()
    elif action == '3':
        print(colored("This feature is not implemented yet.", "red"))
    elif action == '4':
        print(colored("This feature is not implemented yet.", "red"))
    elif action == '5':
        delete_records()
    else:
        print(colored("Invalid action selected.", "red"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nYou chose to interrupt the script, Good Bye!")
        sys.exit(0)

print(colored("This is the end", "green"))
