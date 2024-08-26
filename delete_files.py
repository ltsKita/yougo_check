import os
import shutil

def delete_files_and_directories():
    # 削除対象のディレクトリとファイル
    directories = ['xml', 'xml_new']
    files = ['mecab_analysis_log.txt', 'spacy_analysis_log.txt']

    # ディレクトリの削除
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"ディレクトリ '{directory}' を削除しました。")
        else:
            print(f"ディレクトリ '{directory}' は存在しません。")

    # ファイルの削除
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            print(f"ファイル '{file}' を削除しました。")
        else:
            print(f"ファイル '{file}' は存在しません。")

    # 出力ファイルの削除
    output_docx = f"【校閲ずみ】{core_filename}.docx"
    if os.path.exists(output_docx):
        os.remove(output_docx)
        print(f"ファイル '{output_docx}' を削除しました。")
    else:
        print(f"ファイル '{output_docx}' は存在しません。")

    # dataディレクトリ内のファイルを削除
    data_directory = 'data'
    if os.path.exists(data_directory):
        for filename in os.listdir(data_directory):
            file_path = os.path.join(data_directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"dataディレクトリ内のファイル '{file_path}' を削除しました。")
            else:
                print(f"'{file_path}' はファイルではないため、削除されませんでした。")
    else:
        print(f"ディレクトリ '{data_directory}' は存在しません。")

# パスの設定
from make_xml_from_wordfile import get_docx_file
file_path = get_docx_file("data")
core_filename = os.path.splitext(os.path.basename(file_path))[0]

# 関数の呼び出し
delete_files_and_directories()