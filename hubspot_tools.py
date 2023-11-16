import requests
import csv
import os
import glob
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from termcolor import colored
import sys

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

print(colored("HubSpot Tools", "green"))
print(colored("Par Jb-P https://jb-p.fr - Jean-Baptiste Ronssin - @jbronssin", "blue"))
print(colored("https://github.com/Jb-P-org/hubspot_tools", "blue"))
print("###############################################")
print(colored("You can interupt the script when you want by pressing Ctrl+C", "red"))
print("###############################################")
print(colored("This script will create a folder named 'extract' in the same folder as the script", "yellow"))
print("###############################################")

def main():
    
    # Folder creation if not exist
    if not os.path.exists("extract"):
        os.makedirs("extract")
    
    load_dotenv()
    TOKEN = os.environ["HUBSPOT_TOKEN"]

    # Check if the .env file is present and the API key is set
    if not TOKEN:
        print(" ")
        print(" ")
        print("###############################################")
        print(" ")
        print("¯\_(ツ)_/¯")
        print(" ")
        print(colored("It seems you have not set your Hubspot API key in the .env file or the .env file is missing.", "red", attrs=["blink"]))
        print(colored("Please read the README and follow the process to set up your Hubspot API key.", "blue"))
        sys.exit(0)

    HUBSPOT_API_URL = "https://api.hubapi.com"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }

    # Make the user choose the action to perform
    print(colored("What do you want to do today?", "yellow"))
    print(colored("1. Extract all the fields name from an object", "blue"))
    print(colored("2. Extract all the fields name from all the objects", "blue"))
    print(colored("3. Extract a data sample from an object", "blue"))
    print(colored("4. Extract a data sample from all the objects", "blue"))

    action = input("Enter the number of the action you want to perform: ")


    # 1. Extract all the fields name from an object

    # 2. Extract all the fields name from all the objects

    # 3. Extract a data sample from an object

    # 4. Extract a data sample from all the objects


pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nYou chose to interrupt the script, Good Bye!")
        sys.exit(0)

print(colored("This is the end", "green"))