import os
import psycopg2
import datetime
import json
from io import StringIO
from sqlalchemy import create_engine
import sys
from os.path import expanduser

import pandas as pd




# import folium, io, json, sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QComboBox, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, \
    QWidget, QCompleter
from sqlalchemy import create_engine


os.chdir(sys.path[0])
sys.path.append('../modules')

import params
import route_type

# See params.py
data_path, user, password, database, host = params.get_variables()
sys.path.append(data_path)
dp = expanduser(data_path)
number_of_click = 0

conn = psycopg2.connect(database=str(database), user=str(user), host=str(host), password=str(password))
cursor = conn.cursor()
print("database project connected to server")
engine = create_engine('postgresql+psycopg2://' + str(user) + ':' + str(password) + '@' + str(host) + '/' + str(database))


def copy_from_stringio(df, table):
    """
    Here we are going save the dataframe in memory
    and use copy_from() to copy it to the table
    """
    # save dataframe to an in memory buffer
    buffer = StringIO()
    df.to_csv(buffer, index_label='id', header=False, index=False, sep=';')
    df.to_csv('test.csv')
    buffer.seek(0)


    try:
        cursor.execute(f"""select * from {table}""")
        if not cursor.fetchone():
            cursor.copy_from(buffer, table, sep=";")
            conn.commit()
            print("successfully copied the dataframe into the table")
        else:
            print(f"{table} : Copy not possible since table is not empty")
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.resize(600, 600)

        self.main = QWidget()
        self.setCentralWidget(self.main)
        self.main.setLayout(QVBoxLayout())
        self.main.setFocusPolicy(Qt.StrongFocus)

        self.label = QLabel(self)
        self.pixmap = QPixmap('Scrape/BUS 180 Paris.jpg')
        self.label.setPixmap(self.pixmap)

        controls_panel = QHBoxLayout()
        self.main.layout().addLayout(controls_panel)
        self.main.layout().addWidget(self.label)

        # _label.setFixedSize(30,20)
        self.route_box = QComboBox()
        self.route_box.setEditable(True)
        self.route_box.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.route_box.setInsertPolicy(QComboBox.NoInsert)
        controls_panel.addWidget(self.route_box, stretch=1)

        self.go_button = QPushButton("Go!")
        self.go_button.clicked.connect(self.button_Go)
        controls_panel.addWidget(self.go_button, stretch=1)

        self.connect_DB()
        self.show()


    def connect_DB(self):
        cursor.execute(f"SELECT * FROM information_schema.tables WHERE table_name='lines'")
        if (cursor.rowcount <= 0):
            with open('referentiel-des-lignes.json', 'r') as f:
                json_file = json.load(f)
            data = [[line['fields']['transportmode'], line['fields']['id_line'], line['fields']['name_line']] for line in
                    json_file]
            urls = pd.DataFrame(data, columns=['transportmode', 'id_line', 'name_line'])

            with open('fiches-horaires-et-plans.json', 'r') as f:
                json_file = json.load(f)

            data = [[line['fields']['id_line'], line['fields']['url']] for line in json_file]
            lines = pd.DataFrame(data, columns=['id_line', 'url'])
            print(lines)
            merge = pd.merge(lines, urls, how='inner', on=["id_line"])
            merge = merge.drop_duplicates()
            print(merge)
            merge.to_sql('lines', con=engine, if_exists='replace', index=False)

            cursor.execute("""ALTER TABLE lines
            ADD PRIMARY KEY (url, id_line)""")
            conn.commit()

        cursor.execute("""SELECT distinct route_type,route_name FROM routes ORDER BY route_type DESC""")
        conn.commit()
        rows = cursor.fetchall()
        for row in rows:
            self.route_box.addItem(route_type.str_route_type(row[0]) + ' ' + row[1])

    def button_Go(self):
        self.route = str(self.route_box.currentText())
        if os.path.exists(os.path.join('./data_json/', self.route)):
            self.pixmap = QPixmap(os.path.join('./data_json/', self.route),
                                  '1')  # .scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio)
            self.label.setPixmap(self.pixmap)
        else:
            #Code to downnload the pdf/jpeg file from the url indicated in the database, then display it


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
