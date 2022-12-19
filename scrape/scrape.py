
import requests, lxml, re, json, datetime, urllib.request, psycopg2
from bs4 import BeautifulSoup
from os.path import expanduser

user = 'postgres'
dbname = 'dbproject'
password = 'jalanji'
conn = psycopg2.connect(database="dbproject", user="postgres", host="localhost", password="jalanji")
cursor = conn.cursor()

def str_route_type(route_type):
    route_type=int(route_type)
    if route_type == 0:
        route='TRAM'
    elif route_type ==1:
        route='METRO'
    elif route_type == 2:
        route='RER'
    elif route_type == 3:
        route='BUS'
    else:
        route='ERROR'
    return route

def get_google_images_data(soup, query_name, html, headers, pathtofolder):
    all_script_tags = soup.select('script')
    matched_images_data = ''.join(re.findall(r"AF_initDataCallback\(([^<]+)\);", str(all_script_tags)))
    matched_images_data_fix = json.dumps(matched_images_data)
    matched_images_data_json = json.loads(matched_images_data_fix)
    matched_google_image_data = re.findall(r'\[\"GRID_STATE0\",null,\[\[1,\[0,\".*?\",(.*),\"All\",', matched_images_data_json)
    matched_google_images_thumbnails = ', '.join(
        re.findall(r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]',
                   str(matched_google_image_data))).split(', ')
    for fixed_google_image_thumbnail in matched_google_images_thumbnails:
        google_image_thumbnail_not_fixed = bytes(fixed_google_image_thumbnail, 'ascii').decode('unicode-escape')
        google_image_thumbnail = bytes(google_image_thumbnail_not_fixed, 'ascii').decode('unicode-escape')

    # removing previously matched thumbnails for easier full resolution image matches.
    removed_matched_google_images_thumbnails = re.sub(
        r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]', "", str(matched_google_image_data))

    matched_google_full_resolution_images = re.findall(r"(?:'|,),\[\"(https:|http.*?)\",\d+,\d+\]",
                                                       removed_matched_google_images_thumbnails)

    fixed_full_res_image = matched_google_full_resolution_images[0]
    original_size_img_not_fixed = bytes(fixed_full_res_image, 'ascii').decode('unicode-escape')
    original_size_img = bytes(original_size_img_not_fixed, 'ascii').decode('unicode-escape')

    opener=urllib.request.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    try:
        urllib.request.urlretrieve(original_size_img, pathtofolder+'/'+query_name+'.jpg')
    except:
        pass

headers = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
}

pathtofolder= expanduser('~')+'/PycharmProjects/pythonProject2/Scrape/'

cursor.execute("""select route_type, route_name from routes
                   f group by route_type, route_name
                    ORDER BY route_type
                    """)

conn.commit()
rows = cursor.fetchall()
for ii,i in enumerate(rows):
    print(f"""{ii}"""+'/'+f'{len(rows)}')
    query = str_route_type(int(i[0]))+' '+str(i[1])+' Paris'
    params = {
    "q": query,
    "tbm": "isch",
    "ijn": "0",
    }
    print('')
    html = requests.get("https://www.google.com/search", params=params, headers=headers)
    print('')
    soup = BeautifulSoup(html.text, 'lxml')
    get_google_images_data(soup, query, html, headers, pathtofolder)



