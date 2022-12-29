import datetime
import io
import json
import sys
import time
import webbrowser
from os.path import expanduser

import folium
import networkx as nx
import pandas as pd
import psycopg2
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QLabel, \
    QSplitter, QHBoxLayout, QVBoxLayout, QWidget, QCompleter, QDialog, QLineEdit, QDialogButtonBox, QMessageBox, \
    QFileDialog
from PyQt5 import QtWidgets
from branca.element import Element
from jinja2 import Template
from sqlalchemy import create_engine
import os

os.chdir(sys.path[0])
sys.path.append('../modules')
import params
import route_type
import parse

number_of_click = 0


class DialogParams(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Entrez les informations de connexion")

        self.user_input = QLineEdit(self)
        self.user_label = QLabel("Utilisateur:", self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_label = QLabel("Mot de passe:", self)
        self.database_input = QLineEdit(self)
        self.database_label = QLabel("Base de données:", self)
        self.host_input = QLineEdit(self)
        self.host_label = QLabel("Hôte:", self)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)

        layout = QVBoxLayout()

        # ajout de chaque QLabel et QLineEdit dans un QHBoxLayout
        user_layout = QHBoxLayout()
        user_layout.addWidget(self.user_label)
        user_layout.addWidget(self.user_input)
        layout.addLayout(user_layout)

        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        database_layout = QHBoxLayout()
        database_layout.addWidget(self.database_label)
        database_layout.addWidget(self.database_input)
        layout.addLayout(database_layout)

        host_layout = QHBoxLayout()
        host_layout.addWidget(self.host_label)
        host_layout.addWidget(self.host_input)
        layout.addLayout(host_layout)

        layout.addWidget(self.button_box)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):

        super().__init__()

        # Setting up the window layout
        self.resize(600, 600)
        main = QWidget()
        self.setCentralWidget(main)
        main.setLayout(QVBoxLayout())
        main.setFocusPolicy(Qt.StrongFocus)
        self.tableWidget = QTableWidget()
        self.tableWidget.doubleClicked.connect(self.table_Click)
        self.tableWidget.itemClicked.connect(self.cell_Click)
        self.rows = []
        self.webView = myWebView()

        controls_panel = QHBoxLayout()
        mysplit = QSplitter(Qt.Vertical)
        mysplit.addWidget(self.tableWidget)
        mysplit.addWidget(self.webView)
        main.layout().addLayout(controls_panel)
        main.layout().addWidget(mysplit)

        _label = QLabel('From: ', self)
        _label.setFixedSize(30, 20)
        self.from_box = QComboBox()
        self.from_box.setEditable(True)
        self.from_box.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.from_box.setInsertPolicy(QComboBox.NoInsert)
        controls_panel.addWidget(_label)
        controls_panel.addWidget(self.from_box)

        _label = QLabel('  To: ', self)
        _label.setFixedSize(20, 20)
        self.to_box = QComboBox()
        self.to_box.setEditable(True)
        self.to_box.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.to_box.setInsertPolicy(QComboBox.NoInsert)
        controls_panel.addWidget(_label)
        controls_panel.addWidget(self.to_box)

        self.go_button = QPushButton("Go!")
        self.go_button.clicked.connect(self.button_Go)
        controls_panel.addWidget(self.go_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.button_Clear)
        controls_panel.addWidget(self.clear_button)

        self.maptype_box = QComboBox()
        self.maptype_box.addItems(self.webView.maptypes)
        self.maptype_box.currentIndexChanged.connect(self.webView.setMap)
        controls_panel.addWidget(self.maptype_box)

        # On demande à l'utilisateur de créer le fichier params.json s'il n'existe pas encore
        if params.get_variables() is None:
            err = QtWidgets.QMessageBox()
            err.setIcon(QtWidgets.QMessageBox.Information)
            err.setText("Veuillez définir les paramètres relatifs à la base de données et au dossier 'data' .")
            while True:
                err.exec_()
                dialog = DialogParams()
                result = dialog.exec_()
                if result == QDialog.Accepted:
                    user = dialog.user_input.text()
                    password = dialog.password_input.text()
                    database = dialog.database_input.text()
                    host = dialog.host_input.text()
                    while True:
                        options = QFileDialog.Options()
                        options |= QFileDialog.ReadOnly
                        folder_path = QFileDialog.getExistingDirectory(self, "Sélectionnez un dossier", options=options)

                        if folder_path:
                            params.set_variables(folder_path, user, password, database, host)
                            break
                        else:
                            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un dossier.")

                    break

        # See params.py
        data_path, user, password, database, host = params.get_variables()

        sys.path.append(data_path)
        dp = expanduser(data_path)

        self.cursor = None
        # Initiating connection with the PostgreSQL database
        self.engine = create_engine(
            'postgresql+psycopg2://' + str(user) + ':' + str(password) + '@' + str(host) + '/' + str(database))
        self.conn = psycopg2.connect(database=str(database), user=str(user), host=str(host), password=str(password))

        self.connect_DB()
        self.show()

    def connect_DB(self):

        print("database project connected to server")
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute("""SELECT distinct name FROM nodes ORDER BY name""")
            self.conn.commit()
            rows = self.cursor.fetchall()

            for row in rows:
                self.from_box.addItem(str(row[0]))
                self.to_box.addItem(str(row[0]))
        except psycopg2.ProgrammingError as e:
            self.conn.rollback()
            err = QtWidgets.QMessageBox()
            err.setIcon(QtWidgets.QMessageBox.Warning)
            err.setText("La table n'existe pas! récupération des données en cours.")
            err.exec_()
            parse.main()
            self.connect_DB()
        return

    def path_processing(self, G, path):
        shortest_names = pd.concat([self.nodes.loc[self.nodes['stop_i'] == i] for i in path]).reset_index()
        duration = nx.classes.function.path_weight(G, path, weight="duration_avg")
        print(f"The time without taking into account the waiting time is {duration / 60} minutes")
        pathGraph = nx.path_graph(path)
        edges = [[ea, G.edges[ea[0], ea[1]]] for ea in pathGraph.edges()]
        # Case where the user decided to try out a path where they stay on the same stop
        for node in list(pathGraph.nodes):
            edges.append(node)

        routes_taken = []
        for i in edges:
            try:
                routes_taken.append(self.routes.loc[self.routes['route_i'] == int(float(i[1]['route_i']))])
            except Exception:
                routes_taken.append(pd.DataFrame([['w', 'w', 'w']], columns=['route_type', 'route_name', 'route_i']))

        routes_taken = pd.concat(routes_taken, ignore_index=True)
        which_routes_taken = routes_taken[['route_type', 'route_name']].drop_duplicates()
        which_routes_taken = which_routes_taken[which_routes_taken.route_type != 'w']
        # adding waiting time each time you have to take a new route

        today = datetime.datetime.utcnow()
        curr_unix_time = time.mktime(today.utctimetuple())
        starting_time = datetime.datetime.utcfromtimestamp(curr_unix_time).strftime('%Y-%m-%d %H:%M:%S')[-8:].split(':')
        starting_time = int(starting_time[0]) * 3600 + int(starting_time[1]) * 60 + int(starting_time[2])

        current_time = starting_time
        for i, j in enumerate(which_routes_taken.index):
            self.rows = []
            query = f"""
                SELECT dep_time_ut
                FROM temporal_day
                WHERE {edges[j][0][0]} = from_stop_i
                AND {edges[j][0][1]} = to_stop_i
                AND dep_time_ut > {current_time}
                ORDER BY dep_time_ut
                LIMIT 1
                """
            self.cursor.execute(query)
            self.conn.commit()
            self.rows += self.cursor.fetchall()

            # no rows can be selected, leading to self.rows being empty if you've missed the last train for the day, so you need to look for tomorrow's one
            if not self.rows:
                query = f"""
                    SELECT dep_time_ut + 24*3600
                    FROM temporal_day
                    WHERE {edges[j][0][0]} = from_stop_i
                    AND {edges[j][0][1]} = to_stop_i
                    ORDER BY dep_time_ut
                    LIMIT 1
                    """
                self.cursor.execute(query)
                self.conn.commit()
                self.rows += self.cursor.fetchall()
            try:
                current_time = float(self.rows[0][0])
                k = j
                if j != which_routes_taken.index[-1]:
                    while k < which_routes_taken.index[i + 1]:
                        current_time += float(edges[k][1].get("duration_avg"))
                        current_time += 30  # to account for time spent in each station
                        k += 1
                else:
                    while k <= routes_taken.index[-1]:
                        current_time += float(edges[k][1].get("duration_avg"))
                        current_time += 30  # to account for time spent in each station
                        k += 1
            except Exception:
                pass

        total_time = current_time - starting_time
        print(
            f"The time taking into account the wait is {int(total_time // 3600)}h {int(total_time % 3600 // 60)}m {int(total_time % 3600 % 60)}s")
        return shortest_names, which_routes_taken, total_time

    def button_Go(self):
        if (self.from_box.findText(self.from_box.currentText()) == -1) or (
                self.to_box.findText(self.to_box.currentText()) == -1):
            err = QtWidgets.QMessageBox()
            err.setIcon(QtWidgets.QMessageBox.Warning)
            err.setText('Une de vos valeurs est invalide!')
            err.exec_()
            return
        self.to_stop_i = str(self.to_box.currentText()).replace("'", "''")

        self.cursor.execute(f""" SELECT stop_i FROM nodes WHERE name = '{self.to_stop_i}'""")
        self.conn.commit()
        myrows = self.cursor.fetchall()
        self.to_stop_i = int(myrows[0][0])
        self.from_stop_i = str(self.from_box.currentText()).replace("'", "''")
        self.cursor.execute(f""" SELECT stop_i FROM nodes WHERE name = '{self.from_stop_i}'""")
        self.conn.commit()
        myrows = self.cursor.fetchall()
        self.from_stop_i = int(myrows[0][0])

        self.tableWidget.clearContents()
        self.rows = []

        self.nodes = pd.read_sql("SELECT * FROM \"{}\";".format("nodes"), self.engine)
        self.routes = pd.read_sql("SELECT * FROM \"{}\";".format("routes"), self.engine)

        super_short_comb_walk = pd.read_sql("SELECT * FROM \"{}\";".format("shortest_route"), self.engine)
        G = nx.from_pandas_edgelist(super_short_comb_walk, source="from_stop_i", target="to_stop_i", edge_attr=True)
        self.shortest = nx.shortest_path(G, source=self.from_stop_i, target=self.to_stop_i, weight="duration_avg")
        self.shortest = [int(i) for i in self.shortest]
        self.shortest_names, self.shortest_routes, self.shortest_time = self.path_processing(G, self.shortest)
        numrows = 2
        numcols = len(self.shortest_routes.index)
        self.tableWidget.setRowCount(numrows)
        self.tableWidget.setColumnCount(2 * numcols + 1)
        self.add_path_to_table(self.shortest_names, self.shortest_routes, 0)
        self.tableWidget.resizeColumnsToContents()

        shortest = self.shortest
        HEX = ['#52766c', 'blue', 'pink', 'black', 'purple', '#52766c', '#52766c', 'blue', 'pink', 'black', 'purple']
        nth_route = 0
        self.colors = []
        for sss, i in enumerate(shortest):
            if i != 'w':
                # Vérifie que l'index nth_route est dans les limites du tableau
                if nth_route < len(self.shortest_routes) - 1:
                    if sss <= self.shortest_routes.index[-1] and sss == self.shortest_routes.index[nth_route + 1]:
                        nth_route += 1

                lat = self.nodes.loc[self.nodes['stop_i'] == i]['lat'].head(1)
                lng = self.nodes.loc[self.nodes['stop_i'] == i]['lon'].head(1)
                self.colors.append(HEX[nth_route])
                self.webView.addPoint(lat, lng, HEX[nth_route])
            else:
                self.colors.append('w')

    def add_path_to_table(self, shortest_names, which_routes_taken, row_num):
        numcols = self.tableWidget.columnCount()
        jj = 0
        for sss, route in which_routes_taken.iterrows():
            self.tableWidget.setItem(row_num, jj, QTableWidgetItem(shortest_names.iloc[sss]['name']))
            self.tableWidget.setItem(row_num, jj + 1,
                                     QTableWidgetItem(
                                         route_type.str_route_type(route['route_type']) + ' ' + route['route_name']))
            jj += 2
        self.tableWidget.setItem(row_num, jj, QTableWidgetItem(shortest_names.iloc[-1]['name']))
        total_time = self.shortest_time
        self.tableWidget.setSpan(row_num + 1, 1, 1, 2 * numcols)
        newItem = QTableWidgetItem('Total time With Waiting')
        self.tableWidget.setItem(row_num + 1, 0, newItem)
        newItem = QTableWidgetItem(
            f"""{int(total_time // 3600)}h {int(total_time % 3600 // 60)}m {int(total_time % 3600 % 60)}s""")
        self.tableWidget.setItem(row_num + 1, 1, newItem)

    def button_Clear(self):
        self.webView.clearMap(self.maptype_box.currentIndex())
        self.from_box.clearEditText()
        self.to_box.clearEditText()
        self.update()
        global number_of_click
        number_of_click = 0

    def mouseClick(self, lat, lng):
        global number_of_click
        print(f"Clicked on: latitude {lat}, longitude {lng}")
        self.cursor.execute(f"""SELECT A.name, A.stop_i FROM nodes as A 
            WHERE ((A.lat - {lat})^2 + (A.lon - {lng})^2) <= ALL (SELECT (lat - {lat})^2 + (lon - {lng})^2 FROM nodes)""")
        self.conn.commit()
        myrows = self.cursor.fetchall()

        if number_of_click == 0:
            self.webView.addPoint(lat, lng, 'green')
            self.from_box.setCurrentIndex(self.from_box.findText(myrows[0][0], Qt.MatchFixedString))
            self.from_stop_i = int(myrows[0][1])

        else:
            self.webView.addPoint(lat, lng, 'red')
            self.to_box.setCurrentIndex(self.to_box.findText(myrows[0][0], Qt.MatchFixedString))
            self.to_stop_i = int(myrows[0][1])

        number_of_click += 1

    def table_Click(self):
        """for a weird reason, if there are multiple polylines on a map,
        folium will choose one of their colour and colour every polyline with this colour,
        but when you zoom in, you get the expected color"""
        for sss in range(len(self.colors) - 1):

            if self.colors[sss] == self.colors[sss + 1]:
                self.cursor.execute(f"""select lat, lon from nodes where stop_i = {self.shortest[sss]}""")
                self.conn.commit()
                lat1, lng1 = self.cursor.fetchall()[0]
                self.cursor.execute(f"""select lat, lon from nodes where stop_i = {self.shortest[sss + 1]}""")
                self.conn.commit()
                lat2, lng2 = self.cursor.fetchall()[0]
                self.webView.addSegment(lat1, lng1, lat2, lng2, self.colors[sss])

    def cell_Click(self, item):
        row = item.row()
        column = item.column()
        text = item.text()
        type_cur = route_type.str_route_num(text.split(' ')[0])
        name = text.split(' ')[1]
        if (row == 0) and (column % 2 == 1):
            ask = QtWidgets.QMessageBox()
            ask.setIcon(QtWidgets.QMessageBox.Question)
            ask.setText(f"Voulez-vous accèder au plan de la ligne {text} ?")
            ask.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            result = ask.exec_()

            if result == QtWidgets.QMessageBox.Yes:
                # Code to downnload the pdf/jpeg file from the url indicated in the database, then display it
                self.cursor.execute(
                    f""" SELECT id_line, url FROM lines WHERE name_line = '{name}' and route_type = {type_cur}""")
                self.conn.commit()
                myrows = self.cursor.fetchall()
                if len(myrows) <= 0:
                    err = QtWidgets.QMessageBox()
                    err.setIcon(QtWidgets.QMessageBox.Warning)
                    err.setText(f"pas d'URL spécifiée pour la ligne {name} !")
                    err.exec_()
                    return
                for index, row in enumerate(myrows):
                    file_name = row[0]
                    file_url = row[1]
                    # Ouvre l'URL dans le navigateur
                    webbrowser.open(file_url)
                    # Si ce n'est pas la dernière itération de la boucle, on demande à l'utilisateur s'il est satisfait
                    if index != len(myrows) - 1:
                        message = QMessageBox()
                        message.setText(f"Ce plan est-il le bon ? Un autre est disponible à consulter")
                        message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        result = message.exec_()
                        # Si l'utilisateur est satisfait, on s'arrête
                        if result == QMessageBox.Yes:
                            return
            print("La ligne a été traitée")
            return
        return


