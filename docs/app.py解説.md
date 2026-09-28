# 初心者でもわかる！AIライティングツールの心臓部「app.py」を読み解く

AIライティングツールの画面は、すべて `app.py` という1つのファイルで作られています。約200行のコードを、上から順番に読んでいきましょう。

---

## まず知っておきたい大事なルール：Streamlit は「毎回、上から全部」実行する

コードを読む前に、これだけは覚えておいてください。

> **Streamlit は、ボタンを押す・文字を入力するなどの操作があるたびに、`app.py` を1行目から最後まで丸ごと実行し直します。**

画面を「部分的に書き換える」のではなく、「毎回ゼロから描き直す」仕組みです。この性質のおかげで、コードが素直に上から下へ読めます。ただ、そのままでは「前回の結果」を覚えておけません。そこで出てくるのが、あとで説明する `st.session_state` です。

---

## 第1章：準備（1〜23行目）

### 部品の読み込み

```python
import streamlit as st
from dotenv import load_dotenv
from gemini_client import stream_generate
from tools import TOOLS, Field, Tool
```

使う部品を読み込んでいます。役割分担は次のとおりです。

| 読み込むもの | 役割 |
|---|---|
| `streamlit` | 画面を作るライブラリ |
| `dotenv` | `.env` ファイルからAPIキーを読むライブラリ |
| `gemini_client` | Gemini にお願いを送る係（別ファイル） |
| `tools` | 9種類のツールの設計図（別ファイル） |

`app.py` は「画面担当」に集中しています。AIとの通信やツールの中身は、別のファイルに任せています。

### 設定の読み込みと定数

```python
load_dotenv()
DEFAULT_MODELS = ["gemini-3.8-flash", "gemini-2.5-flash", ...]
```

`load_dotenv()` で `.env` の中身（APIキーなど）を読み込みます。`DEFAULT_MODELS` は、サイドバーで選べるモデルの一覧です。

### 記憶の箱を用意する

```python
if "results" not in st.session_state:
    st.session_state.results = {}
if "history" not in st.session_state:
    st.session_state.history = []
```

ここが冒頭で話した「覚えておく仕組み」です。`st.session_state` は、**再実行されても中身が消えない特別な箱**です。

- `results`：ツールごとの最新の生成結果
- `history`：これまでの生成履歴

`if ... not in` で「まだ箱がなければ作る」としています。2回目以降の実行で中身が空にリセットされないようにするためです。

---

## 第2章：サイドバー（29〜64行目）`render_sidebar()`

画面左側のメニューと設定を作る関数です。

### ツールの選択メニュー

```python
pages = [f"{t.icon} {t.name}" for t in TOOLS] + [HISTORY_PAGE]
page = st.radio("ツールを選択", pages, label_visibility="collapsed")
```

`tools.py` のツール一覧から「📝 ブログ記事作成」のような名前を並べ、最後に「🕘 履歴」を加えています。`st.radio` は選択肢を1つ選ぶ部品で、**選ばれた項目の文字がそのまま `page` に入ります**。

ツール名をここに直接書いていないのがポイントです。`tools.py` にツールを足せば、メニューにも自動で出てきます。

### APIキーの入力欄

```python
api_key = os.getenv("GEMINI_API_KEY", "")
if api_key:
    st.caption("✅ APIキーは .env から読み込み済みです")
else:
    api_key = st.text_input("Gemini APIキー", type="password", ...)
```

`.env` にキーがあればそれを使い、なければ入力欄を出します。`type="password"` にしているので、入力した文字は「●●●」で隠れます。

### モデルと temperature

```python
model = st.selectbox("モデル", models + [CUSTOM_MODEL], ...)
if model == CUSTOM_MODEL:
    model = st.text_input("モデル名", ...)
```

モデルはプルダウンで選びます。「その他（手入力）」を選んだときだけ、文字入力欄が現れます。

```python
temp_override = st.checkbox("創造性（temperature）を手動で指定する")
temperature = st.slider(..., disabled=not temp_override)
```

temperature は「AIの文章の自由度」です。チェックを入れたときだけスライダーを動かせるようにしています（`disabled=not temp_override`）。

### 設定をまとめて返す

```python
settings = {"api_key": ..., "model": ..., "temperature": temperature if temp_override else None}
return page, settings
```

「どのページを選んだか」と「設定」を返します。temperature はチェックがなければ `None`（空っぽ）にしておきます。こうすると、あとで「ツールごとのおすすめ値を使う」と判断できます。

---

## 第3章：AIに文章を作ってもらう（70〜103行目）

### `generate()`：AIへの依頼係

```python
if not settings["api_key"]:
    st.error("サイドバーの「設定」で Gemini APIキーを入力してください。")
    return None
```

まず「APIキーはある？」「モデル名は入ってる？」を確認します。足りなければ、エラーを出してここで止めます。

```python
temperature = settings["temperature"] if settings["temperature"] is not None else tool.temperature
```

手動で指定されていればその値を、なければツールごとのおすすめ値（要約なら 0.3、キャッチコピーなら 1.0 など）を使います。

```python
try:
    with st.container(border=True):
        with st.spinner("生成中..."):
            stream = stream_generate(...)
            result = st.write_stream(stream)
except Exception as e:
    st.error(f"生成に失敗しました：{e}")
    return None
```

ここがこのアプリの見どころです。

