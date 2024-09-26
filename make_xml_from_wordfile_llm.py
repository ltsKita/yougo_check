"""
このファイルではwordファイルをxmlファイルに分割する。
生成AIに文脈判断させる際により長い文章が必要となるため、結合可能な<w:t>要素を結合したうえでテキスト情報を取得している。
ただしこの方法では図表内のテキストを取得できないため、あくまでも生成AI適用検証用に通常段落のテキストを取得するために用いている。
"""
import zipfile
import os
from lxml import etree as ET

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
    
    # document.xml のパスを取得
    document_xml_path = os.path.join(output_dir, "word", "document.xml")
    
    if not os.path.exists(document_xml_path):
        print("document.xml が見つかりませんでした")
        return
    
    # XML を解析
    parser = ET.XMLParser(ns_clean=True, recover=True)
    tree = ET.parse(document_xml_path, parser)
    root = tree.getroot()
    namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    # <w:p> 内の <w:r> 要素を処理する。
    for paragraph in root.findall('.//w:p', namespaces=namespace):
        runs = paragraph.findall('w:r', namespaces=namespace)
        new_runs = []
        combined_text = ''
        first_r = None

        for r in runs:
            t_element = r.find('w:t', namespaces=namespace)

            # 図表関連の要素をスキップして保持。ここからテキストの抽出は行わない。
            if r.find('.//w:drawing', namespaces=namespace) is not None or \
               r.find('.//w:pict', namespaces=namespace) is not None:
                new_runs.append(r)
                continue

            # <w:br w:type="page"> や <w:tab> をそのまま保持し、元文書の体裁を維持
            if r.find('w:tab', namespaces=namespace) is not None or \
               r.find('.//w:br[@w:type="page"]', namespaces=namespace) is not None:
                
                # これまでのテキストを保存
                if combined_text and first_r is not None:
                    first_t_element = first_r.find('w:t', namespaces=namespace)
                    if first_t_element is None:
                        first_t_element = ET.SubElement(first_r, 'w:t')
                    first_t_element.text = combined_text
                    new_runs.append(first_r)
                    combined_text = ''

                
                new_runs.append(r)
                first_r = None

            else:
                # <w:t xml:space="preserve"> も含めて結合
                if t_element is not None and t_element.text is not None:
                    if first_r is None:
                        first_r = r  # 最初の <w:r> を保存
                    combined_text += t_element.text

        # 最後に残ったテキストを保存
        if combined_text and first_r is not None:
            first_t_element = first_r.find('w:t', namespaces=namespace)
            if first_t_element is None:
                first_t_element = ET.SubElement(first_r, 'w:t')
            first_t_element.text = combined_text
            new_runs.append(first_r)

        # 既存の <w:r> 要素を削除して新しいものを追加
        for r in runs:
            paragraph.remove(r)
        
        for new_r in new_runs:
            paragraph.append(new_r)
    
    # 名前空間マッピングを指定してXMLをバイナリ形式に変換
    xml_bytes = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
    
    # バイナリ形式で名前空間プレフィックスを'ns0'から'w'に置き換え
    xml_str = xml_bytes.decode('utf-8').replace('ns0:', 'w:')
    
    # XML文字列をファイルに書き出し
    with open(document_xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"{document_xml_path} を更新しました。")


if __name__ == "__main__":
    docx_file = get_docx_file("data")
    extract_docx_to_xml(docx_file, "xml/")
    extract_docx_to_xml(docx_file, "xml_new/")