---
name: add-tool
description: AIライティングツールに新しいツール（例：「プレスリリース作成」「謝罪文作成」）を追加する。ユーザーが新しいライティング機能・ツールの追加を頼んだときに使う。
argument-hint: "[追加したいツールの内容]"
---

# 新しいライティングツールを追加する

追加したいツール: $ARGUMENTS

（内容が空、または曖昧なら、どんな文章を作るツールかを1問だけ確認する）

## 手順

1. `tools.py` を読み、既存ツールの書き方（特に `BLOG` や `EMAIL`）に合わせる。
2. `tools.py` の最後の `TOOLS = [...]` の直前に、次の3つを追加する。
   - `_<key>_prompt(v: dict) -> str` 関数。任意項目は `_optional(label, value)` で「入力があるときだけ」追加する。
   - `Tool(...)` 定義。
     - `key`: 英小文字（ウィジェットのキーとテストの指定に使うので、既存と重複させない）
     - `name` / `icon` / `description`: 日本語の名前・絵文字・1行説明
     - `system_prompt`: 役割と出力形式（Markdown か、見出し構成、余計な前置きを書かない など）
     - `fields`: 主となる入力は `required=True` にする。選択肢は `kind="select"`（先頭がデフォルト）
     - `temperature`: 正確さ重視（要約・校正・翻訳）は 0.3、通常は 0.7、アイデア出しは 0.9〜1.0
3. `TOOLS` リストに追加する（サイドバーの並び順になる）。
4. `README.md` の機能表に1行追加する。
5. 動作確認する:
   ```
   .venv/Scripts/python.exe tests/smoke_test.py <key>
   .venv/Scripts/python.exe tests/smoke_test.py
   ```
6. 追加したツールの内容（入力項目・出力のイメージ）を、ユーザーにわかりやすい日本語で短く報告する。実際の Gemini の出力はまだ確認していないことを伝え、`start.bat` で試すよう案内する。

## 注意

- `Field.kind` は `text` / `textarea` / `select` だけが使える。それ以外が必要なら `app.py` の `render_field` も修正する。
- `app.py` は `tools.py` の定義から画面を自動生成するので、ツールを追加するだけなら `app.py` は変更しない。
