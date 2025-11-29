import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem
from PyQt6.QtCore import Qt

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from ui import DuplicateFinderUI

class TestDeletionLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.ui = DuplicateFinderUI()
        # Mock the history manager to avoid DB writes
        self.ui.history_manager = MagicMock()
        self.ui.start_scan = MagicMock() # Prevent actual rescanning

    @patch('os.remove')
    @patch('os.path.getsize')
    @patch('PyQt6.QtWidgets.QMessageBox.question')
    def test_delete_selected_calculates_space(self, mock_question, mock_getsize, mock_remove):
        # Setup mocks
        mock_question.return_value = 16384 # QMessageBox.StandardButton.Yes (value varies, but usually Yes is accepted if we mock the return to match the check)
        # Actually, let's check what StandardButton.Yes value is or just mock the result comparison
        # In the code: if reply == QMessageBox.StandardButton.Yes:
        # We can just return the actual enum value if we import it, or mock the comparison.
        # Easier: return QMessageBox.StandardButton.Yes
        from PyQt6.QtWidgets import QMessageBox
        mock_question.return_value = QMessageBox.StandardButton.Yes
        
        mock_getsize.return_value = 1024 * 1024 # 1 MB per file
        
        # Populate tree with mock items
        root = self.ui.tree.invisibleRootItem()
        group = QTreeWidgetItem(root)
        group.setText(0, "Group 1")
        
        item1 = QTreeWidgetItem(group)
        item1.setText(2, "/path/to/file1.jpg")
        item1.setCheckState(0, Qt.CheckState.Checked)
        
        item2 = QTreeWidgetItem(group)
        item2.setText(2, "/path/to/file2.jpg")
        item2.setCheckState(0, Qt.CheckState.Checked)
        
        # Execute deletion
        self.ui.delete_selected()
        
        # Verify os.remove was called
        self.assertEqual(mock_remove.call_count, 2)
        
        # Verify status label text
        # Expected: "Deleted 2 files." -> This is the CURRENT behavior.
        # We want to verify it changes to something like "Deleted 2 files (2.00 MB recovered)."
        status_text = self.ui.status_label.text()
        print(f"Status Text: {status_text}")
        
        # Verify history logging
        # self.ui.history_manager.log_cleanup.assert_called_with(['/path/to/file1.jpg', '/path/to/file2.jpg'], 2097152)

if __name__ == '__main__':
    unittest.main()
