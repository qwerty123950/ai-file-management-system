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
            st.caption(f"Stored summary type: {res.get('summary_type', 'unknown')}")

            st.markdown("**Best matching snippet:**")
            st.write(res.get("snippet", ""))

            with st.expander("Stored Summary (default medium)"):
                st.write(res["summary"])

            st.write("---")
    else:
        st.error("Search failed")

# ------------------------
# All uploaded files + dynamic summaries + relations
# ------------------------
st.header("All Uploaded Files & Summaries")

if st.button("Reindex all files"):
    resp = requests.post(f"{BACKEND_URL}/api/reindex")
    if resp.status_code == 200:
        data = resp.json()
        st.success(f"Reindexed {data.get('reindexed', 0)} files.")
    else:
        st.error("Reindex failed")

if st.button("Refresh File List"):
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
                st.caption(f"Stored summary type: {f.get('summary_type', 'unknown')}")

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
    else:
        st.error("Could not fetch uploaded files")
