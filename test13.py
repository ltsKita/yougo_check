from allennlp.predictors.predictor import Predictor
import allennlp_models.tagging
import lxml.etree as ET
import MeCab
import spacy
import copy

# MeCabのトークナイザーを初期化
mecab = MeCab.Tagger("-Ochasen")

# spaCyの日本語モデルをロード
nlp = spacy.load("ja_core_news_md")

# AllenNLPのSRLモデルをロード
srl_predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/structured-prediction-srl-bert.2020.12.15.tar.gz")

# 名前空間の定義
namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
ET.register_namespace('w', namespaces['w'])

def analyze_and_replace(text, log_file):
    tokens = mecab.parse(text).splitlines()
    new_text = ""
    highlighted_runs = []

    log_file.write(f"解析前のテキスト: {text}\n")

    for token in tokens:
        if token == 'EOS':
            continue

        parts = token.split('\t')
        if len(parts) < 4:
            continue

        surface = parts[0]
        pronunciation = parts[1]
        pos = parts[3]

        log_file.write(f"表層形: {surface}, 読み仮名: {pronunciation}, 品詞: {pos}\n")

        if (surface in ["他", "外"] and pos.startswith("名詞") and pronunciation != "ソト"):
            highlighted_runs.append((surface, "ほか", "yellow"))
            new_text += "ほか"
        else:
            new_text += surface

    log_file.write(f"変換後のテキスト: {new_text}\n\n")
    
    return new_text, highlighted_runs

def semantic_role_labeling(text, srl_log_file):
    """
    Semantic Role Labelingを使用して「時(とき)」の条件や時点を判断する
    """
    srl_results = srl_predictor.predict(sentence=text)
    predicates = srl_results['verbs']

    highlighted_runs = []
    modified_text = list(text)  # 文字列をリストに変換して編集をしやすくする

    for verb in predicates:
        description = verb['description']
        tags = verb['tags']
        for i, tag in enumerate(tags):
            if tag == "B-TMP" or tag == "I-TMP":
                if text[i] in ["時", "とき"]:
                    highlighted_runs.append((text[i], "とき", "blue"))
                    modified_text[i] = "とき"
                    srl_log_file.write(f"SRL解析: {text[i]} -> とき (時間)\n")
            elif tag == "B-ARGM-PRP" or tag == "I-ARGM-PRP":
                if text[i] in ["時", "とき"]:
                    highlighted_runs.append((text[i], "とき", "green"))
                    modified_text[i] = "とき"
                    srl_log_file.write(f"SRL解析: {text[i]} -> とき (条件)\n")

    return "".join(modified_text), highlighted_runs

def syntactic_analysis_and_highlight(doc, original_rpr, syntax_log_file, combined_text, combined_pronunciation):
    modified_text = []
    highlighted_runs = []

    mecab_result = mecab.parse(combined_text).splitlines()
    pronunciation_map = {}
    for mecab_token in mecab_result:
        if mecab_token == 'EOS':
            continue

        parts = mecab_token.split('\t')
        if len(parts) < 4:
            continue

        surface = parts[0]
        pronunciation = parts[1]

        pronunciation_map[surface] = pronunciation

    for token in doc:
        surface = token.text
        pronunciation = pronunciation_map.get(surface, "")

        if surface in ["時", "とき"] and pronunciation == "トキ":
            if token.dep_ == "obl" and surface == "時":
                highlighted_runs.append((surface, "とき", "red"))
                modified_text.append("とき")
                syntax_log_file.write(f"解析: {surface}, 読み仮名: {pronunciation}, dep: {token.dep_}\n")
                syntax_log_file.write(f"変換: {surface} -> とき\n")
            else:
                modified_text.append(surface)
                syntax_log_file.write(f"解析: {surface}, 読み仮名: {pronunciation}, dep: {token.dep_}\n")
        else:
            syntax_log_file.write(f"--: {surface}, 読み仮名: {pronunciation}, dep: {token.dep_}\n")
            modified_text.append(surface)

    return "".join(modified_text), highlighted_runs

def split_and_highlight_text_element(text_element, log_file, syntax_log_file, srl_log_file):
    parent_run = text_element.getparent()
    original_rpr = parent_run.find('.//w:rPr', namespaces)

    combined_text = "".join([t.text for t in parent_run.findall('.//w:t', namespaces) if t.text])

    modified_text, highlighted_runs_mecab = analyze_and_replace(combined_text, log_file)

    doc = nlp(modified_text)
    syntactically_modified_text, highlighted_runs_spacy = syntactic_analysis_and_highlight(doc, original_rpr, syntax_log_file, combined_text, modified_text)

    semantically_modified_text, highlighted_runs_srl = semantic_role_labeling(syntactically_modified_text, srl_log_file)

    new_elements = []
    highlighted_runs = highlighted_runs_mecab + highlighted_runs_spacy + highlighted_runs_srl
    current_position = 0

    for original_text, modified_text, color in highlighted_runs:
        index = semantically_modified_text.find(modified_text, current_position)
        if index == -1:
            continue

        if current_position < index:
            unhighlighted_text = semantically_modified_text[current_position:index]
            if unhighlighted_text:
                new_elements.append(create_plain_run(original_rpr, unhighlighted_text))

        new_elements.append(create_highlighted_run(original_rpr, modified_text, color))
        current_position = index + len(modified_text)

    if current_position < len(semantically_modified_text):
        remaining_text = semantically_modified_text[current_position:]
        new_elements.append(create_plain_run(original_rpr, remaining_text))

    parent = parent_run.getparent()
    for new_element in new_elements:
        parent.insert(parent.index(parent_run), new_element)
    parent.remove(parent_run)

def process_xml(xml_file, log_filename, syntax_log_filename, srl_log_filename):
    keyword_count = 0
    processed_elements = []

    with open(log_filename, 'w', encoding='utf-8') as log_file, open(syntax_log_filename, 'w', encoding='utf-8') as syntax_log_file, open(srl_log_filename, 'w', encoding='utf-8') as srl_log_file:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for paragraph in root.findall('.//w:p', namespaces):
            full_text = "".join(text_elem.text for text_elem in paragraph.findall('.//w:t', namespaces) if text_elem.text)

            if any(keyword in full_text for keyword in ["とき", "時", "他", "外"]):
                keyword_count += 1
                processed_elements.append(full_text)

                for text_elem in paragraph.findall('.//w:t', namespaces):
                    if text_elem.text:
                        split_and_highlight_text_element(text_elem, log_file, syntax_log_file, srl_log_file)

    tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)

# 使用例
process_xml('xml_new/word/document.xml', 'mecab_analysis_log.txt', 'spacy_analysis_log.txt', 'srl_analysis_log.txt')
