"""
このファイルでは校閲対象となる文字列を含むテキストを抽出し、LLMを使用して用語の校閲を行います。
"""

from lxml import etree as ET  # lxmlを使用
import MeCab  # MeCabを使用した形態素解析
import spacy  # spaCyを使用した構文解析
import copy
from model_download import get_tokenizer, get_model
from transformers import pipeline
from langchain_huggingface.llms import HuggingFacePipeline
import re


# MeCabのトークナイザーを初期化
mecab = MeCab.Tagger("-Ochasen")

# spaCyの日本語モデルをロード
nlp = spacy.load("ja_core_news_md")

# 名前空間の定義
namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
ET.register_namespace('w', namespaces['w'])  # 処理の前後でxmlタグの名称が変更されないように指定

model_dir = "./model/elyza_llama3"
# ローカルのモデルとトークナイザを読み込む
# トークナイザとモデルを取得
tokenizer = get_tokenizer()
model = get_model()

# パイプラインの作成
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    # max_new_tokens=1,
    device=0
    # temperatureを0に
)

# HuggingFace Pipelineのラッパーを作成
llm = HuggingFacePipeline(pipeline=pipe)

def create_highlight(original_rpr, text, color):
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
    元の<w:rPr>を保持しつつ、<w:r>要素を複製
    """
    plain_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
    if original_rpr is not None:
        plain_rpr = copy.deepcopy(original_rpr)
        plain_run.append(plain_rpr)
    plain_text_element = ET.SubElement(plain_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
    plain_text_element.text = text
    return plain_run

def analyze_hoka(text, log_file):
    """
    形態素解析で表層形が「他」、「外」となるものを検知し、「ほか」に変換する関数
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
        # 「ソト」または「ガイ」と読まれない場合にのみ「ほか」として検知する条件を追加
        if (surface in ["他", "外"] and pos.startswith("名詞") and pronunciation not in ["ソト", "ガイ"]):
            highlighted_runs.append((surface, "ほか", "yellow"))
            new_text += "ほか"
        else:
            new_text += surface

    # 変換後のテキストをログファイルに書き出し
    log_file.write(f"変換後のテキスト: {new_text}\n\n")
    
    return new_text, highlighted_runs

