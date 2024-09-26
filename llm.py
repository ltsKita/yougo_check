from model_download import get_tokenizer, get_model
from transformers import pipeline
from langchain_huggingface.llms import HuggingFacePipeline
import re

tokenizer = get_tokenizer()
model = get_model()

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=0
    )
llm = HuggingFacePipeline(pipeline=pipe)

result = llm(
    """
    次のテキストに含まれる「時」と「とき」の使い分けを判断してください。
    テキスト: この時，修復作業を3日間と仮定すると，(2)第2.1.2-9表の条件で評価した総放出量のうち，希ガス約55％，よう素約75％が非常用ガス処理系の修復作業によって，よう素除去あり，非常用ガス処理系の排気口放出に変わることとなる。

    次のルールに従って使い分けを判断してください:
    単独で用いられる「時」や「とき」という語を検出した場合、そのまま「場合」と言い換えても自然な文章が成立するのであれば「とき」が正しい用法です。
    そうでないものは「時」が正しい用法になります。

    次のルールに従って使い分けを判断してください:
    単独で用いられる「時」や「とき」という語を検出した場合、そのまま「場合」と言い換えても自然な文章が成立するのであれば「とき」が正しい用法です。
    「時点」と言い換えても意味が通るものは「時」が正しい用法になります。

    次に、以下のステップに従って各ステップの内容を段階的に考察してください。
    1. **ステップ1**: 「テキスト:」に続く文章から「時」または「とき」のいずれが使用されているか判断します。
    2. **ステップ2**: 「時」を検出した場合、「場合」と置き換えてみてください。ただし、助詞を追加せず単語そのものを置き換えてください。そして文脈を確認し、自然な文章が成立するかどうかを確認します。ただし、「とき」を検出した場合、このステップはスキップしてください。
    - 自然な文章だと判断した場合、「時→とき」に変換します（この場合、後で「2」を選びます）。
    - 自然な文章でないと判断した場合、すでに文中で正しく「時」が使用されていると回答してください。（後で「0」を選びます）。
    3. **ステップ3**: 「とき」を検出した場合、「時点」と置き換えてみてください。そして文脈を確認し、自然な文章が成立するかどうかを確認します。ただし、「時」を検出した場合、このステップはスキップしてください。
    - 自然な文章だと判断した場合、「とき→時」に変換します（この場合、後で「1」を選びます）。
    - 自然な文章でないと判断した場合、すでに文中で正しく「とき」が使用されていると回答してください。（後で「0」を選びます）。
    4. **ステップ4**: 元のテキストと、ステップ2もしくは3で変換したテキストを比較します。ステップ2またはステップ3で0を選択している場合、変換前後の比較は行わず「0」と回答してください。
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
,temperature=0)

# 回答部分を抽出
print("-"*10 + "判定結果" + "-"*10)
print(result)
