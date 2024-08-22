import xml.etree.ElementTree as ET
import MeCab

# MeCabのトークナイザーを初期化
mecab = MeCab.Tagger("-Ochasen")

# 名前空間の定義
namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
ET.register_namespace('w', namespaces['w'])  # 名前空間プレフィックスを指定

def highlight_paragraph(paragraph):
    """
    段落<w:p>にハイライトを追加する関数
    """
    for run in paragraph.findall('.//w:r', namespaces):
        rpr = run.find('.//w:rPr', namespaces)
        if rpr is None:
            rpr = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
            run.insert(0, rpr)
        ET.SubElement(rpr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight', {'w:val': 'yellow'})
    print(f"ハイライトが追加されました: {ET.tostring(paragraph, 'unicode')}")

def process_text(text):
    """
    テキストに対してMeCabを用いた形態素解析を行い、「ホカ」と読める語句を判定
    """
    tokens = mecab.parse(text).splitlines()
    for token in tokens:
        if token == 'EOS':  # EOS(End of Sentence)は無視
            continue

        parts = token.split('\t')
        if len(parts) < 4:
            continue
        
        surface = parts[0]  # 表層形
        pronunciation = parts[1]  # 読み仮名

        if "ホカ" in pronunciation:
            if surface != "ほか":
                print(f"不適切な「ホカ」が検出されました: {surface}")
                return True
    return False

def process_xml(xml_file):
    keyword_count = 0   # 処理対象となった要素をカウント
    processed_elements = []  # 処理対象の要素を格納するリスト

    tree = ET.parse(xml_file)
    root = tree.getroot()

    for paragraph in root.findall('.//w:p', namespaces):
        for text_elem in paragraph.findall('.//w:t', namespaces):
            text = text_elem.text
            if text and any(keyword in text for keyword in ["とき", "時", "他", "外"]):
                keyword_count += 1  # カウントを増加
                processed_elements.append(text)  # 処理対象の要素をリストに追加
                if process_text(text):
                    highlight_paragraph(paragraph)

    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    print(f"処理済みのXMLが {xml_file} に保存されました。")
    print(f"処理対象となった要素の数: {keyword_count}")  # カウントを出力
    print("処理対象の要素リスト:")
    for element in processed_elements:
        print(element)  # 処理対象の要素を出力

# 使用例
process_xml('xml_new/word/document.xml')
