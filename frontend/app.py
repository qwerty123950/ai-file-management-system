import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

if "last_uploaded_id" not in st.session_state:
    st.session_state["last_uploaded_id"] = None
if "last_uploaded_filename" not in st.session_state:
    st.session_state["last_uploaded_filename"] = None

st.title("AI File Management System")

# ------------------------
# Upload section
# ------------------------
st.header("Upload a File")

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    if st.button("Upload"):
        files = {"file": uploaded_file}
        response = requests.post(f"{BACKEND_URL}/api/upload", files=files)

        if response.status_code == 200:
            data = response.json()
            file_id = data.get("file_id")

            if file_id is not None:
                # store in session so we can show summary right away
                st.session_state["last_uploaded_id"] = file_id
                st.session_state["last_uploaded_filename"] = uploaded_file.name

            st.success("File uploaded successfully!")
        else:
            st.error("Failed to upload file")

# If we have a last uploaded file, show a button to get its summary
if st.session_state.get("last_uploaded_id"):
    st.markdown("---")
    st.subheader("Summary of last uploaded file")

    st.write(
        f"**File:** {st.session_state['last_uploaded_filename']} "
        f"(ID: {st.session_state['last_uploaded_id']})"
    )

    mode = st.radio(
        "Summary length",
        ["short", "medium", "long"],
        horizontal=True,
        key="last_upload_summary_mode",
    )

    if st.button("Show summary for last uploaded file"):
        resp = requests.get(
            f"{BACKEND_URL}/api/files/{st.session_state['last_uploaded_id']}/summary",
            params={"mode": mode},
        )
        if resp.status_code == 200:
            data = resp.json()
            st.markdown(f"**{mode.capitalize()} summary:**")
            st.write(data["summary"])
        else:
            st.error("Failed to fetch summary for last uploaded file")

# ------------------------
# Search section
# ------------------------
st.header("Search Files")

query = st.text_input("Search query (word or phrase)")

cols = st.columns(2)

# --- Button 1: existing semantic search (Qdrant) ---
with cols[0]:
    if st.button("Semantic search", key="semantic_search"):
        response = requests.get(f"{BACKEND_URL}/api/search", params={"query": query})
        if response.status_code == 200:
            results = response.json().get("results", [])
            if not results:
                st.info("No matching files found (semantic search).")
            for res in results:
                st.subheader(f"{res['filename']}  (Score: {res['score']:.2f})")
                st.caption(f"Stored summary type: {res.get('summary_type', 'unknown')}")

                st.markdown("**Best matching snippet:**")
                st.write(res.get("snippet", ""))

                with st.expander("Stored Summary (default medium)"):
                    st.write(res["summary"])

                st.write("---")
        else:
            st.error("Semantic search failed")

