# 該当項目を一文字だけ補足することに成功
# リストで全体の検知もできている
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

def split_and_highlight_text_element(text_element, keywords):
    """
    該当する<w:t>要素を切り分け、キーワードを含む部分にハイライトを追加する関数
    """
    parent_run = text_element.getparent()
    original_rpr = parent_run.find('.//w:rPr', namespaces)  # 元の<w:rPr>情報を取得
    text = text_element.text

    # キーワードが含まれている部分を順次処理
    new_elements = []
    for keyword in keywords:
        while keyword in text:
            # キーワードの前後でテキストを分割
            before_text, after_text = text.split(keyword, 1)

            # 新しい<w:r>と<w:t>を作成し、「前の部分」を挿入
            if before_text:
                before_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
                before_rpr = ET.SubElement(before_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
                if original_rpr is not None:
                    before_rpr.extend(original_rpr)
                before_text_element = ET.SubElement(before_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                before_text_element.text = before_text
                new_elements.append(before_run)

            # 新しい<w:r>と<w:t>を作成し、ハイライト付きのキーワードを挿入
            highlighted_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
            highlighted_rpr = ET.SubElement(highlighted_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
            if original_rpr is not None:
                highlighted_rpr.extend(original_rpr)
            ET.SubElement(highlighted_rpr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight', {'{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val': 'yellow'})
            highlighted_text_element = ET.SubElement(highlighted_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
            highlighted_text_element.text = keyword
            new_elements.append(highlighted_run)

            # 残りのテキストを次に処理
            text = after_text

    # 最後の残りテキストも新しい<w:r>として追加
    if text:
        after_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
        after_rpr = ET.SubElement(after_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
        if original_rpr is not None:
            after_rpr.extend(original_rpr)
        after_text_element = ET.SubElement(after_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        after_text_element.text = text
        new_elements.append(after_run)

    # 元の<w:r>要素を新しい要素に置き換え
    for new_element in reversed(new_elements):
        parent_run.addnext(new_element)
    parent_run.getparent().remove(parent_run)

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
                    split_and_highlight_text_element(text_elem, ["とき", "時", "他", "外"])

    tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
    print(f"処理対象となった要素の数: {keyword_count}")  # カウントを出力

    # 処理対象の要素リストを出力
    print("処理対象の要素リスト:")
    for element in processed_elements:
        print(element)  # 処理対象の要素を出力

# 使用例
process_xml('xml_new/word/document.xml')
