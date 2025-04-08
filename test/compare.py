import xml.etree.ElementTree as ET


def read_opf_file(opf_path):
    # پارس کردن فایل OPF
    tree = ET.parse(opf_path)
    root = tree.getroot()

    # فضای نام (namespace) معمولاً در فایل‌های OPF وجود دارد
    namespaces = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # استخراج متاداده‌ها (عنوان، نویسنده، شناسه و ...)
    title = root.find('.//dc:title', namespaces).text
    author = root.find('.//dc:creator', namespaces).text
    book_id = root.find('.//dc:identifier', namespaces).text

    # print(f"عنوان: {title}")
    # print(f"نویسنده: {author}")
    print(f"شناسه کتاب: {book_id}")
    # لیست فایل‌های موجود در کتاب (مانند صفحات HTML، تصاویر و ...)
    # manifest = root.find('.//opf:manifest', namespaces)
    # for item in manifest.findall('opf:item', namespaces):
    #     print(f"فایل: {item.get('href')} (نوع: {item.get('media-type')})")


file = r"C:\Users\HP\Videos\01.opf"
file2 = r"C:\Users\HP\Videos\02.opf"

# read_opf_file(file)
# read_opf_file(file2)

from lxml import etree


def print_pretty_opf(opf_path):
    tree = etree.parse(opf_path)
    root = tree.getroot()

    # چاپ XML با قالب‌بندی خوانا
    xml_str = etree.tostring(root, encoding="utf-8", pretty_print=True).decode("utf-8")
    print(xml_str)


from lxml import etree
from collections import defaultdict


def compare_opf_files(opf_path1, opf_path2):
    # پارس کردن فایل‌های OPF
    tree1 = etree.parse(opf_path1)
    tree2 = etree.parse(opf_path2)

    root1 = tree1.getroot()
    root2 = tree2.getroot()

    # جمع‌آوری تمام عناصر و ویژگی‌ها از فایل اول
    elements_info1 = defaultdict(list)
    for element in root1.iter():
        elements_info1[element.tag].append(dict(element.attrib))

    # جمع‌آوری تمام عناصر و ویژگی‌ها از فایل دوم
    elements_info2 = defaultdict(list)
    for element in root2.iter():
        elements_info2[element.tag].append(dict(element.attrib))

    # یافتن عناصر مشترک
    common_tags = set(elements_info1.keys()) & set(elements_info2.keys())

    print("=" * 50)
    print("مقایسه فایل‌های OPF:")
    print(f"فایل ۱: {opf_path1}")
    print(f"فایل ۲: {opf_path2}")
    print("=" * 50)

    # بررسی شباهت‌ها و تفاوت‌ها برای هر تگ مشترک
    for tag in common_tags:
        print(f"\nتگ: {tag}")

        # مقایسه تعداد عناصر
        count1 = len(elements_info1[tag])
        count2 = len(elements_info2[tag])
        print(f"تعداد در فایل ۱: {count1}")
        print(f"تعداد در فایل ۲: {count2}")

        # مقایسه ویژگی‌ها
        attrs1 = elements_info1[tag]
        attrs2 = elements_info2[tag]

        common_attrs = []
        different_attrs = []

        # مقایسه ویژگی‌های عناصر با همان اندیس (اگر تعداد عناصر برابر باشد)
        for i in range(min(count1, count2)):
            if attrs1[i] == attrs2[i]:
                common_attrs.append(attrs1[i])
            else:
                different_attrs.append((attrs1[i], attrs2[i]))

        if common_attrs:
            print("\nویژگی‌های مشترک:")
            for attr in common_attrs:
                print(f"  {attr}")

        if different_attrs:
            print("\nویژگی‌های متفاوت:")
            for attr1, attr2 in different_attrs:
                print(f"  فایل ۱: {attr1}")
                print(f"  فایل ۲: {attr2}")
                print("  ---")

    # یافتن عناصر منحصر به فرد در هر فایل
    unique_to_file1 = set(elements_info1.keys()) - set(elements_info2.keys())
    unique_to_file2 = set(elements_info2.keys()) - set(elements_info1.keys())

    if unique_to_file1:
        print("\nعناصر منحصر به فرد در فایل ۱:")
        for tag in unique_to_file1:
            print(f"  {tag}: {len(elements_info1[tag])} مورد")

    if unique_to_file2:
        print("\nعناصر منحصر به فرد در فایل ۲:")
        for tag in unique_to_file2:
            print(f"  {tag}: {len(elements_info2[tag])} مورد")


# مثال استفاده:
compare_opf_files("book1.opf", "book2.opf")