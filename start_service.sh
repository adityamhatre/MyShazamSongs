#!/usr/bin/env bash
APP_HOME="/home/aditya/MyShazamSongs"

$APP_HOME/kill_service.sh

rm -f $APP_HOME/*.html
rm -f $APP_HOME/*.out
rm -f $APP_HOME/*.pid

python3 $APP_HOME/test.py $APP_HOME
nohup python3 $APP_HOME/Connector.py $APP_HOME &
echo $! > $APP_HOME/script_run.pid
cat $APP_HOME/script_run.pid

nohup python3 -m http.server -d $APP_HOME 1337 &
echo $! > $APP_HOME/server.pid
cat $APP_HOME/server.pid

if [[ $1 -ne 1 ]]
then
	tail -f --retry $APP_HOME/info.html
else
	echo "Not printing logs"
fi

