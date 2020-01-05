import base64
import json
import time
import uuid
from datetime import datetime
from GDrive import GDrive
from GDrive import notify
import requests


def download_file(name, link):
    r = requests.get(link)
    file_path = "{}.mp3".format(name)
    file_path = file_path.replace("/", "_")
    with open(file_path, "wb") as f:
        f.write(r.content)
    return file_path


def delete_file(file_path):
    import os
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print("The file '{}' does not exist".format(file_path))


def get_pretty_id(t):
    u = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "M", "N", "P", "Q", "R", "S", "T", "U", "V", "W", "X",
         "Y", "Z", "a", "b", "c", "d", "e", "f", "g", "h", "j", "k", "m", "n", "p", "q", "r", "s", "t", "u", "v",
         "x", "y", "z", "1", "2", "3"]

    length = len(u)
    e = ""
    if t == 0:
        return u[0]

    if t < 0:
        t *= -1
        e += "-"

    while True:
        val = int(t % length)
        t = int(t / length)
        e += u[val]
        if t > 0:
            continue
        else:
            break
    return e


def get_db():
    import mysql.connector

    database = mysql.connector.connect(
        host="localhost",
        user="user",
        password="pwd",
        auth_plugin='mysql_native_password',
        database='shazam'
    )
    return database


def execute_query(query, values=None, fetch_one=False):
    database = get_db()
    cursor = database.cursor()
    if values:
        cursor.execute(query, values)
    else:
        cursor.execute(query)
    if not query.__contains__("select"):
        database.commit()
    res = -1
    if not (query.__contains__("update") or query.__contains__("insert")):
        res = cursor.fetchall() if not fetch_one else cursor.fetchone()
    database.close()
    return res


def yield_all_songs_from_db():
    query = 'select name from song_list order by time desc'
    res = execute_query(query)
    for name in res:
        yield name[0]


def check_already_exists(key):
    query = 'select * from song_list where id = {}'.format(key)
    res = execute_query(query, fetch_one=True)
    return res if res else False


def update_timestamp(key, timestamp):
    query = 'update song_list set time = {} where id = {}'.format(timestamp, key)
    execute_query(query)


def search_by_name(name):
    url = "https://myfreemp3c.com/api/search.php?callback=jQuery213025636066715463635_1577790089580"

    payload = "q={}+mp3&page=0".format(name.replace(" ", "+"))
    headers = {
        'authority': 'myfreemp3c.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, '
                  '*/*; q=0.01',
        'origin': 'https://myfreemp3c.com',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.88 Safari/537.36',
        'dnt': '1',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://myfreemp3c.com/',
        # 'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7',
        'cookie': '__cfduid=dbbc905772a004b0895705f8f313d73b61577790088; musicLang=en'
    }

    response = requests.post(url, headers=headers, data=payload.encode('utf-8'))
    res = str(response.text)
    res = res.replace("jQuery213025636066715463635_1577790089580(", "")
    res = res.replace(");", "")
    json_res = json.loads(res)

    if len(json_res['response']) == 0:
        return -1

    pretty_id = get_pretty_id(json_res["response"][1]["owner_id"]) + ":" + get_pretty_id(
        json_res["response"][1]["id"])
    link = "https://d.mp3-send.com/" + pretty_id
    return link


def update_song_link(song_key, song_name):
    link = search_by_name(song_name)
    if link != -1:
        query = 'update song_list set link_found = true, link = \'{}\' where id = {}'.format(link, song_key)
        execute_query(query)
        print("\nLink for song {} found".format(song_name))
        return link
    else:
        print("\nLink for song {} not found".format(song_name))
    return None


def check_old_songs():
    query = 'select * from song_list where link_found = false'
    res = execute_query(query)
    for r in res:
        link = update_song_link(r[0], r[1])
        if link:
            download_and_upload(r[0], r[1], link)


def filesize(file_path):
    import os
    statinfo = os.stat(file_path)
    return statinfo.st_size


def download_and_upload(song_key, song_name, link):
    file_path = download_file(song_name, link)
    if filesize(file_path) > 5 * 1024:
        print("Uploading song {} to drive".format(song_name))
        gdrive = GDrive()
        gdrive.upload(song_key, song_name, file_path)
    else:
        print("File for song {} was less than 5 KB, therefore not uploading song".format(song_name))
    delete_file(file_path)
    print("Song {} deleted from temp storage".format(song_name))
    notify(song_name)


