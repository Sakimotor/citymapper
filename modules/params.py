import json
import os


def get_variables():
    # Variables we need to change depending on the environment we execute the project on
    print (os.getcwd())
    try:
        with open("../modules/params.json", mode="rt", encoding="utf-8") as file:
            test_json = json.load(file)
            data_path = os.path.expanduser(test_json["path"])
            if not data_path.endswith(os.sep):
                data_path += os.sep
            user = test_json["user"]
            password = test_json["password"]
            database = test_json["database"]
            host = test_json["host"]
            return data_path, user, password, database, host
    except FileNotFoundError:
        print("Fichier de paramètres inexistant.")
        return None
    except OSError:
        print("Fichier vide.")
        return None


def set_variables(path, user, password, database, host):
    data = {
        'path': path,
        'user': user,
        'password': password,
        'database': database,
        'host': host
    }
    with open("../modules/params.json", mode="w", encoding="utf-8") as file:
        json.dump(data, file)






