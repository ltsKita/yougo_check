from lxml import etree as ET  # lxmlを使用
import MeCab  # MeCabを使用した形態素解析
import spacy

# spaCyの日本語モデルをロード（事前にインストールが必要）
nlp = spacy.load("ja_core_news_md")

# MeCabのトークナイザーを初期化
mecab = MeCab.Tagger("-Ochasen")

# 名前空間の定義
namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
ET.register_namespace('w', namespaces['w'])  # 名前空間プレフィックスを指定

def analyze_and_highlight_toki_with_spacy(paragraph, log_file_morph, log_file_syntax, review_log_file):
    """
    SpaCyを使って段落全体を解析し、「時(とき)」を判定、校閲対象を記録。
    """
    # <w:t>要素を結合して段落全体のテキストを取得
    full_text = "".join(text_elem.text for text_elem in paragraph.findall('.//w:t', namespaces) if text_elem.text)
    if not full_text:
        log_file_syntax.write("Text element is empty or not found.\n")
        return

    log_file_syntax.write(f"Analyzing paragraph: {full_text}\n")
    doc = nlp(full_text)
    new_text = ""
    review_target = False

    for token in doc:
        mecab_result = mecab.parse(token.text).splitlines()

        if len(mecab_result) > 1:
            mecab_token = mecab_result[0].split('\t')
            surface = mecab_token[0]
            pronunciation = mecab_token[1]

            log_file_morph.write(f"Surface: {surface}, Pronunciation: {pronunciation}, Token: {token.text}\n")

            if surface in ["時", "とき"] and pronunciation != "ジ":
                review_target = True
                if token.dep_ == "obl" and token.text == "時":
                    log_file_syntax.write(f"Highlighting: {token.text} as とき\n")
                    new_text += '<highlight color="red">とき</highlight>'
                elif token.dep_ == "ROOT" and token.text == "とき":
                    log_file_syntax.write(f"Highlighting: {token.text} as 時\n")
                    new_text += '<highlight color="red">時</highlight>'
                else:
                    new_text += token.text
            else:
                new_text += token.text
        else:
            new_text += token.text

    if review_target:
        review_log_file.write(f"Review Target Paragraph: {ET.tostring(paragraph, pretty_print=True, encoding='unicode')}\n")

    new_text = new_text.replace("&lt;", "<").replace("&gt;", ">")

    # 更新されたテキストを段落全体に反映
    for text_elem in paragraph.findall('.//w:t', namespaces):
        text_elem.text = new_text

def analyze_and_replace(text, log_file):
    """
    MeCabで形態素解析を行い、特定の単語を検出して変換を行う関数。
    """
    tokens = mecab.parse(text).splitlines()
    new_text = ""

    # 解析前のテキストをログファイルに書き出し
    log_file.write(f"解析前のテキスト: {text}\n")

    for token in tokens:
        if token == 'EOS':  # EOS(End of Sentence)は無視
            continue

        parts = token.split('\t')
        if len(parts) < 4:
            continue

        surface = parts[0]  # 表層形
        pronunciation = parts[1]  # 読み仮名
        pos = parts[3]  # 品詞情報

        # 解析結果をログファイルに書き出し
        log_file.write(f"表層形: {surface}, 読み仮名: {pronunciation}, 品詞: {pos}\n")

        # 「ほか」を意味するものを検知し、変換
        if (surface in ["他", "外"] and pos.startswith("名詞")) or "ホカ" in pronunciation:
            new_text += "ほか"
        else:
            new_text += surface

    # 変換後のテキストをログファイルに書き出し
    log_file.write(f"変換後のテキスト: {new_text}\n\n")

    return new_text


def split_and_highlight_text_element(text_element, log_file_hoka, log_file_morph, log_file_syntax, review_log_file):
    """
    テキスト要素を分割してハイライトを追加する関数。
    """
    parent_run = text_element.getparent()
    original_rpr = parent_run.find('.//w:rPr', namespaces)  # 元の<w:rPr>情報を取得
    text = text_element.text

    # 「ほか」の変換処理
    modified_text_hoka = analyze_and_replace(text, log_file_hoka)
    # 「とき」の変換処理
    modified_text_toki = analyze_and_highlight_toki_with_spacy(text_element, log_file_morph, log_file_syntax, review_log_file)

    # 「ほか」のハイライト処理を追加
    if "ほか" in modified_text_hoka:
        text_element.text = modified_text_hoka
    else:
        text_element.text = modified_text_toki


def process_xml(xml_file, log_filename_hoka, log_filename_morph, log_filename_syntax, review_log_filename):
    """
    XMLファイルを処理し、校閲とハイライトを実行するメイン関数。
    """
    keyword_count = 0
    processed_elements = []

    with open(log_filename_hoka, 'w', encoding='utf-8') as log_file_hoka, \
         open(log_filename_morph, 'w', encoding='utf-8') as log_file_morph, \
         open(log_filename_syntax, 'w', encoding='utf-8') as log_file_syntax, \
         open(review_log_filename, 'w', encoding='utf-8') as review_log_file:

        tree = ET.parse(xml_file)
        root = tree.getroot()

        for paragraph in root.findall('.//w:p', namespaces):
            full_text = "".join(text_elem.text for text_elem in paragraph.findall('.//w:t', namespaces) if text_elem.text)

            if any(keyword in full_text for keyword in ["とき", "時", "他", "外"]):
                keyword_count += 1
                processed_elements.append(full_text)

                analyze_and_highlight_toki_with_spacy(paragraph, log_file_morph, log_file_syntax, review_log_file)

    tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
    print(f"処理対象となった要素の数: {keyword_count}")

    for element in processed_elements:
        print(element)

# 使用例
process_xml('xml_new/word/document.xml', 'mecab_analysis_log.txt', 'morph_analysis_log.txt', 'syntax_analysis_log.txt', 'review_targets.txt')