"""
main.py
Entry point to PoC
Creates and starts web server to serve APIs
Start Orchestrator and Health Monitor after initializing respective web sockets
"""

# main.py - Admin Panel with Script Execution
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# WebSocket Health Monitor Configuration
HS_HM_HOST = os.getenv("HS_HM_HOST", "localhost")
HS_HM_PORT = os.getenv("HS_HM_PORT", "9001")

app = FastAPI(title="Admin Panel", description="Admin control panel for system management")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    """Serve the admin panel homepage"""
    return FileResponse("static/index.html")


@app.get("/api/health")
async def get_health():
    """API endpoint for health data (will be used for WebSocket later)"""
    return {
        "status": "ok",
        "message": "Admin panel is running",
        "version": "1.0.0"
    }


@app.get("/run/{script_name}")
async def run_script(script_name: str):
    """
    Execute a Python script in a new PowerShell terminal
    Allowed scripts: 1.py, 2.py, 3.py, upgrade_checker.py, orchestrator.py, health_websocket_simulator.py
    Special case: 1.py runs Code1.bat instead
    """
        # Validate script name to prevent security issues
    # Allow specific .py and .bat files only to avoid command injection
    allowed_scripts = [
        '1.py', '2.py', '3.py', 'upgrade_checker.py', 'orchestrator.py', 'health_websocket_simulator.py',
        'UpdateChecker.bat'
    ]
    
    if script_name not in allowed_scripts:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid script name. Allowed scripts: {', '.join(allowed_scripts)}"
        )
    
    try:
        # Special handling: run batch files directly (including Code1.bat for 1.py)
        if script_name == '1.py':
            script_path = os.path.abspath('Code1.bat')
            command_to_run = f'"{script_path}"'
        elif script_name.lower().endswith('.bat'):
            # Run the provided .bat file directly
            script_path = os.path.abspath(script_name)
            command_to_run = f'"{script_path}"'
        else:
            # Default: run Python scripts
            script_path = os.path.abspath(script_name)
            command_to_run = f'python "{script_path}"'
        
        # Check if the file exists
        if not os.path.exists(script_path):
            raise HTTPException(
                status_code=404,
                detail=f"File {script_name} not found"
            )
        
        # Open a new PowerShell terminal and run the command
        # The -NoExit flag keeps the terminal open after execution
        command = f'start pwsh -NoExit -Command "{command_to_run}"'
        
        subprocess.Popen(
            command,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        
        return JSONResponse(
            content={
                'success': True,
                'message': f'Opened new terminal to run {script_name}',
                'script': script_name
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-logs")
async def clear_logs():
    """
    Clear the log.txt file
    """
    try:
        # Ensure log file is in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, 'log.txt')

        # Truncate the file (create if not exists)
        with open(log_path, 'w', encoding='utf-8') as f:
            f.truncate(0)

        return JSONResponse(
            content={
                'success': True, 
                'message': 'Logs cleared successfully.'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear logs: {str(e)}"
        )


@app.get("/api/scripts")
async def get_scripts():
    """
    Get list of available scripts with their status
    """
    allowed_scripts = ['1.py', '2.py', '3.py', 'upgrade_checker.py', 'orchestrator.py', 'health_websocket_simulator.py']
    scripts_info = []
    
    for script in allowed_scripts:
        script_path = os.path.abspath(script)
        exists = os.path.exists(script_path)
        
        info = {
            'name': script,
            'exists': exists,
            'path': script_path if exists else None
        }
        
        if exists:
            # Get file size
            info['size'] = os.path.getsize(script_path)
            # Get last modified time
            info['modified'] = os.path.getmtime(script_path)
        
        scripts_info.append(info)
    
    return JSONResponse(content={'scripts': scripts_info})


@app.get("/api/logs")
async def get_logs():
    """
    Retrieve the contents of log.txt
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, 'log.txt')
        
        if not os.path.exists(log_path):
            return JSONResponse(content={'logs': '', 'message': 'Log file does not exist'})
        
        with open(log_path, 'r', encoding='utf-8') as f:
            logs = f.read()
        
        return JSONResponse(content={'logs': logs, 'size': len(logs)})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ws-logs")
async def get_ws_logs():
    """
    Retrieve the WebSocket server logs
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, '_ws_server_log.txt')
        
        if not os.path.exists(log_path):
            return JSONResponse(content={'logs': 'WebSocket server not started yet or no logs available.', 'size': 0})
        
        with open(log_path, 'r', encoding='utf-8') as f:
            logs = f.read()
        
        return JSONResponse(content={'logs': logs if logs else 'No logs yet...', 'size': len(logs)})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear-ws-logs")
async def clear_ws_logs():
    """
    Clear the WebSocket server log file
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, '_ws_server_log.txt')
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.truncate(0)
        
        return JSONResponse(content={'success': True, 'message': 'WebSocket logs cleared successfully.'})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")


@app.get("/api/orchestrator-logs")
async def get_orchestrator_logs():
    """
    Retrieve the Orchestrator logs
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, '_orchestrator_log.txt')
        
        if not os.path.exists(log_path):
            return JSONResponse(content={'logs': 'Orchestrator not started yet or no logs available.', 'size': 0})
        
        with open(log_path, 'r', encoding='utf-8') as f:
            logs = f.read()
        
        return JSONResponse(content={'logs': logs if logs else 'No logs yet...', 'size': len(logs)})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear-orchestrator-logs")
async def clear_orchestrator_logs():
    """
    Clear the Orchestrator log file
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, '_orchestrator_log.txt')
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.truncate(0)
        
        return JSONResponse(content={'success': True, 'message': 'Orchestrator logs cleared successfully.'})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")


@app.get("/api/health-status")
async def get_health_status():
    """
    Parse WebSocket logs to get health status of 1.py, 2.py, 3.py
    Reads only the last 2 lines for performance
    """
    try:
        import json
        import re
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, '_ws_server_log.txt')
        
        # Default status: all unhealthy
        health_status = {
            '1.py': {'healthy': False, 'status': 'Unhealthy'},
            '2.py': {'healthy': False, 'status': 'Unhealthy'},
            '3.py': {'healthy': False, 'status': 'Unhealthy'}
        }
        
        if not os.path.exists(log_path):
            return JSONResponse(content={'health': health_status})
        
        # Read last 2 lines of the file
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return JSONResponse(content={'health': health_status})
        
        # Get last 2 lines (or less if file has fewer lines)
        last_lines = lines[-2:] if len(lines) >= 2 else lines
        
        # Try to parse JSON from the last lines
        for line in reversed(last_lines):
            try:
                # Extract JSON from log line - look for pattern after "Received from ..."
                if 'Received from' in line and '{' in line:
                    # Find the JSON part (everything after the IP address)
                    json_start = line.find('{')
                    json_str = line[json_start:].strip()
                    
                    # Parse JSON
                    data = json.loads(json_str)
                    
                    # Extract apps data
                    if 'apps' in data and isinstance(data['apps'], list) and len(data['apps']) > 0:
                        # Iterate through ALL items in the apps array
                        for app_item in data['apps']:
                            # Each item is a dict like {"2.py": {"uuid": true}}
                            if isinstance(app_item, dict):
                                # Check each app we're interested in
                                for app_name in ['1.py', '2.py', '3.py']:
                                    if app_name in app_item:
                                        app_data = app_item[app_name]
                                        # Get the first value (which should be the boolean health status)
                                        if isinstance(app_data, dict):
                                            # Get first value from the dict
                                            health_value = next(iter(app_data.values()), False)
                                            health_status[app_name]['healthy'] = bool(health_value)
                                            health_status[app_name]['status'] = 'Healthy' if health_value else 'Unhealthy'
                        
                        # If we found valid data, break
                        break
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error parsing line: {e}")
                continue
        
        return JSONResponse(content={'health': health_status})
    
    except Exception as e:
        print(f"Error in get_health_status: {e}")
        return JSONResponse(content={
            'health': {
                '1.py': {'healthy': False, 'status': 'Error'},
                '2.py': {'healthy': False, 'status': 'Error'},
                '3.py': {'healthy': False, 'status': 'Error'}
            }
        })


if __name__ == '__main__':
    import uvicorn
    
    # Start WebSocket server in a new PowerShell terminal
    print("Launching Health Monitor WebSocket Server in new terminal...")
    
    # Create a Python script to run the WebSocket server
    ws_log_path = os.path.join(os.path.dirname(__file__), "_ws_server_log.txt")
    ws_script = f"""
import asyncio
import websockets
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

HS_HM_HOST = os.getenv("HS_HM_HOST", "localhost")
HS_HM_PORT = os.getenv("HS_HM_PORT", "9001")

# Log file path
LOG_FILE = r"{ws_log_path}"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{{timestamp}}] {{message}}"
    print(log_message)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + "\\n")
    except Exception as e:
        print(f"Error writing to log: {{e}}")

