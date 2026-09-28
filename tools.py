"""ライティングツールの定義。

新しいツールを追加するときは、Tool を1つ作って TOOLS に追加するだけでよい。
画面（入力フォーム）は fields の定義から自動で組み立てられる。
"""

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Field:
    key: str
    label: str
    kind: str = "text"  # "text" | "textarea" | "select"
    options: list[str] = field(default_factory=list)
    placeholder: str = ""
    required: bool = False
    help: str | None = None
    height: int = 150


@dataclass
class Tool:
    key: str
    name: str
    icon: str
    description: str
    system_prompt: str
    fields: list[Field]
    build_prompt: Callable[[dict], str]
    temperature: float = 0.7


def _optional(label: str, value: str) -> str:
    """値が入力されているときだけプロンプトに1行追加する。"""
    value = (value or "").strip()
    return f"- {label}: {value}\n" if value else ""


# ---------------------------------------------------------------------------
# ブログ記事作成
# ---------------------------------------------------------------------------
def _blog_prompt(v: dict) -> str:
    main_keyword = v["main_keyword"].strip() or "（未指定：テーマから最適な検索キーワードを判断してください）"
    return (
        "以下の条件で、SEOを意識したブログ記事を執筆してください。\n\n"
        f"- テーマ: {v['theme']}\n"
        f"- 上位表示を狙うメインキーワード: {main_keyword}\n"
        + _optional("関連キーワード（共起語）", v["keywords"])
        + _optional("想定読者", v["target"])
        + f"- 文体・トーン: {v['tone']}\n"
        f"- 本文の文字数の目安: {v['length']}\n"
        + _optional("盛り込みたい内容・補足", v["notes"])
    )


BLOG = Tool(
    key="blog",
    name="ブログ記事作成",
    icon="📝",
    description="テーマとキーワードから、SEOを意識した見出し構成つきのブログ記事を作成します。",
    system_prompt="""\
あなたはSEOライティングに精通したプロのブログライター兼編集者です。
Googleの「ユーザーにとって有益で信頼できるコンテンツ」の考え方に沿って、検索上位を狙える記事を書いてください。

# 執筆方針
1. 検索意図を最優先する：メインキーワードで検索する人が「何を知りたいか・何に困っているか」を最初に考え、その答えを記事の前半で明確に示す。
2. タイトル：メインキーワードをできるだけ前半に入れ、32文字前後で、数字・具体性・ベネフィットでクリックしたくなるものにする。
3. 導入文（リード文）：読者の悩みへの共感 → この記事でわかること → 結論の要約、の順で200〜300字程度。
4. 見出し構成：## と ### で論理的に階層化する。主要な ## 見出しにはメインキーワードや関連キーワードを「自然に」含める。
5. 本文：結論を先に書き（PREP法）、具体例・手順・数値・比較を使う。1段落は2〜4文程度で、箇条書きや表も活用して読みやすくする。
6. キーワードは自然な文脈で使い、不自然な詰め込み（キーワードスタッフィング）はしない。関連語・言い換え表現も使って網羅性を高める。
7. 信頼性（E-E-A-T）：事実・数値は断定しすぎず、確認が必要なものは【要確認】と印を付ける。書き手の実体験を入れると良い箇所には【ここに体験談を追記】のようなプレースホルダーを置き、体験談を創作しない。
8. 「## よくある質問」を設け、検索されやすい疑問を Q&A 形式で3つ程度まとめる。
9. 「## まとめ」で要点を箇条書きで振り返り、読者が次に取る行動を1つ提示する。

# 出力形式（Markdown）
最初に次のSEO情報を書き、`---` で区切ってから記事本文を書く。

## SEO情報
- **タイトル案**：3案（それぞれの文字数を併記）
- **メタディスクリプション**：120字前後。メインキーワードを含め、記事を読むメリットが伝わるもの
- **想定する検索意図**：1〜2文
- **URLスラッグ案**：英小文字とハイフン

---

# （タイトル案の1案目）
（本文）
""",
    fields=[
        Field("theme", "テーマ", required=True, placeholder="例：在宅ワークで集中力を保つコツ"),
        Field("main_keyword", "メインキーワード（上位表示を狙う検索語）",
              placeholder="例：在宅ワーク 集中できない",
              help="読者が検索窓に入力しそうな言葉。空欄ならAIがテーマから判断します。"),
        Field("keywords", "関連キーワード（共起語）", placeholder="例：在宅ワーク, 集中力, ポモドーロ"),
        Field("target", "想定読者", placeholder="例：在宅勤務を始めたばかりの会社員"),
        Field("tone", "文体・トーン", kind="select",
              options=["親しみやすい（です・ます調）", "丁寧・フォーマル", "専門的・解説調", "カジュアル（だ・である調）"]),
        Field("length", "文字数の目安", kind="select",
              options=["約1,000字", "約2,000字", "約3,000字", "約5,000字"]),
        Field("notes", "盛り込みたい内容・補足", kind="textarea", height=100,
              placeholder="例：自分の体験談として朝の散歩の話を入れたい"),
    ],
    build_prompt=_blog_prompt,
)


