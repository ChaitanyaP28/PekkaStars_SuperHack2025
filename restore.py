"""
restore.py
Removes some files / replaces them with the backed up code
"""

import os
import shutil
from pathlib import Path


def restore_backup_files(directory='.'):
    """
    Restore all .bkp files to their original filenames.
    
    Args:
        directory: The directory to search for .bkp files (default: current directory)
    """
    directory_path = Path(directory)
    
    # Find all .bkp files
    backup_files = list(directory_path.rglob('*.bkp'))
    
    if not backup_files:
        print("No .bkp files found.")
        return
    
    print(f"Found {len(backup_files)} backup file(s):\n")
    
    restored_count = 0
    skipped_count = 0
    
    for backup_file in backup_files:
        # Get the original filename by removing .bkp extension
        original_file = backup_file.with_suffix('')
        
        print(f"Processing: {backup_file.name}")
        
        # Check if original file exists
        if original_file.exists():
            response = input(f"  '{original_file.name}' already exists. Overwrite? (y/n): ").lower()
            if response != 'y':
                print(f"  Skipped: {backup_file.name}")
                skipped_count += 1
                continue
        
        try:
            # Restore the backup file
            shutil.copy2(backup_file, original_file)
            print(f"  ✓ Restored: {backup_file.name} -> {original_file.name}")
            restored_count += 1
            
            # Optionally, remove the backup file after restoration
            # Uncomment the next two lines if you want to delete .bkp files after restoring
            # os.remove(backup_file)
            # print(f"  ✓ Removed backup: {backup_file.name}")
            
        except Exception as e:
            print(f"  ✗ Error restoring {backup_file.name}: {e}")
    
    print(f"\n{'='*50}")
    print(f"Restoration complete!")
    print(f"  Restored: {restored_count} file(s)")
    print(f"  Skipped: {skipped_count} file(s)")
    print(f"{'='*50}")


if __name__ == "__main__":
    import sys
    print("Setting tmp1_py.txt to 'false' for testing purposes.")
    with open("tmp1_py.txt", "w") as f:
        f.write("false")
    
    # Allow specifying a directory as command-line argument
    if len(sys.argv) > 1:
        target_directory = sys.argv[1]
    else:
        target_directory = '.'
    
    print("=" * 50)
    print("Backup File Restoration Tool")
    print("=" * 50)
    print(f"Searching for .bkp files in: {os.path.abspath(target_directory)}\n")
    
    restore_backup_files(target_directory)

    with open ("requirements.txt", "w") as f:
        f.write("fastapi==0.120.4")
        f.write("uvicorn==0.38.0")
        f.write("packaging==25.0")
        f.write("numpy==2.2.3")

    print("Restored req.txt")