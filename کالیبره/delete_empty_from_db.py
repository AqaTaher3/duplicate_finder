import sqlite3
import os

# مسیر پایگاه داده و پوشه‌ی کتابخانه
db_path = r"D:\00_Calibre\metadata.db"
library_path = r"C:\Users\HP\Music\Cal"

# اتصال به دیتابیس
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ۱. حذف کتاب‌هایی که فایلشون وجود نداره
cursor.execute("SELECT id, path FROM books")
books = cursor.fetchall()

deleted_books = []
for book_id, book_path in books:
    full_path = os.path.join(library_path, book_path)
    if not os.path.exists(full_path):
        deleted_books.append(book_id)

if deleted_books:
    cursor.executemany("DELETE FROM books WHERE id = ?", [(book_id,) for book_id in deleted_books])
    conn.commit()
    print(f"✅ {len(deleted_books)} کتاب حذف شد (فایلشون وجود نداشت).")

# ۲. حذف کتاب‌های تکراری بر اساس عنوان و نویسنده (با بررسی مقادیر NULL)
cursor.execute("""
    DELETE FROM books WHERE id NOT IN (
        SELECT MIN(books.id) 
        FROM books 
        LEFT JOIN books_authors_link ON books.id = books_authors_link.book
        LEFT JOIN authors ON books_authors_link.author = authors.id
        GROUP BY books.title, COALESCE(authors.name, '')  -- نویسنده‌های NULL به مقدار '' تغییر داده می‌شوند
    )
""")
conn.commit()
print("✅ کتاب‌های تکراری حذف شدند.")

# ۳. بهینه‌سازی پایگاه داده
cursor.execute("VACUUM;")
conn.commit()
print("✅ پایگاه داده بهینه‌سازی شد.")

# بستن اتصال
conn.close()
