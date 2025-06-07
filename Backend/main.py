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
            pass
            print("\n-> Add Debt")
        elif choice == '2':
            pass
            print("\n-> Make Payment")
        elif choice == '3':
            pass
            print("\n-> Show Summary")
        elif choice == '4':
            pass
            print("\n-> List all Entries")
        elif choice.lower() == 'q':
            print("Quitting and Saving application...")
            break
        else:
            print("\nInvalid choice. Please enter a valid option.")

    

        #Test scenario

        new_debt = Debt_Manager.add_debt(label = "Coffee",amount = 5)

        new_payment = Payment_Manager.add_payment(debt_id=new_debt.id, amount = 3)

        all_debts = Debt_Manager.get_all_debts()
        all_payments = Payment_Manager.get_all_payments()

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