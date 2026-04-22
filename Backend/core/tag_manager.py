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
