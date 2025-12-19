import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MediaConsolidator:
    def __init__(self):
        self.media_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',  # Images
            '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v' # Videos
        }
        self.default_exclusions = {
            'Windows', 'Program Files', 'Program Files (x86)', 
            'ProgramData', 'AppData', '$RECYCLE.BIN', 'System Volume Information',
            'ConsolidatedMedia' # Skip our target if it exists
        }

    def is_media_file(self, filename):
        return os.path.splitext(filename)[1].lower() in self.media_extensions

    def get_unique_filename(self, directory, filename):
        """
        Generates a unique filename if the target already exists.
        Appends _1, _2, etc.
        """
        name, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        while os.path.exists(os.path.join(directory, new_filename)):
            new_filename = f"{name}_{counter}{ext}"
            counter += 1
        return new_filename

    def consolidate_drive(self, drive_path, progress_callback=None, log_callback=None):
        """
        Scans the drive and moves media files to [Drive]:\ConsolidatedMedia.
        Preserves immediate parent folder name.
        """
        drive_path = os.path.abspath(drive_path)
        
        # Handle long paths on Windows
        if os.name == 'nt' and not drive_path.startswith('\\\\?\\'):
            drive_path = f"\\\\?\\{drive_path}"
            
        base_target = os.path.join(drive_path, "ConsolidatedMedia")
        
        if not os.path.exists(base_target):
            try:
                os.makedirs(base_target)
                if log_callback:
                    log_callback(f"Created target directory: {base_target}")
            except OSError as e:
                logging.error(f"Failed to create target directory {base_target}: {e}")
                if log_callback:
                    log_callback(f"Error: Failed to create target directory {base_target}: {e}")
                return

        files_moved = 0
        bytes_moved = 0
        
        logging.info(f"Starting consolidation for {drive_path}")
        if log_callback:
            log_callback(f"Scanning {drive_path}...")

        # Walk the directory tree
        for root, dirs, files in os.walk(drive_path):
            # Skip hidden/system directories and exclusions
            dirs[:] = [d for d in dirs if d not in self.default_exclusions and not d.startswith('.')]
            
            # Check if we are in the target directory itself
            if os.path.commonpath([root, base_target]) == base_target:
                continue

            for file in files:
                if self.is_media_file(file):
                    source_path = os.path.join(root, file)
                    
                    # Get immediate parent folder name
                    parent_folder = os.path.basename(root)
                    
                    # If root is drive root
                    if parent_folder == os.path.basename(drive_path) or not parent_folder:
                        parent_folder = "Root_Files"

                    target_dir = os.path.join(base_target, parent_folder)
                    
                    try:
                        if not os.path.exists(target_dir):
                            os.makedirs(target_dir)
                        
                        target_filename = self.get_unique_filename(target_dir, file)
                        target_path = os.path.join(target_dir, target_filename)
                        
                        # Get size for logging
                        size = os.path.getsize(source_path)
                        
                        # Move the file
                        shutil.move(source_path, target_path)
                        
                        files_moved += 1
                        bytes_moved += size
                        
                        msg = f"Moved: {file} ({size / 1024:.2f} KB) -> {parent_folder}"
                        logging.info(msg)
                        if log_callback:
                            log_callback(msg)
                            
                        if progress_callback:
                            progress_callback(files_moved)
                            
                    except Exception as e:
                        # Log the error but continue (skip the file)
                        err_msg = f"Skipping file {file} due to error: {e}"
                        logging.warning(err_msg)
                        if log_callback:
                            log_callback(err_msg)

        summary = f"Consolidation Complete. Moved {files_moved} files ({bytes_moved / (1024*1024):.2f} MB)."
        logging.info(summary)
        if log_callback:
            log_callback(summary)
        
        return files_moved, bytes_moved

    def organize_folder(self, target_folder, log_callback=None):
        """
        Organizes files in the target folder into Photos and Videos subfolders.
        Flattens the structure.
        """
        target_folder = os.path.abspath(target_folder)
        if os.name == 'nt' and not target_folder.startswith('\\\\?\\'):
            target_folder = f"\\\\?\\{target_folder}"

        logging.info(f"Starting organization for {target_folder}")
        if log_callback:
            log_callback(f"Organizing {target_folder}...")

        photos_dir = os.path.join(target_folder, "Photos")
        videos_dir = os.path.join(target_folder, "Videos")

        for d in [photos_dir, videos_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

        files_moved = 0
        
        # Walk and move
        for root, dirs, files in os.walk(target_folder):
            # Skip the destination folders themselves to avoid loops if they are inside target
            if os.path.abspath(root) == os.path.abspath(photos_dir) or os.path.abspath(root) == os.path.abspath(videos_dir):
                continue
                
            for file in files:
                if self.is_media_file(file):
                    source_path = os.path.join(root, file)
                    
                    # Determine type
                    ext = os.path.splitext(file)[1].lower()
                    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}:
                        dest_dir = photos_dir
                        type_name = "Photos"
                    else:
                        dest_dir = videos_dir
                        type_name = "Videos"
                    
                    try:
                        target_filename = self.get_unique_filename(dest_dir, file)
                        target_path = os.path.join(dest_dir, target_filename)
                        
                        shutil.move(source_path, target_path)
                        files_moved += 1
                        
                        if log_callback:
                            log_callback(f"Organized: {file} -> {type_name}\\{target_filename}")
                            
                    except Exception as e:
                        if log_callback:
                            log_callback(f"Error organizing {file}: {e}")

        # Cleanup empty directories
        for root, dirs, files in os.walk(target_folder, topdown=False):
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass # Directory not empty

        # Remove junk files
        self.remove_junk_files(target_folder, log_callback)
        
        if log_callback:
            log_callback(f"Organization Complete. Organized {files_moved} files.")

    def remove_junk_files(self, target_root, log_callback=None):
        """
        Removes files starting with '._' in the target directory.
        """
        logging.info(f"Starting cleanup in {target_root}")
        if log_callback:
            log_callback("Starting cleanup of junk files (._*)...")
            
        count = 0
        for root, _, files in os.walk(target_root):
            for file in files:
                if file.startswith("._"):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        count += 1
                        logging.info(f"Removed junk file: {file_path}")
                    except OSError as e:
                        logging.error(f"Failed to remove {file_path}: {e}")
        
        msg = f"Cleanup finished. Removed {count} junk files."
        logging.info(msg)
        if log_callback:
            log_callback(msg)
