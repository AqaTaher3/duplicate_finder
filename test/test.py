from src1.finder import FileFinder
from src2.file_hasher import FileHasher

corrupted_folder = r"D:\zzz_corrupted_folder"
music_exts = ['.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma']
ignored_exts = ['.opf', '.db', '.json', '.py', '.jpg', '.ini', '.mp4', '.ebup']

# # ایجاد شیء از کلاس FileFinder
file_finder = FileHasher()

# فراخوانی متد برای گرفتن هش
file1_hash = file_finder._hash_pdf(
    r"C:\Users\HP\Music\co.pdf")
file3_hash = file_finder._hash_pdf(
    r"C:\Users\HP\Music\ca.pdf")


print(file1_hash)
print(file3_hash)

