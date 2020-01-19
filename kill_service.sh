#!/usr/bin/env bash
APP_HOME="/home/aditya/MyShazamSongs"
kill $(cat $APP_HOME/script_run.pid)
kill $(cat $APP_HOME/server.pid)
