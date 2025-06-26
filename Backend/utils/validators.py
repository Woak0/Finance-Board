def get_string_input(prompt: str, allow_empty: bool = False, default_value: str | None = None) -> str | None:
    """
    Prompts the user for a string, handles cancellation, allows a default value, 
    and optionally allows empty input. Returns the string or None if cancelled.
    """
    prompt_with_default = f"{prompt} [{default_value}]" if default_value else prompt
    
    while True:
        user_input = input(f"{prompt_with_default} (or 'c' to cancel): ")
        
        if user_input.lower() == 'c':
            print("Operation cancelled.")
            return None
        
        if default_value and not user_input:
            return default_value
        
        if allow_empty or user_input.strip():
            return user_input
        else:
            print("Input cannot be empty. Please try again.")

def get_positive_float_input(prompt: str, default_value: str | None = None) -> float | None:
    """
    Prompts for a positive float, handles errors, allows a default, and cancellation.
    Returns the float or None if cancelled.
    """
    prompt_with_default = f"{prompt} [{default_value}]" if default_value else prompt

    while True:
        user_input = input(f"{prompt_with_default} (or 'c' to cancel): ")
        
        if user_input.lower() == 'c':
            print("Operation cancelled.")
            return None
        
        if default_value and not user_input:
            input_to_process = default_value
        else:
            input_to_process = user_input
            
        try:
            value = float(input_to_process)
            if value > 0:
                return value
            else:
                print("Error: Amount must be a positive number.")
        except (ValueError, TypeError):
            print("Error: Invalid number. Please try again.")

def get_comma_separated_tags(prompt: str) -> list[str] | None:
    """Gets comma-separated input, handles cancellation, and returns a cleaned list."""
    user_input = input(f"{prompt} (or 'c' to cancel): ")
    if user_input.lower() == 'c':
        print("\nOperation cancelled.")
        return None
    if not user_input:
        return []
    tags = [tag.strip() for tag in user_input.split(',')]
    return [tag for tag in tags if tag]