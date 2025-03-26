import wx
from src.gui import FileFinderFrame
from src.logic import FileHandler
from src.finder import FileFinder
import os
import hashlib
import wx
from tqdm import tqdm


def hash_file(file_path):
    """Generate SHA-256 hash for a file."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):  # Read in chunks to handle large files
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError) as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return (None)



file1_hash = hash_file(
    r"C:\Users\HP\Music\music\222_Persian\Yegane\Mohsen Yeganeh - Nadaramet [320].mp3")
file2_hash = hash_file(r"C:\Users\HP\Music\music\222_Persian\Yegane\Nadaramet [320].mp3")
print(file1_hash, file2_hash)
