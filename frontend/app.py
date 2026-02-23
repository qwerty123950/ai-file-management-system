#frontend/apps.py

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
st.session_state.setdefault("search_type", "Semantic Search")
st.session_state.setdefault("search_query", "")
st.session_state.setdefault("search_results", None)


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
        ["Files", "Upload", "Search", "Merge", "Chatbot"],
        index=["Files", "Upload", "Search", "Merge","Chatbot"].index(st.session_state.page),
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

    query = st.text_input("Enter search text").strip()

    search_type = st.radio(
        "Search type",
        ["Semantic Search", "Word Count Search", "Tag Search"],
        horizontal=True,
    )

    if st.button("Search"):
        st.session_state.search_query = query
        st.session_state.search_type = search_type

        if search_type == "Semantic Search":
            r = requests.get(
                f"{BACKEND_URL}/api/search",
                params={"query": query},
            )
            st.session_state.search_results = r.json() if r.status_code == 200 else []

        elif search_type == "Word Count Search":
            r = requests.get(
                f"{BACKEND_URL}/api/search/word",
                params={"word": query},
            )
            st.session_state.search_results = r.json() if r.status_code == 200 else None

        elif search_type == "Tag Search":
            r = requests.get(f"{BACKEND_URL}/api/files/tag/{query}")
            st.session_state.search_results = r.json() if r.status_code == 200 else []

    # ----------------------------------
    # SEMANTIC SEARCH RESULTS
    # ----------------------------------
    if st.session_state.search_type == "Semantic Search":
        results = st.session_state.search_results

        if not results:
            st.info("No semantic matches found.")
        else:
            st.divider()
            st.subheader("🔎 Semantic Results")

            for idx, res in enumerate(results):
                filename = res.get("filename", "Unknown file")
                score = res.get("score", 0.0)
                summary = res.get("summary", "")
                file_id = res.get("id")

                st.markdown(f"### 📄 {filename}")
                st.caption(f"Relevance score: **{score:.3f}**")

                if summary:
                    st.write(summary)

                show_full = st.checkbox(
                    "Show full content",
                    key=f"semantic_full_{file_id}",
                )

                if show_full and file_id is not None:
                    content_resp = requests.get(
                        f"{BACKEND_URL}/api/files/{file_id}/content"
                    )
                    if content_resp.status_code == 200:
                        st.text_area(
                            "Full content",
                            content_resp.json().get("content", ""),
                            height=300,
                            key=f"semantic_content_{file_id}",
                        )

                st.divider()

    # ----------------------------------
    # WORD COUNT SEARCH RESULTS
    # ----------------------------------
    if st.session_state.search_type == "Word Count Search":
        data = st.session_state.search_results

        # Word-count API returns a DICT, not a list
        if not isinstance(data, dict) or not data.get("filename"):
            st.info("No word count matches found.")
        else:
            st.divider()
            st.subheader("📊 Word Count Result")

            st.markdown(f"### 📄 {data['filename']}")
            st.caption(f"Occurrences: **{data.get('count', 0)}**")

            highlighted = highlight(data.get("content", ""), query)
            st.markdown(highlighted, unsafe_allow_html=True)

    # ----------------------------------
    # TAG SEARCH RESULTS
    # ----------------------------------
    if st.session_state.search_type == "Tag Search":
        results = st.session_state.search_results

        if not results:
            st.info("No files found with that tag.")
        else:
            st.divider()
            st.subheader("🏷️ Tag Search Results")

            for res in results:
                filename = res.get("filename", "Unknown file")
                tags = res.get("tags", "")
                file_id = res.get("id")

                st.markdown(f"### 📄 {filename}")
                if tags:
                    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
                    st.markdown("**Tags:** " + ", ".join([f"`{t}`" for t in tags_list]))

                if st.button("Open File", key=f"tag_open_{file_id}"):
                    st.session_state.selected_file_id = file_id
                    st.session_state.page = "Files"
                    st.rerun()

                st.divider()

# ======================================================
# FILES PAGE
# ======================================================
elif st.session_state.page == "Files":
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

        file_info = next((f for f in st.session_state.files_cache if f.get("id") == file_id), None)
        if file_info and file_info.get("tags"):
            tags_list = [t.strip() for t in file_info.get("tags").split(",") if t.strip()]
            if tags_list:
                st.markdown("**Tags:** " + " ".join([f"`{t}`" for t in tags_list]))
        st.write("")

        mode = st.selectbox("Summary length", ["short", "medium", "long"])

        if st.button("Generate Summary"):
            r = requests.get(
                f"{BACKEND_URL}/api/files/{file_id}/summary",
                params={"mode": mode},
            )
            if r.status_code == 200:
                data = r.json()
                summary_text = data.get("summary", "No summary available.")
                st.info(summary_text)
            else:
                st.error("Failed to fetch summary")

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

