"""
orchestrator.py
Interface between web UI and individiual services
Each service when starting requests for an ID provided by orchestrator
ID used to track health of the service
Invokes AI agent on Critical Failure logs are seen
Collects heartbeat logs and sends health status to health monitor
"""

import asyncio
import websockets
import uuid
import re
import os
import threading
import subprocess
import sys
import shutil
import json
import time

from datetime import datetime, timedelta
from threading import Thread
from dotenv import load_dotenv
load_dotenv()

WS_HOST = os.getenv("WS_HOST")
WS_PORT = os.getenv("WS_PORT")

APP_HOST = os.getenv("APP_HOST")
APP_PORT = os.getenv("APP_PORT")

HB_HOST = os.getenv("HB_HOST")
HB_PORT = os.getenv("HB_PORT")
HB_TIMEOUT = int(os.getenv("HB_TIMEOUT"))

HS_HOST = os.getenv("HS_HOST")
HS_PORT = os.getenv("HS_PORT")

HS_HM_HOST = os.getenv("HS_HM_HOST")
HS_HM_PORT = os.getenv("HS_HM_PORT")

HS_HM_URI = "ws://" + HS_HM_HOST + ":" + HS_HM_PORT

# Dict: 'app_id' : (last_health_ts, current_health)
HEALTH = dict()

LOG_FORMAT = r'\[[^\]]*\] '

app_name_to_id = dict()

connection_app_map = {}  # Maps websocket connections to app IDs
ai_agent_running = False  # Flag to prevent multiple simultaneous AI agent executions
ai_agent_lock = threading.Lock()  # Thread lock for AI agent execution

def parse_log(msg):
    app_id, sev, ts = [x.lstrip('[').rstrip('] ') for x in re.findall(LOG_FORMAT, msg)]
    txt = re.split(LOG_FORMAT, msg)[-1]
    return app_id, sev, ts