# ---------------------------------------------------------------------------
# メール返信作成
# ---------------------------------------------------------------------------
def _email_prompt(v: dict) -> str:
    return (
        "以下の受信メールへの返信文を作成してください。\n\n"
        f"【受信したメール】\n{v['received']}\n\n"
        f"【返信で伝えたいこと】\n{v['intent']}\n\n"
        "【条件】\n"
        f"- 相手との関係: {v['relation']}\n"
        f"- トーン: {v['tone']}\n"
        + _optional("署名に使う名前", v["sender_name"])
    )


EMAIL = Tool(
    key="email",
    name="メール返信作成",
    icon="✉️",
    description="受け取ったメールと伝えたい内容から、適切な返信文を作成します。",
    system_prompt=(
        "あなたはビジネスコミュニケーションに長けたアシスタントです。"
        "相手との関係性に応じた適切な敬語・言葉遣いで、簡潔で失礼のない返信メールを作成してください。"
        "出力は「件名：」の行から始め、その後に本文を書いてください。"
        "件名は元のメールへの返信であることがわかるように「Re:」を付けてください。"
        "署名の名前が指定されていない場合は【名前】のようなプレースホルダーを使ってください。"
    ),
    fields=[
        Field("received", "受信したメール", kind="textarea", required=True, height=220,
              placeholder="返信したいメールの本文を貼り付けてください"),
        Field("intent", "返信で伝えたいこと", kind="textarea", required=True, height=100,
              placeholder="例：日程は了承。ただし15時以降にしてほしい。資料は明日送る。"),
        Field("relation", "相手との関係", kind="select",
              options=["社外（取引先・顧客）", "社内（上司・目上）", "社内（同僚・部下）", "友人・知人"]),
        Field("tone", "トーン", kind="select", options=["丁寧", "標準", "カジュアル"]),
        Field("sender_name", "署名に使う名前", placeholder="例：山田太郎"),
    ],
    build_prompt=_email_prompt,
    temperature=0.5,
)


# ---------------------------------------------------------------------------
# 文章要約
# ---------------------------------------------------------------------------
def _summary_prompt(v: dict) -> str:
    return (
        "以下の文章を要約してください。\n\n"
        f"- 要約の形式: {v['style']}\n"
        f"- 要約の長さ: {v['length']}\n"
        + _optional("特に注目してほしい観点", v["focus"])
        + f"\n【要約する文章】\n{v['text']}"
    )


SUMMARY = Tool(
    key="summary",
    name="文章要約",
    icon="📋",
    description="長い文章を、指定した形式・長さで要約します。",
    system_prompt=(
        "あなたは優秀な編集者です。元の文章の重要なポイントを漏らさず、"
        "正確かつ簡潔に要約してください。元の文章にない情報を付け加えてはいけません。"
    ),
    fields=[
        Field("text", "要約する文章", kind="textarea", required=True, height=300,
              placeholder="要約したい文章を貼り付けてください"),
        Field("style", "要約の形式", kind="select",
              options=["箇条書き", "文章（段落）", "3行要約", "1行要約（タイトル風）"]),
        Field("length", "要約の長さ", kind="select", options=["標準", "短め", "詳しめ"]),
        Field("focus", "特に注目してほしい観点", placeholder="例：費用に関する部分、決定事項"),
    ],
    build_prompt=_summary_prompt,
    temperature=0.3,
)


# ---------------------------------------------------------------------------
# 文章校正・推敲
# ---------------------------------------------------------------------------
def _proofread_prompt(v: dict) -> str:
    return (
        f"以下の文章を「{v['level']}」のレベルで校正してください。\n\n"
        f"【校正する文章】\n{v['text']}"
    )


