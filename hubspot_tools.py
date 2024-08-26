import requests
import csv
import os
import glob
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from termcolor import colored
import sys
import random
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

def get_user_input(prompt, options=None):
    while True:
        user_input = input(colored(f"{prompt} (or 'back' to return): ", "green")).lower()
        if user_input == 'back':
            return 'back'
        if options is None or user_input in options:
            return user_input
        print(colored("Invalid input. Please try again.", "red"))

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

def get_sample_data(object_type, sample_type='recent'):
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/crm/v3/objects/{object_type}"
    
    params = {
        'limit': 100,
        'properties': '__all__'
    }
    
    if sample_type == 'recent':
        params['sort'] = '-createdate'  # Le signe moins indique un tri descendant
    elif sample_type == 'random':
        # Pour l'échantillonnage aléatoire, nous allons utiliser une approche différente
        # Nous allons récupérer les 100 premiers enregistrements, puis les mélanger
        params['sort'] = 'createdate'  # Tri ascendant pour varier les résultats
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(colored(f"Error fetching sample data for {object_type}", "red"))
        return None
    
    results = response.json().get('results', [])
    
    if sample_type == 'random' and results:
        random.shuffle(results)
    
    return results[:100]  # Assure que nous retournons au maximum 100 résultats

def get_all_properties(object_type):
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/crm/v3/properties/{object_type}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(colored(f"Error fetching properties for {object_type}: Status code {response.status_code}", "red"))
        print(colored(f"Response: {response.text}", "red"))
        return None
    return [prop['name'] for prop in response.json()['results']]

def get_sample_data(object_type, sample_type='recent'):
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/crm/v3/objects/{object_type}/search"
    
    # Get all properties for the object type
    properties = get_all_properties(object_type)
    if not properties:
        return None
    
    # Divide properties into chunks to avoid payload size issues
    property_chunks = [properties[i:i + 50] for i in range(0, len(properties), 50)]
    
    all_results = []
    
    if sample_type == 'recent':
        # For recent, we only need one API call to get the last 100 records
        body = {
            "limit": 100,
            "properties": properties,
            "sorts": [
                {
                    "propertyName": "createdate",
                    "direction": "DESCENDING"
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            all_results = response.json().get('results', [])
        except requests.exceptions.RequestException as e:
            print(colored(f"Error fetching sample data for {object_type}: {str(e)}", "red"))
            if response:
                print(colored(f"Status code: {response.status_code}", "red"))
                print(colored(f"Response: {response.text}", "red"))
            return None
    else:
        # For random, we need to fetch more records and then shuffle
        for chunk in tqdm(property_chunks, desc="Fetching data", total=len(property_chunks)):
            body = {
                "limit": 100,
                "properties": chunk,
                "sorts": [
                    {
                        "propertyName": "createdate",
                        "direction": "ASCENDING"
                    }
                ]
            }
            
            try:
                response = requests.post(url, headers=headers, json=body)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(colored(f"Error fetching sample data for {object_type}: {str(e)}", "red"))
                if response:
                    print(colored(f"Status code: {response.status_code}", "red"))
                    print(colored(f"Response: {response.text}", "red"))
                continue
            
            results = response.json().get('results', [])
            all_results.extend(results)
        
        if all_results:
            random.shuffle(all_results)
    
    return all_results[:100]  # Ensure we return at most 100 results

def extract_sample_data():
    while True:
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
            continue

        sample_type = 'recent' if sample_choice == '1' else 'random'
        
        print(colored(f"Fetching {sample_type} sample data for {selected_object}...", "yellow"))
        sample_data = get_sample_data(selected_object, sample_type)

        if not sample_data:
            print(colored(f"No data found for {selected_object}", "red"))
            continue

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'extract/{selected_object}_sample_{sample_type}_{timestamp}.csv'

        # Collect all possible fields
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

        another = get_user_input("Do you want to extract data for another object? (yes/no):", ['yes', 'no'])
        if another != 'yes':
            break

def extract_sample_data_all_objects():
    objects = get_hubspot_objects()
    if not objects:
        return

    print(colored("Select sample type:", "yellow"))
    print(colored("1. Recent (last 100 records)", "cyan"))
    print(colored("2. Random (100 random records)", "cyan"))

    while True:
        sample_choice = input(colored("Enter your choice (1 or 2): ", "green"))
        if sample_choice in ['1', '2']:
            break
        else:
            print(colored("Invalid choice. Please enter 1 or 2.", "red"))

    sample_type = 'recent' if sample_choice == '1' else 'random'

    for obj in objects:
        print(colored(f"\nExtracting {sample_type} sample data for {obj}...", "yellow"))
        try:
            sample_data = get_sample_data(obj, sample_type)

            if not sample_data:
                print(colored(f"No data found for {obj}", "red"))
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f'extract/{obj}_sample_{sample_type}_{timestamp}.csv'

            # Collect all possible fields
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
            print(colored(f"Error processing {obj}: {str(e)}", "red"))
            continue

    print(colored("Extraction of sample data for all objects completed.", "green"))

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
    while True:
        print(colored("\nWhat do you want to do today?", "yellow"))
        print(colored("1. Extract all the fields name from an object", "blue"))
        print(colored("2. Extract all the fields name from all the objects", "blue"))
        print(colored("3. Extract a data sample from an object", "blue"))
        print(colored("4. Extract a data sample from all the objects", "blue"))
        print(colored("5. Delete records from a CSV file", "blue"))
        print(colored("6. Exit", "blue"))

        action = get_user_input("Enter the number of the action you want to perform:", ['1', '2', '3', '4', '5', '6'])

        if action == '1':
            list_objects_and_fields()
        elif action == '2':
            extract_all_objects_fields()
        elif action == '3':
            extract_sample_data()
        elif action == '4':
            extract_sample_data_all_objects()
        elif action == '5':
            delete_records()
        elif action == '6':
            print(colored("Exiting the program. Goodbye!", "green"))
            break
        else:
            print(colored("Invalid action selected.", "red"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nYou chose to interrupt the script, Good Bye!")
        sys.exit(0)

print(colored("This is the end", "green"))
