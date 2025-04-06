from src1.finder import FileFinder

corrupted_folder = r"D:\zzz_corrupted_folder"
music_exts = ['.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma']
ignored_exts = ['.opf', '.db', '.json', '.py', '.jpg', '.ini', '.mp4', '.ebup']

# ایجاد شیء از کلاس FileFinder
file_finder = FileFinder(folder_path=r"D:\zzz_corrupted_folder")

# فراخوانی متد برای گرفتن هش
file1_hash = file_finder._hash_pdf(
    r"C:\Users\HP\Calibre Library\000_keep_folder\نیل دونالد والش\جا پای خداوند\جا پای خداوند - نیل دونالد والش.pdf")
file3_hash = file_finder._hash_pdf(
    r"C:\Users\HP\Calibre Library\nyl dwnald walsh\ja pay khdawnd (904)\ja pay khdawnd - nyl dwnald walshh.pdf")

print(file1_hash)
print(file3_hash)
