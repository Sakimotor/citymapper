# citymapper

A citymapper-inspired PyQt application for public transport that uses a PostgreSQL database.

![app screenshot](https://i.imgur.com/Sglmejb.png)

## Setup guide

* Put all the necessary data (taken from [this paper](https://www.nature.com/articles/sdata201889)) in a `data` folder. Here is the allowed files list:
  * csv files : `network_*.csv`
  * geojson files : `routes.geojson`
  * json (taken from [here](https://prim.iledefrance-mobilites.fr/fr/donnees-statiques/fiches-horaires-et-plans?staticDataSlug=fiches-horaires-et-plans) and [there](https://data.iledefrance-mobilites.fr/explore/dataset/referentiel-des-lignes/)) : `fiches-horaires-et-plans.json, referentiel-des-lignes.json`

* Install all the necessary modules with the following command : `pip install -r requirements.txt`

* **Automatic Way**: run the main program, `parse/main.py`. It will ask you to input the information required to make the databases work, then fill the database by itself.
* **Manual Way**: 
  * Set your data folder, and some other settings in the `params/params.json` file. An example file names `example_params.json` has been provided.
  * Run the parsing software, `parse/parse.py`
  * Run the main program, `parse/main.py`
