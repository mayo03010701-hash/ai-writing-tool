"""動作確認用のスモークテスト（Gemini APIは呼ばずにダミー応答を使う）。

使い方:
    .venv\\Scripts\\python.exe tests\\smoke_test.py           # 全ツール + 履歴
    .venv\\Scripts\\python.exe tests\\smoke_test.py blog      # 指定したツールだけ（tool.key）
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")  # Windows のコンソールで日本語が文字化けしないように
os.environ["GEMINI_API_KEY"] = "dummy"  # .env の値より優先させる（load_dotenv は上書きしない）

import gemini_client  # noqa: E402

CALLS: list[dict] = []


def fake_stream_generate(api_key, model, system_instruction, prompt, temperature):
    CALLS.append({"model": model, "system": system_instruction, "prompt": prompt, "temperature": temperature})
    yield "# テスト結果\n"
    yield "ダミーの本文です。"


gemini_client.stream_generate = fake_stream_generate

from streamlit.testing.v1 import AppTest  # noqa: E402

from tools import TOOLS  # noqa: E402

APP = os.path.join(ROOT, "app.py")


def new_app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def check_tool(tool) -> AppTest:
    at = new_app()
    at.sidebar.radio[0].set_value(f"{tool.icon} {tool.name}").run()
    assert not at.exception, at.exception

    # 必須項目が未入力なら警告が出て、APIは呼ばれない
    before = len(CALLS)
    at.button[0].click().run()
    if any(f.required for f in tool.fields):
        assert any("必須項目" in w.value for w in at.warning), "必須項目の警告が出ていない"
        assert len(CALLS) == before, "未入力なのにAPIが呼ばれた"

    # 必須項目を埋めて生成
    for f in tool.fields:
        if f.required:
            widget = at.text_area if f.kind == "textarea" else at.text_input
            widget(key=f"{tool.key}__{f.key}").set_value("テスト入力")
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert at.session_state.results[tool.key].startswith("# テスト結果"), "結果が保存されていない"
    assert "テスト入力" in CALLS[-1]["prompt"], "入力がプロンプトに入っていない"
    assert CALLS[-1]["temperature"] == tool.temperature
    return at


def check_refine_and_history(at: AppTest) -> None:
    at.text_input[-1].set_value("短く").run()
    at.button[-1].click().run()
    assert not at.exception, at.exception
    assert "短く" in CALLS[-1]["prompt"]
    assert len(at.session_state.history) == 2

    at.sidebar.radio[0].set_value("🕘 履歴").run()
    assert not at.exception, at.exception
    assert len(at.main.expander) == 2


def main() -> int:
    targets = sys.argv[1:]
    tools = [t for t in TOOLS if not targets or t.key in targets]
    unknown = set(targets) - {t.key for t in TOOLS}
    if unknown:
        print(f"不明なツール: {', '.join(unknown)}（使えるキー: {', '.join(t.key for t in TOOLS)}）")
        return 1

    failed = 0
    at = None
    for tool in tools:
        try:
            at = check_tool(tool)
            print(f"OK   {tool.key}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {tool.key}: {e}")

    if at is not None and not targets:
        try:
            check_refine_and_history(at)
            print("OK   refine + history")
        except AssertionError as e:
            failed += 1
            print(f"FAIL refine + history: {e}")

    print("すべて成功" if not failed else f"{failed}件失敗")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
