import os
import hashlib
import pickle
import atexit
import logging
from PyPDF2 import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup
import warnings


class FileHasher:
    def __init__(self, cache_file=None):
        """
        Initialize FileHasher with optional cache

        :param cache_file: Path to cache file for faster subsequent runs
        """
        self.cache_file = cache_file
        self.cache = {}
        self.ignored_exts = {'.opf', '.db', '.json', '.py', '.jpg', '.ini', '.mp4', '.ebup'}
        self.music_exts = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}

        if cache_file:
            self._load_cache()
            atexit.register(self._save_cache)

        logging.basicConfig(filename='file_hasher.log', level=logging.ERROR)

    def _load_cache(self):
        """Load hash cache from file"""
        try:
            with open(self.cache_file, 'rb') as f:
                self.cache = pickle.load(f)
        except (FileNotFoundError, pickle.PickleError):
            self.cache = {}

    def _save_cache(self):
        """Save hash cache to file"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            logging.error(f"خطا در ذخیره کش: {str(e)}")

    def _hash_pdf(self, file_path):
        """Specialized PDF hashing"""
        hasher = hashlib.sha256()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                with open(file_path, 'rb') as f:
                    hasher.update(f.read(1024 * 1024))  # Hash first 1MB

                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                hasher.update(text.encode('utf-8'))
                return hasher.hexdigest()
            except Exception as e:
                logging.error(f"خطا در پردازش PDF: {file_path} - {str(e)}")
                return None

    def _hash_epub(self, file_path):
        """Specialized EPUB hashing"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(128 * 1024), b''):
                    hasher.update(chunk)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                book = epub.read_epub(file_path)
                for i, item in enumerate(book.get_items()):
                    if i >= 3:
                        break
                    if item.get_type() == epub.EpubHtml:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        hasher.update(soup.get_text().encode('utf-8', errors='replace'))

            return hasher.hexdigest()
        except Exception as e:
            logging.error(f"خطا در پردازش EPUB: {file_path} - {str(e)}")
            return None

    def _hash_music(self, file_path):
        """Specialized music file hashing"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(256 * 1024), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logging.error(f"خطا در پردازش فایل موزیک: {file_path} - {str(e)}")
            return None

    def _hash_generic(self, file_path):
        """Generic file hashing"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(128 * 1024):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logging.error(f"خطا در خواندن فایل: {file_path} - {str(e)}")
            return None

    def hash_file(self, file_path):
        """Determine file type and generate appropriate hash"""
        # Check cache first
        if self.cache_file:
            try:
                mtime = os.path.getmtime(file_path)
                if file_path in self.cache and self.cache[file_path]['mtime'] == mtime:
                    return self.cache[file_path]['hash']
            except OSError:
                pass

        ext = os.path.splitext(file_path)[1].lower()

        if ext in self.ignored_exts:
            return None
        elif ext == '.pdf':
            result = self._hash_pdf(file_path)
        elif ext == '.epub':
            result = self._hash_epub(file_path)
        elif ext in self.music_exts:
            result = self._hash_music(file_path)
        else:
            result = self._hash_generic(file_path)

        # Update cache
        if self.cache_file and result:
            try:
                mtime = os.path.getmtime(file_path)
                self.cache[file_path] = {'mtime': mtime, 'hash': result}
            except OSError:
                pass

        return result

    @staticmethod
    def check_file_health(file_path):
        """Check if file is accessible and valid"""
        try:
            return (os.path.exists(file_path) and
                    os.path.isfile(file_path) and
                    os.path.getsize(file_path) > 0)
        except OSError:
            return False