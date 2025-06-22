import json
import os

class StorageManager:
    def __init__(self, filepath='Backend/data/ledger_data.json'): 
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def save_data(self, ledger_manager, transaction_manager, journal_manager, net_worth_manager):
        """Saves the current state of all data to the JSON file."""
        try:
            all_data_to_save = {
                "ledger_entries": [e.to_dict() for e in ledger_manager.get_all_entries()],
                "transactions": [t.to_dict() for t in transaction_manager.get_all_transactions()],
                "journal_entries": [j.to_dict() for j in journal_manager.get_all_entries()],
                "net_worth_snapshots": [n.to_dict() for n in net_worth_manager.get_all_snapshots()],
            }
            with open(self.filepath, 'w') as json_file:
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
        if not os.path.exists(self.filepath): return empty_data
        try:
            with open(self.filepath, 'r') as f:
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