# ======================================================
# MERGE PAGE
# ======================================================
elif st.session_state.page == "Merge":
    st.subheader("🧩 Merge Files")

    files = st.session_state.files_cache

    if not files:
        st.info("No files available to merge.")
    else:
        # Map display names → IDs
        file_map = {
            f"{f.get('filename', 'Unnamed')} (ID {f.get('display_id')})": f["id"]
            for f in files
        }

        selected_labels = st.multiselect(
            "Select files to merge (order matters)",
            options=list(file_map.keys()),
        )
        merged_filename = st.text_input(
            "Merged file name (without extension)", 
            placeholder="merged_document",
            value="merged_file"
            )
        
        output_format = st.selectbox(
            "Output format",
            [".txt", ".docx", ".pdf"]
        )

        download_after_merge = st.checkbox("Download merged file to my system")

        if st.button("Merge Files", type="primary"):
            if len(selected_labels) < 2:
                st.warning("Select at least two files.")
            elif not merged_filename.strip():
                st.warning("Please enter a file name.")
            else:
                payload = {
                    "file_ids": [file_map[l] for l in selected_labels],
                    "filename": merged_filename,
                    "format": output_format,
                    "download": download_after_merge
                }

                with st.spinner("Merging files..."):
                    r = requests.post(
                        f"{BACKEND_URL}/api/files/merge",
                        json=payload,timeout=30,stream=True,
                    )

                if r.status_code == 200:
                    if download_after_merge:
                        st.download_button(
                            label="⬇ Download merged file",
                            data=r.content,          # ✅ RAW BYTES
                            file_name=f"{merged_filename}{output_format}",
                            mime={
                                ".txt": "text/plain",
                                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                ".pdf": "application/pdf",
                            }[output_format],
                        )
                    else:
                        st.success("Merged file saved successfully")
                else:
                    st.error("Merge failed")

# ======================================================
# CHATBOT PAGE
# ======================================================
elif st.session_state.page == "Chatbot":
    st.subheader("🤖 Groq Document Chatbot")

    files = st.session_state.files_cache

    source = st.radio(
        "Select input source",
        ["From existing files", "Upload local file"],
        horizontal=True,
    )

    content = ""

    # -------------------------------
    # From DB files
    # -------------------------------
    if source == "From existing files":
        options = {
            f"{f['filename']} (ID {f['display_id']})": f["id"]
            for f in files
        }

        selected = st.multiselect(
            "Select files (order matters)",
            options=list(options.keys()),
        )

        if selected:
            contents = []
            for label in selected:
                fid = options[label]
                r = requests.get(f"{BACKEND_URL}/api/files/{fid}/content")
                if r.status_code == 200:
                    contents.append(r.json().get("content", ""))
            content = "\n\n".join(contents)

    # -------------------------------
    # Local upload
    # -------------------------------
    else:
        uploaded = st.file_uploader(
            "Upload a document",
            type=["txt", "pdf", "docx"],
        )
        if uploaded:
            content = uploaded.read().decode("utf-8", errors="ignore")

    # -------------------------------
    # Chat
    # -------------------------------
    if content.strip():
        st.success(f"Loaded document ({len(content.split())} words)")

        instruction = st.text_area(
            "What do you want to do with this document?",
            placeholder="e.g. Shorten to 500 words focusing on Apache Pig",
            height=120,
        )

        if st.button("Ask Groq", type="primary"):
            with st.spinner("Groq is thinking..."):
                r = requests.post(
                    f"{BACKEND_URL}/api/chat",
                    json={
                        "content": content,
                        "instruction": instruction,
                    },
                    timeout=180,
                )

            if r.status_code == 200:
                result = r.json().get("result", "").strip()
                st.session_state.chat_final = result  # 🔒 LOCK OUTPUT
            else:
                st.error("Chat failed")
                st.stop()

    # -------------------------------
    # Result + Download
    # -------------------------------
    if st.session_state.get("chat_final"):
        st.divider()
        st.subheader("🧾 Result")

        st.text_area(
            "Generated content",
            st.session_state.chat_final,
            height=400,
        )

        format = st.selectbox(
            "Download format",
            [".txt", ".docx", ".pdf"],
        )

        if st.button("⬇ Download result"):
            with st.spinner("Preparing download..."):
                r = requests.post(
                    f"{BACKEND_URL}/api/chat/convert",
                    json={
                        "content": st.session_state.chat_final,
                        "format": format,
                    },
                    timeout=120,
                )

            if r.status_code == 200:
                st.download_button(
                    label="Click to download",
                    data=r.content,  # ✅ RAW BYTES (IMPORTANT)
                    file_name=f"chat_result{format}",
                    mime={
                        ".txt": "text/plain",
                        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        ".pdf": "application/pdf",
                    }[format],
                )
            else:
                st.error("Failed to generate download")
