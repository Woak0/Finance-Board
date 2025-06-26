import os
import json

def get_config_path() -> str:
    """Returns the platform-specific path for the config file."""
    app_name = "FinancialCoPilot"
    if os.name == 'nt': 
        return os.path.join(os.getenv('APPDATA'), app_name)
    else:
        return os.path.join(os.path.expanduser('~'), '.config', app_name)

def load_config() -> dict:
    """Loads the config.json file, returning its content or an empty dict."""
    config_dir = get_config_path()
    config_file = os.path.join(config_dir, 'config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

def save_config(config_data: dict):
    """Saves the given dictionary to config.json."""
    config_dir = get_config_path()
    os.makedirs(config_dir, exist_ok=True)
    config_file = os.path.join(config_dir, 'config.json')
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=4)