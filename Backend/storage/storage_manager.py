import json
import os

class StorageManager:
    def __init__(self, filepath='Backend/data/debt_data.json'):
        self.filepath = filepath

        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def save_data(self, debt_manager, payment_manager):
        try:
            # ---- Debts ----
            all_debt_objects = debt_manager.get_all_debts()

            debts_data_to_save = []

            for debt_object in all_debt_objects:
                debt_dictionary = debt_object.to_dict()

                debts_data_to_save.append(debt_dictionary)

            # ---- Payments ----
            all_payment_objects = payment_manager.get_all_payments()

            payments_data_to_save = []

            for payment_objects in all_payment_objects:
                payment_dictionary = payment_objects.to_dict()

                payments_data_to_save.append(payment_dictionary)

            all_data_to_save = {
                "debts" : debts_data_to_save,
                "payments" : payments_data_to_save
            }

            with open(self.filepath, 'w', indent=None) as json_file:
                json.dump(all_data_to_save, json_file, indent=4)

                print(f"Data successfully saved to {self.filepath}")

        except IOError as e:
            print (f"Error saving data to {self.filepath}: {e}")
        except Exception as e:
            print(f"An unexpected error occured during saving: {e}")

    def load_data(self) -> dict:
        if not os.path.exists(self.filepath):
            print(f"Data file {self.filepath} not found. Starting with no data.")
            return ({"debts": [], "payments":[]})
            
    
        try:
            with open(self.filepath, 'r') as json_file:
                file_content = json_file.read()
                
                if not file_content.strip():
                    print(f"Data file '{self.filepath}' is empty. Starting with empty data.")
                    return ({"debts": [], "payments":[]})
                
                json_file.seek(0)

                loaded_data = json.load(json_file)

                print(f"Data successfully loaded from '{self.filepath}'.")

                if "debts" not in loaded_data:
                    print("Warning: 'debts' key missing in loaded data. Defaulting to empty list.")
                    loaded_data["debts"] = []
                if "payments" not in loaded_data:
                    print("Warning: 'payments' key missing in loaded data. Defaulting to empty list.")
                    loaded_data["payments"] = []

                return loaded_data
            print(f"Data successfully saved to {self.filepath}")
            
        except json.JSONDecodeError:
            print(f"Error decoding JSON from '{self.filepath}'. FIle might be corrupted. Starting with empty data.")
            return ({"debts": [], "payments":[]})
        except IOError as e:
            print(f"Could not read file '{self.filepath}': {e}. Starting with empty data.")
            return ({"debts": [], "payments":[]})
        except Exception as e:
            print(f"An unexpected error occured while loading data: {e}. Starting with empty data.")
            return ({"debts": [], "payments":[]})