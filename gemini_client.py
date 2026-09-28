"""Gemini API との通信をまとめたモジュール。"""

from collections.abc import Iterator

import streamlit as st
from google import genai
from google.genai import types


@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def stream_generate(
    api_key: str,
    model: str,
    system_instruction: str,
    prompt: str,
    temperature: float,
) -> Iterator[str]:
    """Gemini の応答をストリーミングでテキストの断片として返す。"""
    client = get_client(api_key)
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
    )
    for chunk in client.models.generate_content_stream(
        model=model, contents=prompt, config=config
    ):
        if chunk.text:
            yield chunk.text