def analyze_toki(original_rpr, syntax_log_file, combined_text):
    """
    テキスト結合を行なったcombined_text全体に対して「時」と「とき」の検知を行い、文脈に応じて適切に変換する関数。
    LLMが0を返した場合は処理を行わない。
    """
    modified_text = combined_text  # まず、combined_textをそのままmodified_textにコピー
    highlighted_runs = []

    # テキスト全体に対して「時」または「とき」を検索
    if "時" in combined_text or "とき" in combined_text:
        # LLMで文脈に応じた変換を行う
        prompt = f"""
        次のテキストに含まれる「時」と「とき」の使い分けを判断してください。
        テキスト: {combined_text}

        次のルールに従って使い分けを判断してください:
        単独で用いられる「時」や「とき」という語を検出した場合、そのまま「場合」と言い換えても自然な文章が成立するのであれば「とき」が正しい用法です。
        「時点」と言い換えても意味が通るものは「時」が正しい用法になります。

        次に、以下のステップに従って各ステップの内容を段階的に考察してください。
        **ステップ1**: 「テキスト:」に続く文章から「時」または「とき」のいずれが使用されているか判断します。
        **ステップ2**: 「時」を検出した場合、「場合」と置き換えてみてください。ただし、助詞を追加せず単語そのものを置き換えてください。そして文脈を確認し、自然な文章が成立するかどうかを確認します。ただし、「とき」を検出した場合、このステップはスキップしてください。
        - 自然な文章だと判断した場合、「時→とき」に変換します（この場合、後で「2」を選びます）。
        - 自然な文章でないと判断した場合、すでに文中で正しく「時」が使用されていると回答してください。（後で「0」を選びます）。
        **ステップ3**: 「とき」を検出した場合、「時点」と置き換えてみてください。そして文脈を確認し、自然な文章が成立するかどうかを確認します。ただし、「時」を検出した場合、このステップはスキップしてください。
        - 自然な文章だと判断した場合、「とき→時」に変換します（この場合、後で「1」を選びます）。
        - 自然な文章でないと判断した場合、すでに文中で正しく「とき」が使用されていると回答してください。（後で「0」を選びます）。
        **ステップ4**: 元のテキストと、ステップ2もしくは3で変換したテキストを比較します。このとき、『時間』と『状況』のいずれを意味しているかに注目して分析してください。ステップ2またはステップ3で0を選択している場合、変換前後の比較は行わず「0」と回答してください。
        - ステップ2またはステップ3で変換したテキストの方が適切だと判断した場合、ステップ2またはステップ3で選択した数字を回答します。
        - 元のテキストの方が適切だと判断した場合、0を回答します。

        以下のようなフォーマットで回答してください。
        ----------------------------------------------------------------------------
        思考：
        (ステップ1)
        テキスト：「いざという時は頼りになる」は、「時」を使用しています。
        
        (ステップ2)
        「時」を検出したので「場合」と置き換えます。
        「いざという場合は頼りになる」
        自然な文章なので、「時→とき」に変換します。(後で2と回答)

        (ステップ3)
        「時」を検出したのでスキップします。

        (ステップ4)
        元のテキスト：いざという時は頼りになる
        変換後のテキスト：いざという場合は頼りになる
        文脈を確認すると、ここで使用されている「時(とき)」は時間に関係なく、状況全体や可能性について議論していると捉えられるため、変換後のテキストが適切です。
        よって、ステップ2で選択した「2」が回答となります。

        回答:2
        ----------------------------------------------------------------------------
        思考：
        (ステップ1)
        テキスト：「今は15時30分です」は、「時」を使用しています。
        
        (ステップ2)
        「時」を検出したので「場合」と置き換えます。
        「今は15場合30分です」
        自然な文章ではないので、すでに文中で正しく「時」が使用されています。(後で0と回答)

        (ステップ3)
        「時」を検出したのでスキップします。

        (ステップ4)
        ステップ2で「0」を選択しているので、変換前後の比較は行いません。
        よって、回答は「0」となります。

        回答:0
        ----------------------------------------------------------------------------
        思考：
        (ステップ1)
        テキスト：「母が私を呼んだとき、私は数学を勉強していた」から、「とき」を検出しました。
        
        (ステップ2)
        「とき」を検出したのでスキップします。

        (ステップ3)
        「とき」を検出したので「時点」と置き換えます。
        「母が私を呼んだ時点で、私は数学を勉強していた」
        自然な文章なので、「とき→時」に変換します。(後で1と回答)

        (ステップ4)
        元のテキスト：母が私を呼んだとき、私は数学を勉強していた
        変換後のテキスト：母が私を呼んだ時点で、私は数学を勉強していた
        文脈を確認すると、ここで使用されている「時(とき)」は具体的な時間や瞬間を意味しており、ある特定の時点で何かが発生しているというニュアンスを持っています。
        そのため、変換後のテキストが適切です。
        よって、ステップ3で選択した「1」が回答となります。

        回答:1
        ----------------------------------------------------------------------------
        思考：
        (ステップ1)
        テキスト：「荷物が多いときにはタクシーを使う。」から、「とき」を検出しました。
        
        (ステップ2)
        「とき」を検出したのでスキップします。

        (ステップ3)
        「とき」を検出したので「時点」と置き換えます。
        「荷物が多い時点にはタクシーを使う。」
        自然な文章ではないので、すでに文中で正しく「とき」が使用されています。(後で0と回答)

        (ステップ4)
        ステップ3で「0」を選択しているので、変換前後の比較は行いません。
        よって、回答は「0」となります。

        回答:0
        ----------------------------------------------------------------------------
        では「思考：」に続けてステップバイステップで考察し、「回答:」に続けて考察に紐付く数字を出力してください。
        """

        # プロンプトの長さを計算
        prompt_length = len(prompt)

        # LLM の出力を取得
        result = llm(prompt, temperature=0)

        # プロンプト部分を除いた LLM の生成部分だけを取得
        generated_text = result[prompt_length:]
        
        # 回答部分を取り出すための正規表現
        answer_pattern = r'(?<![「（])回答:\s*(\d)'

        # 回答部分を抽出
        answer_match = re.findall(answer_pattern, result)
        answer = answer_match[-1] if answer_match else None

        # LLM判定結果をログファイルに書き出し
        syntax_log_file.write(f"-"*50+"\n")
        syntax_log_file.write(f"LLMによる思考: {generated_text}\n")
        syntax_log_file.write(f"LLMによる判定結果: {answer}\n")
        syntax_log_file.write(f"対象テキスト: {combined_text}\n")

        # LLMの結果に基づいて変換を行う
        if answer == "1":
            # 「とき -> 時」の変換
            modified_text = combined_text.replace("とき", "時")
            highlighted_runs.append(("とき", "時", "red"))
            syntax_log_file.write(f"変換: とき -> 時\n")
            syntax_log_file.write(f"変換後のテキスト: {modified_text}\n")
        elif answer == "2":
            # 「時 -> とき」の変換
            modified_text = combined_text.replace("時", "とき")
            highlighted_runs.append(("時", "とき", "red"))
            syntax_log_file.write(f"変換: 時 -> とき\n")
            syntax_log_file.write(f"変換後のテキスト: {modified_text}\n")
        elif answer == "0":
            # LLMが0を返した場合は処理を行わない
            syntax_log_file.write(f"変換なし \n")
            syntax_log_file.write(f"変換後のテキスト: {modified_text}（変更なし）\n")
        else:
            syntax_log_file.write(f"うまく判定できませんでした。 \n")

    return modified_text, highlighted_runs

