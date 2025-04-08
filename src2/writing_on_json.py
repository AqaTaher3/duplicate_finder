import json
import os


def prepend_text_to_json(file_path, new_text):
    """
    این تابع یک متن جدید را به ابتدای لیست متون در فایل JSON اضافه می‌کند.
    اگر فایل وجود نداشته باشد، آن را ایجاد می‌کند.

    پارامترها:
        file_path (str): مسیر فایل JSON
        new_text (str): متن جدیدی که می‌خواهید اضافه شود
    """
    try:
        # بررسی وجود فایل
        if os.path.exists(file_path):
            # اگر فایل وجود دارد، آن را می‌خوانیم
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # اطمینان از اینکه 'texts' وجود دارد و یک لیست است
            if 'texts' not in data or not isinstance(data['texts'], list):
                data['texts'] = []
        else:
            # اگر فایل وجود ندارد، یک ساختار جدید ایجاد می‌کنیم
            data = {'texts': []}

        # اضافه کردن متن جدید به ابتدای لیست
        data['texts'].insert(0, new_text)

        # ذخیره دیکشنری در فایل JSON
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print(f"متن جدید با موفقیت به فایل {file_path} اضافه شد.")

    except Exception as e:
        print(f"خطا در پردازش فایل JSON: {e}")




# for message in sample_messages:
#     prepend_text_to_json(file_path, message)
#
# # محتوای نهایی فایل
# print("\nمحتوای نهایی فایل:")
# with open(file_path, 'r', encoding='utf-8') as file:
#     print(json.dumps(json.load(file), ensure_ascii=False, indent=4))