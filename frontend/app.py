import streamlit as st
import requests
import re

BACKEND_URL = "http://localhost:8000"

# ===============================
# Session State
# ===============================
st.session_state.setdefault("files_cache", [])
st.session_state.setdefault("selected_file_id", None)
st.session_state.setdefault("page", "Files")


# ===============================
# Helpers
# ===============================
def highlight(text, word):
    if not text or not word:
        return text or ""
    return re.sub(
        rf"({re.escape(word)})",
        r"**\1**",
        text,
        flags=re.IGNORECASE,
    )

def get_display_id(file_id):
    for f in st.session_state.files_cache:
        if f.get("id") == file_id:
            return f.get("display_id")
    return "—"

def refresh_files():
    resp = requests.get(f"{BACKEND_URL}/api/files", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        for i, f in enumerate(data, 1):
            f["display_id"] = i
        st.session_state.files_cache = data


# ===============================
# Page Config
# ===============================
st.set_page_config(
    page_title="AI File Management System",
    layout="wide",
)


# ===============================
# Sidebar
# ===============================
with st.sidebar:
    st.markdown("## 📁 Resource Library")

    page = st.radio(
        "Navigation",
        ["Files", "Upload", "Search"],
        index=["Files", "Upload", "Search"].index(st.session_state.page),
    )

    if page != st.session_state.page:
        st.session_state.page = page
        st.session_state.selected_file_id = None
        st.rerun()

    if st.button("🔄 Refresh Files"):
        refresh_files()
        st.success("Files refreshed")


# ===============================
# Header
# ===============================
st.markdown(
    """
    <div style="background:#4b3fa7;padding:16px;border-radius:8px">
        <h2 style="color:white;margin:0;">AI File Management System</h2>
        <p style="color:#ddd;margin:0;">Upload • Search • Summarize</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")


# ======================================================
# UPLOAD PAGE
# ======================================================
if st.session_state.page == "Upload":
    st.header("📤 Upload Files")

    files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=["pdf", "docx", "png", "jpg", "jpeg", "zip"],
    )

    if files:
        if st.button("Upload All", type="primary"):
            total = len(files)
            progress_text = st.empty()
            progress_bar = st.progress(0)

            for i, file in enumerate(files, 1):
                # Live status update
                progress_text.markdown(
                    f"**Uploading {i}/{total}**: {file.name}..."
                )

                with st.spinner(f"Uploading {file.name}"):
                    try:
                        r = requests.post(
                            f"{BACKEND_URL}/api/upload",
                            files={"file": (file.name, file.getvalue(), file.type)},
                            timeout=300,
                        )
                        if r.status_code >= 400:
                            st.error(f"Failed: {file.name} ({r.status_code})")
                    except Exception as e:
                        st.error(f"Error: {file.name} → {str(e)}")

                progress_bar.progress(i / total)

            refresh_files()
            st.success("Upload completed!")
            
            # Small delay so user can see success message
            import time
            time.sleep(1.5)
            st.rerun()
            progress_text.empty()  # clean up status text

# ======================================================
# SEARCH PAGE
# ======================================================
elif st.session_state.page == "Search":
    st.subheader("🔍 Search Files")

    query = st.text_input("Search text")

    if st.button("Semantic Search"):
        r = requests.get(f"{BACKEND_URL}/api/search", params={"query": query})
        if r.status_code == 200:
            for res in r.json():
                st.markdown(f"**{res['filename']}**")
                st.write(highlight(res["snippet"], query))


# ======================================================
# FILES PAGE
# ======================================================
else:
    # ---------------- LIST VIEW ----------------
    if st.session_state.selected_file_id is None:
        st.subheader("📚 All Files")

        files = st.session_state.files_cache

        if not files:
            st.info("No files loaded. Click Refresh Files in sidebar.")
        else:
            total_files = len(files)
            cols = st.columns(4)

            for i, f in enumerate(files):
                with cols[i % 4]:
                    filename = f.get("filename", "Unnamed file")
                    file_id = f.get("id")

                    # NEW: reverse numbering
                    display_id = total_files - i

                    st.markdown(
                        f"""
                        <div style="text-align: center; padding: 8px 0;">
                            <div style="font-size: 48px; line-height: 1;">📄</div>
                            <div style="margin: 8px 0 4px 0; font-weight: 600;">
                                {filename}
                            </div>
                            <div style="color: #666; font-size: 0.9rem; margin-bottom: 10px;">
                                ID: {display_id}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button("Open", key=f"open_{file_id}", use_container_width=True):
                        st.session_state.selected_file_id = file_id
                        st.rerun()

    # ---------------- DETAIL VIEW ----------------
    else:
        file_id = st.session_state.selected_file_id

        if st.button("← Back"):
            st.session_state.selected_file_id = None
            st.rerun()

        st.subheader("📄 File Details")

        mode = st.selectbox("Summary length", ["short", "medium", "long"])

        if st.button("Generate Summary"):
            r = requests.get(
                f"{BACKEND_URL}/api/files/{file_id}/summary",
                params={"mode": mode},
            )
            if r.status_code == 200:
                st.info(r.json())

        if st.checkbox("Show full content"):
            r = requests.get(f"{BACKEND_URL}/api/files/{file_id}/content")
            if r.status_code == 200:
                st.text_area(
                    "Content",
                    r.json().get("content", ""),
                    height=400,
                )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔗 Similar Files"):
                r = requests.get(
                    f"{BACKEND_URL}/api/files/{file_id}/similar",
                    params={"top_k": 5},
                )
                for s in r.json():
                    disp_id = get_display_id(s.get("id"))
                    st.write(
                        f"{s['filename']} | ID: {disp_id} | Score: {s['score']:.3f}"
                    )

        with col2:
            if st.button("🧬 Duplicates"):
                r = requests.get(
                    f"{BACKEND_URL}/api/files/{file_id}/duplicates",
                    params={"threshold": 0.9},
                )
                for d in r.json().get("duplicates", []):
                    disp_id = get_display_id(d.get("id"))
                    st.write(
                        f"{d['filename']} | ID: {disp_id} | Score: {d['score']:.3f}"
                    )

        if st.button("🗑 Delete File", type="primary"):
            r = requests.delete(f"{BACKEND_URL}/api/files/{file_id}")
            if r.status_code in (200, 204):
                refresh_files()
                st.session_state.selected_file_id = None
                st.success("File deleted")
                st.rerun()
