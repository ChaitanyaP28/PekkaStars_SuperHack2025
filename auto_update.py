"""
auto_update.py
Creates a backup of the dependencies and their versions
For each depenedency, updates requirements.txt with latest version available online
Upgrade each depenedency to the version listed in requiremnets.txt
Runs service to check if dependency works with upgraded version
Rollsback to backup if service failed to start with upgraded version
"""
import os
import subprocess
import shutil

REQ_FILE = "requirements.txt"
BACKUP_FILE = "requirements.txt.bkp"

def backup_requirements():
    if os.path.exists(REQ_FILE):
        shutil.copy(REQ_FILE, BACKUP_FILE)
        with open(BACKUP_FILE, "r") as f:
            libs = [line.strip().split("==")[0] for line in f if line.strip()]
        with open(BACKUP_FILE, "w") as f:
            for lib in libs:
                result = subprocess.run(["pip", "show", lib], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if line.startswith("Version:"):
                        version = line.split(":")[1].strip()
                        f.write(f"{lib}=={version}\n")

        print("[+] Backup created as requirements.txt.bkp")
    else:
        print("[-] requirements.txt not found.")
        exit()

def upgrade_libraries():
    print("[+] Upgrading libraries to latest versions...")
    subprocess.run(["pip", "install", "-r", REQ_FILE])
    with open(REQ_FILE, "r") as f:
        libs = [line.strip().split("==")[0] for line in f if line.strip()]
    with open(REQ_FILE, "w") as f:
        for lib in libs:
            result = subprocess.run(["pip", "show", lib], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    version = line.split(":")[1].strip()
                    f.write(f"{lib}=={version}\n")
    print("[+] requirements.txt updated with latest versions.")

def install_requirements(file):
    subprocess.run(["pip", "install", "-r", file])

def run_test():
    print("[+] Running 3.py ...")
    result = subprocess.run(["python", "3.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("[-] Crash detected:", result.stderr)
        return False
    return True

def restore_backup():
    print("[+] Restoring from backup...")
    shutil.copy(BACKUP_FILE, REQ_FILE)
    install_requirements(REQ_FILE)
    print("[+] Old versions restored successfully.")

def main():
    print("=== MCP LIBRARY UPDATE SYSTEM ===")
    backup_requirements()
    upgrade_libraries()
    success = run_test()
    if not success:
        restore_backup()
        print("[+] Re-running test with old versions...")
        run_test()
    print("=== PROCESS COMPLETE ===")

if __name__ == "__main__":
    main()
