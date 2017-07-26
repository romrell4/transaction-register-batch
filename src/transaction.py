from database import DB
from enum import Enum
from datetime import datetime
from decimal import Decimal, InvalidOperation

import json
import requests
import re

DATE_LAG = 2
CREDIT_BUSINESS_LENGTH = 25
VISA_ID_LENGTH = 18

class TransactionFactory:
    @classmethod
    def create_transaction(cls, account_type, cells):
        if account_type == PaymentType.CREDIT:
            purchase_date = datetime.strptime(cls.clean_cell(cells[2]), "%m/%d/%y")
            full_business = cls.clean_cell(cells[3])
            short_business = cells[3].text.lstrip()[:CREDIT_BUSINESS_LENGTH].rstrip().upper()
            tx_id = full_business[-VISA_ID_LENGTH:]
            amount = cls.get_amount(cells[4])

            # Remove txs already added or too recent (since they might change order in the next day or two)
            if DB.is_visa_tx_completed(tx_id) or (datetime.today() - purchase_date).days < DATE_LAG:
                return None
            return Transaction(account_type, purchase_date, full_business, short_business, amount, tx_id)
        else:
            purchase_date = datetime.strptime(cls.clean_cell(cells[1]), "%m/%d/%y")
            business = cls.clean_cell(cells[2])
            amount = cls.get_amount(cells[4]) - cls.get_amount(cells[3])
            tx_id = "{}|{}|{}".format(purchase_date, business, amount)

            if DB.is_account_tx_completed(tx_id):
                return None
            return Transaction(account_type, purchase_date, business, business, amount, tx_id)

    @classmethod
    def get_amount(cls, cell):
        try:
            return Decimal(re.sub(r'[^-\d.]', '', cls.clean_cell(cell).replace("+", "-")))
        except InvalidOperation:
            return 0

    @staticmethod
    def clean_cell(cell):
        # Remove all excess whitespace
        return re.sub("\s+", " ", cell.text).strip()

class Transaction:
    def __init__(self, payment_type, purchase_date, full_business, business, amount, tx_id):
        self.payment_type = payment_type
        self.purchase_date = purchase_date
        self.full_business = full_business
        self.business = business
        self.amount = amount
        self.tx_id = tx_id
        self.category_id = None
        self.category_name = None
        self.description = None

    def verify(self, categories, predictions):
        print(self)
        answer = input("Is this transaction already added? (n) ").lower()
        if answer.startswith("y"):
            if self.payment_type == PaymentType.CREDIT:
                DB.put_completed_visa_tx_id(self.tx_id)
            else:
                DB.put_completed_account_tx_id(self.tx_id)
            return False
        elif answer == "quit":
            DB.save()
            raise StopException()
        self.verify_business()
        self.verify_category(categories, predictions)
        self.description = self._verify("Description", None)
        print(self)
        return True

    def verify_business(self):
        default_value = DB.get_business(self.business)
        business = self._verify("Business", default_value)

        # If they modified the business, update the database
        if business != default_value:
            DB.put_business(self.business, business)
        self.business = business

    def verify_category(self, categories, predictions):
        default_category_id = next(iter([pred["predictedCategoryId"] for pred in predictions if pred["businessName"] == self.business]), 0)
        default_category_name = next(iter([category["name"] for category in categories if category["categoryId"] == default_category_id]), "")

        category = None
        while category is None:
            category_name = self._verify("Category Name", default_category_name)
            category = next(iter([category for category in categories if category["name"].upper() == category_name.upper()]), None)
        self.category_id = category["categoryId"]
        self.category_name = category["name"]

    @staticmethod
    def _verify(field_name, default_value):
        prompt = "{}{}: ".format(field_name, ("" if default_value is None or default_value is "" else " ({})".format(default_value)))
        input_value = input(prompt)
        return input_value if input_value is not "" else default_value

    def save(self):
        response = requests.post("https://transaction-register.herokuapp.com/transactions", json = self.to_dict())
        if response.status_code == 200:
            if self.payment_type == PaymentType.CREDIT:
                DB.put_completed_visa_tx_id(self.tx_id)
            else:
                DB.put_completed_account_tx_id(self.tx_id)

    def to_dict(self):
        return {
            "wfTxId": self.tx_id,
            "paymentType": self.payment_type.name,
            "purchaseDate": self.purchase_date.strftime("%m/%d/%Y %H:%M:%S"),
            "fullBusiness": self.full_business,
            "business": self.business,
            "amount": str(self.amount),
            "categoryId": self.category_id,
            "categoryName": self.category_name,
            "description": self.description
        }

    def __str__(self):
        return json.dumps(self.to_dict(), indent = 4)

class PaymentType(Enum):
    CREDIT = 1
    DEBIT = 2
    SAVINGS = 3
    PERMANENT_SAVINGS = 4

class StopException(Exception):
    def __init__(self): pass
