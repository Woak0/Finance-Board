import json
import os

class StorageManager:
    def __init__(self, filepath='Backend/data/ledger_data.json'): 
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def save_data(self, ledger_manager, transaction_manager):
        """Saves the current state of entries and transactions to the JSON file."""
        try:
            all_entries = ledger_manager.get_all_entries()
            entries_to_save = [entry.to_dict() for entry in all_entries]

            all_transactions = transaction_manager.get_all_transactions()
            transactions_to_save = [transaction.to_dict() for transaction in all_transactions]

            all_data_to_save = {
                "ledger_entries": entries_to_save,
                "transactions": transactions_to_save
            }

            with open(self.filepath, 'w') as json_file:
                json.dump(all_data_to_save, json_file, indent=4)
            print(f"Data successfully saved to {self.filepath}")

        except IOError as e:
            print(f"Error saving data to {self.filepath}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during saving: {e}")

    def load_data(self) -> dict:
        """Loads entries and transactions from the JSON file."""
        empty_data = {"ledger_entries": [], "transactions": []}

        if not os.path.exists(self.filepath):
            print(f"Data file {self.filepath} not found. Starting with empty data.")
            return empty_data
        
        try:
            with open(self.filepath, 'r') as json_file:
                file_content = json_file.read()
                
                if not file_content.strip():
                    print(f"Data file '{self.filepath}' is empty. Starting with empty data.")
                    return empty_data
                
                json_file.seek(0)
                loaded_data = json.load(json_file)
                print(f"Data successfully loaded from '{self.filepath}'.")

                if "ledger_entries" not in loaded_data and "debts" in loaded_data:
                    print("Found old 'debts' key. Migrating to 'ledger_entries'.")
                    loaded_data["ledger_entries"] = loaded_data.pop("debts")
                
                if "transactions" not in loaded_data and "payments" in loaded_data:
                    print("Found old 'payments' key. Migrating to 'transactions'.")
                    loaded_data["transactions"] = loaded_data.pop("payments")
                
                if "ledger_entries" not in loaded_data:
                    loaded_data["ledger_entries"] = []
                if "transactions" not in loaded_data:
                    loaded_data["transactions"] = []

                return loaded_data
            
        except json.JSONDecodeError:
            print(f"Error decoding JSON from '{self.filepath}'. File might be corrupt. Starting with empty data.")
            return empty_data
        except IOError as e:
            print(f"Could not read file '{self.filepath}': {e}. Starting with empty data.")
            return empty_data
        except Exception as e:
            print(f"An unexpected error occurred while loading data: {e}. Starting with empty data.")