async def health_websocket_handler(ws):
    client_addr = ws.remote_address
    #log(f"Client connected: {{client_addr}}")
    try:
        async for msg in ws:
            log(f"Received from {{client_addr}}: {{msg}}")
            # Echo back or handle message
            await ws.send(f"Echo: {{msg}}")
            #log(f"Sent to {{client_addr}}: Echo: {{msg}}")
    except websockets.exceptions.ConnectionClosed:
        #log(f"Client disconnected: {{client_addr}}")
        pass
    except Exception as e:
        log(f"Error handling client {{client_addr}}: {{e}}")

async def start_websocket_server():
    log("=" * 60)
    log("WebSocket Health Monitor Server Starting...")
    log("=" * 60)
    server = await websockets.serve(health_websocket_handler, HS_HM_HOST, int(HS_HM_PORT))
    log(f"WebSocket server started on ws://{{HS_HM_HOST}}:{{HS_HM_PORT}}")
    log("Waiting for connections...")
    await asyncio.Future()

if __name__ == "__main__":
    # Clear log file on startup
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("")
    except:
        pass
    asyncio.run(start_websocket_server())
"""
    
    # Write temporary WebSocket script
    ws_script_path = os.path.join(os.path.dirname(__file__), "_ws_server_temp.py")
    with open(ws_script_path, 'w') as f:
        f.write(ws_script)
    
    # Launch WebSocket server in new terminal
    command = f'start pwsh -NoExit -Command "python {ws_script_path}"'
    subprocess.Popen(command, shell=True)
    
    print("WebSocket server launched in separate terminal")
    
    # Launch orchestrator.py in a new PowerShell terminal with output redirection
    print("Launching Orchestrator in new terminal...")
    orchestrator_path = os.path.join(os.path.dirname(__file__), "orchestrator.py")
    orchestrator_log_path = os.path.join(os.path.dirname(__file__), "_orchestrator_log.txt")
    
    if os.path.exists(orchestrator_path):
        # Clear log file
        with open(orchestrator_log_path, 'w', encoding='utf-8') as f:
            f.write("")
        
        # Use PowerShell to run Python and capture output with Tee-Object (shows in terminal AND saves to file)
        ps_command = f"$env:PYTHONUNBUFFERED='1'; python '{orchestrator_path}' 2>&1 | Tee-Object -FilePath '{orchestrator_log_path}'"
        command = f'start pwsh -NoExit -Command "{ps_command}"'
        subprocess.Popen(command, shell=True)
        print("Orchestrator launched in separate terminal")
    else:
        print("Warning: orchestrator.py not found, skipping...")
    
    # Give services time to start
    import time
    time.sleep(2)
    
    # Start FastAPI server
    print("Starting Admin Panel on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
