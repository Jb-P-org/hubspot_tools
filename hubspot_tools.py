import requests
import csv
import os
import glob
import time
import json
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from termcolor import colored
import sys
import random
from tqdm import tqdm
import logging
from typing import List, Dict, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
BATCH_SIZE = 100

def get_delete_url(object_type: str) -> str:
    return f"{BASE_URL}/crm/v3/objects/{object_type}/batch/archive"

def get_hubspot_objects() -> Optional[List[str]]:
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    # Liste des objets standard connus
    standard_objects = ['contacts', 'companies', 'deals', 'tickets', 'products', 'line_items', 'quotes']
    
    # Get custom objects
    custom_url = f"{BASE_URL}/crm/v3/schemas"
    try:
        custom_response = requests.get(custom_url, headers=headers)
        custom_response.raise_for_status()
        custom_objects = [obj['name'] for obj in custom_response.json().get('results', [])]
        return standard_objects + custom_objects
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching custom objects from HubSpot: {str(e)}")
        return None

def get_user_input(prompt: str, options: Optional[List[str]] = None) -> str:
    while True:
        user_input = input(colored(f"{prompt} (or 'back' to return): ", "green")).lower()
        if user_input == 'back':
            return 'back'
        if options is None or user_input in options:
            return user_input
        print(colored("Invalid input. Please try again.", "red"))

def get_object_fields(object_name: str) -> Optional[Dict]:
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/crm/v3/properties/{object_name}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching fields for {object_name}: {str(e)}")
        return None

def extract_fields_to_csv(object_name: str, fields: Dict, output_file: str):
    field_data = [(field['name'], field.get('label', field['name']), field['type'], field.get('fieldType', 'N/A')) for field in fields['results']]

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
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

    selection = get_user_input("Enter the number of the object to extract fields:", [str(i) for i in range(1, len(objects) + 1)])
    if selection == 'back':
        return

    selected_object = objects[int(selection) - 1]
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
            logger.warning(f"Skipping {obj} due to error fetching fields")
            continue

        output_file = f'extract/{obj}_fields.csv'
        extract_fields_to_csv(obj, fields, output_file)

    print(colored("Fields for all objects saved in the 'extract' folder", "green"))

def delete_records_batch(object_type: str, record_ids: List[str]) -> Tuple[bool, int, str]:
    """Delete a batch of records from HubSpot."""
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "inputs": [{"id": id} for id in record_ids]
    }
    url = get_delete_url(object_type)
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True, response.status_code, response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error deleting records: {str(e)}")
        return False, getattr(e.response, 'status_code', 0), str(e)

