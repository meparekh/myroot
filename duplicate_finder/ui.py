import sys
import os
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, 
                             QProgressBar, QLabel, QMessageBox, QTabWidget, QHeaderView,
                             QSplitter, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
from scanner import DuplicateScanner
from database import HistoryManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ScanThread(QThread):
    progress_update = pyqtSignal(int)
    scan_complete = pyqtSignal(list)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.scanner = DuplicateScanner()

    def run(self):
        duplicates = self.scanner.scan_directory(self.path, self.progress_update.emit)
        self.scan_complete.emit(duplicates)

class DuplicateFinderUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Duplicate File Finder")
        self.resize(1000, 700)
        self.history_manager = HistoryManager()
        self.init_ui()

    def init_ui(self):
        from PyQt6.QtGui import QImageReader
        supported_formats = [fmt.data().decode('utf-8') for fmt in QImageReader.supportedImageFormats()]
        logging.info(f"UI: Supported image formats: {supported_formats}")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Scan & Results
        self.scan_tab = QWidget()
        self.init_scan_tab()
        self.tabs.addTab(self.scan_tab, "Scan & Clean")

        # Tab 2: History
        self.history_tab = QWidget()
        self.init_history_tab()
        self.tabs.addTab(self.history_tab, "History")
        
        self.tabs.currentChanged.connect(self.on_tab_change)

    def init_scan_tab(self):
        layout = QVBoxLayout(self.scan_tab)

        # Top Bar: Path Selection
        path_layout = QHBoxLayout()
        self.path_input = QLabel("No directory selected")
        self.path_input.setStyleSheet("border: 1px solid #ccc; padding: 5px; background: white;")
        browse_btn = QPushButton("Browse Folder")
        browse_btn.clicked.connect(self.browse_folder)
        self.scan_btn = QPushButton("Start Scan")
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)

        path_layout.addWidget(self.path_input, 1)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(self.scan_btn)
        layout.addLayout(path_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results Area (Splitter for Tree and Preview)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File", "Size", "Path"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree.itemChanged.connect(self.on_item_changed)
        self.tree.itemClicked.connect(self.on_item_clicked)
        splitter.addWidget(self.tree)

        # Preview Widget
        self.preview_label = QLabel("Select an image to preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.setMinimumWidth(300)
        splitter.addWidget(self.preview_label)

        layout.addWidget(splitter, 1)

        # Bottom Bar: Actions
        action_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected)
        
        # Auto-select buttons
        select_older_btn = QPushButton("Select Older")
        select_older_btn.clicked.connect(lambda: self.auto_select('older'))
        select_newer_btn = QPushButton("Select Newer")
        select_newer_btn.clicked.connect(lambda: self.auto_select('newer'))

        action_layout.addWidget(self.status_label, 1)
        action_layout.addWidget(select_older_btn)
        action_layout.addWidget(select_newer_btn)
        action_layout.addWidget(delete_btn)
        layout.addLayout(action_layout)

    def init_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)
        refresh_btn = QPushButton("Refresh History")
        refresh_btn.clicked.connect(self.load_history)
        layout.addWidget(refresh_btn)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.path_input.setText(folder)
            self.scan_btn.setEnabled(True)

    def start_scan(self):
        path = self.path_input.text()
        if not os.path.exists(path):
            logging.warning(f"Path does not exist: {path}")
            return

        logging.info(f"UI: Starting scan for path: {path}")
        self.tree.clear()
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.status_label.setText("Scanning...")

        self.thread = ScanThread(path)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.scan_complete.connect(self.on_scan_complete)
        self.thread.start()

    def update_progress(self, count):
        self.status_label.setText(f"Scanned {count} files...")

    def on_scan_complete(self, duplicates):
        logging.info(f"UI: Scan complete. Received {len(duplicates)} duplicate groups.")
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.status_label.setText(f"Found {len(duplicates)} groups of duplicates.")
        self.populate_tree(duplicates)

    def populate_tree(self, duplicates):
        self.tree.clear()
        for group in duplicates:
            size_str = f"{group['size'] / 1024:.2f} KB"
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, f"Duplicate Group ({len(group['files'])} files)")
            group_item.setText(1, size_str)
            group_item.setFlags(group_item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            group_item.setCheckState(0, Qt.CheckState.Unchecked)

            for file_path in group['files']:
                file_item = QTreeWidgetItem(group_item)
                file_item.setText(0, os.path.basename(file_path))
                file_item.setText(1, size_str)
                file_item.setText(2, file_path)
                file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                file_item.setCheckState(0, Qt.CheckState.Unchecked)
        
        self.tree.expandAll()

    def on_item_changed(self, item, column):
        # Handle parent/child checkbox logic if needed (Tristate handles most)
        pass

    def on_item_clicked(self, item, column):
        path = item.text(2)
        logging.info(f"UI: Item clicked. Column: {column}, Path from text(2): '{path}'")
        
        if path and os.path.exists(path):
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff')):
                try:
                    pixmap = QPixmap(path)
                    if not pixmap.isNull():
                        logging.info(f"UI: Loaded pixmap for {path}. Size: {pixmap.width()}x{pixmap.height()}")
                        scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.preview_label.setPixmap(scaled_pixmap)
                    else:
                        logging.error(f"UI: Failed to load pixmap for {path}. Pixmap is null.")
                        self.preview_label.setText("Invalid Image (Load Failed)")
                except Exception as e:
                    logging.error(f"UI: Exception loading image {path}: {e}")
                    self.preview_label.setText(f"Error loading image: {e}")
            else:
                logging.info(f"UI: File extension not supported for preview: {path}")
                self.preview_label.setText("No preview available (Unsupported Type)")
        else:
            if not path:
                logging.info("UI: Clicked item has no path (likely a group header).")
            else:
                logging.warning(f"UI: Path does not exist: {path}")

    def auto_select(self, criteria):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            files = []
            for j in range(group.childCount()):
                item = group.child(j)
                path = item.text(2)
                files.append((os.path.getmtime(path), item))
            
            if not files:
                continue

            files.sort(key=lambda x: x[0]) # Sort by time
            
            # Uncheck all first
            for _, item in files:
                item.setCheckState(0, Qt.CheckState.Unchecked)

            if criteria == 'older':
                # Select all except the newest
                for _, item in files[:-1]:
                    item.setCheckState(0, Qt.CheckState.Checked)
            elif criteria == 'newer':
                # Select all except the oldest
                for _, item in files[1:]:
                    item.setCheckState(0, Qt.CheckState.Checked)

    def delete_selected(self):
        files_to_delete = []
        space_recovered = 0
        
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            for j in range(group.childCount()):
                item = group.child(j)
                if item.checkState(0) == Qt.CheckState.Checked:
                    path = item.text(2)
                    files_to_delete.append(path)
                    try:
                        space_recovered += os.path.getsize(path)
                    except OSError:
                        pass

        if not files_to_delete:
            QMessageBox.information(self, "Info", "No files selected.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete {len(files_to_delete)} files?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_files = []
            total_recovered_bytes = 0
            for path in files_to_delete:
                try:
                    # Get size before deleting to ensure accuracy
                    size = os.path.getsize(path)
                    os.remove(path)
                    deleted_files.append(path)
                    total_recovered_bytes += size
                except OSError as e:
                    print(f"Error deleting {path}: {e}")
            
            self.history_manager.log_cleanup(deleted_files, total_recovered_bytes)
            
            # Format the size string
            if total_recovered_bytes < 1024 * 1024:
                size_str = f"{total_recovered_bytes / 1024:.2f} KB"
            else:
                size_str = f"{total_recovered_bytes / (1024 * 1024):.2f} MB"
            
            summary_msg = f"Deleted {len(deleted_files)} files.\n{size_str} recovered."
            self.status_label.setText(summary_msg.replace("\n", " "))
            
            # Show message box so user sees it before rescan wipes the status
            QMessageBox.information(self, "Deletion Complete", summary_msg)
            
            self.start_scan() # Rescan to update view
            self.load_history()

    def load_history(self):
        self.history_list.clear()
        history = self.history_manager.get_history()
        for record in history:
            timestamp = record['timestamp']
            count = len(record['files_removed'])
            space = record['space_recovered'] / (1024 * 1024) # MB
            item = QListWidgetItem(f"{timestamp}: Removed {count} files ({space:.2f} MB)")
            self.history_list.addItem(item)

    def on_tab_change(self, index):
        if index == 1: # History tab
            self.load_history()
