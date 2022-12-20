import sys, os, psycopg2
from os.path import expanduser
# import folium, io, json, sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView, QGraphicsPixmapItem, QGraphicsScene, QMainWindow, QApplication, QTableWidget, \
    QTableWidgetItem, QComboBox, QPushButton, QLabel, QSplitter, QHBoxLayout, QVBoxLayout, QWidget, QCompleter
from PyQt5.QtGui import QPixmap
from sqlalchemy import create_engine


sys.path.append('../parse')

import parse
import route_type

# See params.py
data_path, user, password, database, host = params.get_variables()
sys.path.append(data_path)
dp = expanduser(data_path)
number_of_click = 0


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
        self.conn = psycopg2.connect(database=str(database), user=str(user), host=str(host), password=str(password))
        self.cursor = self.conn.cursor()
        print("database project connected to server")
        self.engine = create_engine(
            'postgresql+psycopg2://' + str(user) + ':' + str(password) + '@' + str(host) + '/' + str(database))
        self.cursor.execute("""SELECT distinct route_type,route_name FROM routes ORDER BY route_type DESC""")
        self.conn.commit()
        rows = self.cursor.fetchall()
        for row in rows:
            self.route_box.addItem(route_type.str_route_type(row[0]) + ' ' + row[1])

    def button_Go(self):
        self.route = str(self.route_box.currentText())
        if os.path.exists('Scrape/' + self.route + ' Paris.jpg'):
            self.pixmap = QPixmap('Scrape/' + self.route + ' Paris.jpg',
                                  '1')  # .scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio)
            self.label.setPixmap(self.pixmap)
        else:
            self.pixmap = QPixmap('Scrape/' + self.route + ' Paris.jpg',
                                  '1')  # .scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio)
            self.label.setPixmap(self.pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
