from Backend.core.debt_manager import Debt, DebtManager
from Backend.core.payment_manager import Payment, PaymentManager
from Backend.storage.storage_manager import StorageManager
from Backend.core.summary_calculator import *

def main():
    StorageMana = StorageManager()
    Debt_Manager = DebtManager()
    Payment_Manager = PaymentManager()

    All_Data = StorageMana.load_data()
    list_of_debt_dicts = All_Data["debts"]
    list_of_payments_dicts = All_Data["payments"]


    Hydrated_debts = [Debt.from_dict(debt) for debt in list_of_debt_dicts]
    Hydrated_Payments = [Payment.from_dict(payment) for payment in list_of_payments_dicts]


    Debt_Manager.debts = Hydrated_debts
    Payment_Manager.payments = Hydrated_Payments

    print("Welcome to your Debt Tracker!")
    print(f"Loaded {len(Debt_Manager.debts)} debt entries and {len(Payment_Manager.payments)} payment entries.")

    while True:
        print("\n--- Main Menu ---")

        print("[1] Add a new debt")
        print("[2] Make a payment")
        print("[3] Show summary")
        print("[4] List all entries")
        print("[5] Clear all saved data")
        print("[q] Quit and Save")

        choice = input("Enter your choice: ")

        if choice == '1':
            print("\n--- Add New Debt ---")
            debt_label = input("Enter debt name: ")

            while True:
                amount_str = input("Enter the amount: ")
                try:
                    amount = float(amount_str)
                    break
                except ValueError:
                    print("Invalid amount. Please enter a valid number (e.g., 50.75).")
            print(f"You entered a valid amount: {amount}")

            user_comment = input("Enter any comments (Optional, Enter to skip): ")
            comments_to_save = user_comment if user_comment else None

            Debt_Manager.add_debt(label=debt_label, amount=amount, comments=comments_to_save)

        elif choice == '2':
            print("\n--- Make Payment---")
            all_debts = Debt_Manager.get_all_debts()

            if not all_debts:
                print("There are no debts to make a payment on.\nReturning to main menu.")
                continue

            for debt in all_debts:
                short_debt_id = debt.id[:8]
                date_str = debt.date_incurred.strftime("%Y-%m-%d")
                print(f"ID: {short_debt_id} | Date: {date_str} | label: {debt.label} | Amount: ${debt.amount:.2f}")
            
            target_short_id = input("Enter the 8-character ID of the debt to pay: ")

            if target_short_id.lower() == 'c':
                continue

            target_debt = None

            for debt in all_debts:
                if debt.id.startswith(target_short_id):
                    target_debt = debt
                    break
            if target_debt is None:
                print("Error: No debt found with that ID.")
                continue

            while True:
                amount_str = input(f"Enter the amount to pay towards '{target_debt.label}': ")
                try:
                    amount = float(amount_str)
                    break
                except ValueError:
                    print("Invalid amount. Please enter a valid number (e.g., 50.75).")
            print(f"You entered a valid amount: {amount}\n Making payment of ${amount}")

            user_comment = input("Enter any comments (Optional, Enter to skip): ")
            comments_to_save = user_comment if user_comment else None

            Payment_Manager.add_payment(debt_id = target_debt.id, amount=amount, label=target_debt.label, comments=comments_to_save)

            all_payments_updated = Payment_Manager.get_all_payments()

            new_balance = calculate_remaining_balance_for_specific_debt(target_debt, all_payments_updated)

            if new_balance <= 0:
                target_debt.status = "paid"
                print(f"\n--- Congratulations! Debt '{target_debt.label}' has been paid off! ---")


        elif choice == '3':
            print("\n--- Showing Summary---")

            current_debts = Debt_Manager.get_all_debts()
            current_payments = Payment_Manager.get_all_payments()

            total_debt_incurred = calculate_total_debt_incurred(current_debts)
            total_payments = calculate_total_amount_paid(current_payments)

            Overall_balance = calculate_overall_remaining_balance(total_debt_incurred=total_debt_incurred, total_amount_paid=total_payments)

            print(f"Total Debt Incurred: ${total_debt_incurred:.2f}")
            print(f"Total Payments Made: ${total_payments:.2f}")
            print("-------------------------")
            print(f"Overall Balance:     ${Overall_balance:.2f}")

        elif choice == '4':
            print("\n--- Listing all Debt Entries ---")
            all_debts = Debt_Manager.get_all_debts()
            all_payments = Payment_Manager.get_all_payments()

            if not all_debts:
                print("No debts recorded.")
            else:
                for debt in all_debts:
                    short_debt_id = debt.id[:8]
                    date_str = debt.date_incurred.strftime("%Y-%m-%d")
                    status_display_text = ""

                    if debt.status == "paid":
                        status_display_text = "[Paid]"
                    else:
                        status_display_text = "[Active]"

                    print(f"Status: {status_display_text} | ID: {short_debt_id} | Date: {date_str} | label: {debt.label} | Amount: ${debt.amount:.2f}")
                    if debt.comments:
                        print(f"      -> Comments: {debt.comments}")

                    if debt.status == "active":
                        eta_string = calculate_smart_eta(debt, all_payments)

                        print(f"      -> {eta_string}")

            print("\n--- Listing all Payment Entries---")

            if not all_payments:
                print("No payments recorded.")
            else:
                for payment in all_payments:
                    short_debt_id_for_payment = payment.debt_id[:8]
                    date_str_payment = payment.date_paid.strftime("%Y-%m-%d")
                    print(f"  Date: {date_str_payment} | Paid ${payment.amount:7.2f} towards Debt ID {short_debt_id_for_payment} (Label: {payment.label})")
                
                    if payment.comments:
                        print(f"      -> Comments: {payment.comments}")
        
        elif choice == '5':
            print("WARNING!!! YOU ARE ABOUT TO DELETE ALL SAVED DATA! TO CONFIRM, PLEASE TYPE: DELETE")
            keyword = input("Type DELETE to confirm or Enter any value to cancel: ")

            if keyword == 'DELETE':
                Debt_Manager.debts.clear()
                Payment_Manager.payments.clear()
                print("Successfully deleted all debt and payment history.")
            else:
                print("Cancelling...")
                continue

        elif choice.lower() == 'q':
            print("Quitting and Saving application...")
            break
        else:
            print("\nInvalid choice. Please enter a valid option.")

    print("\n--- Saving Data---")
    StorageMana.save_data(debt_manager=Debt_Manager, payment_manager=Payment_Manager)
    print("Goodbye!")

if __name__ == "__main__":
    main()