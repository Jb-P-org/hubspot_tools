import requests
import csv
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()
API_KEY = os.getenv('HUBSPOT_TOKEN')

# URL de base de l'API HubSpot
base_url = "https://api.hubapi.com/"

# Spécifier les objets que vous voulez extraire (e.g., 'contacts', 'companies')
objects = ['contacts', 'companies', 'deals']

# Fonction pour extraire les champs par objet
def extract_fields(obj):
    url = f"{base_url}crm/v3/properties/{obj}?hapikey={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erreur lors de la récupération des données pour {obj}: {response.status_code}")
        return []
    return response.json()['results']

# Créer et écrire dans le fichier CSV
with open('hubspot_fields.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Object', 'FieldName', 'DataType'])

    for obj in objects:
        fields = extract_fields(obj)
        for field in fields:
            writer.writerow([obj, field['name'], field['fieldType']])

print("Extraction terminée et enregistrée dans 'hubspot_fields.csv'")
