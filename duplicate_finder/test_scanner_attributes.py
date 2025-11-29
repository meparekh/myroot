import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from scanner import DuplicateScanner

class TestScannerAttributes(unittest.TestCase):
    def setUp(self):
        self.scanner = DuplicateScanner()

    @patch('os.walk')
    @patch('os.path.getsize')
    @patch('os.stat')
    @patch('os.path.islink')
    def test_skip_offline_files(self, mock_islink, mock_stat, mock_getsize, mock_walk):
        # Setup
        mock_walk.return_value = [('/root', [], ['file1.txt', 'file2.txt'])]
        mock_islink.return_value = False
        mock_getsize.return_value = 100
        
        # Mock file attributes
        # file1.txt is normal
        # file2.txt is offline (0x1000)
        
        attrs_normal = MagicMock()
        attrs_normal.st_file_attributes = 0
        
        attrs_offline = MagicMock()
        attrs_offline.st_file_attributes = 0x1000
        
        def stat_side_effect(path):
            if 'file2.txt' in path:
                return attrs_offline
            return attrs_normal
            
        mock_stat.side_effect = stat_side_effect
        
        # Execute
        self.scanner.scan_directory('/root')
        
        # Verify
        # Only file1.txt should be in files_by_size
        # Key is (size, ext) -> (100, '.txt')
        self.assertIn((100, '.txt'), self.scanner.files_by_size)
        self.assertEqual(len(self.scanner.files_by_size[(100, '.txt')]), 1)
        self.assertIn('file1.txt', self.scanner.files_by_size[(100, '.txt')][0])
        
        # file2.txt should NOT be there
        all_files = [f for files in self.scanner.files_by_size.values() for f in files]
        self.assertFalse(any('file2.txt' in f for f in all_files))

    @patch('os.walk')
    @patch('os.path.getsize')
    @patch('os.stat')
    @patch('os.path.islink')
    def test_skip_executables(self, mock_islink, mock_stat, mock_getsize, mock_walk):
        mock_walk.return_value = [('/root', [], ['program.exe', 'script.py'])]
        mock_islink.return_value = False
        mock_getsize.return_value = 500
        
        attrs = MagicMock()
        attrs.st_file_attributes = 0
        mock_stat.return_value = attrs
        
        self.scanner.scan_directory('/root')
        
        # program.exe should be skipped
        # script.py should be present
        self.assertIn((500, '.py'), self.scanner.files_by_size)
        self.assertNotIn((500, '.exe'), self.scanner.files_by_size)

    @patch('os.walk')
    @patch('os.path.getsize')
    @patch('os.stat')
    @patch('os.path.islink')
    def test_group_by_size_and_type(self, mock_islink, mock_stat, mock_getsize, mock_walk):
        mock_walk.return_value = [('/root', [], ['image.jpg', 'image.png'])]
        mock_islink.return_value = False
        
        # Both have same size
        mock_getsize.return_value = 2048
        
        attrs = MagicMock()
        attrs.st_file_attributes = 0
        mock_stat.return_value = attrs
        
        self.scanner.scan_directory('/root')
        
        # Should be in DIFFERENT groups despite same size
        self.assertIn((2048, '.jpg'), self.scanner.files_by_size)
        self.assertIn((2048, '.png'), self.scanner.files_by_size)
        
        # Neither group should be considered a "potential duplicate" yet (len=1)
        potential_duplicates = [paths for paths in self.scanner.files_by_size.values() if len(paths) > 1]
        self.assertEqual(len(potential_duplicates), 0)

if __name__ == '__main__':
    unittest.main()
