"""
このファイルではwordファイルをxml形式に分解します。
"""

import zipfile
import os

def get_docx_file(data_dir):
    """
    指定ディレクトリ内のwordファイルを取得する
    """
    docx_files = [f for f in os.listdir(data_dir) if f.endswith('.docx')]
    
    if not docx_files:
        print("dataディレクトリにファイルが見つかりませんでした")
        return None
    
    return os.path.join(data_dir, docx_files[0])

def extract_docx_to_xml(docx_file, output_dir):
    """
    wordファイルをxmlファイルに変換する
    """
    if docx_file is None:
        print("有効な.docxファイルが指定されていません")
        return
    
    # 出力ディレクトリが存在しない場合は作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # .docxファイルを解凍し、.xmlとして展開
    with zipfile.ZipFile(docx_file, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    print(f"{docx_file} を {output_dir} に展開しました。")


if __name__ == "__main__":
    docx_file = get_docx_file("data")
    extract_docx_to_xml(docx_file, "xml/")
    extract_docx_to_xml(docx_file, "xml_new/")