# --- Button 2: new word-count-based search ---
with cols[1]:
    if st.button("Search by word count", key="word_count_search"):
        if not query.strip():
            st.warning("Enter a word to search for.")
        else:
            response = requests.get(
                f"{BACKEND_URL}/api/search/word",
                params={"word": query.strip()},
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get("result")
                if not result:
                    st.info("No file contains that word as a separate word.")
                else:
                    st.subheader(
                        f"File with highest count for '{query.strip()}': "
                        f"{result['filename']} (ID: {result['id']})"
                    )
                    st.caption(
                        f"Occurrences: {result['count']} | "
                        f"Summary type: {result.get('summary_type', 'unknown')}"
                    )
                    if result.get("tags"):
                        st.write(f"**Tags:** {result['tags']}")

                    st.markdown("**Full file content:**")
                    st.text_area(
                        "Content",
                        result.get("content", ""),
                        height=300,
                    )
            else:
                st.error("Word-count search failed")

st.header("Search by Word (show full file with highest count)")

word_query = st.text_input("Word to search in all files", key="word_query")

if st.button("Search word in all files"):
    if not word_query.strip():
        st.warning("Please enter a word to search.")
    else:
        resp = requests.get(f"{BACKEND_URL}/api/search-word", params={"query": word_query})
        if resp.status_code == 200:
            data = resp.json()
            if not data.get("found"):
                st.info(data.get("message", "No file contains that word."))
            else:
                f = data["file"]
                st.subheader(f"Best file: {f['filename']}")
                st.caption(
                    f"ID: {f['id']} | Path: {f['filepath']} | "
                    f"Occurrences of '{word_query}': {f['count']}"
                )

                # Show full content (this is the entire OCR/text content)
                st.markdown("**Full file content (text):**")
                st.text_area(
                    label="",
                    value=f["content"],
                    height=400,
                )
        else:
            st.error("Search failed")

# ------------------------
# All uploaded files + dynamic summaries + relations
# ------------------------
st.header("All Uploaded Files & Summaries")

# Keep cached file list in session_state
if "files_cache" not in st.session_state:
    st.session_state["files_cache"] = []

# Reindex button (unchanged)
if st.button("Reindex all files"):
    resp = requests.post(f"{BACKEND_URL}/api/reindex")
    if resp.status_code == 200:
        data = resp.json()
        st.success(f"Reindexed {data.get('reindexed', 0)} files.")
    else:
        st.error("Reindex failed")

# Tag filter (unchanged)
tag_filter = st.text_input(
    "Filter files by tag (e.g. 'tuberculosis', 'report')",
    key="tag_filter",
)

if st.button("Search by tag"):
    if tag_filter.strip():
        resp = requests.get(
            f"{BACKEND_URL}/api/files/by-tag",
            params={"tag": tag_filter.strip()},
        )
        if resp.status_code == 200:
            data = resp.json()
            files = data.get("files", [])
            if not files:
                st.info("No files matched that tag.")
            else:
                st.success(f"Found {len(files)} file(s) with tag matching '{tag_filter}'.")
                for f in files:
                    st.subheader(f["filename"])
                    st.write(f"**ID:** {f['id']}")
                    st.write(f"**Path:** {f['filepath']}")
                    if f.get("tags"):
                        st.write(f"**Tags:** {f['tags']}")
                    st.caption(f"Stored summary type: {f.get('summary_type', 'unknown')}")
                    with st.expander("Stored Summary (default medium)"):
                        st.write(f["summary"])
                    st.write("---")
        else:
            st.error("Tag search failed")
    else:
        st.warning("Enter a tag to search by.")

# 🔁 REFRESH just updates the cache
if st.button("Refresh File List"):
    response = requests.get(f"{BACKEND_URL}/api/files")
    if response.status_code == 200:
        data = response.json()
        st.session_state["files_cache"] = data.get("files", [])
        st.success("File list refreshed.")
    else:
        st.error("Could not fetch uploaded files")

# ✅ Always use cached files to render buttons
files = st.session_state["files_cache"]

if not files:
    st.info("No files uploaded yet. Click 'Refresh File List' to load files.")
else:
    for f in files:
        st.subheader(f["filename"])
        st.write(f"**ID:** {f['id']}")
        st.write(f"**Path:** {f['filepath']}")
        st.caption(f"Stored summary type: {f.get('summary_type', 'unknown')}")
        if f.get("tags"):
            st.write(f"**Tags:** {f['tags']}")

        # Stored default (medium) summary
        with st.expander("Stored Summary (default medium)"):
            st.write(f["summary"])

        # Dynamic summary modes
        st.markdown("**Generate Custom Summary:**")
        mode = st.radio(
            "Summary length",
            ["short", "medium", "long"],
            horizontal=True,
            key=f"mode_{f['id']}",
        )

        if st.button("Show summary", key=f"show_{f['id']}"):
            resp = requests.get(
                f"{BACKEND_URL}/api/files/{f['id']}/summary",
                params={"mode": mode},
            )
            if resp.status_code == 200:
                dyn = resp.json()
                st.write(f"**{mode.capitalize()} summary:**")
                st.write(dyn["summary"])
            else:
                st.error("Failed to generate summary")

        # Similar documents
        st.markdown("**Related Documents:**")
        cols = st.columns(2)

        with cols[0]:
            if st.button("Show similar files", key=f"sim_{f['id']}"):
                resp = requests.get(
                    f"{BACKEND_URL}/api/files/{f['id']}/similar",
                    params={"top_k": 5},
                )
                if resp.status_code == 200:
                    data_sim = resp.json()
                    sims = data_sim.get("similar", [])
                    if not sims:
                        st.info("No similar files found.")
                    else:
                        for s in sims:
                            st.write(
                                f"- {s['filename']} "
                                f"(Score: {s['score']:.3f}, ID: {s['id']})"
                            )
                else:
                    st.error("Failed to fetch similar files")

        with cols[1]:
            if st.button("Show duplicates", key=f"dup_{f['id']}"):
                resp = requests.get(
                    f"{BACKEND_URL}/api/files/{f['id']}/duplicates",
                    params={"threshold": 0.9},
                )
                if resp.status_code == 200:
                    data_dup = resp.json()
                    dups = data_dup.get("duplicates", [])
                    if not dups:
                        st.info("No duplicates (above threshold) found.")
                    else:
                        st.write("Potential duplicates:")
                        for d in dups:
                            st.write(
                                f"- {d['filename']} "
                                f"(Score: {d['score']:.3f}, ID: {d['id']})"
                            )
                else:
                    st.error("Failed to fetch duplicates")

            # Delete file
            if st.button("Delete file", key=f"del_{f['id']}"):
                resp = requests.delete(f"{BACKEND_URL}/api/files/{f['id']}")
                if resp.status_code == 200:
                    st.success("File deleted. Click 'Refresh File List' to update.")
                else:
                    st.error("Failed to delete file")

        st.write("---")
