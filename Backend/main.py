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
            Debt_Manager.add_debt(label=debt_label, amount=amount)

        elif choice == '2':
            pass
            print("\n-> Make Payment")
            
        elif choice == '3':
            pass
            print("\n-> Show Summary")

        elif choice == '4':
            print("\n--- Listing all Debt Entries ---")
            all_debts = Debt_Manager.get_all_debts()

            if not all_debts:
                print("No debts recorded.")
            else:
                for debt in all_debts:
                    short_debt_id = debt.id[:8]
                    date_str = debt.date_incurred.strftime("%Y-%m-%d")
                    print(f"ID: {short_debt_id} | Date: {date_str} | label: {debt.label} | Amount: ${debt.amount:.2f}")

            print("\n--- Listing all Payment Entries---")
            all_payments = Payment_Manager.get_all_payments()

            if not all_payments:
                print("No payments recorded.")
            else:
                for payment in all_payments:
                    short_debt_id_for_payment = payment.debt_id[:8]
                    date_str_payment = payment.date_paid.strftime("%Y-%m-%d")
                    print(f"  Date: {date_str_payment} | Paid ${payment.amount:7.2f} towards Debt ID {short_debt_id_for_payment} (Label: {payment.label})")

        elif choice.lower() == 'q':
            print("Quitting and Saving application...")
            break
        else:
            print("\nInvalid choice. Please enter a valid option.")

    

        #Test scenario

        new_debt = Debt_Manager.add_debt(label = "Coffee",amount = 5)

        new_payment = Payment_Manager.add_payment(debt_id=new_debt.id, amount = 3)

        total_debt_incurred = calculate_total_debt_incurred(all_debts)
        total_amount_paid = calculate_total_amount_paid(all_payments)
        overall_remaining_balance = calculate_overall_remaining_balance(total_debt_incurred, total_amount_paid)

    print("\n--- Current Summary ---")
    print(f"Total Debt Incurred: ${total_debt_incurred:.2f}")
    print(f"Total Amount Paid: ${total_amount_paid:.2f}")
    print(f"Overall Remaining Balance: ${overall_remaining_balance:.2f}")

    print("\n--- Saving Data ---")
    StorageMana.save_data(debt_manager=Debt_Manager, payment_manager=Payment_Manager)




if __name__ == "__main__":
    main()