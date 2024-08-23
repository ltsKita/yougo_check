from lxml import etree as ET  # lxmlを使用

# 名前空間の定義
namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
ET.register_namespace('w', namespaces['w'])  # 名前空間プレフィックスを指定

def highlight_text_element(text_element):
    """
    特定の<w:t>要素にハイライトを追加する関数
    """
    parent_run = text_element.getparent()  # getparent()メソッドが利用可能
    rpr = parent_run.find('.//w:rPr', namespaces)
    if rpr is None:
        rpr = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
        parent_run.insert(0, rpr)
    # 正しい名前空間でハイライトの要素を追加する
    highlight_elem = ET.SubElement(rpr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight')
    highlight_elem.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', 'yellow')
    print(f"ハイライトが追加されました: {ET.tostring(parent_run, pretty_print=True, encoding='unicode')}")

def process_xml(xml_file):
    keyword_count = 0   # 処理対象となった要素をカウント
    processed_elements = []  # 処理対象の要素を格納するリスト

    tree = ET.parse(xml_file)
    root = tree.getroot()

    for paragraph in root.findall('.//w:p', namespaces):
        # <w:p>内部のすべての<w:t>要素を結合
        full_text = "".join(text_elem.text for text_elem in paragraph.findall('.//w:t', namespaces) if text_elem.text)
        
        # 処理対象の文字列を含むかチェック
        if any(keyword in full_text for keyword in ["とき", "時", "他", "外"]):
            keyword_count += 1  # カウントを増加
            processed_elements.append(full_text)  # 処理対象の要素をリストに追加

            # キーワードを含む<w:t>要素にハイライトを追加
            for text_elem in paragraph.findall('.//w:t', namespaces):
                if text_elem.text and any(keyword in text_elem.text for keyword in ["とき", "時", "他", "外"]):
                    highlight_text_element(text_elem)  # 該当の<w:t>要素にハイライトを追加

    tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
    print(f"処理済みのXMLが {xml_file} に保存されました。")
    print(f"処理対象となった要素の数: {keyword_count}")  # カウントを出力

    # 処理対象の要素リストを出力
    print("処理対象の要素リスト:")
    for element in processed_elements:
        print(element)  # 処理対象の要素を出力

# 使用例
process_xml('xml_new/word/document.xml')
