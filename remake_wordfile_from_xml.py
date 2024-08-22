# 分解したxmlを.docxに再構築するためのコード

import zipfile
import os
from make_xml_from_wordfile import get_docx_file

# パスの設定
file_path = get_docx_file("data")
core_filename = os.path.splitext(os.path.basename(file_path))[0]
xml_dir = 'xml_new'  # 解凍先のフォルダ
output_docx = f"【校閲ずみ】{core_filename}.docx"  # 出力するWordファイル

def create_docx(folder_path, output_docx):
    with zipfile.ZipFile(output_docx, 'w', zipfile.ZIP_DEFLATED) as docx:
        for foldername, subfolders, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, folder_path)
                docx.write(file_path, arcname)

# 再度ZIPファイルとしてまとめる
create_docx(xml_dir, output_docx)