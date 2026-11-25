import streamlit as st
import requests
from components.document_comparison_component import document_comparison_component
from components.theme import apply_theme, render_page_header
from config import TEXT_EXTRACTION_ENDPOINT
from auth_guard import check_credentials, require_auth


# ---------------------------------------------------------------------------
# Auth guard — ensures the user is authenticated (or stub mode if no creds)
# ---------------------------------------------------------------------------
check_credentials()
user = require_auth()

st.set_page_config(
    page_title="LatLegalAI - Developer Tool",
    layout="wide",
    page_icon="../static/LegalAiLogo.png",
)

# Apply the theme
apply_theme()


render_page_header("⚖️ Developer Tool", "PDF Comparison Tool")
st.write("Upload source and ground truth files to compare text extraction accuracy.")

# File Uploaders
uploaded_file = st.file_uploader("Upload Source File", type=["pdf", "txt", "docx"])
uploaded_txt = st.file_uploader("Upload Ground Truth TXT", type=["txt"])

# Store uploaded files in session state
if uploaded_file is not None:
    st.session_state["uploaded_file"] = uploaded_file

if uploaded_txt is not None:
    st.session_state["uploaded_txt"] = uploaded_txt

# Extraction Mode Toggle
extraction_mode = st.radio(
    "Extraction Mode",
    ["Flow-Aware", "Column-Aware"],
    index=0,
    help="Select the text extraction mode: Flow-Aware"
    " (default reading order) or Column-Aware (column-based extraction)",
)
st.session_state["extraction_mode"] = extraction_mode

# Handle file upload and API call when both files are available
if "uploaded_file" in st.session_state and "uploaded_txt" in st.session_state:
    if st.button("🚀 Process Files", type="primary"):
        try:
            # Determine file type from uploaded file
            uploaded_file = st.session_state["uploaded_file"]
            file_name = uploaded_file.name
            file_extension = file_name.split(".")[-1].lower()

            # Validate file type
            supported_types = ["pdf", "txt", "docx"]
            if file_extension not in supported_types:
                st.error(
                    f"❌ Unsupported file type: {file_extension}. \n"
                    f"Please upload a PDF, TXT, or DOCX file."
                )
                st.stop()

            # Prepare file for upload
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)  # Reset file pointer

            # Make POST request to backend
            files = {
                "file": (
                    uploaded_file.name,
                    file_bytes,
                    (
                        "application/pdf"
                        if file_extension == "pdf"
                        else (
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document"
                            if file_extension == "docx"
                            else "text/plain"
                        )
                    ),
                )
            }
            # Map frontend labels to backend expected values
            extraction_mode_value = (
                "flow"
                if st.session_state.get("extraction_mode") == "Flow-Aware"
                else "column"
            )
            data = {
                "extraction_mode": extraction_mode_value,
                "file_type": file_extension,
            }
            response = requests.post(TEXT_EXTRACTION_ENDPOINT, files=files, data=data)

            if response.status_code == 200:
                # Extract parsed text from response
                response_data = response.json()
                extracted_text_pages = response_data.get("content", [])

                # Read and process ground truth text
                ground_truth_bytes = st.session_state["uploaded_txt"].read()
                st.session_state["uploaded_txt"].seek(0)  # Reset file pointer
                ground_truth_text = ground_truth_bytes.decode("utf-8")

                # Split ground truth text into pages if it's a single string
                # We need to define a function to split text into pages
                def split_text_into_pages(text: str, lines_per_page: int = 50) -> list:
                    """
                    Split text into pages based on number of lines.

                    Args:
                        text: Input text to split
                        lines_per_page: Number of lines per page

                    Returns:
                        List of text pages
                    """
                    lines = text.splitlines()
                    pages = []

                    for i in range(0, len(lines), lines_per_page):
                        page_lines = lines[i : i + lines_per_page]
                        pages.append("\n".join(page_lines))

                    return pages

                if not isinstance(ground_truth_text, list):
                    ground_truth_pages = split_text_into_pages(ground_truth_text)
                else:
                    ground_truth_pages = ground_truth_text

                # Show PDF viewer only if the uploaded file is a PDF
                if file_extension == "pdf":
                    # Call the new document comparison component
                    document_comparison_component(
                        extracted_text_pages=extracted_text_pages,
                        ground_truth_text_pages=ground_truth_pages,
                        raw_pdf_bytes=file_bytes,
                        num_pdf_pages=len(extracted_text_pages),
                    )
                else:
                    # For non-PDF files, show a message instead of PDF viewer
                    st.info(
                        f"File type '{file_extension}' does not support PDF preview."
                    )
                    st.write(
                        "The document was processed successfully. "
                        "You can view the extracted text below:"
                    )

                    # Display extracted text
                    st.subheader("Extracted Text")
                    for i, page in enumerate(extracted_text_pages):
                        st.markdown(f"### Page {i + 1}")
                        st.text_area("", page, height=200, key=f"page_{i}")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error making API call: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