- `stream_generate(...)` は、Gemini の返事を**少しずつ**受け取る仕組みです。
- `st.write_stream(stream)` は、受け取った文字を**届いた順に画面へ書き出し**ます。ChatGPT のように文字がスルスル出てくるのはこのためです。最後に、完成した全文を `result` に入れてくれます。
- `try ... except` は「失敗したときの保険」です。APIキーの間違いや通信エラーがあっても、アプリが落ちずにエラーメッセージを表示します。

### `save_result()`：記録係

```python
st.session_state.results[tool.key] = result
st.session_state.history.insert(0, {...})
```

生成した文章を、第1章で用意した「記憶の箱」に保存します。`insert(0, ...)` はリストの先頭に入れる命令なので、履歴は新しい順に並びます。

---

## 第4章：ツールの画面（109〜174行目）

### `render_field()`：入力欄を作る係

```python
if f.kind == "textarea":
    return st.text_area(...)
if f.kind == "select":
    return st.selectbox(...)
return st.text_input(...)
```

`tools.py` の設計図に書かれた種類に応じて、入力欄を作り分けます。

| 種類 | できる入力欄 |
|---|---|
| `textarea` | 長文用の大きな入力欄 |
| `select` | プルダウン |
| それ以外 | 1行の入力欄 |

`key = f"{tool.key}__{f.key}"` で、入力欄ごとに固有の名前を付けています。こうすると、ツールを切り替えて戻ってきても入力内容が残ります。

### `render_tool()`：ツール画面の組み立て係

```python
with st.form(f"form_{tool.key}"):
    values = {f.key: render_field(tool, f) for f in tool.fields}
    submitted = st.form_submit_button("✨ 生成する", ...)
```

`st.form` は「入力欄をひとまとめにする枠」です。普通は1文字入力するたびに再実行が起きますが、form の中では**「生成する」ボタンを押すまで待って**くれます。

```python
if submitted:
    missing = [f.label for f in tool.fields if f.required and not str(values[f.key]).strip()]
    if missing:
        st.warning(...)
    else:
        result = generate(tool, tool.build_prompt(values), settings)
        if result:
            save_result(...)
            st.rerun()
```

ボタンが押されたら、次の順に進みます。

1. 必須項目（`*` 付き）が空でないかチェックする
2. `tool.build_prompt(values)` で、入力内容からAIへの依頼文を組み立てる
3. `generate()` でAIに依頼する
4. 成功したら保存して、`st.rerun()` で画面を描き直す

最後の `st.rerun()` には理由があります。描き直さないと、「ストリーミング中に表示した文章」と「下の結果表示エリアの文章」が二重に表示されてしまいます。いったん描き直して、画面をすっきりさせているわけです。

### `render_result()`：結果の表示係

```python
preview, raw = st.tabs(["プレビュー", "テキスト（コピー用）"])
```

結果を2つのタブで見せます。

- **プレビュー**：見出しや太字がきれいに表示された状態
- **テキスト（コピー用）**：右上のボタンで、まるごとコピーできる状態

タブの下には、文字数の表示、ダウンロードボタン、クリアボタンが並んでいます。

### 「追加指示で修正する」の仕組み

```python
prompt = (
    "以下は先ほどあなたが作成した文章です。次の指示に従って修正し、..."
    f"【指示】\n{instruction}\n\n【文章】\n{result}"
)
```

実は、AIは前回の会話を覚えていません。そこで、**「さっきの文章」と「今回の指示」をセットにして、もう一度お願いしています**。「前回こう書いてもらったので、これをこう直して」と毎回説明し直すイメージです。

---

## 第5章：履歴画面（180〜199行目）`render_history()`

```python
for h in history:
    with st.expander(f"{h['time']}　{h['tool']}　—　{h['input']}"):
        st.markdown(h["output"])
```

保存された履歴を1件ずつ、クリックで開閉できる箱（`st.expander`）に入れて並べます。「すべてダウンロード」を押すと、全履歴を1つのファイルにつなげて保存できます。

---

## 最終章：司令塔（203〜207行目）

```python
page, settings = render_sidebar()
if page == HISTORY_PAGE:
    render_history()
else:
    render_tool(next(t for t in TOOLS if f"{t.icon} {t.name}" == page), settings)
```

たった5行ですが、ここがアプリ全体の**スタート地点**です。

1. サイドバーを描いて、「どのページ？」と「設定」を受け取る
2. 履歴ページなら履歴画面を出す
3. それ以外なら、名前が一致するツールを探して、その画面を出す

ここまでの関数は、すべてこの5行から呼び出されています。

---

## まとめ：全体の流れ

```
ユーザーが操作
   ↓
app.py を上から再実行
   ↓
サイドバーを描く → ページを判定
   ↓
ツール画面を描く（tools.py の設計図から自動で）
   ↓
「生成する」が押された？
   → 依頼文を作る → Gemini に送る → 文字を少しずつ表示
   → session_state に保存 → 画面を描き直す
```

**押さえておきたい3つのポイント**

1. **Streamlit は毎回上から全部実行する。** 覚えておきたいものは `st.session_state` に入れる。
2. **画面は設計図（`tools.py`）から自動で作られる。** だから `app.py` を触らずにツールを追加できる。
3. **AIは会話を覚えていない。** 修正のときは、前の文章ごと渡してお願いし直している。
