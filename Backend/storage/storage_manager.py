import json
import os

def get_app_data_path() -> str:
    """
    Returns the platform-specific, persistent path for application data.
    This ensures data is saved in a reliable location, not a temporary folder.
    """
    app_name = "Finance Board" 
    
    if os.name == 'nt': 
        return os.path.join(os.getenv('APPDATA'), app_name)
    else:
        return os.path.join(os.path.expanduser('~'), '.config', app_name)

class StorageManager:
    def __init__(self):
        """
        Initializes the StorageManager to save data in a persistent app data directory.
        """
        app_data_dir = get_app_data_path()
        self.filepath = os.path.join(app_data_dir, 'ledger_data.json')
        os.makedirs(app_data_dir, exist_ok=True)

    def save_data(self, ledger_manager, transaction_manager, journal_manager, net_worth_manager):
        """Saves the current state of all data to the JSON file."""
        try:
            all_data_to_save = {
                "ledger_entries": [e.to_dict() for e in ledger_manager.get_all_entries()] if ledger_manager else [],
                "transactions": [t.to_dict() for t in transaction_manager.get_all_transactions()] if transaction_manager else [],
                "journal_entries": [j.to_dict() for j in journal_manager.get_all_entries()] if journal_manager else [],
                "net_worth_snapshots": [n.to_dict() for n in net_worth_manager.get_all_snapshots()] if net_worth_manager else [],
            }
            with open(self.filepath, 'w', encoding='utf-8') as json_file:
                json.dump(all_data_to_save, json_file, indent=4)
            print(f"Data successfully saved to {self.filepath}")
        except Exception as e:
            print(f"An unexpected error occurred during saving: {e}")

    def load_data(self) -> dict:
        """Loads all data from the JSON file."""
        empty_data = {
            "ledger_entries": [], 
            "transactions": [],
            "journal_entries": [],
            "net_worth_snapshots": [],
        }
        if not os.path.exists(self.filepath):
            print(f"Data file not found at {self.filepath}. Starting with a fresh session.")
            return empty_data
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip(): return empty_data
                data = json.loads(content)
                for key in empty_data:
                    if key not in data:
                        data[key] = []
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading data from {self.filepath}: {e}. Starting fresh.")
            return empty_data