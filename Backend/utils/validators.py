def get_string_input(prompt: str, allow_empty: bool = False) -> str | None:
    """
    Prompts the user for a string, handles cancellation, and optionally allows empty input.
    Returns the string or None if cancelled.
    """
    while True:
        user_input = input(f"{prompt} (or 'c' to cancel): ")
        if user_input.lower() == 'c':
            print("Operation cancelled.")
            return None
        
        if allow_empty or user_input.strip():
            return user_input
        else:
            print("Input cannot be empty. Please try again.")

def get_positive_float_input(prompt: str) -> float | None:
    """
    Prompts the user for a positive float, handles errors, and allows cancellation.
    Returns the float or None if cancelled.
    """
    while True:
        user_input = input(f"{prompt} (or 'c' to cancel): ")
        if user_input.lower() == 'c':
            print("Operation cancelled.")
            return None
        try:
            value = float(user_input)
            if value > 0:
                return value
            else:
                print("Error: Amount must be a positive number.")
        except ValueError:
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