from src1.finder import FileFinder
from src2.file_hasher import FileHasher
from PyPDF2 import PdfReader

corrupted_folder = r"D:\zzz_corrupted_folder"
music_exts = ['.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma']
ignored_exts = ['.opf', '.db', '.json', '.py', '.jpg', '.ini', '.mp4', '.ebup']

# # ایجاد شیء از کلاس FileFinder
file_finder = FileHasher()
file1 = r"C:\Users\HP\Music\co.pdf"
file2 = r"C:\Users\HP\Music\ca.pdf"


file1_hash = file_finder._hash_pdf_10(
    file1)
file3_hash = file_finder._hash_pdf_10(
    file2)
print(file1_hash)
print(file3_hash)

