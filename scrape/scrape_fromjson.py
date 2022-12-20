import json
import re
import sys
import urllib.request
from os.path import expanduser

import psycopg2
import requests
from bs4 import BeautifulSoup


def get_plans():
    # Variables we need to change depending on the environment we execute the project on
    with open("fiches-horaires-et-plans.json", mode="rt", encoding="utf-8") as file:
        json_file = json.load(file)
        for ligne in json_file:
            tab = ligne['fields']
            print("nom ligne: " + tab['id_line'] + "; type donnée: " + tab['type'] + "; url: " + tab['url'])


get_plans()