def apply_fixed_code(original_filename=None):
    """
    After AI agent completes, this function:
    1. Reads fixed_output.py
    2. Determines the original faulty filename from app_name
    3. Creates a backup of the original file as <filename>.py.bkp
    4. Replaces the original file with the fixed code
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fixed_output_path = os.path.join(script_dir, "fixed_output.py")
    
    # Check if fixed_output.py exists
    if not os.path.exists(fixed_output_path):
        print("fixed_output.py not found. AI agent may not have completed successfully.")
        return False
    
    # Use provided filename or default
    if not original_filename:
        print("Original filename not provided. Using 'faulty.py' as default.")
        original_filename = "faulty.py"
    
    original_path = os.path.join(script_dir, original_filename)
    
    # Check if original file exists
    if not os.path.exists(original_path):
        print(f"Original file '{original_filename}' not found at {original_path}")
        return False
    
    try:
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{original_filename}.bkp"
        backup_path = os.path.join(script_dir, backup_filename)
        
        # If a backup already exists, add timestamp to avoid overwriting
        if os.path.exists(backup_path):
            base_name = original_filename.rsplit('.', 1)[0]
            backup_filename = f"{base_name}_{timestamp}.py.bkp"
            backup_path = os.path.join(script_dir, backup_filename)
        
        # Create backup of original file
        print(f"\nCreating backup: {backup_filename}")
        shutil.copy2(original_path, backup_path)
        print(f"Backup created successfully at {backup_path}")
        
        # Read the fixed code
        with open(fixed_output_path, "r", encoding="utf-8") as f:
            fixed_code = f.read()
        
        # Replace original file with fixed code
        print(f"\nReplacing {original_filename} with fixed code...")
        with open(original_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)
        print(f"{original_filename} has been updated with the fixed code!")
        
        print(f"\n{'='*60}")
        print("Code fix applied successfully!")
        print(f"Original backed up to: {backup_filename}")
        print(f"Fixed code applied to: {original_filename}")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\nError applying fixed code: {e}")
        return False


def run_ai_agent(original_filename=None):
    """Run AiAgent.py in a separate thread to analyze and fix errors."""
    global ai_agent_running
    
    with ai_agent_lock:
        if ai_agent_running:
            print("AI Agent is already running. Skipping duplicate execution.")
            return
        ai_agent_running = True
    
    try:
        print("\n" + "="*60)
        print("Starting AI Agent to analyze and fix the error...")
        print("="*60 + "\n")
        
        # Get the path to AiAgent.py in the same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ai_agent_path = os.path.join(script_dir, "AiAgent.py")
        
        if not os.path.exists(ai_agent_path):
            print(f"AiAgent.py not found at {ai_agent_path}")
            return
        
        # Run AiAgent.py as a subprocess
        result = subprocess.run(
            [sys.executable, ai_agent_path],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        # Print the output from AiAgent
        if result.stdout:
            print("\n--- AI Agent Output ---")
            print(result.stdout)
        
        if result.stderr:
            print("\n--- AI Agent Errors ---")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\nAI Agent completed successfully!")
            
            # Apply the fixed code automatically
            print("\nAttempting to apply the fixed code...")
            if apply_fixed_code(original_filename):
                print("Fixed code has been applied and original backed up!")
            else:
                print("Could not automatically apply fixed code. Please check manually.")
        else:
            print(f"\nAI Agent exited with code {result.returncode}")
        
        print("\n" + "="*60 + "\n")
        
    except subprocess.TimeoutExpired:
        print("\nAI Agent execution timed out after 2 minutes")
    except Exception as e:
        print(f"\nError running AI Agent: {e}")
    finally:
        with ai_agent_lock:
            ai_agent_running = False

async def app_id_handler(ws):
    global app_name_to_id
    try:
        msg = await ws.recv()
        app_id = str(uuid.uuid4())
        if msg not in app_name_to_id.keys():
            app_name_to_id[msg] = []
        app_name_to_id[msg].append(app_id)
        await ws.send(app_id)
    finally:
        pass

async def hb_handler(ws):
    global HEALTH
    try:
        msg = await ws.recv()
        app_id, sev, ts = parse_log(msg)
        if "Heartbeat" in msg:
            HEALTH[app_id] = ts
        else:
            del HEALTH[app_id]
    finally:
        pass

def is_healthy(ts, app_id):
    global HEALTH
    if app_id not in HEALTH.keys():
        return False

    new_ts = datetime.fromisoformat(ts)
    old_ts = datetime.fromisoformat(HEALTH[app_id])

    if (new_ts - old_ts) >= timedelta(seconds=HB_TIMEOUT):
        return False
    return True

def health_handler():
    ts = datetime.now().isoformat()
    all_apps_health = {"timestamp": ts, "apps": []}
    for app_name in app_name_to_id.keys():
        # {"id1": True, "id2": False}
        app_id_healths = {}
        for app_id in set(app_name_to_id[app_name]) & set(HEALTH.keys()):
            app_id_healths[app_id] = is_healthy(ts, app_id)

        # {"name1": {"id1": True, "id2": False}}
        app_name_health = None
        if app_id_healths:
            app_name_health = {app_name: app_id_healths}

        # {"timestamp": "now()", "apps": ["name1": {...}, "name2": {...}]}
        if app_name_health:
            all_apps_health["apps"].append(app_name_health)
    return json.dumps(all_apps_health)

async def stream_handler(ws):
    try:
        # Get app identifier from first message
        first_msg = True
        app_name = None
        
        async for msg in ws:
            # Check if first message contains app name/identifier
            if first_msg:
                first_msg = False
                # Extract app name from the message format: [APP_NAME] rest of message
                match = re.match(r'\[([^\]]+)\]\s', msg)
                if match:
                    app_name = match.group(1)
                else:
                    app_name = f"App_{id(ws)}"  # Using connection ID as fallback
                

            sev=parse_log(msg)[1]
            print(f"\n{'='*60}\nApplication: {app_name}\n{'='*60}\n")
            print(msg, end='')
            if sev == "ERROR" or sev == "FATAL":
                with open('log.txt', 'a', encoding='utf-8') as log_file:
                    log_file.write(f"{'='*60}\n")
                    log_file.write(f"Application: {app_name}\n")
                    log_file.write(f"{'='*60}\n")
                    log_file.write(msg)
            
            # Trigger AI Agent in a separate thread for ERROR or FATAL
            if sev == "ERROR" or sev == "FATAL":
                print(f"{sev.strip()} detected! Triggering AI Agent...")
                # Run AI Agent in a separate thread to avoid blocking
                # Pass the app_name (which is the original filename) to the AI agent
                ai_thread = threading.Thread(target=run_ai_agent, args=(app_name,), daemon=False)
                ai_thread.start()
            
            if sev == "FATAL":
                print(f"Application {app_name} has logged a FATAL error. Closing connection.")
                await ws.close()
            elif sev == "ERROR":
                print(f"Application {app_name} has logged an ERROR.")
    finally:
        pass

async def appid_ws():
    app_server = websockets.serve(app_id_handler, APP_HOST, APP_PORT)
    async with app_server:
        await asyncio.Future()

async def stream_ws():
    ws_server = websockets.serve(stream_handler, WS_HOST, WS_PORT)
    async with ws_server:
        await asyncio.Future()

async def hb_ws():
    hb_server = websockets.serve(hb_handler, HB_HOST, HB_PORT)
    async with hb_server:
        await asyncio.Future()

async def report_health_ws():
    while True:
        all_health = health_handler()
        try:
            async with websockets.connect(HS_HM_URI) as ws:
                await ws.send(all_health)
        finally:
            pass
        time.sleep(1)

def hs_hm_thread():
    asyncio.run(report_health_ws())

async def main():
    print("I am Running")
    appid_task = asyncio.create_task(appid_ws())
    stream_task = asyncio.create_task(stream_ws())
    hb_task = asyncio.create_task(hb_ws())
    Thread(target=hs_hm_thread, daemon=True).start()

    await asyncio.gather(appid_task, stream_task, hb_task)

if __name__ == "__main__":
    asyncio.run(main())
