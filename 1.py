""" Service 1.py: Simulate auto-restart on failure """

import os
import asyncio
import websockets
import time

from datetime import datetime
from threading import Thread, Event

from dotenv import load_dotenv
load_dotenv()

LOG_FILE = "log.txt"
LOG_MODE = "a"

WS_HOST = os.getenv("WS_HOST")
WS_PORT = os.getenv("WS_PORT")

APP_HOST = os.getenv("APP_HOST")
APP_PORT = os.getenv("APP_PORT")

HB_HOST = os.getenv("HB_HOST")
HB_PORT = os.getenv("HB_PORT")

APPSOCKET_URI = "ws://" + APP_HOST + ":" + APP_PORT
WEBSOCKET_URI = "ws://" + WS_HOST + ":" + WS_PORT
HB_URI = "ws://" + HB_HOST + ":" + HB_PORT

APP_ID = "read-from-serv"
APP_NAME = "1.py"

hb_stop = Event()
hb_thread = None

async def send_heartbeats():
    global hb_stop
    while not hb_stop.is_set():
        async with websockets.connect(HB_URI) as ws:
            hb_line = f"[{APP_ID}] [INFO] [{datetime.now().isoformat()}] Heartbeat"
            await ws.send(hb_line)
        time.sleep(1)

def hb_thread_wrapper():
    asyncio.run(send_heartbeats())

async def get_app_id():
    global APP_ID
    global APP_NAME
    async with websockets.connect(APPSOCKET_URI) as ws:
        await ws.send(f"{APP_NAME}")
        APP_ID = await ws.recv()

def init():
    global APP_ID
    global hb_thread
    asyncio.run(get_app_id())
    if os.path.exists(LOG_FILE):
        log(f"Application 1.py restarted with UUID: ${APP_ID}")
    else:
        LOG_MODE = "w"
        log(f"Application 1.py started with UUID: ${APP_ID}")
        LOG_MODE = "a"
    hb_thread = Thread(target=hb_thread_wrapper, daemon=True)
    hb_thread.start()

async def rm_app_id():
    global APP_ID
    global APP_NAME
    async with websockets.connect(HB_URI) as ws:
        rm_line = f"[{APP_ID}] [INFO] [{datetime.now().isoformat()}] Exit"
        await ws.send(rm_line)

def deinit():
    global hb_stop
    global hb_thread
    hb_stop.set()
    hb_thread.join()

    asyncio.run(rm_app_id())

async def stream(log_line):
    global APPID
    async with websockets.connect(WEBSOCKET_URI) as ws:
        await ws.send(f"[{APP_NAME}] {log_line}")

def log(msg, sev="INFO", ts=datetime.now().isoformat()):
    global APP_ID
    log_line = f"[{sev}] [{ts}] {msg}\n"
    asyncio.run(stream(log_line))

def info(msg):
    log(msg, sev="INFO")

if __name__ == "__main__":
    init()
    try:
        time.sleep(1)
        with open("tmp1_py.txt", "r") as f:
            data = f.read().strip().lower()

        with open("tmp1_py.txt", "w") as f:
            f.write("true")

        if data == "false":
            print("Im Good")
            time.sleep(5)
            print("Error:")
            raise "DIE"

        info("Hello World from 1.py!")
        while True:
            print("I am Good Now")
            time.sleep(1000)
        log("Application 1.py completed successfully")

    finally:
        deinit()
