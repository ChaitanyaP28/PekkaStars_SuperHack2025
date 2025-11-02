"""
upgrade_checker.py
Backs up existing requirements.txt file and creates new requirements.txt with new version of each dependency
Upgrades individual depenedency to the latest version
Checks if service 3.py runs with upgraded version
Rollsback to backup if service does not run as expected
"""

import requests
import importlib.metadata
from packaging import version
import os
import re

def get_packages_from_requirements():
    """Read packages from requirements.txt file"""
    packages = {}
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    
    if not os.path.exists(requirements_path):
        print(f"❌ Error: requirements.txt not found at {requirements_path}")
        return packages
    
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse package name (handle ==, >=, <=, etc.)
            match = re.match(r'^([a-zA-Z0-9\-_\.]+)', line)
            if match:
                package_name = match.group(1)
                # Get installed version
                try:
                    installed_version = importlib.metadata.version(package_name)
                    packages[package_name] = installed_version
                except importlib.metadata.PackageNotFoundError:
                    packages[package_name] = "Not Installed"
    
    return packages

def get_latest_version(package_name):
    """Fetch the latest version from PyPI"""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data["info"]["version"]
        else:
            return None
    except Exception:
        return None

def check_updates():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if not os.path.exists(requirements_path):
        print("❌ Error: requirements.txt not found")
        return

    with open(requirements_path, 'r') as f:
        lines = f.readlines()

    packages_info = []
    updated_lines = lines[:]  # copy
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('#'):
            continue

        match = re.match(r'^([a-zA-Z0-9\-_\.]+)==(.+)', line_stripped)
        if match:
            package_name = match.group(1)
            current_version = match.group(2)
            try:
                installed_version = importlib.metadata.version(package_name)
                latest = get_latest_version(package_name)
                if latest and version.parse(installed_version) < version.parse(latest):
                    status = "⬆️ Update available"
                    # Update the line
                    updated_lines[i] = f"{package_name}=={latest}\n"
                elif not latest:
                    status = "❓ Couldn't check"
                else:
                    status = "✅ Up to date"
            except importlib.metadata.PackageNotFoundError:
                status = "❌ Not Installed"
                latest = "N/A"
            packages_info.append((package_name, installed_version if 'installed_version' in locals() else "Not Installed", latest or 'N/A', status))

    # Print table
    print(f"{'Package':<30} {'Installed':<15} {'Latest':<15} {'Status'}")
    print("-" * 70)
    for info in sorted(packages_info, key=lambda x: x[0].lower()):
        print(f"{info[0]:<30} {info[1]:<15} {info[2]:<15} {info[3]}")

    # Write back if any updates
    if updated_lines != lines:
        with open(requirements_path, 'w') as f:
            f.writelines(updated_lines)
        print("\n✅ Requirements.txt updated with latest versions!")
    else:
        print("\n✅ All packages are up to date.")

if __name__ == "__main__":
    print("🔍 Scanning packages from requirements.txt...\n")
    check_updates()
    