PROOFREAD = Tool(
    key="proofread",
    name="文章校正・推敲",
    icon="🔍",
    description="誤字脱字・文法ミスを見つけ、読みやすい文章に整えます。",
    system_prompt=(
        "あなたはプロの校正者です。指定されたレベルで文章を校正してください。\n"
        "出力は次の形式にしてください。\n"
        "## 修正後の文章\n（修正後の全文）\n\n"
        "## 修正点\n| 修正前 | 修正後 | 理由 |\n の表形式で主な修正点を列挙。\n"
        "修正点がない場合はその旨を伝えてください。元の文章の意図や内容は変えないでください。"
    ),
    fields=[
        Field("text", "校正する文章", kind="textarea", required=True, height=300),
        Field("level", "校正レベル", kind="select",
              options=["標準（誤字脱字＋読みやすさの改善）", "誤字脱字・文法ミスのみ", "しっかり推敲（表現や構成も改善）"]),
    ],
    build_prompt=_proofread_prompt,
    temperature=0.3,
)


# ---------------------------------------------------------------------------
# リライト・トーン変換
# ---------------------------------------------------------------------------
def _rewrite_prompt(v: dict) -> str:
    return (
        f"以下の文章を「{v['style']}」という方針でリライトしてください。\n"
        + _optional("追加の指示", v["extra"])
        + f"\n【元の文章】\n{v['text']}"
    )


REWRITE = Tool(
    key="rewrite",
    name="リライト・トーン変換",
    icon="🔄",
    description="文章の意味を保ったまま、文体やトーンを変えて書き直します。",
    system_prompt=(
        "あなたは文章表現のプロです。元の文章の意味・事実関係を保ちながら、"
        "指定された方針で書き直してください。リライト後の文章のみを出力してください。"
    ),
    fields=[
        Field("text", "元の文章", kind="textarea", required=True, height=250),
        Field("style", "リライトの方針", kind="select",
              options=["ビジネス向けの丁寧な敬語に", "やわらかく親しみやすく", "簡潔に短く",
                       "詳しく膨らませる", "小学生にもわかるように", "説得力を高める", "箇条書きに整理"]),
        Field("extra", "追加の指示", placeholder="例：200字以内で、最後に問いかけを入れる"),
    ],
    build_prompt=_rewrite_prompt,
)


# ---------------------------------------------------------------------------
# 翻訳
# ---------------------------------------------------------------------------
def _translate_prompt(v: dict) -> str:
    explain = "\n翻訳の後に「## 表現の解説」として、重要な表現や訳し方のポイントを簡潔に解説してください。" \
        if v["explain"] == "付ける" else "\n翻訳文のみを出力してください。"
    return (
        f"以下の文章を{v['target']}に翻訳してください。スタイルは「{v['style']}」です。"
        + explain
        + f"\n\n【翻訳する文章】\n{v['text']}"
    )


TRANSLATE = Tool(
    key="translate",
    name="翻訳",
    icon="🌐",
    description="文章を自然な表現で他の言語に翻訳します。",
    system_prompt=(
        "あなたはプロの翻訳者です。原文の意味とニュアンスを正確に保ちつつ、"
        "翻訳先の言語のネイティブスピーカーにとって自然な表現で翻訳してください。"
    ),
    fields=[
        Field("text", "翻訳する文章", kind="textarea", required=True, height=250),
        Field("target", "翻訳先の言語", kind="select",
              options=["英語", "日本語", "中国語（簡体字）", "韓国語", "スペイン語", "フランス語", "ドイツ語"]),
        Field("style", "翻訳スタイル", kind="select",
              options=["自然な訳", "ビジネス向け", "カジュアル", "直訳寄り"]),
        Field("explain", "表現の解説", kind="select", options=["付けない", "付ける"]),
    ],
    build_prompt=_translate_prompt,
    temperature=0.3,
)


# ---------------------------------------------------------------------------
# SNS投稿作成
# ---------------------------------------------------------------------------
def _sns_prompt(v: dict) -> str:
    return (
        f"{v['platform']}向けの投稿文を{v['count']}作成してください。\n\n"
        f"- 投稿したい内容: {v['content']}\n"
        f"- トーン: {v['tone']}\n"
        f"- ハッシュタグ: {v['hashtags']}\n"
    )


