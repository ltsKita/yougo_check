用語の校閲を行います。
コマンドライン上で操作を行なってください。

# 以下を入力してプログラムが存在するディレクトリに移動してください。
cd /home/kita/yougo_check/

# venv仮想環境を作成してください。
python3 -m venv venv
※venvは任意の名前を設定できます。その場合は python3 -m venv projectenv のように変更してください

# venv仮想環境を有効化してください。
source venv/bin/activate
※venvに任意の名前を設定した場合は source projectenv/bin/activate のように変更してください。

# 以下を入力して生成AIモデルをダウンロードしてください(初回に一度だけ実行してください)
python model_download.py

# dataディレクトリに校閲対象のファイルを格納してください。

# 処理方法に応じて実行するファイルを変更しています。以下のいずれかを入力してください。
    ①ルールベースで用語誤りを修正する場合
    python main.py

    ②ルールベース+生成AI適用(時(とき)のみ対応)で用語誤りを修正する場合
    python main_llm.py

# (オプション)以下を入力するとプログラム実行時に生成したファイルを一括で削除できます。
python delete_files.py
