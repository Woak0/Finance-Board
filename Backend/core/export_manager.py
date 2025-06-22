import os
import csv
from datetime import datetime
from Backend.core.ledger_manager import LedgerEntry, LedgerManager
from Backend.core.transaction_manager import Transaction, TransactionManager

def export_data_to_csv(ledger_manager, transaction_manager):
    os.makedirs("Exports", exist_ok=True)

    output_dir = "Exports"

    datetime_now = datetime.now()
    formatted_datetime = datetime_now.strftime("%Y-%m-%d_%H-%M-%S")

    ledger_filename = f"ledger_entries_{formatted_datetime}.csv"
    transaction_filename = f"transaction_entries_{formatted_datetime}.csv"

    ledger_filepath = os.path.join(output_dir, ledger_filename)
    transaction_filepath = os.path.join(output_dir, transaction_filename)

    print(ledger_filepath)
    print(transaction_filepath)


    Ledger_Headers = ['id', 'label', 'amount', 'entry_type', 'status', 'date_incurred', 'comments', 'tags']

    all_ledger_entries = ledger_manager.get_all_entries()

    with open(ledger_filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(Ledger_Headers)
        for entry in all_ledger_entries:
            row_data = [
                entry.id,
                entry.label,
                entry.amount,
                entry.entry_type,
                entry.status,
                entry.date_incurred.isoformat(),
                entry.comments if entry.comments is not None else "",
                ", ".join(entry.tags)
            ]

            writer.writerow(row_data)

    Transaction_Headers = ['id', 'entry_id', 'transaction_type', 'label', 'amount', 'date_paid', 'comments', 'tags']

    all_transactions = transaction_manager.get_all_transactions()

    with open(transaction_filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(Transaction_Headers)
        for transaction in all_transactions:
            row_data = [
                transaction.id,
                transaction.entry_id,
                transaction.transaction_type,
                transaction.label,
                transaction.amount,
                transaction.date_paid.isoformat(),
                transaction.comments if entry.comments is not None else "",
                ", ".join(transaction.tags)
            ]

            writer.writerow(row_data)



    
