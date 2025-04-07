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
    def __init__(self):
        """
        Initialize FileHasher with optional cache

        """
        self.cache = {}
        self.ignored_exts = {'.opf', '.db', '.json', '.py', '.jpg', '.ini', '.mp4', '.ebup'}
        self.music_exts = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}

    def _hash_pdf(self, file_path):
        """هش مقاوم به تغییرات خودکار Calibre"""
        hasher = hashlib.sha256()
        try:
            # 1. خواندن ساختار اصلی PDF
            reader = PdfReader(file_path)

            # 2. هش ویژگی‌های ساختاری کلیدی
            structure_data = [
                f"pages:{len(reader.pages)}",
                *[f"pg{i}_size:{page.mediabox.width:.1f}x{page.mediabox.height:.1f}"
                  for i, page in enumerate(reader.pages[:3])],  # فقط 3 صفحه اول
                f"fonts:{sum(1 for page in reader.pages[:3] for font in page.get('/Font') or [])}"
            ]
            hasher.update("|".join(structure_data).encode('utf-8'))

            # 3. هش محتوای متنی (از صفحات میانی)
            text_samples = []
            sample_pages = [
                min(5, len(reader.pages) - 1),
                len(reader.pages) // 2,
                max(len(reader.pages) - 5, 0)
            ]

            for i in sample_pages:
                try:
                    text = reader.pages[i].extract_text() or ""
                    clean_text = "".join(c for c in text if c.isalnum() or c.isspace())
                    if clean_text:
                        text_samples.append(clean_text[:1000])  # محدودیت حجم
                except:
                    continue

            hasher.update("|".join(text_samples).encode('utf-8', errors='ignore'))

            # 4. هش بخش‌های باینری امن
            with open(file_path, 'rb') as f:
                file_size = os.path.getsize(file_path)

                # مناطق نمونه‌گیری (دور از 10% ابتدا و انتها)
                sample_offsets = [
                    int(file_size * 0.1) + 1024,
                    int(file_size * 0.5),
                    int(file_size * 0.9) - 1024
                ]

                for offset in sample_offsets:
                    if 0 <= offset < file_size - 512:
                        f.seek(offset)
                        hasher.update(f.read(512))

            return hasher.hexdigest()
        except Exception as e:
            logging.error(f"PDF hashing error (Calibre-resistant): {file_path} - {str(e)}")
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
        """Determine file type"""
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

        return result  # این خط اضافه شد

    @staticmethod
    def check_file_health(file_path):
        """Check if file is accessible and valid"""
        try:
            return (os.path.exists(file_path) and
                    os.path.isfile(file_path) and
                    os.path.getsize(file_path) > 0)
        except OSError:
            return False