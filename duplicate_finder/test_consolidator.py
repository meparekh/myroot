import os
import shutil
import unittest
from pathlib import Path
from consolidator import MediaConsolidator

class TestMediaConsolidator(unittest.TestCase):
    def remove_long_path(self, path):
        path = str(path)
        if os.name == 'nt' and not path.startswith('\\\\?\\'):
            path = f"\\\\?\\{path}"
        
        if os.path.isdir(path):
            try:
                for entry in os.scandir(path):
                    self.remove_long_path(entry.path)
                os.rmdir(path)
            except OSError:
                pass
        else:
            try:
                os.remove(path)
            except OSError:
                pass

    def setUp(self):
        self.test_dir = Path("test_consolidation_env")
        if self.test_dir.exists():
            self.remove_long_path(self.test_dir.resolve())
        self.test_dir.mkdir()
        
        # Create mock structure
        (self.test_dir / "Photos" / "Vacation").mkdir(parents=True)
        (self.test_dir / "Downloads").mkdir()
        (self.test_dir / "AppData" / "Local").mkdir(parents=True)
        (self.test_dir / "Documents").mkdir()
        
        # Create files
        self.create_file(self.test_dir / "Photos" / "Vacation" / "img1.jpg")
        self.create_file(self.test_dir / "Photos" / "Vacation" / "img2.jpg")
        self.create_file(self.test_dir / "Downloads" / "img3.png")
        self.create_file(self.test_dir / "AppData" / "Local" / "cache.jpg")
        self.create_file(self.test_dir / "Documents" / "doc.txt")
        
        self.consolidator = MediaConsolidator()

    def create_file(self, path):
        with open(path, 'w') as f:
            f.write("content")

    def tearDown(self):
        if self.test_dir.exists():
            # Custom rmtree for long paths on Windows
            def remove_long_path(path):
                path = str(path)
                if os.name == 'nt' and not path.startswith('\\\\?\\'):
                    path = f"\\\\?\\{path}"
                
                if os.path.isdir(path):
                    try:
                        for entry in os.scandir(path):
                            remove_long_path(entry.path)
                        os.rmdir(path)
                    except OSError:
                        pass
                else:
                    try:
                        os.remove(path)
                    except OSError:
                        pass

            remove_long_path(self.test_dir.resolve())

    def test_consolidation_and_organization(self):
        print("\nRunning Consolidation Test...")
        
        # Create junk file to test cleanup
        self.create_file(self.test_dir / "Photos" / "Vacation" / "._junk.jpg")
        
        # Create long path file
        # We need to ensure the path we create is also using extended syntax for the test setup to work
        long_dir_name = "VeryLongPathName" * 15
        if os.name == 'nt':
            long_dir = Path(f"\\\\?\\{os.path.abspath(self.test_dir / 'Photos' / long_dir_name)}")
        else:
            long_dir = self.test_dir / "Photos" / long_dir_name
            
        long_dir.mkdir(parents=True)
        self.create_file(long_dir / "long_path_img.jpg")
        
        # Run consolidation (Step 1)
        files_moved, bytes_moved = self.consolidator.consolidate_drive(
            str(self.test_dir), 
            log_callback=lambda msg: print(f"LOG: {msg}")
        )
        
        target_root = self.test_dir / "ConsolidatedMedia"
        
        # Assertions for Consolidation (Structure Preserved)
        self.assertTrue(target_root.exists(), "Target root should exist")
        
        # Check moved files - Should be in [ParentFolder] directly, NOT Photos/Videos yet
        self.assertTrue((target_root / "Vacation" / "img1.jpg").exists(), "img1 should be in Vacation")
        self.assertTrue((target_root / "Downloads" / "img3.png").exists(), "img3 should be in Downloads")
        
        # Check long path file moved
        parent_name = long_dir.name
        long_file_path = target_root / parent_name / "long_path_img.jpg"
        if os.name == 'nt':
            long_file_path = Path(f"\\\\?\\{os.path.abspath(long_file_path)}")
        self.assertTrue(long_file_path.exists(), "Long path file should be moved")
        
        print(f"Consolidation Passed. Moved {files_moved} files.")
        
        # Run Organization (Step 2)
        print("\nRunning Organization Test...")
        self.consolidator.organize_folder(
            str(target_root),
            log_callback=lambda msg: print(f"ORG_LOG: {msg}")
        )
        
        # Assertions for Organization (Flattened into Photos/Videos)
        self.assertTrue((target_root / "Photos" / "img1.jpg").exists(), "img1 should be in Photos")
        self.assertTrue((target_root / "Photos" / "img3.png").exists(), "img3 should be in Photos")
        
        # Check long path file organized
        long_file_path_org = target_root / "Photos" / "long_path_img.jpg"
        if os.name == 'nt':
            long_file_path_org = Path(f"\\\\?\\{os.path.abspath(long_file_path_org)}")
        self.assertTrue(long_file_path_org.exists(), "Long path file should be in Photos")
        
        # Check cleanup of empty folders
        self.assertFalse((target_root / "Vacation").exists(), "Vacation folder should be removed")
        
        print("Organization Passed.")

if __name__ == '__main__':
    unittest.main()
