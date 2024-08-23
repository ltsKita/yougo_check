# 該当要素を別の<w:r>および<w:t>に切り分け
# ただし、複数要素に対応せず
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

def split_and_highlight_text_element(text_element, keyword):
    """
    該当する<w:t>要素を切り分け、キーワードを含む部分にハイライトを追加する関数
    """
    parent_run = text_element.getparent()
    text = text_element.text

    # キーワードの前後でテキストを分割
    parts = text.split(keyword, 1)

    if len(parts) == 2:
        before_text = parts[0]
        after_text = parts[1]

        # 元の<w:t>を「前の部分」として更新
        text_element.text = before_text

        # 新しい<w:r>と<w:t>を作成し、キーワードを挿入
        highlighted_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
        highlighted_rpr = ET.SubElement(highlighted_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
        ET.SubElement(highlighted_rpr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight', {'{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val': 'yellow'})
        highlighted_text_element = ET.SubElement(highlighted_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        highlighted_text_element.text = keyword
        parent_run.addnext(highlighted_run)

        # さらに新しい<w:r>と<w:t>を作成し、後ろのテキストを挿入
        after_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
        after_text_element = ET.SubElement(after_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        after_text_element.text = after_text
        highlighted_run.addnext(after_run)

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

            # キーワードを含む<w:t>要素を切り分け、ハイライトを追加
            for text_elem in paragraph.findall('.//w:t', namespaces):
                if text_elem.text:
                    for keyword in ["とき", "時", "他", "外"]:
                        if keyword in text_elem.text:
                            split_and_highlight_text_element(text_elem, keyword)

    tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
    print(f"処理対象となった要素の数: {keyword_count}")  # カウントを出力

    # 処理対象の要素リストを出力
    print("処理対象の要素リスト:")
    for element in processed_elements:
        print(element)  # 処理対象の要素を出力

# 使用例
process_xml('xml_new/word/document.xml')
