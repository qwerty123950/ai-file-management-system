import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

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
            st.success("File uploaded successfully!")
        else:
            st.error("Failed to upload file")

# ------------------------
# Search section
# ------------------------
st.header("Search Files")

query = st.text_input("Search query")
if st.button("Search"):
    response = requests.get(f"{BACKEND_URL}/api/search", params={"query": query})
    if response.status_code == 200:
        results = response.json()["results"]
        if not results:
            st.info("No matching files found.")
        for res in results:
            st.subheader(f"{res['filename']}  (Score: {res['score']:.2f})")
            st.caption(f"Summary type: {res.get('summary_type', 'unknown')}")
            st.write(res["summary"])
            st.write("---")
    else:
        st.error("Search failed")

# ------------------------
# All uploaded files + summaries
# ------------------------
st.header("All Uploaded Files & Summaries")

if st.button("Show All Files"):
    response = requests.get(f"{BACKEND_URL}/api/files")
    if response.status_code == 200:
        data = response.json()
        files = data.get("files", [])
        if not files:
            st.info("No files uploaded yet.")
        else:
            for f in files:
                st.subheader(f["filename"])
                st.write(f"**ID:** {f['id']}")
                st.write(f"**Path:** {f['filepath']}")
                st.caption(f"Summary type: {f.get('summary_type', 'unknown')}")
                st.write(f["summary"])
                st.write("---")
    else:
        st.error("Could not fetch uploaded files")
