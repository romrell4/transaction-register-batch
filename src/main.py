import requests
from bs4 import BeautifulSoup

from database import DB
from transaction import TransactionFactory, PaymentType, StopException

def run():
    global CATEGORIES
    global PREDICTIONS
    # Load the categories needed to validate the category ids
    CATEGORIES = requests.get("https://transaction-register.herokuapp.com/categories/active").json()
    PREDICTIONS = requests.get("https://transaction-register.herokuapp.com/categories/predictions").json()

    # Load the json db into memory
    DB.load()

    # Gather the account data from the HTML page, then allow the user to enter the correct data (updating the in memory db along the way)
    try:
        run_account(PaymentType.CREDIT)
        run_account(PaymentType.DEBIT)
        run_account(PaymentType.SAVINGS)
        run_account(PaymentType.PERMANENT_SAVINGS)
    except:
        pass

    # Save the in memory db back to a json file
    DB.save()

def run_account(account_type):
    # Gather information from HTML and create Transaction objects
    txs = []
    for row in reversed(get_rows(account_type.name.lower())):
        tx = TransactionFactory.create_transaction(account_type, row.find_all("td"))
        if tx is not None:
            txs.append(tx)

    # Loop through transactions and allow the user to modify before saving
    for tx in txs:
        # Keep looping until the user is satisfied with the transaction
        finished = False
        while not finished:
            # This will prompt the user for updates to the transaction
            if tx.verify(CATEGORIES, PREDICTIONS):
                # The user made all the changes they wanted. Ask if they are ready to send the transaction as is
                if input("{}\nCreate this transaction? (n) ".format(tx)).startswith("y"):
                    tx.save()
                    finished = True
            else:
                # The user said that they didn't want to add the transaction
                finished = True

def get_rows(filename):
    with open("../res/html/{}.htm".format(filename)) as f:
        html = BeautifulSoup(f, "html.parser")
    table = html.find("table", "transaction-expand-collapse").find("tbody")
    rows = table.find_all("tr", "detailed-transaction")
    rows = [row for row in rows if len(row.find("td").contents) != 0]
    return rows

if __name__ == "__main__":
    run()
