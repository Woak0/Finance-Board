class TagManager:
    def __init__(self):
        self._standard_tags = [
            "Business", "Cash", "Childcare", "Eating Out & Takeaway", "Education",
            "Entertainment", "Fees & Interest", "Gifts & Donations", "Groceries",
            "Health & Medical", "Home", "Home Loan", "Insurance", "Investments",
            "Personal Care", "Pets", "Professional Services", "Shopping",
            "Sport & Fitness", "Subscriptions", "Tax", "Travel & Holidays",
            "Utilities", "Vehicle & Transport"
        ]
        self._standard_tags.sort()
        self._standard_tags.append("Other (Specify Custom)")

    def get_standard_tags(self) -> list[str]:
        """Returns the list of all standard, pre-defined tags."""
        return self._standard_tags

def handle_edit_tags_ui(item, tag_manager):
    """
    A helper function to manage the command-line UI for editing tags on an item.
    'item' can be a LedgerEntry or a Transaction.
    'tag_manager' is an instance of the TagManager.
    """
    while True:
        current_tags_display = ", ".join(item.tags) if item.tags else "None"
        print(f"\n--- Editing Tags for '{item.label}' ---")
        print(f"  Current Tags: {current_tags_display}")
        print("\n  [1] Add Standard Tag(s)")
        print("  [2] Add Custom Tag(s)")
        print("  [3] Remove a Tag")
        print("  [c] Finish Editing Tags")
        
        tag_choice = input("  Select an option: ")

        if tag_choice == '1':
            standard_tags = tag_manager.get_standard_tags()
            for index, tag_name in enumerate(standard_tags):
                print(f"    [{index + 1}] {tag_name}")
            
            selection_input = input("    Enter numbers of tags to add, separated by commas: ")
            if selection_input:
                chosen_numbers_str = selection_input.split(',')
                for num_str in chosen_numbers_str:
                    try:
                        user_number = int(num_str.strip())
                        if 1 <= user_number <= len(standard_tags):
                            tag_to_add = standard_tags[user_number - 1]
                            if tag_to_add not in item.tags:
                                item.tags.append(tag_to_add)
                                print(f"    Added tag: '{tag_to_add}'")
                            else:
                                print(f"    Warning: Tag '{tag_to_add}' is already present.")
                        else:
                            print(f"    Warning: Invalid number '{user_number}'.")
                    except ValueError:
                        print(f"    Warning: Invalid input '{num_str.strip()}'.")

        elif tag_choice == '2':
            custom_input = input("    Enter custom tags to add, separated by commas: ")
            if custom_input:
                custom_tags_list = [tag.strip() for tag in custom_input.split(',')]
                for custom_tag in custom_tags_list:
                    if custom_tag:
                        formatted_tag = f"other:{custom_tag}"
                        if formatted_tag not in item.tags:
                            item.tags.append(formatted_tag)
                            print(f"    Added custom tag: '{formatted_tag}'")
                        else:
                            print(f"    Warning: Tag '{formatted_tag}' is already present.")

        elif tag_choice == '3':
            if not item.tags:
                print("    There are no tags to remove.")
                continue
            
            for index, tag_name in enumerate(item.tags):
                print(f"    [{index + 1}] {tag_name}")
            
            removal_input = input("    Enter number of the tag to remove: ")
            try:
                user_number = int(removal_input.strip())
                if 1 <= user_number <= len(item.tags):
                    removed_tag = item.tags.pop(user_number - 1)
                    print(f"    Removed tag: '{removed_tag}'")
                else:
                    print("    Warning: Invalid number.")
            except ValueError:
                print("    Warning: Not a valid number.")

        elif tag_choice.lower() == 'c':
            print("  Finished editing tags.")
            break
        else:
            print("  Invalid choice.")