# ✍️ AIライティングツール

Streamlit と Gemini API で作った、個人用のAIライティングツールです。

## 機能

| ツール | 内容 |
|---|---|
| 📝 ブログ記事作成 | テーマ・キーワードから、見出し構成つきの記事を作成 |
| ✉️ メール返信作成 | 受信メールと伝えたい内容から、件名つきの返信文を作成 |
| 📋 文章要約 | 箇条書き・3行要約などの形式で要約 |
| 🔍 文章校正・推敲 | 修正後の文章と修正点の一覧を出力 |
| 🔄 リライト・トーン変換 | 敬語に、やわらかく、簡潔に などの書き直し |
| 🌐 翻訳 | 各国語への自然な翻訳（表現の解説つきも可） |
| 📣 SNS投稿作成 | X / Instagram / LinkedIn などに合わせた投稿文 |
| 💡 タイトル・キャッチコピー | タイトル・コピー・件名の案を複数提案 |
| 🗂️ メモ整理・議事録 | 走り書きのメモを議事録・報告書・To-Doに整理 |

共通機能：ストリーミング表示、追加指示で修正、コピー、Markdownダウンロード、セッション内の履歴

## セットアップ

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # .env に GEMINI_API_KEY を記入
```

APIキーは [Google AI Studio](https://aistudio.google.com/apikey) で取得できます。
`.env` を使わず、画面のサイドバーから入力することもできます。

## 起動

`start.bat` をダブルクリックすると、ブラウザでアプリが開きます（黒い画面を閉じると終了）。

コマンドで起動する場合：

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

## ツールの追加方法

`tools.py` に `Tool` を1つ定義して、ファイル末尾の `TOOLS` リストに追加するだけで、
サイドバーと入力フォームが自動で作られます。
