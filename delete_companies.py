import os
import csv
import json
from dotenv import load_dotenv
import requests
from tqdm import tqdm
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get HubSpot API token from environment variables
HUBSPOT_TOKEN = os.getenv('HUBSPOT_TOKEN')

# HubSpot API base URL
BASE_URL = 'https://api.hubapi.com/crm/v3/objects/companies/batch/archive'

def delete_companies_batch(company_ids):
    """Delete a batch of companies from HubSpot."""
    headers = {
        'Authorization': f'Bearer {HUBSPOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "inputs": [{"id": id} for id in company_ids]
    }
    response = requests.post(BASE_URL, headers=headers, json=payload)
    return response.status_code == 204, response.status_code, response.text

def main():
    csv_path = "companies_to_delete.csv"

    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: The file '{csv_path}' does not exist.")
        return

    # Read the CSV file and extract Record IDs
    company_ids = []
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'Record ID' in row:
                company_ids.append(row['Record ID'])
            else:
                print("Error: 'Record ID' column not found in the CSV.")
                return

    # Display the number of companies to delete and ask for confirmation
    total_companies = len(company_ids)
    print(f"Number of companies to delete: {total_companies}")
    confirmation = input("Are you sure you want to delete these companies? (yes/no): ")

    if confirmation.lower() != 'yes':
        print("Operation cancelled.")
        return

    # Delete the companies in batches
    batch_size = 100  # HubSpot allows up to 100 objects per batch request
    success_count = 0
    errors = []

    with tqdm(total=total_companies, desc="Deleting companies") as pbar:
        for i in range(0, total_companies, batch_size):
            batch = company_ids[i:i+batch_size]
            success, status_code, response_text = delete_companies_batch(batch)
            if success:
                success_count += len(batch)
                pbar.update(len(batch))
            else:
                errors.append({
                    'Batch': f"{i}-{i+len(batch)}",
                    'Status Code': status_code,
                    'Error Message': response_text
                })
                pbar.update(len(batch))

    print(f"\nOperation completed. {success_count}/{total_companies} companies successfully deleted.")

    # Create a CSV file with errors if necessary
    if errors:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = f"deletion_errors_{timestamp}.csv"
        with open(error_file, 'w', newline='') as csvfile:
            fieldnames = ['Batch', 'Status Code', 'Error Message']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for error in errors:
                writer.writerow(error)
        print(f"Errors have been recorded in the file '{error_file}'.")

if __name__ == "__main__":
    main()
