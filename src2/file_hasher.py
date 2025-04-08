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

    import os
    import hashlib
    import logging
    from PyPDF2 import PdfReader

    def _hash_pdf_10(self, file_path):
        """هش مقاوم به تغییرات خودکار Calibre همراه با گزارش متادیتای فایل"""
        hasher = hashlib.sha256()
        file_info = {
            'file_path': file_path,
            'file_size_bytes': os.path.getsize(file_path),
            'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
            'pages': 0,
            'sampling_range': "20%-30% (انتهای فایل)",
            'structural_data': None,
            'binary_samples': []
        }

        try:
            # 1. خواندن ساختار اصلی PDF
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            file_info['pages'] = total_pages

            # 2. هش ویژگی‌های ساختاری کلیدی
            structure_data = [
                f"pages:{total_pages}",
                *[f"pg{i}_size:{page.mediabox.width:.1f}x{page.mediabox.height:.1f}"
                  for i, page in enumerate(reader.pages[:3])],
                f"fonts:{sum(1 for page in reader.pages[:3] for font in page.get('/Font') or [])}"
            ]
            file_info['structural_data'] = structure_data
            hasher.update("|".join(structure_data).encode('utf-8'))

            # 3. هش محتوای متنی (از 20% تا 30% انتهای PDF)
            text_samples = []
            start_page = int(total_pages * 0.7)
            end_page = int(total_pages * 0.8)
            file_info['sampled_pages'] = f"{start_page}-{end_page} (از {total_pages} صفحه)"

            for i in range(start_page, min(end_page, total_pages)):
                try:
                    text = reader.pages[i].extract_text() or ""
                    clean_text = "".join(c for c in text if c.isalnum() or c.isspace())
                    if clean_text:
                        text_samples.append(clean_text[:1000])
                except:
                    continue

            hasher.update("|".join(text_samples).encode('utf-8', errors='ignore'))

            # 4. هش بخش‌های باینری امن
            with open(file_path, 'rb') as f:
                file_size = os.path.getsize(file_path)
                sample_offsets = [
                    int(file_size * 0.1) + 1024,
                    int(file_size * 0.5),
                    int(file_size * 0.9) - 1024
                ]
                file_info['binary_samples'] = [
                    f"offset:{offset}/size:512B" for offset in sample_offsets
                ]

                for offset in sample_offsets:
                    if 0 <= offset < file_size - 512:
                        f.seek(offset)
                        hasher.update(f.read(512))

            # ترکیب هش و متادیتا برای خروجی
            return {
                'hash': hasher.hexdigest(),
                'metadata': file_info
            }

        except Exception as e:
            logging.error(f"PDF hashing error: {file_path} - {str(e)}")
            file_info['error'] = str(e)
            return {
                'hash': None,
                'metadata': file_info
            }


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