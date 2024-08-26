# Hubspot Tools

## Author

Par Jb-P https://jb-p.fr - Jean-Baptiste Ronssin - @jbronssin

GitHub Repository: https://github.com/Jb-P-org/hubspot_tools

## What is this?

This is a versatile script designed to assist Hubspot administrators, consultants, and power users in managing their Hubspot data. It provides various functionalities including field extraction and bulk record deletion.

## Features

- Extract field names from a specific Hubspot object
- Extract field names from all Hubspot objects
- Delete records in bulk for any Hubspot object type
- User-friendly command-line interface
- Error handling and logging

## How to use it?

1. Clone the repository
2. Install the requirements by running `sh pythonstarter.sh` in your terminal (this will install all the necessary tools to run the script)
3. At the end of the installation, you'll be prompted to enter your Hubspot API key. You can find it in your Hubspot account under `Settings` -> `Account Setup` -> `Integrations` -> `Private Apps`.
4. Run the script by executing `python3 hubspot_tools.py` in your terminal

Note: You can interrupt the script at any time by pressing Ctrl+C.

## Folder Structure

The script will create the following folders if they don't exist:

- `extract`: Contains CSV files with extracted field information
- `delete`: Place CSV files containing record IDs to be deleted here
- `errors`: Contains error logs from deletion operations

## CSV File Naming for Deletion

When deleting records, name your CSV files according to the object type, e.g., `contacts.csv`, `companies.csv`, `deals.csv`, etc. The script will recognize both singular and plural forms (e.g., both `contact.csv` and `contacts.csv` will work for contacts).

## How to contribute?

Contributions are welcome! Feel free to add new features, fix bugs, or improve documentation. You can also contact me if you have any questions or suggestions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. This means you can use, modify, and distribute the code freely, but I'm not liable for any consequences of its use. If you create something cool with it, I'd love to hear about it! However, please don't use it for commercial purposes without permission.

Don't forget to star the project if you find it helpful!
