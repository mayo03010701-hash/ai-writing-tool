"""AIライティングツール（Streamlit + Gemini API）"""

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from gemini_client import stream_generate
from tools import TOOLS, Field, Tool

load_dotenv()

DEFAULT_MODELS = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]
CUSTOM_MODEL = "その他（手入力）"
HISTORY_PAGE = "🕘 履歴"

st.set_page_config(page_title="AIライティングツール", page_icon="✍️", layout="wide")

if "results" not in st.session_state:
    st.session_state.results = {}  # tool.key -> 最新の生成結果
if "history" not in st.session_state:
    st.session_state.history = []  # 生成履歴（新しい順）


# ---------------------------------------------------------------------------
# サイドバー
# ---------------------------------------------------------------------------
def render_sidebar() -> tuple[str, dict]:
    with st.sidebar:
        st.title("✍️ AIライティング")

        pages = [f"{t.icon} {t.name}" for t in TOOLS] + [HISTORY_PAGE]
        page = st.radio("ツールを選択", pages, label_visibility="collapsed")

        st.divider()
        with st.expander("⚙️ 設定", expanded=not os.getenv("GEMINI_API_KEY")):
            api_key = os.getenv("GEMINI_API_KEY", "")
            if api_key:
                st.caption("✅ APIキーは .env から読み込み済みです")
            else:
                api_key = st.text_input(
                    "Gemini APIキー",
                    type="password",
                    help="Google AI Studio で取得できます。.env に GEMINI_API_KEY を書いておくと入力不要になります。",
                )

            env_model = os.getenv("GEMINI_MODEL")
            models = ([env_model] if env_model and env_model not in DEFAULT_MODELS else []) + DEFAULT_MODELS
            model = st.selectbox("モデル", models + [CUSTOM_MODEL],
                                 index=models.index(env_model) if env_model in models else 0)
            if model == CUSTOM_MODEL:
                model = st.text_input("モデル名", placeholder="例：gemini-3.8-flash")

            temp_override = st.checkbox("創造性（temperature）を手動で指定する")
            temperature = st.slider("temperature", 0.0, 2.0, 0.7, 0.1, disabled=not temp_override,
                                    help="低いほど正確で安定、高いほど自由で多様な文章になります。")

    settings = {
        "api_key": api_key.strip(),
        "model": (model or "").strip(),
        "temperature": temperature if temp_override else None,
    }
    return page, settings


# ---------------------------------------------------------------------------
# 生成処理
# ---------------------------------------------------------------------------
def generate(tool: Tool, prompt: str, settings: dict) -> str | None:
    """Gemini で生成し、ストリーミング表示した結果を返す。失敗時は None。"""
    if not settings["api_key"]:
        st.error("サイドバーの「設定」で Gemini APIキーを入力してください。")
        return None
    if not settings["model"]:
        st.error("モデル名を入力してください。")
        return None

    temperature = settings["temperature"] if settings["temperature"] is not None else tool.temperature
    try:
        with st.container(border=True):
            with st.spinner("生成中..."):
                stream = stream_generate(settings["api_key"], settings["model"],
                                         tool.system_prompt, prompt, temperature)
                result = st.write_stream(stream)
    except Exception as e:  # APIキー誤り・レート制限・ネットワークエラーなど
        st.error(f"生成に失敗しました：{e}")
        return None

    if not isinstance(result, str) or not result.strip():
        st.warning("応答が空でした。入力内容を変えて再度お試しください。")
        return None
    return result


def save_result(tool: Tool, summary: str, result: str) -> None:
    st.session_state.results[tool.key] = result
    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tool": f"{tool.icon} {tool.name}",
        "input": summary,
        "output": result,
    })


# ---------------------------------------------------------------------------
# ツール画面
# ---------------------------------------------------------------------------
def render_field(tool: Tool, f: Field):
    key = f"{tool.key}__{f.key}"
    label = f"{f.label} *" if f.required else f.label
    if f.kind == "textarea":
        return st.text_area(label, key=key, placeholder=f.placeholder, help=f.help, height=f.height)
    if f.kind == "select":
        return st.selectbox(label, f.options, key=key, help=f.help)
    return st.text_input(label, key=key, placeholder=f.placeholder, help=f.help)


def render_tool(tool: Tool, settings: dict) -> None:
    st.header(f"{tool.icon} {tool.name}")
    st.caption(tool.description)

    with st.form(f"form_{tool.key}"):
        values = {f.key: render_field(tool, f) for f in tool.fields}
        submitted = st.form_submit_button("✨ 生成する", type="primary", use_container_width=True)

    if submitted:
        missing = [f.label for f in tool.fields if f.required and not str(values[f.key]).strip()]
        if missing:
            st.warning(f"必須項目を入力してください：{'、'.join(missing)}")
        else:
            result = generate(tool, tool.build_prompt(values), settings)
            if result:
                first = next(str(values[f.key]) for f in tool.fields if f.required)
                save_result(tool, first[:80], result)
                st.rerun()

    result = st.session_state.results.get(tool.key)
    if result:
        render_result(tool, result, settings)


def render_result(tool: Tool, result: str, settings: dict) -> None:
    st.subheader("生成結果")
    preview, raw = st.tabs(["プレビュー", "テキスト（コピー用）"])
    with preview:
        with st.container(border=True):
            st.markdown(result)
    with raw:
        st.code(result, language=None, wrap_lines=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    col1.caption(f"文字数：{len(result):,}字")
    col2.download_button("💾 ダウンロード", result, file_name=f"{tool.key}_{datetime.now():%Y%m%d_%H%M%S}.md",
                         mime="text/markdown", use_container_width=True)
    if col3.button("🗑️ クリア", key=f"clear_{tool.key}", use_container_width=True):
        del st.session_state.results[tool.key]
        st.rerun()

    # 生成結果への追加指示（ブラッシュアップ）
    with st.form(f"refine_{tool.key}", clear_on_submit=True):
        instruction = st.text_input("🔧 追加指示で修正する",
                                    placeholder="例：もう少し短く / もっとくだけた感じに / 結論を先に")
        refine = st.form_submit_button("修正する")

    if refine and instruction.strip():
        prompt = (
            "以下は先ほどあなたが作成した文章です。次の指示に従って修正し、修正後の文章全体を出力してください。\n\n"
            f"【指示】\n{instruction}\n\n【文章】\n{result}"
        )
        new_result = generate(tool, prompt, settings)
        if new_result:
            save_result(tool, f"（修正）{instruction[:70]}", new_result)
            st.rerun()


# ---------------------------------------------------------------------------
# 履歴画面
# ---------------------------------------------------------------------------
def render_history() -> None:
    st.header(HISTORY_PAGE)
    st.caption("このセッション中に生成した文章の履歴です（ブラウザを閉じる・再読み込みすると消えます）。")

    history = st.session_state.history
    if not history:
        st.info("まだ履歴がありません。")
        return

    all_md = "\n\n---\n\n".join(f"## {h['tool']}（{h['time']}）\n\n{h['output']}" for h in history)
    col1, col2 = st.columns(2)
    col1.download_button("💾 すべてダウンロード", all_md, file_name="history.md",
                         mime="text/markdown", use_container_width=True)
    if col2.button("🗑️ 履歴を削除", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    for h in history:
        with st.expander(f"{h['time']}　{h['tool']}　—　{h['input']}"):
            st.markdown(h["output"])


# ---------------------------------------------------------------------------
page, settings = render_sidebar()
if page == HISTORY_PAGE:
    render_history()
else:
    render_tool(next(t for t in TOOLS if f"{t.icon} {t.name}" == page), settings)
