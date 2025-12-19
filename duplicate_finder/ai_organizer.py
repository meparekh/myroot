import os
import shutil
import logging

# Optional imports for AI features
try:
    from nudenet import NudeDetector
    NUDENET_AVAILABLE = True
except ImportError:
    NUDENET_AVAILABLE = False
    logging.warning("NudeNet not installed. NSFW detection disabled.")

try:
    import face_recognition
    import cv2
    import numpy as np
    from sklearn.cluster import DBSCAN
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logging.warning("face_recognition, cv2, or sklearn not installed. Face grouping disabled.")

class AIOrganizer:
    def __init__(self):
        self.nude_detector = None
        if NUDENET_AVAILABLE:
            try:
                self.nude_detector = NudeDetector()
            except Exception as e:
                logging.error(f"Failed to initialize NudeDetector: {e}")

    def is_nsfw(self, file_path):
        """
        Checks if an image or video contains explicit content.
        Returns True if unsafe, False otherwise.
        """
        # Try NudeNet first if available
        if NUDENET_AVAILABLE and self.nude_detector:
            try:
                preds = self.nude_detector.detect(file_path)
                for pred in preds:
                    if pred['class'] in [
                        'BUTTOCKS_EXPOSED', 'FEMALE_BREAST_EXPOSED', 'FEMALE_GENITALIA_EXPOSED', 
                        'MALE_BREAST_EXPOSED', 'MALE_GENITALIA_EXPOSED', 'ANUS_EXPOSED'
                    ]:
                        if pred['score'] > 0.5:
                            return True
                return False
            except Exception as e:
                logging.error(f"Error checking NSFW with NudeNet for {file_path}: {e}")
        
        # Fallback: Simple skin detection (basic heuristic)
        return self._simple_skin_detection(file_path)

    def _simple_skin_detection(self, file_path):
        """
        Simple skin tone detection as a basic NSFW heuristic.
        Returns True if >30% of image is skin-colored.
        NOTE: This is a basic approximation and much less accurate than AI models.
        """
        try:
            # Try to use opencv if available
            if 'cv2' in globals():
                import cv2
                img = cv2.imread(file_path)
                if img is None:
                    return False
                
                # Convert to HSV for better skin detection
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                
                # Skin tone range in HSV
                lower_skin = np.array([0, 20, 70], dtype=np.uint8)
                upper_skin = np.array([20, 255, 255], dtype=np.uint8)
                
                # Create mask
                mask = cv2.inRange(hsv, lower_skin, upper_skin)
                skin_pixels = np.sum(mask > 0)
                total_pixels = img.shape[0] * img.shape[1]
                
                skin_percentage = skin_pixels / total_pixels
                
                # If more than 30% skin, flag as potential NSFW
                return skin_percentage > 0.30
            else:
                # No opencv, cannot do detection
                return False
        except Exception as e:
            logging.error(f"Error in skin detection for {file_path}: {e}")
            return False

    def scan_faces(self, folder_path):
        """
        Scans a folder for faces and returns:
        - face_data: {file_path: [encodings]}
        - family_photos: [file_paths with >3 faces]
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {}, []

        face_data = {}
        family_photos = []
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    path = os.path.join(root, file)
                    try:
                        image = face_recognition.load_image_file(path)
                        encodings = face_recognition.face_encodings(image)
                        
                        if len(encodings) > 3:
                            # Family photo (>3 faces)
                            family_photos.append(path)
                        elif encodings:
                            # 1-3 faces, save for clustering
                            face_data[path] = encodings
                    except Exception as e:
                        logging.error(f"Error scanning faces in {path}: {e}")
        
        return face_data, family_photos

    def group_faces(self, face_data):
        """
        Groups faces using clustering.
        Returns a dictionary: {label_id: [list_of_file_paths]}
        """
        if not FACE_RECOGNITION_AVAILABLE or not face_data:
            return {}

        # Flatten all encodings with their source paths
        all_encodings = []
        encoding_to_path = []  # Track which encoding came from which file
        
        for path, encodings in face_data.items():
            for encoding in encodings:
                all_encodings.append(encoding)
                encoding_to_path.append(path)

        if not all_encodings:
            return {}

        # Cluster with tolerance for face similarity
        clt = DBSCAN(metric="euclidean", n_jobs=-1, eps=0.5, min_samples=2)
        clt.fit(all_encodings)

        # Group by label
        groups = {}
        for label, path in zip(clt.labels_, encoding_to_path):
            if label == -1:
                continue  # Noise/unknown faces
            if label not in groups:
                groups[label] = set()
            groups[label].add(path)
            
        return groups
    
    def get_unique_filename(self, dest_dir, filename):
        """Handle filename collisions by appending a counter."""
        dest_path = os.path.join(dest_dir, filename)
        if not os.path.exists(dest_path):
            return filename
        
        base, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_filename = f"{base}_{counter}{ext}"
            new_path = os.path.join(dest_dir, new_filename)
            if not os.path.exists(new_path):
                return new_filename
            counter += 1
