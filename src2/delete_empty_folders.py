import os


def delete_empty_folders(directory):
    if not os.path.exists(directory):
        return

    while True:
        folder_deleted = False
        count = 0
        # بررسی پوشه‌ها از پایین به بالا (پوشه‌های تو در تو اول)
        for foldername, subfolders, filenames in os.walk(directory, topdown=False):
            # شرط جدید: اگر فقط یک فایل با نام 'metadata.opf' وجود داشته باشد و هیچ زیرپوشه‌ای نباشد
            if (not subfolders and
                    len(filenames) == 1 and
                    filenames[0].lower() == 'metadata.opf'):
                opf_path = os.path.join(foldername, filenames[0])
                try:
                    os.remove(opf_path)  # حذف فایل OPF
                    os.rmdir(foldername)  # حذف پوشه خالی
                    count += 1
                    print(f"Deleted folder (only OPF): {foldername}")
                    folder_deleted = True
                except OSError as e:
                    print(f"Error deleting {foldername}: {e}")

            # شرط اصلی: اگر پوشه کاملاً خالی باشد
            elif not subfolders and not filenames:
                try:
                    os.rmdir(foldername)
                    print(f"Deleted empty folder: {foldername}")
                    folder_deleted = True
                except OSError as e:
                    print(f"Error deleting {foldername}: {e}")

        if not folder_deleted:
            break

    # حذف پوشه اصلی اگر خالی شد
    if not os.listdir(directory):
        try:
            os.rmdir(directory)
            print(f"Deleted main directory: {directory}")
        except OSError as e:
            print(f"Could not delete {directory}: {e}")
    print('removed_dir : ', count)


delete_empty_folders(r"C:\Users\HP\Music\Cal")