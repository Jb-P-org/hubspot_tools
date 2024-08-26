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

def get_hubspot_objects():
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    # Liste des objets standard connus
    standard_objects = ['contacts', 'companies', 'deals', 'tickets', 'products', 'line_items', 'quotes']
    
    # Get custom objects
    custom_url = "https://api.hubapi.com/crm/v3/schemas"
    custom_response = requests.get(custom_url, headers=headers)
    
    if custom_response.status_code != 200:
        print(f'Error: {custom_response.status_code}')
        print("Error fetching custom objects from HubSpot")
        return None
    
    custom_objects = [obj['name'] for obj in custom_response.json().get('results', [])]
    
    return standard_objects + custom_objects

def get_object_fields(object_name):
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    url = f"https://api.hubapi.com/crm/v3/properties/{object_name}"
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

def main():
    # Folder creation if not exist
    if not os.path.exists("extract"):
        os.makedirs("extract")

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

    action = input(colored("Enter the number of the action you want to perform: ", "green"))

    if action == '1':
        list_objects_and_fields()
    elif action == '2':
        extract_all_objects_fields()
    elif action == '3':
        print(colored("This feature is not implemented yet.", "red"))
    elif action == '4':
        print(colored("This feature is not implemented yet.", "red"))
    else:
        print(colored("Invalid action selected.", "red"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nYou chose to interrupt the script, Good Bye!")
        sys.exit(0)

print(colored("This is the end", "green"))
