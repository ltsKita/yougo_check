from transformers import AutoModelForCausalLM, AutoTokenizer

# モデルとトークナイザをダウンロードしてローカルのmodelディレクトリに保存
model_name = "elyza/Llama-3-ELYZA-JP-8B"
# モデル格納先ディレクトリを指定
model_dir = "model"

# トークナイザーとモデルを指定ディレクトリにキャッシュ
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=model_dir)
model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=model_dir)


def get_tokenizer():
    # トークナイザーを別ファイルで使用するための関数
    return tokenizer

def get_model():
    # トークナイザーを別ファイルで使用するための関数
    return model