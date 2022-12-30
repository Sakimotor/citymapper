import json

import pandas as pd
import psycopg2, datetime, sys, geojson, os
from io import StringIO
from sqlalchemy import create_engine
from schema import sql_schema
from os.path import expanduser

os.chdir(sys.path[0])
sys.path.append('../modules')
import params
import route_type

data_path = None
user = None
password = None
database = None
host = None
conn = None
cursor = None
engine = None
dp = None


# copy dataFrame into a table defined in the schema.
def copy_to_db(df, table):
    df.to_sql(table, con=engine, if_exists='append', index=False)

    try:
        cursor.execute(f"""select * from {table}""")
        print(f"successfully copied the dataframe into {table}")
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1


def create_nodes():
    nodes = pd.read_csv(dp + 'network_' + 'nodes.csv', delimiter=';')
    nodes.columns = nodes.columns.str.lower()
    nodes['name'] = nodes['name'].str.lower()
    copy_to_db(nodes, 'nodes')


def create_temporal_day():
    temporal_day = pd.read_csv(dp + 'network_temporal_day.csv', delimiter=';').drop(
        columns=['trip_I', 'seq']).drop_duplicates(keep='first')
    temporal_day.columns = temporal_day.columns.str.lower()

    def secs(time_ut):
        """return number of seconds since midnigh, so we can later compare dep_time_ut with our current unix time"""
        relative_time = datetime.datetime.utcfromtimestamp(time_ut).strftime('%Y-%m-%d %H:%M:%S')[-8:].split(':')
        return int(relative_time[0]) * 3600 + int(relative_time[1]) * 60 + int(relative_time[2])

    dep = temporal_day['dep_time_ut']
    dep = dep.apply(secs)
    arr = temporal_day['arr_time_ut']
    arr = arr.apply(secs)
    temporal_day['dep_time_ut'] = dep
    temporal_day['arr_time_ut'] = arr

    copy_to_db(temporal_day, 'temporal_day')


def create_routes():
    with open(dp + 'routes.geojson') as f:
        gj = geojson.load(f)['features']

    data = [[line['properties']['route_type'], line['properties']['route_name'], line['properties']['route_I']] for line
            in gj]
    routes = pd.DataFrame(data, columns=['route_type', 'route_name', 'route_I'])
    routes.columns = routes.columns.str.lower()
    copy_to_db(routes, 'routes')


def create_combined():
    comb = pd.read_csv(dp + 'network_combined.csv', delimiter=';')
    comb.columns = comb.columns.str.lower()
    comb_split_routes = comb['route_i_counts'].str.split(',|:')
    comb_split_routes = pd.DataFrame(comb_split_routes)
    comb = pd.concat([comb[['from_stop_i', 'to_stop_i', 'duration_avg']], comb_split_routes], axis=1)
    comb = comb.explode('route_i_counts')
    comb = comb.iloc[::2]
    comb = comb.rename(columns={'route_i_counts': 'route_i'})
    copy_to_db(comb, 'combined')


def create_walk():
    walk = pd.read_csv(dp + 'network_walk.csv', delimiter=';')
    walk.columns = walk.columns.str.lower()
    # we assumed a person walks at 1.5 m.s-1, and we want the duration in minutes
    walk['d_walk'] /= 1.5
    walk['route_i'] = 'w'
    walk = walk.drop(columns=['d'])
    walk = walk.rename(columns={'d_walk': 'duration_avg'})
    copy_to_db(walk, 'walk')

    cursor.execute("""SELECT * into shortest_route
    from walk
    
    where duration_avg < 300;
    
    insert into shortest_route
    select * from combined;
    """)
    conn.commit()

    cursor.execute("""alter table shortest_route
    add primary key(from_stop_i, to_stop_i, route_i)""")
    conn.commit()


def create_lines():
    # Open the json file that tells the line names related to their line IDs

    # File source: https://data.iledefrance-mobilites.fr/explore/dataset/referentiel-des-lignes
    with open(os.path.join(data_path, 'referentiel-des-lignes.json'), 'r') as f:
        json_file = json.load(f)
    data = [[line['fields']['transportmode'], line['fields']['id_line'], line['fields']['name_line']] for line
            in
            json_file]
    lines = pd.DataFrame(data, columns=['transportmode', 'id_line', 'name_line'])

    # Open the json file that gives the url relative to a line_id

    # File source: https://data.iledefrance-mobilites.fr/explore/dataset/fiches-horaires-et-plans/
    with open(os.path.join(data_path, 'fiches-horaires-et-plans.json'), 'r') as f:
        json_file = json.load(f)
    data = [[line['fields']['id_line'], line['fields']['url']] for line in json_file]
    urls = pd.DataFrame(data, columns=['id_line', 'url'])

    # Merge the results of the two json files above, then add it to the database
    merge = pd.merge(lines, urls, how='inner', on=["id_line"])
    merge = merge.drop_duplicates()
    route_merge = merge['transportmode'].values

    # Convert transportmode to route_type before moving on
    for route_x in range(len(route_merge)):
        route_merge[route_x] = int(route_type.str_route_num(route_merge[route_x]))
    merge['transportmode'] = route_merge
    merge = merge.rename(columns={'transportmode': 'route_type'})
    merge.to_sql('lines', con=engine, if_exists='replace', index=False)

    cursor.execute("""ALTER TABLE lines
                ADD PRIMARY KEY (url, id_line)""")
    conn.commit()


def main():
    global data_path, user, password, database, host, conn, cursor, engine, dp
    data_path, user, password, database, host = params.get_variables()

    sys.path.append(data_path)

    conn = psycopg2.connect(database=str(database), user=str(user), host=str(host), password=str(password))
    cursor = conn.cursor()
    dp = expanduser(data_path)
    print("database projet connected to the remote server")
    engine = create_engine(
        'postgresql+psycopg2://' + str(user) + ':' + str(password) + '@' + str(host) + '/' + str(database))
    try:
        try:
            cursor.execute('DROP SCHEMA public CASCADE')
            conn.commit()
        except psycopg2.ProgrammingError:
            conn.rollback()
        cursor.execute('CREATE SCHEMA public')
        conn.commit()
        cursor.execute('GRANT ALL ON SCHEMA public TO postgres')
        conn.commit()
        cursor.execute('GRANT ALL ON SCHEMA public TO public')
        conn.commit()
    except psycopg2.ProgrammingError:
        conn.rollback()
        cursor.execute('DROP owned by l3info_32')
        conn.commit()

    for i in sql_schema.split(';'):
        try:
            cursor.execute(i)
            conn.commit()
        except psycopg2.ProgrammingError:
            # print("we caught the exception")
            conn.rollback()

    create_nodes()
    create_routes()
    create_combined()
    create_walk()
    create_temporal_day()
    create_lines()


if __name__ == '__main__':
    main()
