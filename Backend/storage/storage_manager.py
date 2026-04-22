import json
import os
import shutil
import glob
from datetime import datetime

MAX_AUTO_BACKUPS = 5

def get_app_data_path() -> str:
    """Returns the platform-specific, persistent path for application data."""
    app_name = "Finance Board"
    if os.name == 'nt':
        return os.path.join(os.getenv('APPDATA'), app_name)
    else:
        return os.path.join(os.path.expanduser('~'), '.config', app_name)

class StorageManager:
    def __init__(self):
        app_data_dir = get_app_data_path()
        self.filepath = os.path.join(app_data_dir, 'ledger_data.json')
        self.backup_dir = os.path.join(app_data_dir, 'backups')
        os.makedirs(app_data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

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
        except Exception as e:
            print(f"Error saving data: {e}")

    def load_data(self) -> dict:
        """Loads all data from the JSON file."""
        empty_data = {
            "ledger_entries": [],
            "transactions": [],
            "journal_entries": [],
            "net_worth_snapshots": [],
        }
        if not os.path.exists(self.filepath):
            return empty_data
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return empty_data
                data = json.loads(content)
                for key in empty_data:
                    if key not in data:
                        data[key] = []
                return data
        except (json.JSONDecodeError, IOError):
            return empty_data

    def create_auto_backup(self):
        """Creates a timestamped backup and removes old ones beyond MAX_AUTO_BACKUPS."""
        if not os.path.exists(self.filepath):
            return
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(self.backup_dir, f"auto_backup_{timestamp}.json")
        try:
            shutil.copy2(self.filepath, backup_path)
            self._prune_auto_backups()
        except Exception as e:
            print(f"Error creating auto-backup: {e}")

    def _prune_auto_backups(self):
        """Keeps only the most recent MAX_AUTO_BACKUPS auto-backups."""
        pattern = os.path.join(self.backup_dir, "auto_backup_*.json")
        backups = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        for old_backup in backups[MAX_AUTO_BACKUPS:]:
            try:
                os.remove(old_backup)
            except OSError:
                pass

    def create_manual_backup(self, destination_path: str) -> bool:
        """Creates a backup at a user-specified location. Returns True on success."""
        if not os.path.exists(self.filepath):
            return False
        try:
            shutil.copy2(self.filepath, destination_path)
            return True
        except Exception:
            return False

    def restore_from_backup(self, backup_path: str) -> bool:
        """Restores data from a backup file. Returns True on success."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Validate structure
            required_keys = ["ledger_entries", "transactions"]
            if not any(key in data for key in required_keys):
                return False
            # Backup current data before restoring
            self.create_auto_backup()
            shutil.copy2(backup_path, self.filepath)
            return True
        except (json.JSONDecodeError, IOError, KeyError):
            return False

    def get_backup_list(self) -> list[dict]:
        """Returns a list of available backups with metadata."""
        backups = []
        pattern = os.path.join(self.backup_dir, "*.json")
        for path in sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True):
            size = os.path.getsize(path)
            modified = datetime.fromtimestamp(os.path.getmtime(path))
            backups.append({
                "path": path,
                "filename": os.path.basename(path),
                "size_kb": round(size / 1024, 1),
                "date": modified,
            })
        return backups