SNS = Tool(
    key="sns",
    name="SNS投稿作成",
    icon="📣",
    description="伝えたい内容から、各SNSに合った投稿文を作成します。",
    system_prompt=(
        "あなたはSNSマーケティングの専門家です。各プラットフォームの特性"
        "（Xは140字程度で簡潔に、Instagramは共感と改行・絵文字、LinkedInはビジネス寄りなど）"
        "に合わせて、反応が得られやすい投稿文を作成してください。"
        "複数案を作る場合は「### 案1」のように見出しで区切ってください。"
    ),
    fields=[
        Field("content", "投稿したい内容", kind="textarea", required=True, height=150,
              placeholder="例：新しいカフェに行った。ラテアートが可愛くて、店内も静かで作業しやすかった。"),
        Field("platform", "プラットフォーム", kind="select",
              options=["X（旧Twitter）", "Instagram", "Threads", "Facebook", "LinkedIn"]),
        Field("count", "作成数", kind="select", options=["3案", "1案", "5案"]),
        Field("tone", "トーン", kind="select", options=["カジュアル", "丁寧", "熱量高め", "ユーモアあり"]),
        Field("hashtags", "ハッシュタグ", kind="select", options=["付ける", "付けない"]),
    ],
    build_prompt=_sns_prompt,
    temperature=0.9,
)


# ---------------------------------------------------------------------------
# タイトル・キャッチコピー案
# ---------------------------------------------------------------------------
def _headline_prompt(v: dict) -> str:
    return (
        f"以下の内容について「{v['use']}」の案を{v['count']}個考えてください。\n\n"
        f"- 内容・概要: {v['subject']}\n"
        + _optional("ターゲット", v["target"])
    )


HEADLINE = Tool(
    key="headline",
    name="タイトル・キャッチコピー",
    icon="💡",
    description="記事タイトル、キャッチコピー、メール件名などのアイデアを複数提案します。",
    system_prompt=(
        "あなたは一流のコピーライターです。読み手の興味を引き、内容が一目で伝わる案を考えてください。"
        "数字・問いかけ・ベネフィット提示など、さまざまな切り口を混ぜてください。"
        "番号付きリストで出力し、各案の後ろに（ねらい：〜）と一言添えてください。"
    ),
    fields=[
        Field("subject", "内容・概要", kind="textarea", required=True, height=120,
              placeholder="例：初心者向けに、1日10分でできる筋トレメニューを紹介する記事"),
        Field("use", "用途", kind="select",
              options=["ブログ記事タイトル", "商品・サービスのキャッチコピー", "メール件名",
                       "YouTube動画タイトル", "プレゼン・資料タイトル"]),
        Field("count", "案の数", kind="select", options=["10", "5", "20"]),
        Field("target", "ターゲット", placeholder="例：運動が苦手な30代"),
    ],
    build_prompt=_headline_prompt,
    temperature=1.0,
)


# ---------------------------------------------------------------------------
# メモ整理・議事録作成
# ---------------------------------------------------------------------------
def _notes_prompt(v: dict) -> str:
    return (
        f"以下の走り書きのメモを「{v['format']}」の形式に整理してください。\n"
        + _optional("補足", v["extra"])
        + f"\n【メモ】\n{v['notes']}"
    )


NOTES = Tool(
    key="notes",
    name="メモ整理・議事録",
    icon="🗂️",
    description="箇条書きや走り書きのメモを、議事録や報告書などの整った文書にまとめます。",
    system_prompt=(
        "あなたは情報整理が得意なアシスタントです。断片的なメモから内容を読み取り、"
        "Markdown形式で見やすく構造化してください。メモにない事実を創作してはいけません。"
        "不明確な点があれば最後に「## 確認が必要な点」として挙げてください。"
    ),
    fields=[
        Field("notes", "メモ", kind="textarea", required=True, height=300,
              placeholder="例：\n・10/1 定例\n・参加 田中 佐藤 鈴木\n・新機能リリース 来月中旬で\n・テスト 佐藤さん担当"),
        Field("format", "整理の形式", kind="select",
              options=["議事録", "報告書", "To-Doリスト", "見やすく整理したメモ"]),
        Field("extra", "補足", placeholder="例：決定事項と宿題（担当者・期限）を明確に"),
    ],
    build_prompt=_notes_prompt,
    temperature=0.3,
)


TOOLS: list[Tool] = [BLOG, EMAIL, SUMMARY, PROOFREAD, REWRITE, TRANSLATE, SNS, HEADLINE, NOTES]
