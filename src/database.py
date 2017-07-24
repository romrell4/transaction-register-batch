import json

COMPLETED_VISA_KEY = "completedVisaTxIds"
COMPLETED_ACCOUNT_KEY = "completedAccountTxIds"

class DB:
    database = None

    @classmethod
    def load(cls):
        cls.database = json.load(open("../res/json/db.json"))

    @classmethod
    def get_business(cls, key):
        if key in cls.database["businesses"]:
            return cls.database["businesses"][key]
        return key

    @classmethod
    def put_business(cls, key, value):
        DB.database["businesses"][key] = value

    @classmethod
    def is_visa_tx_completed(cls, tx_id):
        return tx_id in DB.database[COMPLETED_VISA_KEY]

    @classmethod
    def put_completed_visa_tx_id(cls, tx_id):
        DB.database[COMPLETED_VISA_KEY].append(tx_id)

    @classmethod
    def is_account_tx_completed(cls, tx_id):
        return tx_id in DB.database[COMPLETED_ACCOUNT_KEY]

    @classmethod
    def put_completed_account_tx_id(cls, tx_id):
        DB.database[COMPLETED_ACCOUNT_KEY].append(tx_id)

    @classmethod
    def save(cls):
        json.dump(cls.database, open("../res/json/db.json", "w"))