# docx_processing.py から関数をインポート
from make_xml_from_wordfile_llm import get_docx_file, extract_docx_to_xml
from process_llm import process_xml
from remake_wordfile_from_xml import create_docx
import os


# .docx ファイルのパス取得
docx_file = get_docx_file("data")  # ディレクトリを指定

# XMLへ変換
extract_docx_to_xml(docx_file, "xml/")
extract_docx_to_xml(docx_file, "xml_new/")  # 別ディレクトリへの変換

# document.xml の存在確認と待機
document_xml_path = 'xml_new/word/document.xml'

# 校閲処理を実行
process_xml(document_xml_path, 'mecab_analysis_log.txt', 'spacy_analysis_log.txt')

# 校閲後のXMLファイルをWordファイルに再構成
core_filename = os.path.splitext(os.path.basename(docx_file))[0]
output_docx = f"【校閲ずみ】{core_filename}.docx"
create_docx("xml_new", output_docx)