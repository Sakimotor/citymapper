import json
import os


def get_variables():
    # Variables we need to change depending on the environment we execute the project on
    print (os.getcwd())
    with open("../modules/params.json", mode="rt", encoding="utf-8") as file:
        test_json = json.load(file)
        data_path = os.path.expanduser(test_json["path"])
        user = test_json["user"]
        password = test_json["password"]
        database = test_json["database"]
        host = test_json["host"]
        return data_path, user, password, database, host




