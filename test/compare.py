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


print_pretty_opf(file)
print_pretty_opf(file2)