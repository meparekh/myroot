import os
import shutil
import time
from scanner import DuplicateScanner

def create_dummy_files(base_path):
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    os.makedirs(base_path)

    # File 1
    with open(os.path.join(base_path, "file1.txt"), "w") as f:
        f.write("content A")
    
    # File 2 (Duplicate of 1)
    with open(os.path.join(base_path, "file2.txt"), "w") as f:
        f.write("content A")

    # File 3 (Different)
    with open(os.path.join(base_path, "file3.txt"), "w") as f:
        f.write("content B")

    # File 4 (Duplicate of 1 in subdir)
    os.makedirs(os.path.join(base_path, "subdir"))
    with open(os.path.join(base_path, "subdir", "file4.txt"), "w") as f:
        f.write("content A")

    # File 5 (Same size as 1 but different content)
    with open(os.path.join(base_path, "file5.txt"), "w") as f:
        f.write("content C") # Assuming "content C" is same length as "content A" (9 chars)

    return base_path

def test_scanner():
    base_path = "test_duplicates"
    create_dummy_files(base_path)
    
    scanner = DuplicateScanner()
    duplicates = scanner.scan_directory(base_path)
    
    print(f"Found {len(duplicates)} duplicate groups.")
    for group in duplicates:
        print(f"Hash: {group['hash']}, Size: {group['size']}")
        for file in group['files']:
            print(f"  - {file}")
            
    # Assertions
    assert len(duplicates) == 1
    assert len(duplicates[0]['files']) == 3
    print("Test Passed!")

if __name__ == "__main__":
    test_scanner()