def add_customjs(map_object):
    my_js = f"""{map_object.get_name()}.on("click",
             function (e) {{
                var data = `{{"coordinates": ${{JSON.stringify(e.latlng)}}}}`;
                console.log(data)}}); """
    e = Element(my_js)
    html = map_object.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e

    return map_object


class myWebView(QWebEngineView):
    def __init__(self):
        super().__init__()

        self.mymap = None
        self.maptypes = ["Stamen Terrain", "Esri Satellite", "OpenStreetMap", "stamentoner", "cartodbpositron"]
        self.setMap(0)

    def handleClick(self, msg):
        data = json.loads(msg)
        lat = data['coordinates']['lat']
        lng = data['coordinates']['lng']

        window.mouseClick(lat, lng)

    def addSegment(self, lat1, lng1, lat2, lng2, color):
        js = Template(
            """
        L.polyline(
            [ [{{latitude1}}, {{longitude1}}], [{{latitude2}}, {{longitude2}}] ], {
                "color": '{{color}}',
                "opacity": 1.0,
                "weight": 4,
                "line_cap": "butt"
            }
        ).addTo({{map}});
        """
        ).render(map=self.mymap.get_name(), latitude1=lat1, longitude1=lng1, latitude2=lat2, longitude2=lng2)

        self.page().runJavaScript(js)

    def addPoint(self, lat, lng, color):
        js = Template(
            """
        L.circleMarker(
            [{{latitude}}, {{longitude}}], {
                "bubblingMouseEvents": true,
                "color": '{{color}}',
                "popup": "hello",
                "dashArray": null,
                "dashOffset": null,
                "fill": false,
                "fillColor": 'green',
                "fillOpacity": 0.2,
                "fillRule": "evenodd",
                "lineCap": "round",
                "lineJoin": "round",
                "opacity": 1.0,
                "radius": 2,
                "stroke": true,
                "weight": 5
            }
        ).addTo({{map}});
        """
        ).render(map=self.mymap.get_name(), latitude=lat, longitude=lng, color=color)
        self.page().runJavaScript(js)

    def setMap(self, i):
        if i != 1:
            self.mymap = folium.Map(location=[48.8619, 2.3519], tiles=self.maptypes[i], zoom_start=12,
                                    prefer_canvas=True)
        else:
            self.mymap = folium.Map(location=[48.8619, 2.3519],
                                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                                    attr='Esri', zoom_start=12, prefer_canvas=True)
        self.mymap = add_customjs(self.mymap)

        page = WebEnginePage(self)
        self.setPage(page)

        data = io.BytesIO()
        self.mymap.save(data, close_file=False)

        self.setHtml(data.getvalue().decode())

    def clearMap(self, index):
        self.setMap(index)


class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        if 'coordinates' in msg:
            self.parent.handleClick(msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