def split_and_highlight_text_element(text_element, log_file, syntax_log_file):
    """
    該当する<w:t>要素を切り分け、キーワードを含む部分にハイライトを追加する関数
    """
    parent_run = text_element.getparent()
    original_rpr = parent_run.find('.//w:rPr', namespaces)  # 元の<w:rPr>情報を取得
    
    # 親要素の<w:t>要素を結合して1つのテキストにする
    combined_text = "".join([t.text for t in parent_run.findall('.//w:t', namespaces) if t.text])
    
    # テキスト全体を形態素解析で変換
    modified_text, highlighted_runs_mecab = analyze_hoka(combined_text, log_file)

    # 変換されたテキストでLLMによる判定を実行
    syntactically_modified_text, highlighted_runs_spacy = analyze_toki(original_rpr, syntax_log_file, combined_text)

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
        new_elements.append(create_highlight(original_rpr, modified_text, color))
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
    """
    xmlからテキストを取得し、対象文字列（「他」、「外」、「時」、「とき」）を検索
    変換条件に一致する場合は変換を行い、ハイライトを付与
    """
    keyword_count = 0   # 処理対象となった要素をカウント
    processed_elements = []  # 処理対象の要素を格納するリスト

    # ログファイルを開く
    with open(log_filename, 'w', encoding='utf-8') as log_file, open(syntax_log_filename, 'w', encoding='utf-8') as syntax_log_file:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for paragraph in root.findall('.//w:p', namespaces):
            # <w:t>要素を取得
            full_text = "".join(text_elem.text for text_elem in paragraph.findall('.//w:t', namespaces) if text_elem.text)

            # 処理対象の文字列を含むかチェック
            if any(keyword in full_text for keyword in ["とき", "時", "他", "外"]):
                keyword_count += 1  # カウントを増加(デバッグ用)
                processed_elements.append(full_text)  # 処理対象の要素をリストに追加

                # キーワードを含む<w:t>要素を切り分け、ハイライトを追加
                for text_elem in paragraph.findall('.//w:t', namespaces):
                    if text_elem.text:
                        split_and_highlight_text_element(text_elem, log_file, syntax_log_file)  # 変換後にハイライトを適用

    tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)



# process_xml('xml_new/word/document.xml', 'mecab_analysis_log.txt', 'judge_llm_log.txt')