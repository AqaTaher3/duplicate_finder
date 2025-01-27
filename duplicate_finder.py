import os
import hashlib

class DuplicateFinder:
    def __init__(self, folder_path, progress_bar, progress_label):
        self.folder_path = folder_path
        self.progress_bar = progress_bar
        self.progress_label = progress_label

    def _hash_file(self, file_path):
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError):
            return None

    def find_duplicates(self):
        file_hashes = {}
        duplicates = {}
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_hash = self._hash_file(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        duplicates.setdefault(file_hash, [file_hashes[file_hash]]).append(file_path)
                    else:
                        file_hashes[file_hash] = file_path
        return duplicates

    @staticmethod
    def _check_file_health(file_path):
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0