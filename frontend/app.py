import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

# -------------------------------
# Session State
# -------------------------------
st.session_state.setdefault("files_cache", [])
st.session_state.setdefault("last_uploaded_id", None)
st.session_state.setdefault("last_uploaded_filename", None)

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
            st.session_state["files_cache"] = resp.json().get("files", [])
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
# UPLOAD PAGE
# ======================================================
if page == "Upload":
    st.subheader("📤 Upload File")

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file and st.button("Upload"):
        files = {"file": uploaded_file}
        resp = requests.post(f"{BACKEND_URL}/api/upload", files=files)

        if resp.status_code == 200:
            data = resp.json()
            st.session_state["last_uploaded_id"] = data.get("file_id")
            st.session_state["last_uploaded_filename"] = uploaded_file.name
            st.success("File uploaded successfully")
        else:
            st.error("Upload failed")

    # Show summary button after upload
    if st.session_state["last_uploaded_id"]:
        st.markdown("### 📝 Last Uploaded File Summary")

        mode = st.radio(
            "Summary length",
            ["short", "medium", "long"],
            horizontal=True,
        )

        if st.button("Show Summary"):
            resp = requests.get(
                f"{BACKEND_URL}/api/files/{st.session_state['last_uploaded_id']}/summary",
                params={"mode": mode},
            )
            if resp.status_code == 200:
                st.write(resp.json()["summary"])

# ======================================================
# SEARCH PAGE
# ======================================================
elif page == "Search":
    st.subheader("🔍 Search Files")

    query = st.text_input("Enter search word or phrase")

    col1, col2 = st.columns(2)

    # Semantic search
    with col1:
        if st.button("Semantic Search"):
            resp = requests.get(f"{BACKEND_URL}/api/search", params={"query": query})
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for r in results:
                    st.markdown(f"### 📄 {r['filename']}")
                    st.caption(f"Score: {r['score']:.2f}")
                    st.write(r["snippet"])
                    with st.expander("Summary"):
                        st.write(r["summary"])

    # Word-count search
    with col2:
        if st.button("Word Count Search"):
            resp = requests.get(
                f"{BACKEND_URL}/api/search/word",
                params={"word": query},
            )
            if resp.status_code == 200:
                r = resp.json().get("result")
                if r:
                    st.markdown(f"### 🏆 {r['filename']}")
                    st.caption(f"Occurrences: {r['count']}")
                    st.text_area("Full content", r["content"], height=300)

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

                with c1:
                    if st.button("📝 Summary", key=f"s_{f['id']}"):
                        r = requests.get(
                            f"{BACKEND_URL}/api/files/{f['id']}/summary",
                            params={"mode": "medium"},
                        )
                        if r.status_code == 200:
                            st.info(r.json()["summary"])

                with c2:
                    if st.button("🔗 Similar", key=f"sim_{f['id']}"):
                        r = requests.get(
                            f"{BACKEND_URL}/api/files/{f['id']}/similar",
                            params={"top_k": 5},
                        )
                        if r.status_code == 200:
                            for s in r.json().get("similar", []):
                                st.write(f"- {s['filename']} ({s['score']:.2f})")

                with c3:
                    if st.button("🧬 Duplicates", key=f"d_{f['id']}"):
                        r = requests.get(
                            f"{BACKEND_URL}/api/files/{f['id']}/duplicates",
                            params={"threshold": 0.9},
                        )
                        if r.status_code == 200:
                            for d in r.json().get("duplicates", []):
                                st.write(f"- {d['filename']}")

                with c4:
                    if st.button("🗑 Delete", key=f"del_{f['id']}"):
                        requests.delete(f"{BACKEND_URL}/api/files/{f['id']}")
                        st.warning("Deleted. Refresh file list.")
