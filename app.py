from __future__ import annotations

import streamlit as st
from html import escape

from agent import ask_agent
from common import load_settings
from ingestion import index_uploaded_pdfs


st.set_page_config(
    page_title="Telco Support Copilot",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    :root { --ink:#edf4ff; --muted:#9aa9c2; --teal:#5eead4; --mint:#b6f09c; --panel:rgba(18,29,49,.82); }
    html, body, [class*="css"] { font-family:'DM Sans','Noto Sans KR',sans-serif; }
    .stApp { color:var(--ink); background:radial-gradient(ellipse at 12% 0%,#123348 0%,transparent 36%),radial-gradient(ellipse at 88% 8%,#28204b 0%,transparent 34%),linear-gradient(145deg,#07111f 0%,#0b1424 54%,#101528 100%); }
    [data-testid="stHeader"] { background:transparent; }
    .block-container { max-width:1240px; padding-top:2.1rem; padding-bottom:5rem; }
    h1,h2,h3,p { color:var(--ink); }
    .eyebrow { color:var(--teal); font-size:.76rem; font-weight:700; letter-spacing:.17em; text-transform:uppercase; margin:0 0 .55rem; }
    .hero-title { font-size:2.35rem; font-weight:700; letter-spacing:-.045em; margin:0; line-height:1.12; }
    .hero-copy { color:var(--muted); margin:.65rem 0 1.35rem; font-size:1rem; }
    .panel-title { font-size:1.05rem; font-weight:700; margin:0 0 .3rem; }
    .panel-copy { color:var(--muted); font-size:.88rem; margin:0 0 1rem; }
    [data-testid="stVerticalBlockBorderWrapper"] { background:var(--panel); border:1px solid rgba(154,180,220,.15); border-radius:20px; box-shadow:0 18px 55px rgba(0,0,0,.22); }
    [data-testid="stFileUploaderDropzone"] { background:rgba(94,234,212,.045); border:1px dashed rgba(94,234,212,.4); border-radius:14px; }
    [data-testid="stFileUploaderDropzone"] p, [data-testid="stFileUploaderDropzone"] span { color:#dce9f6; }
    [data-testid="stFileUploaderDropzone"] button { border-radius:9px; }
    .stButton > button { min-height:2.8rem; border:0; border-radius:11px; color:#06201e; font-weight:700; background:linear-gradient(100deg,#5eead4,#b6f09c); box-shadow:0 8px 22px rgba(94,234,212,.15); transition:transform .15s ease,filter .15s ease; }
    .stButton > button:hover { filter:brightness(1.06); transform:translateY(-1px); color:#06201e; border:0; }
    .stButton > button:disabled { color:#6d7c8d; background:#263449; box-shadow:none; }
    [data-testid="stChatMessage"] { background:rgba(17,28,47,.68); border:1px solid rgba(154,180,220,.1); border-radius:16px; padding:1rem 1.2rem; }
    [data-testid="stChatInput"] { background:rgba(15,25,43,.95); border:1px solid rgba(94,234,212,.22); border-radius:16px; }
    [data-testid="stChatInput"] textarea { color:var(--ink); }
    [data-testid="stAlert"] { border-radius:13px; }
    .status-pill { display:inline-flex; align-items:center; gap:.48rem; padding:.42rem .72rem; border:1px solid rgba(94,234,212,.22); border-radius:999px; color:#a9f4e9; background:rgba(94,234,212,.07); font-size:.79rem; font-weight:600; }
    .status-dot { width:7px; height:7px; border-radius:50%; background:#6df0b0; box-shadow:0 0 10px #6df0b0; }
    .mini-label { color:var(--muted); font-size:.74rem; letter-spacing:.08em; text-transform:uppercase; }
    .mini-value { color:#f1f6ff; font-size:1.02rem; font-weight:700; margin-top:.35rem; }
    .doc-chip { display:inline-block; max-width:100%; overflow-wrap:anywhere; margin:.2rem .35rem .2rem 0; padding:.32rem .62rem; border-radius:8px; background:rgba(147,164,190,.1); color:#d8e4f3; font-size:.8rem; }
    hr { border-color:rgba(154,180,220,.12); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">AI-powered customer operations</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Telco Support Copilot</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-copy">통신 정책 문서를 읽고, 출처와 함께 상담 답변 초안을 만듭니다.</p>',
    unsafe_allow_html=True,
)

upload_col, overview_col = st.columns([1.08, 1.52], gap="large", vertical_alignment="top")
with upload_col:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">01 / Knowledge base</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">상담 문서 업로드</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-copy">PDF를 추가해 상담에 사용할 지식 베이스를 만드세요.</div>', unsafe_allow_html=True)
        uploads = st.file_uploader(
            "PDF 파일 선택",
            type=["pdf"],
            accept_multiple_files=True,
            help="로밍, 요금제, 환불, 유심 안내 PDF를 여러 개 선택할 수 있습니다.",
        )
        if st.button("문서 분석 시작", type="primary", use_container_width=True, disabled=not uploads):
            try:
                load_settings()
                files = [(file.name, file.getvalue()) for file in uploads]
                with st.spinner("문서를 읽고 검색용 지식 베이스를 준비하는 중..."):
                    namespace, pages, chunks, index_name, reused = index_uploaded_pdfs(files)
                st.session_state.namespace = namespace
                st.session_state.corpus_names = [file.name for file in uploads]
                st.session_state.messages = []
                st.session_state.index_name = index_name
                if reused:
                    st.success(
                        f"기존 지식 베이스를 재사용했어요 · {chunks}개 조각 · "
                        f"재임베딩 없음 · Pinecone: {index_name}"
                    )
                else:
                    st.success(
                        f"완료 · {len(uploads)}개 PDF · {pages}페이지 · {chunks}개 검색 조각 · "
                        f"Pinecone: {index_name}"
                    )
            except Exception as exc:
                st.error(f"문서 처리에 실패했습니다: {exc}")

with overview_col:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">Your workspace</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">문서 기반 상담, 한 곳에서</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-copy">업로드한 자료를 바탕으로 에이전트가 관련 내용을 찾아 답변을 작성합니다. 답변에는 문서 출처가 포함됩니다.</div>',
            unsafe_allow_html=True,
        )
        stat1, stat2, stat3 = st.columns(3)
        with stat1:
            st.markdown('<div class="mini-label">Retrieval</div><div class="mini-value">Semantic search</div>', unsafe_allow_html=True)
        with stat2:
            st.markdown('<div class="mini-label">Grounding</div><div class="mini-value">Page citations</div>', unsafe_allow_html=True)
        with stat3:
            st.markdown('<div class="mini-label">Workflow</div><div class="mini-value">Human review</div>', unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.session_state.get("namespace"):
            st.markdown('<span class="status-pill"><span class="status-dot"></span> 지식 베이스 준비 완료</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-pill"><span class="status-dot"></span> PDF 업로드를 기다리는 중</span>', unsafe_allow_html=True)

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
with st.container(border=True):
    chat_header_col, chat_status_col = st.columns([1.4, 1], vertical_alignment="center")
    with chat_header_col:
        st.markdown('<div class="eyebrow">02 / Advisor workspace</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">상담 어시스턴트</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-copy">문서에 근거한 답변 초안을 확인하세요.</div>', unsafe_allow_html=True)
    with chat_status_col:
        if st.session_state.get("namespace"):
            names = st.session_state.get("corpus_names", [])
            st.markdown('<span class="status-pill"><span class="status-dot"></span> 준비 완료</span>', unsafe_allow_html=True)
            if names:
                st.markdown(
                    "".join(f'<span class="doc-chip">{escape(name)}</span>' for name in names),
                    unsafe_allow_html=True,
                )
        else:
            st.caption("PDF를 먼저 업로드하고 문서 분석을 시작하세요.")

    if st.session_state.get("namespace"):
        for message in st.session_state.get("messages", []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        question = st.chat_input("예: 바로 로밍 데이터를 모두 사용하면 어떻게 되나요?")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("문서에서 근거를 찾는 중..."):
                    try:
                        answer = ask_agent(question, st.session_state.namespace)
                    except Exception as exc:
                        answer = f"요청을 처리하지 못했습니다: {exc}"
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.info("왼쪽 위에서 PDF를 업로드한 뒤 ‘문서 분석 시작’을 눌러주세요.")