def get_object_type_from_filename(filename: str) -> str:
    base_name = os.path.splitext(filename)[0].lower()
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
        logger.error(f"The '{delete_folder}' folder does not exist.")
        return

    csv_files = glob.glob(os.path.join(delete_folder, "*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in the '{delete_folder}' folder.")
        return

    print(colored("Available CSV files for deletion:", "yellow"))
    for i, file in enumerate(csv_files, 1):
        print(colored(f"{i}. {os.path.basename(file)}", "cyan"))

    selection = get_user_input("Enter the number of the file to process:", [str(i) for i in range(1, len(csv_files) + 1)])
    if selection == 'back':
        return

    selected_file = csv_files[int(selection) - 1]
    object_type = get_object_type_from_filename(os.path.basename(selected_file))
    
    record_ids = []
    with open(selected_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record_id_key = next((k for k in row.keys() if k.lower() == 'record id'), None)
            if record_id_key:
                record_ids.append(row[record_id_key])
            else:
                logger.error("'Record ID' column not found in the CSV.")
                return

    total_records = len(record_ids)
    print(colored(f"Number of records to delete: {total_records}", "yellow"))
    confirmation = get_user_input(f"Are you sure you want to delete these {object_type}? (yes/no):", ['yes', 'no'])

    if confirmation != 'yes':
        print(colored("Operation cancelled.", "red"))
        return

    success_count = 0
    errors = []

    with tqdm(total=total_records, desc=f"Deleting {object_type}") as pbar:
        for i in range(0, total_records, BATCH_SIZE):
            batch = record_ids[i:i+BATCH_SIZE]
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
        with open(error_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Batch', 'Status Code', 'Error Message']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for error in errors:
                writer.writerow(error)
        print(colored(f"Errors have been recorded in the file '{error_file}'.", "yellow"))

def get_sample_data(object_type: str, sample_type: str = 'recent') -> Optional[List[Dict]]:
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/crm/v3/objects/{object_type}/search"
    
    properties = get_all_properties(object_type)
    if not properties:
        return None
    
    body = {
        "limit": 100,
        "properties": properties,
        "sorts": [
            {
                "propertyName": "createdate",
                "direction": "DESCENDING" if sample_type == 'recent' else "ASCENDING"
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        results = response.json().get('results', [])
        
        if sample_type == 'random':
            random.shuffle(results)
        
        return results[:100]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching sample data for {object_type}: {str(e)}")
        return None

def get_all_properties(object_type: str) -> Optional[List[str]]:
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/crm/v3/properties/{object_type}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return [prop['name'] for prop in response.json()['results']]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching properties for {object_type}: {str(e)}")
        return None

def extract_sample_data(selected_object=None):
    if not selected_object:
        objects = get_hubspot_objects()
        if not objects:
            return

        print(colored("Available HubSpot Objects:", "yellow"))
        for i, obj in enumerate(objects, 1):
            print(colored(f"{i}. {obj}", "cyan"))

        selection = get_user_input("Enter the number of the object to extract sample data:", [str(i) for i in range(1, len(objects) + 1)])
        if selection == 'back':
            return

        selected_object = objects[int(selection) - 1]

    print(colored("Select sample type:", "yellow"))
    print(colored("1. Recent (last 100 records)", "cyan"))
    print(colored("2. Random (100 random records)", "cyan"))

    sample_choice = get_user_input("Enter your choice:", ['1', '2'])
    if sample_choice == 'back':
        return

    sample_type = 'recent' if sample_choice == '1' else 'random'
    
    print(colored(f"Fetching {sample_type} sample data for {selected_object}...", "yellow"))
    sample_data = get_sample_data(selected_object, sample_type)

    if not sample_data:
        logger.warning(f"No data found for {selected_object}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'extract/{selected_object}_sample_{sample_type}_{timestamp}.csv'

    all_fields = set(['Record ID'])
    for record in sample_data:
        all_fields.update(record['properties'].keys())

    fieldnames = ['Record ID'] + sorted(list(all_fields - {'Record ID'}))

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for record in tqdm(sample_data, desc="Writing data to CSV", total=len(sample_data)):
            row = {'Record ID': record['id']}
            row.update(record['properties'])
            writer.writerow(row)

    print(colored(f"Sample data for {selected_object} saved in {output_file}", "green"))
    print(colored(f"Total number of columns: {len(fieldnames)}", "yellow"))

def extract_sample_data_all_objects():
    objects = get_hubspot_objects()
    if not objects:
        return

    print(colored("Select sample type:", "yellow"))
    print(colored("1. Recent (last 100 records)", "cyan"))
    print(colored("2. Random (100 random records)", "cyan"))

    sample_choice = get_user_input("Enter your choice:", ['1', '2'])
    if sample_choice == 'back':
        return

    sample_type = 'recent' if sample_choice == '1' else 'random'

    for obj in objects:
        print(colored(f"\nExtracting {sample_type} sample data for {obj}...", "yellow"))
        try:
            sample_data = get_sample_data(obj, sample_type)

            if not sample_data:
                logger.warning(f"No data found for {obj}")
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f'extract/{obj}_sample_{sample_type}_{timestamp}.csv'

            all_fields = set(['Record ID'])
            for record in sample_data:
                all_fields.update(record['properties'].keys())

            fieldnames = ['Record ID'] + sorted(list(all_fields - {'Record ID'}))

            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for record in tqdm(sample_data, desc=f"Writing data for {obj}", total=len(sample_data)):
                    row = {'Record ID': record['id']}
                    row.update(record['properties'])
                    writer.writerow(row)

            print(colored(f"Sample data for {obj} saved in {output_file}", "green"))
            print(colored(f"Total number of columns: {len(fieldnames)}", "yellow"))
        except Exception as e:
            logger.error(f"Error processing {obj}: {str(e)}")
            continue

    print(colored("Extraction of sample data for all objects completed.", "green"))

def extract_contacts_without_company():
    print(colored("Estimating total number of contacts without company...", "yellow"))
    
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/crm/v3/objects/contacts/search"
    
    properties = ["firstname", "lastname", "email", "phone"]
    
    # First, get the total number of contacts
    initial_body = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "associatedcompanyid",
                        "operator": "NOT_HAS_PROPERTY"
                    }
                ]
            }
        ],
        "limit": 1
    }
    
    try:
        response = requests.post(url, headers=headers, json=initial_body)
        response.raise_for_status()
        data = response.json()
        total_contacts = data.get('total', 0)
        print(colored(f"Estimated total contacts without company: {total_contacts}", "green"))
    except requests.exceptions.RequestException as e:
        logger.error(f"Error estimating total contacts: {str(e)}")
        total_contacts = 0

    if total_contacts == 0:
        print(colored("No contacts without company found.", "yellow"))
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f'extract/contacts_without_company_{timestamp}'
    
    file_index = 1
    total_processed = 0
    current_chunk = []
    all_fields = set(["id"] + properties)
    after = None
    
    with tqdm(total=total_contacts, desc="Fetching contacts", unit=" contacts") as pbar:
        while total_processed < total_contacts:
            body = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "associatedcompanyid",
                                "operator": "NOT_HAS_PROPERTY"
                            }
                        ]
                    }
                ],
                "properties": properties,
                "limit": 100
            }
            
            if after:
                body["after"] = after  # Utilise la valeur 'after' renvoyée par l'API
                logger.info(f"Using after: {after}")
            
            try:
                response = requests.post(url, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()
                
                contacts = data.get('results', [])
                after = data.get('paging', {}).get('next', {}).get('after')
                logger.info(f"Next after: {after}")
                
                if not contacts:
                    break
                
                for contact in contacts:
                    current_chunk.append(contact)
                    all_fields.update(contact["properties"].keys())
                    
                    if len(current_chunk) == 2000:
                        write_chunk_to_csv(current_chunk, all_fields, base_filename, file_index)
                        current_chunk = []
                        file_index += 1
                
                chunk_size = len(contacts)
                total_processed += chunk_size
                pbar.update(chunk_size)
                
                time.sleep(0.1)  # Add a small delay between requests
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching contacts: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response content: {e.response.text}")
                logger.error(f"Request body: {json.dumps(body, indent=2)}")
                
                # Implement retry mechanism
                retry_count = 0
                while retry_count < 3:
                    logger.info(f"Retrying in 5 seconds... (Attempt {retry_count + 1}/3)")
                    time.sleep(5)
                    try:
                        response = requests.post(url, headers=headers, json=body)
                        response.raise_for_status()
                        break  # If successful, break out of the retry loop
                    except requests.exceptions.RequestException as retry_e:
                        logger.error(f"Retry failed: {str(retry_e)}")
                        retry_count += 1
                
                if retry_count == 3:
                    logger.error("Max retries reached. Stopping extraction.")
                    break

    # Write any remaining contacts
    if current_chunk:
        write_chunk_to_csv(current_chunk, all_fields, base_filename, file_index)
    
    print(colored(f"\nTotal contacts without company processed: {total_processed}", "green"))

def write_chunk_to_csv(chunk, all_fields, base_filename, index):
    output_file = f'{base_filename}_{index}.csv'
    fieldnames = sorted(list(all_fields))
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for contact in chunk:
            row = {"id": contact["id"]}
            row.update(contact["properties"])
            writer.writerow(row)
    
    print(colored(f"Saved {len(chunk)} contacts to {output_file}", "green"))

def main():
    for folder in ["extract", "delete", "errors"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created '{folder}' folder")

    if not TOKEN:
        logger.error("HubSpot API key not found in .env file")
        print(colored("Please read the README and follow the process to set up your Hubspot API key.", "blue"))
        sys.exit(0)

    while True:
        print(colored("\nWhat do you want to do today?", "yellow"))
        print(colored("1. Extract fields", "blue"))
        print(colored("2. Extract data sample", "blue"))
        print(colored("3. Delete records from a CSV file", "blue"))
        print(colored("4. Extract contacts without company", "blue"))
        print(colored("5. Exit", "blue"))

        action = get_user_input("Enter the number of the action you want to perform:", ['1', '2', '3', '4', '5'])

        if action == '1':
            print(colored("\nExtract fields for:", "yellow"))
            print(colored("1. All objects", "cyan"))
            objects = get_hubspot_objects()
            if objects:
                for i, obj in enumerate(objects, 2):
                    print(colored(f"{i}. {obj}", "cyan"))
            
            object_choice = get_user_input("Enter your choice:", [str(i) for i in range(1, len(objects) + 2)])
            if object_choice == 'back':
                continue
            elif object_choice == '1':
                extract_all_objects_fields()
            else:
                selected_object = objects[int(object_choice) - 2]
                fields = get_object_fields(selected_object)
                if fields:
                    output_file = f'extract/{selected_object}_fields.csv'
                    extract_fields_to_csv(selected_object, fields, output_file)
                    print(colored(f"Fields for {selected_object} saved in {output_file}", "green"))

        elif action == '2':
            print(colored("\nExtract data sample for:", "yellow"))
            print(colored("1. All objects", "cyan"))
            objects = get_hubspot_objects()
            if objects:
                for i, obj in enumerate(objects, 2):
                    print(colored(f"{i}. {obj}", "cyan"))
            
            object_choice = get_user_input("Enter your choice:", [str(i) for i in range(1, len(objects) + 2)])
            if object_choice == 'back':
                continue
            elif object_choice == '1':
                extract_sample_data_all_objects()
            else:
                selected_object = objects[int(object_choice) - 2]
                extract_sample_data(selected_object)

        elif action == '3':
            delete_records()
        elif action == '4':
            extract_contacts_without_company()
        elif action == '5':
            print(colored("Exiting the program. Goodbye!", "green"))
            break
        else:
            logger.warning("Invalid action selected.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nYou chose to interrupt the script, Good Bye!")
        sys.exit(0)

print(colored("This is the end", "green"))
