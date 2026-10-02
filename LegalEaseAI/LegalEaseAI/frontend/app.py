import re
import sys
from pathlib import Path

import requests
import streamlit as st

# Make project-root modules (config, ai_core) importable when run via `streamlit run frontend/app.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from ai_core.generator import (  # noqa: E402
    format_docx,
    format_html_preview,
    format_pdf,
    sanitize_text,
)

API_URL = config.API_URL

st.set_page_config(page_title="LegalEase", page_icon="⚖️", layout="centered")

ss = st.session_state
for key, default in {
    "document": "", "doc_id": None, "meta": {}, "show_edit": False, "notice": None,
}.items():
    ss.setdefault(key, default)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "document"


def load_into_state(doc_id, text, meta):
    ss.document = sanitize_text(text)
    ss.doc_id = doc_id
    ss.meta = meta
    ss.show_edit = False
    ss.pop("editor", None)  # reset the edit box


# ------------------------------------------------------------------ header
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if Path(config.WEB_LOGO_PATH).exists():
        st.image(str(config.WEB_LOGO_PATH), width="stretch")
    else:
        st.markdown("<h1 style='text-align:center'>⚖️ LegalEase</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>AI Legal Document Generator</h2>", unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar: history (database)
with st.sidebar:
    st.subheader("📚 Document history")
    try:
        items = requests.get(f"{API_URL}/history", timeout=5).json().get("items", [])
        if not items:
            st.caption("No documents yet.")
        for it in items:
            if st.button(f"#{it['id']} · {it['document_type'][:28]}", key=f"h{it['id']}"):
                full = requests.get(f"{API_URL}/history/{it['id']}", timeout=10).json()
                load_into_state(full["id"], full["content"],
                                {"document_type": full["document_type"], "terms": full["terms"]})
                st.rerun()
    except requests.RequestException:
        st.caption("Backend offline - start it to see history.")

# ------------------------------------------------------------------ input form
document_type = st.text_input("Document Type (Ex: Agreement, Contract, NDA)")
parties = st.text_area("Parties Involved")
terms = st.text_area("Terms & Conditions (Use semicolons for bullet points)")
dates = st.text_input("Effective Date")

if st.button("Generate Document", type="primary"):
    if not all(v.strip() for v in (document_type, parties, terms, dates)):
        st.warning("Please fill in all four fields.")
    else:
        try:
            with st.spinner("Drafting your document with Gemini..."):
                resp = requests.post(
                    f"{API_URL}/generate",
                    json={"document_type": document_type, "parties": parties,
                          "terms": terms, "dates": dates},
                    timeout=180,
                )
            if resp.ok:
                data = resp.json()
                load_into_state(data["id"], data["document"],
                                {"document_type": document_type, "terms": terms})
                ss.notice = "✅ Document Generated Successfully!"
            else:
                detail = resp.json().get("detail", resp.text) if resp.headers.get(
                    "content-type", "").startswith("application/json") else resp.text
                st.error(f"Backend error ({resp.status_code}): {detail}")
        except requests.ConnectionError:
            st.error(f"Cannot reach the backend at {API_URL}. Start it with: "
                     "uvicorn legalEaseAPI.main:app --reload")
        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")

# ------------------------------------------------------------------ preview / edit / download
if not ss.document:
    st.info("Click 'Generate Document' to start")
else:
    if ss.notice:
        st.success(ss.notice)
        ss.notice = None

    st.markdown(
        "<div style='background:#111827;color:#e5e7eb;padding:18px 22px;border-radius:10px;"
        "max-height:420px;overflow-y:auto;border:1px solid #1f2937'>"
        f"{format_html_preview(ss.document)}</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    if st.button("✏️ Click to Edit Document"):
        ss.show_edit = not ss.show_edit

    if ss.show_edit:
        edited = st.text_area("Edit Document Below:", value=ss.document, height=350, key="editor")
        ss.document = edited
        if ss.doc_id and st.button("💾 Save edits to history"):
            r = requests.put(f"{API_URL}/history/{ss.doc_id}", json={"content": edited}, timeout=10)
            st.success("Saved.") if r.ok else st.error("Could not save edits.")

    doc_type = ss.meta.get("document_type", "Legal Document")
    doc_terms = ss.meta.get("terms", "")
    base = slug(doc_type)
    text = sanitize_text(ss.document)

    st.download_button("📄 Download as .TXT", data=text, file_name=f"{base}.txt", mime="text/plain")
    st.download_button(
        "📝 Download as .DOCX", data=format_docx(text, doc_type, doc_terms), file_name=f"{base}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    st.download_button(
        "📕 Download as .PDF", data=format_pdf(text, doc_type, doc_terms), file_name=f"{base}.pdf",
        mime="application/pdf",
    )
    st.caption("AI-generated drafts are not legal advice. Have a qualified lawyer review before signing.")
