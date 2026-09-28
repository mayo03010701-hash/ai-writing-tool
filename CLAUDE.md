# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

Streamlit + Gemini API（`google-genai` SDK）で作った個人用AIライティングツール。DB・認証なし。UI・プロンプトはすべて日本語。ユーザーはプログラミング初心者なので、説明は平易な日本語で。

## コマンド（Windows）

```powershell
# 依存関係（仮想環境は .venv に作成済み）
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 起動（ユーザーは start.bat をダブルクリックで起動する）
.venv\Scripts\python.exe -m streamlit run app.py
```

```powershell
# スモークテスト（Gemini APIは呼ばない。全ツール＋追加指示＋履歴）
.venv\Scripts\python.exe tests\smoke_test.py
# 特定のツールだけ（引数は tool.key）
.venv\Scripts\python.exe tests\smoke_test.py blog
```

- リンターはない。コードを変更したら `tests/smoke_test.py` を実行する。このテストは `streamlit.testing.v1.AppTest` で画面を動かし、`gemini_client.stream_generate` をダミーに差し替えている。実際の Gemini の出力品質は確認できないので、ユーザーに `start.bat` で試してもらう。
- 新しいツールの追加は `/add-tool` スキル（`.claude/skills/add-tool/`）の手順に従う。
- `.env` には実際のAPIキーが入るため、`.claude/settings.json` で読み書きを禁止している。
- `.streamlit/config.toml` の `server.headless = true` は、初回起動時のメールアドレス入力プロンプトで起動が止まるのを防ぐためのもの。消さないこと。ブラウザは `start.bat` が開く。
- Bash ツール（Git Bash）で `.bat` を書くと `>nul` が `>/dev/null` に変換されるので、`.bat` は Write ツールで書く。

## アーキテクチャ

- **`tools.py` がツールの唯一の定義場所。** 各ツールは `Tool`（system_prompt、`Field` のリスト、`build_prompt(values: dict) -> str`、既定の temperature）。`TOOLS` リストに追加するだけで、`app.py` がサイドバー項目と入力フォームを自動生成する。`Field.kind` は `text` / `textarea` / `select` のみ。新しい種類を増やすときは `app.py` の `render_field` も修正する。
- **`app.py` の流れ:** フォーム送信 → 必須チェック → `generate()` で `st.write_stream` によりストリーミング表示 → `save_result()` で `st.session_state.results[tool.key]`（ツールごとの最新結果）と `st.session_state.history` に保存 → `st.rerun()`。再実行後に `render_result()` が結果・コピー・ダウンロード・「追加指示で修正」を描画する（rerun するのは、ストリーミング表示と結果表示の二重描画を避けるため）。
- 「追加指示で修正」は会話履歴を使わず、直前の出力と指示を1つのプロンプトにまとめて同じツールの system_prompt で再生成する。
- ウィジェットのキーは `f"{tool.key}__{field.key}"`。ツールを切り替えても入力内容が保持され、AppTest からもこのキーで操作できる。
- temperature はサイドバーで手動指定したときだけその値を使い、それ以外は `Tool.temperature` を使う。
- APIキーは `.env` の `GEMINI_API_KEY`（python-dotenv）を使い、空ならサイドバーの入力欄を使う。キーが空でない値だと入力欄が隠れるため、`.env` / `.env.example` に仮の値を入れないこと。モデルは `DEFAULT_MODELS`、または `.env` の `GEMINI_MODEL`、または手入力で選ぶ。
- 履歴はセッション内のみで、ブラウザを再読み込みすると消える（仕様）。
- `gemini_client.py` はクライアントを `st.cache_resource` で APIキーごとにキャッシュし、`generate_content_stream` の `chunk.text` を yield する。
