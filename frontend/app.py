import streamlit as st
import requests
import re


BACKEND_URL = "http://localhost:8000"

# -------------------------------
# Session State
# -------------------------------
st.session_state.setdefault("files_cache", [])
st.session_state.setdefault("last_uploaded_id", None)
st.session_state.setdefault("last_uploaded_filename", None)

def highlight(text, word):
    return re.sub(
        rf"({re.escape(word)})",
        r"**\1**",
        text,
        flags=re.IGNORECASE
    )

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="AI File Management System",
    layout="wide",
)

# -------------------------------
# Sidebar (Navigation)
# -------------------------------
with st.sidebar:
    st.markdown("## 📁 Resource Library")
    page = st.radio(
        "Navigation",
        ["Files", "Upload", "Search"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    if st.button("🔄 Refresh Files"):
        resp = requests.get(f"{BACKEND_URL}/api/files")
        if resp.status_code == 200:
            data = resp.json()
            st.session_state["files_cache"] = data if isinstance(data, list) else []
            st.success("File list refreshed")

# -------------------------------
# Top Header
# -------------------------------
st.markdown(
    """
    <div style="background:#4b3fa7;padding:16px;border-radius:8px">
        <h2 style="color:white;margin:0;">AI File Management System</h2>
        <p style="color:#ddd;margin:0;">Upload • Search • Summarize • Compare</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

# ======================================================
# PAGE ROUTER
# ======================================================

if page == "Upload":
    st.header("⬆️ Upload Files or Folder (ZIP)")

    uploaded_files = st.file_uploader(
        "Upload files OR a ZIP folder",
        accept_multiple_files=True,
        type=["pdf", "docx", "png", "jpg", "jpeg", "zip"]
    )

    if uploaded_files and st.button("Upload"):
        success_count = 0

        for uf in uploaded_files:
            files = {"file": (uf.name, uf.getvalue())}
            resp = requests.post(f"{BACKEND_URL}/api/upload", files=files)

            if resp.status_code == 200:
                st.success(f"Uploaded: {uf.name}")
                success_count += 1

                data = resp.json()
                if "file_id" in data and data["file_id"] is not None:
                    st.session_state["last_uploaded_id"] = data["file_id"]
                    st.session_state["last_uploaded_filename"] = uf.name
            else:
                st.error(f"Failed to upload: {uf.name}")

        st.success(f"Uploaded {success_count} file(s) successfully!")

# ======================================================
# SEARCH PAGE
# ======================================================
elif page == "Search":
    st.subheader("🔍 Search Files")

    query = st.text_input("Enter search word or phrase")

    col1, col2 = st.columns(2)

    semantic_clicked = False
    word_clicked = False

    with col1:
        if st.button("Semantic Search"):
            semantic_clicked = True

    with col2:
        if st.button("Word Count Search"):
            word_clicked = True

    # =========================
    # FULL-WIDTH RESULTS BELOW
    # =========================

    if semantic_clicked:
        resp = requests.get(
            f"{BACKEND_URL}/api/search",
            params={"query": query},
        )

        if resp.status_code == 200:
            results = resp.json()

            st.divider()
            st.subheader("🔎 Semantic Search Results")

            for r in results:
                st.markdown(f"### 📄 {r['filename']}")
                st.caption(f"Score: {r['score']:.2f}")
                st.write(highlight(r["snippet"], query))

                with st.expander("Summary"):
                    st.write(highlight(r["summary"], query))

    if word_clicked:
        resp = requests.get(
            f"{BACKEND_URL}/api/search/word",
            params={"word": query},
        )

        if resp.status_code == 200:
            r = resp.json()

            st.divider()
            st.subheader("📊 Word Count Result")

            if r:
                st.markdown(f"### 📄 {r['filename']}")
                st.caption(f"Occurrences: {r['count']}")

                # 🔹 Show a short snippet instead of full content
                content = r.get("content", "")
                snippet = content[:500] + "..." if len(content) > 500 else content
                st.write(snippet)

                with st.expander("Full content"):
                    st.write(content)
            else:
                st.warning("No matches found")


# ======================================================
# FILES PAGE (Resource Library)
# ======================================================
else:
    st.subheader("📚 All Files")

    if not st.session_state["files_cache"]:
        st.info("No files loaded. Click **Refresh Files** in sidebar.")
    else:
        for f in st.session_state["files_cache"]:
            with st.container():
                st.markdown(
                    f"""
                    <div style="border:1px solid #eee;padding:12px;border-radius:8px;margin-bottom:12px">
                        <h4 style="margin:0;">📄 {f['filename']}</h4>
                        <small>ID: {f['id']} | {f.get('summary_type','')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Action buttons
                c1, c2, c3, c4 = st.columns(4)

                mode = st.selectbox(
                    "Summary length",
                    ["short", "medium", "long"],
                    key=f"m_{f['id']}"
                )

                if st.button("📝 Summary", key=f"s_{f['id']}"):
                    r = requests.get(
                        f"{BACKEND_URL}/api/files/{f['id']}/summary",
                        params={"mode": mode},
                    )
                    if r.status_code == 200:
                        st.info(r.json())

                with c2:
                    if st.button("🔗 Similar", key=f"sim_{f['id']}"):
                        r = requests.get(
                            f"{BACKEND_URL}/api/files/{f['id']}/similar",
                            params={"top_k": 5},
                        )
                        if r.status_code == 200:
                            for s in r.json():
                                st.write(f"- File ID {s['id']} ({s['score']:.2f})")

                with c3:
                    if st.button("🧬 Duplicates", key=f"d_{f['id']}"):
                        r = requests.get(
                            f"{BACKEND_URL}/api/files/{f['id']}/duplicates",
                            params={"threshold": 0.9},
                        )
                        if r.status_code == 200:
                            data = r.json()

                            st.subheader("Current file")
                            st.write(f"{data['current_file']['filename']} (ID {data['current_file']['id']})")

                            st.subheader("Duplicates")
                            for d in data.get("duplicates", []):
                                st.write(f"- {d['filename']} (ID {d['id']}, score {d['score']:.2f})")

                with c4:
                    if st.button("🗑 Delete", key=f"del_{f['id']}"):
                        requests.delete(f"{BACKEND_URL}/api/files/{f['id']}")
                        st.warning("Deleted. Refresh file list.")
