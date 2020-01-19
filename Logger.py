import sys
import datetime
import time

_info = 0
_error = 0

try:
    APP_HOME = sys.argv[1]
except IndexError:
    APP_HOME = '/home/aditya/MyShazamSongs'

def error(message):
    global _error
    global APP_HOME
    print(message,"lol")
    info("Some error occurred")
    with open(APP_HOME + "/error.html", "a") as err_file:
        if _error == 0:
            _error = 1
            err_file.write('<meta http-equiv="refresh" content="2">\n\n\n<br>')

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        err_file.write(st)
        err_file.write("\n===============================\n")
        err_file.write(message)
        err_file.write("\t\t\t<br><br><br>\n")

    delete(APP_HOME + "/error.html", days=30)


def info(message):
    global _info
    global APP_HOME
    with open(APP_HOME + "/info.html", "a") as info_file:
        if _info == 0:
            _info = 1
            info_file.write('<meta http-equiv="refresh" content="2">\n\n\n<br>')

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        info_file.write(st)
        info_file.write(":\t")
        info_file.write(message)
        info_file.write("\t\t\t\t\t\t<br>\n")

    delete(APP_HOME + "/info.html", days=7)


def delete(file, days):
    with open(file, "r") as target_file:
        splitted = target_file.readline().split('<meta http-equiv="refresh" content="2">\n\n\n')
        if len(splitted) < 2:
            return

        first_date = target_file.readline().split('<meta http-equiv="refresh" content="2">\n\n\n')[1]
        today = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')

        first_date = map(lambda x: int(x), first_date.split("-"))
        today = map(lambda x: int(x), today.split("-"))

        fdate = datetime.date(*first_date)
        tdate = datetime.date(*today)

    if (fdate - tdate).days > days:
        with open(file, "w") as f:
            f.write("--RESET FILE--\n")
            f.close()