def save_to_db(song_key, song_name, song_timestamp):
    query = 'insert into song_list values(%s, %s, %s,%s, %s)'
    values = (song_key, song_name, song_timestamp, False, None)
    execute_query(query, values)
    link = update_song_link(song_key, song_name)
    if link:
        download_and_upload(song_key, song_name, link)


def get_song_list_from_shazam(upto_timestamp=None):
    url = "https://www.shazam.com/discovery/v4/en-US/US/web/-/tag/AC53CA17-11C1-4F7D-91FC-93FCD57B878B"
    i = 0
    song_names = []
    song_keys = set()
    token = ""
    random_uuid = str(uuid.uuid4())

    found = False  # change this to false when blocked on some song

    while True:
        if i == 0:
            # tagId is random uuid, backup=9c26cc1d-a28f-470f-90b0-161a8d04e886

            token = '{"accountId": {"s": "accountid"},' \
                    '"tagId": {"s": "' + random_uuid + '"},' '"timestamp": {"n": "' \
                    + str(int(datetime.timestamp(datetime.now()))) + '000"}}'
            token = str(token).encode("utf-8")
            token = str(base64.b64encode(token))[2:-1]
        querystring = {"limit": "100", "token": token}

        headers = {
            'authority': "www.shazam.com",
            'pragma': "no-cache",
            'cache-control': "no-cache,no-cache",
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/78.0.3904.97 Safari/537.36",
            'dnt': "1",
            'accept': "*/*",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "cors",
            'referer': "https://www.shazam.com/myshazam",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "en-US,en;q=0.9,hi;q=0.8,mr;q=0.7",
            'cookie': "fbm_210827375150=base_domain=.shazam.com; geoip_country=US; geoip_lat=32.925; "
                      "geoip_long=-96.892; "
                      "codever"
                      "=a3b244b8d73c4f5e426954d6822ca00e1c1bdcb949071b552b8165dccaa1d86e4e5dd7bbc50ba313bd270b5208be195a167094d3bfc988a8102dc288dda8f2e8550e629473614471cc148a5d307fb5d0cc548e0b0d3369f5fabef9d71c65dd6e0a93d41232981ee6409c03a760ef8fe0a4c57f308300f1db3defa3a8351b38754737ac20caf41f67adeb349ffb7eb66504f4fb083e4033cdfe92",
            'Host': "www.shazam.com",
            'Connection': "keep-alive"
        }

        response = requests.get(url, headers=headers, params=querystring)
        if not response.text:
            return song_names
        j = json.loads(response.text)
        tags = j["tags"]
        breakout = False
        for x in tags:
            stuck_song_key = -1  # get id from mac intellij db
            if not found and x['track']['key'] == str(stuck_song_key):
                found = True

            if not found:
                continue

            if x['track']['key'] not in song_keys:

                key = x['track']['key']
                name = x["track"]["heading"]["title"] + " - " + x["track"]["heading"]["subtitle"]
                ts = x['timestamp']

                if upto_timestamp and str(ts) <= str(upto_timestamp):
                    breakout = True
                    break
                already_exists = check_already_exists(key)
                if already_exists:
                    print("Song {} already exists, updating timestamp".format(name))
                    update_timestamp(key, ts)
                    if not already_exists[3]:
                        print("Song {} does not have link. Trying to find downloadable link...".format(name))
                        update_song_link(key, name)
                    continue

                song_keys.add(key)
                song_names.append(name)

                save_to_db(song_key=key,
                           song_name=name,
                           song_timestamp=ts)
                print("Added {} to DB".format(name))
        i = 1
        if 'token' not in j:
            break
        if breakout:
            break
        token = j['token']
    return song_names


def check_new():
    query = 'select time from song_list order by time desc limit 1'
    res = execute_query(query, fetch_one=True)

    # change the arg to None when continuing
    # return get_song_list_from_shazam(None)
    return get_song_list_from_shazam(upto_timestamp=res[0] if res else None)


check_old_songs_count = 0
check_old_songs_interval = 30
poll_interval = 10
while True:
    try:
        print("Polling... ", end='')
        added = check_new()
        print("{} songs added".format(len(added)))
        check_old_songs_count += 1
        if check_old_songs_count == check_old_songs_interval:
            print("Checking old songs for new links...")
            check_old_songs()
            check_old_songs_count = 0
        print("Waiting for 10 seconds before polling...")
        time.sleep(poll_interval)
    except Exception as err:
        import traceback

        traceback.print_exc()
        msg = "Crashed ... Restarting in 10 seconds"
        check_old_songs_count = 0
        print(msg)
        notify(msg, crashed=True)
        time.sleep(10)
