import os
import hashlib
import concurrent.futures
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DuplicateScanner:
    def __init__(self):
        self.files_by_size = defaultdict(list)
        self.duplicates = []
        self.scanned_files_count = 0

    def scan_directory(self, path, progress_callback=None):
        """
        Scans the directory for files and groups them by (size, extension).
        Skips offline (cloud) files and executables.
        """
        self.files_by_size.clear()
        self.duplicates.clear()
        self.scanned_files_count = 0
        
        logging.info(f"Starting scan of {path}")
        
        # Windows File Attribute Constant for "Offline"
        FILE_ATTRIBUTE_OFFLINE = 0x1000
        
        try:
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Skip symbolic links
                        if os.path.islink(file_path):
                            continue
                        
                        # Skip executables
                        if file.lower().endswith('.exe'):
                            continue

                        # Check file attributes for "Offline" status (iCloud/OneDrive placeholders)
                        try:
                            # os.stat(path).st_file_attributes is available on Windows Python
                            attrs = os.stat(file_path).st_file_attributes
                            if attrs & FILE_ATTRIBUTE_OFFLINE:
                                logging.info(f"Skipping offline file: {file_path}")
                                continue
                        except AttributeError:
                            # Non-Windows or older Python might not have st_file_attributes
                            pass
                            
                        size = os.path.getsize(file_path)
                        _, ext = os.path.splitext(file)
                        ext = ext.lower()
                        
                        # Group by (size, extension) tuple
                        # We only care if there's more than one file of this exact size AND type
                        self.files_by_size[(size, ext)].append(file_path)
                        self.scanned_files_count += 1
                        
                        if progress_callback and self.scanned_files_count % 100 == 0:
                            progress_callback(self.scanned_files_count)
                            
                    except OSError as e:
                        logging.warning(f"Could not access {file_path}: {e}")
        except Exception as e:
            logging.error(f"Error scanning directory: {e}")

        logging.info(f"Found {self.scanned_files_count} files. Grouping by size and type...")
        return self.find_duplicates(progress_callback)

    def get_partial_hash(self, file_path, chunk_size=4096):
        """
        Hashes the first and last chunk of the file.
        """
        try:
            with open(file_path, 'rb') as f:
                start = f.read(chunk_size)
                f.seek(-chunk_size, 2)
                end = f.read(chunk_size)
                return hashlib.md5(start + end).hexdigest()
        except (OSError, ValueError):
            # Fallback for small files or read errors
            return self.get_full_hash(file_path)

    def get_full_hash(self, file_path, chunk_size=8192):
        """
        Computes the full SHA-256 hash of the file.
        """
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError:
            return None

    def find_duplicates(self, progress_callback=None):
        """
        Identifies duplicates from the size-grouped files using a multi-stage hashing strategy.
        """
        potential_duplicates = [paths for paths in self.files_by_size.values() if len(paths) > 1]
        
        logging.info(f"Processing {len(potential_duplicates)} groups of potential duplicates.")
        
        final_duplicates = []
        
        # Stage 2: Partial Hash
        # We can parallelize this part
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for paths in potential_duplicates:
                hashes = defaultdict(list)
                
                # Helper to process a single file for partial hash
                def process_partial(path):
                    return path, self.get_partial_hash(path)

                results = executor.map(process_partial, paths)
                
                for path, partial_hash in results:
                    if partial_hash:
                        hashes[partial_hash].append(path)
                
                # Stage 3: Full Hash for those with matching partial hashes
                for p_hash, p_paths in hashes.items():
                    if len(p_paths) > 1:
                        full_hashes = defaultdict(list)
                        
                        # Helper for full hash
                        def process_full(path):
                            return path, self.get_full_hash(path)
                            
                        full_results = executor.map(process_full, p_paths)
                        
                        for path, full_hash in full_results:
                            if full_hash:
                                full_hashes[full_hash].append(path)
                        
                        for f_hash, f_paths in full_hashes.items():
                            if len(f_paths) > 1:
                                final_duplicates.append({
                                    'hash': f_hash,
                                    'size': os.path.getsize(f_paths[0]),
                                    'files': f_paths
                                })
        
        self.duplicates = final_duplicates
        logging.info(f"Scan complete. Found {len(self.duplicates)} groups of duplicates.")
        return self.duplicates
