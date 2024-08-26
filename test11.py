from lxml import etree as ET  # lxmlを使用
import MeCab  # MeCabを使用した形態素解析
import spacy  # spaCyを使用した構文解析
import copy

# MeCabのトークナイザーを初期化
mecab = MeCab.Tagger("-Ochasen")

# spaCyの日本語モデルをロード
nlp = spacy.load("ja_core_news_md")

# 名前空間の定義
namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
ET.register_namespace('w', namespaces['w'])  # 名前空間プレフィックスを指定

def create_highlighted_run(original_rpr, text, color):
    """
    新しい <w:r> 要素を作成し、指定された色でハイライトを適用した <w:t> を含む。
    元の <w:rPr> 要素をそのままコピーして適用し、ハイライトを追加する。
    """
    new_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')

    if original_rpr is not None:
        # 元の <w:rPr> 要素を深くコピー
        new_rpr = copy.deepcopy(original_rpr)
        new_run.append(new_rpr)

        # ハイライトの要素を追加
        highlight_elem = ET.SubElement(new_rpr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight')
        highlight_elem.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', color)
    else:
        # 元の <w:rPr> がない場合でもハイライトを追加
        new_rpr = ET.SubElement(new_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
        highlight_elem = ET.SubElement(new_rpr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight')
        highlight_elem.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', color)

    # 新しい <w:t> 要素を追加
    new_text_element = ET.SubElement(new_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
    new_text_element.text = text

    return new_run

def create_plain_run(original_rpr, text):
    """
    元の<w:rPr>を保持しつつ、プレーンテキスト用の<w:r>要素を作成
    """
    plain_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
    if original_rpr is not None:
        plain_rpr = copy.deepcopy(original_rpr)
        plain_run.append(plain_rpr)
    plain_text_element = ET.SubElement(plain_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
    plain_text_element.text = text
    return plain_run

def analyze_and_replace(text, log_file):
    """
    MeCabで形態素解析を行い、「ほか」を意味する部分を検知し、「ほか」に変換する関数
    解析結果を指定されたテキストファイルに書き出す
    """
    tokens = mecab.parse(text).splitlines()
    new_text = ""
    highlighted_runs = []
    
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

        # 「ほか」を意味するものを検知（例: 名詞「他」「外」など）
        if (surface in ["他", "外"] and pos.startswith("名詞")) or pronunciation == "ホカ":
            highlighted_runs.append((surface, "ほか", "yellow"))
            new_text += "ほか"
        else:
            new_text += surface

    # 変換後のテキストをログファイルに書き出し
    log_file.write(f"変換後のテキスト: {new_text}\n\n")
    
    return new_text, highlighted_runs

def syntactic_analysis_and_highlight(doc, original_rpr, syntax_log_file, combined_text, combined_pronunciation):
    """
    spaCyを使用した構文解析を行い、「時」と「とき」の変換とハイライトを行う関数
    形態素解析で表層形が「時」「とき」で、かつ読みが「ジ」でないものを対象とする
    構文解析結果を指定されたテキストファイルに書き出す
    """
    modified_text = []
    highlighted_runs = []
    
    # 結合された文章に対して形態素解析を行い、読み仮名を取得
    mecab_result = mecab.parse(combined_text).splitlines()
    pronunciation_map = {}
    for mecab_token in mecab_result:
        if mecab_token == 'EOS':
            continue

        parts = mecab_token.split('\t')
        if len(parts) < 4:
            continue

        surface = parts[0]  # 表層形
        pronunciation = parts[1]  # 読み仮名

        pronunciation_map[surface] = pronunciation

    # spaCyを用いた構文解析
    for token in doc:
        surface = token.text
        pronunciation = pronunciation_map.get(surface, "")

        # 表層形が「時」または「とき」で、かつ読み方が「ジ」でないものを対象とする
        if surface in ["時", "とき"] and pronunciation == "トキ":
            # 構文解析を行い、必要な処理を適用
            if token.dep_ == "obl" and surface == "時":
                highlighted_runs.append((surface, "とき", "red"))
                modified_text.append("とき")
                syntax_log_file.write(f"解析: {surface}, 読み仮名: {pronunciation}, dep: {token.dep_}\n")
                syntax_log_file.write(f"変換: {surface} -> とき\n")
            elif token.dep_ == "ROOT" and surface == "とき":
                highlighted_runs.append((surface, "時", "red"))
                modified_text.append("時")
                syntax_log_file.write(f"解析: {surface}, 読み仮名: {pronunciation}, dep: {token.dep_}\n")
                syntax_log_file.write(f"変換: {surface} -> 時\n")
            else:
                modified_text.append(surface)
                syntax_log_file.write(f"解析: {surface}, 読み仮名: {pronunciation}, dep: {token.dep_}\n")
        else:
            # 「ジ」と読まれるものもログに出力
            syntax_log_file.write(f"--: {surface}, 読み仮名: {pronunciation}, dep: {token.dep_}\n")
            modified_text.append(surface)
    
    return "".join(modified_text), highlighted_runs

def split_and_highlight_text_element(text_element, log_file, syntax_log_file):
    """
    該当する<w:t>要素を切り分け、キーワードを含む部分にハイライトを追加する関数
    形態素解析で「ほか」を意味する「他、外」を「ほか」に変換し、構文解析で「とき」と「時」をルールベースで変換してハイライトを適用
    """
    parent_run = text_element.getparent()
    original_rpr = parent_run.find('.//w:rPr', namespaces)  # 元の<w:rPr>情報を取得
    
    # <w:t>要素を結合して1つのテキストにする
    combined_text = "".join([t.text for t in parent_run.findall('.//w:t', namespaces) if t.text])
    
    # まずテキスト全体を形態素解析で変換
    modified_text, highlighted_runs_mecab = analyze_and_replace(combined_text, log_file)

    # 変換されたテキストでspaCyによる構文解析を実行
    doc = nlp(modified_text)
    syntactically_modified_text, highlighted_runs_spacy = syntactic_analysis_and_highlight(doc, original_rpr, syntax_log_file, combined_text, modified_text)

    # ハイライトとテキストの置き換え処理
    new_elements = []
    highlighted_runs = highlighted_runs_mecab + highlighted_runs_spacy
    current_position = 0
    
    # 元のテキストのどの位置まで処理されたかを記録
    for original_text, modified_text, color in highlighted_runs:
        index = syntactically_modified_text.find(modified_text, current_position)
        if index == -1:
            continue

        # ハイライトされない部分を追加
        if current_position < index:
            unhighlighted_text = syntactically_modified_text[current_position:index]
            if unhighlighted_text:
                new_elements.append(create_plain_run(original_rpr, unhighlighted_text))

        # ハイライトされた部分を追加
        new_elements.append(create_highlighted_run(original_rpr, modified_text, color))
        current_position = index + len(modified_text)

    # 残りの部分を追加
    if current_position < len(syntactically_modified_text):
        remaining_text = syntactically_modified_text[current_position:]
        new_elements.append(create_plain_run(original_rpr, remaining_text))

    # 元の要素を削除して新しい要素を追加
    parent = parent_run.getparent()
    for new_element in new_elements:
        parent.insert(parent.index(parent_run), new_element)
    parent.remove(parent_run)

def process_xml(xml_file, log_filename, syntax_log_filename):
    keyword_count = 0   # 処理対象となった要素をカウント
    processed_elements = []  # 処理対象の要素を格納するリスト

    # ログファイルを開く
    with open(log_filename, 'w', encoding='utf-8') as log_file, open(syntax_log_filename, 'w', encoding='utf-8') as syntax_log_file:
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
                        split_and_highlight_text_element(text_elem, log_file, syntax_log_file)  # 「ほか」に変換後ハイライトを適用

    tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
    print(f"処理対象となった要素の数: {keyword_count}")  # カウントを出力

    # 処理対象の要素リストを出力
    print("処理対象の要素リスト:")
    for element in processed_elements:
        print(element)  # 処理対象の要素を出力

# 使用例
process_xml('xml_new/word/document.xml', 'mecab_analysis_log.txt', 'spacy_analysis_log.txt')
