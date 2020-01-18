import datetime
import time


def error(message):
    info("Some error occurred")
    with open("error.log", "a") as err_file:
        import time
        import datetime

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        err_file.write(st)
        err_file.write("\n===============================\n")
        err_file.write(message)
        err_file.write("\n\n\n")
    delete("error.log", 30)


def info(message):
    with open("info.log", "a") as info_file:
        import time
        import datetime

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        info_file.write(st)
        info_file.write(":\t")
        info_file.write(message)
        info_file.write("\n")

    delete("info.log", days=7)


def delete(file, days):
    with open(file, "r") as target_file:
        first_date = target_file.readline().split(" ")[0]
        today = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')

        first_date = map(lambda x: int(x), first_date.split("-"))
        today = map(lambda x: int(x), today.split("-"))

        fdate = datetime.date(*first_date)
        tdate = datetime.date(*today)

    if (fdate - tdate).days > days:
        with open(file, "w") as f:
            f.write("--RESET FILE--\n")
            f.close()
