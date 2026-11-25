import streamlit as st
import difflib
import streamlit.components.v1 as components
from components.pdf_viewer_component import pdf_viewer_component


def document_comparison_component(
    extracted_text_pages: list[str],
    ground_truth_text_pages: list[str],
    raw_pdf_bytes: bytes,
    num_pdf_pages: int,
):
    """
    A reusable Streamlit component for comparing extracted text with ground truth text.

    Args:
        extracted_text_pages: List of strings, where each string is text from
        one page extracted by the backend
        ground_truth_text_pages: List of strings, where each string is text from
        one page of the ground truth file
        raw_pdf_bytes: The raw bytes of the uploaded PDF file for the PDF viewer
        num_pdf_pages: The total number of pages in the PDF for pagination control
    """

    # Initialize session state variables if they don't exist
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = 1

    if "normalization_enabled" not in st.session_state:
        st.session_state.normalization_enabled = False

    # PDF Viewer Integration
    st.subheader("PDF Preview")
    pdf_viewer_component(
        raw_pdf_bytes,
        page_number=st.session_state.selected_page,
        total_pages=num_pdf_pages,
    )

    # Page selection slider
    st.session_state.selected_page = st.slider(
        "Select Page",
        min_value=1,
        max_value=num_pdf_pages,
        value=st.session_state.selected_page,
    )

    # Show current page number
    st.info(f"Showing page {st.session_state.selected_page} of {num_pdf_pages}")

    # Normalized Comparison Toggle
    st.session_state.normalization_enabled = st.checkbox(
        "Perform Normalized Comparison", value=st.session_state.normalization_enabled
    )

    # Get text for the selected page
    selected_extracted_page = ""
    if st.session_state.selected_page <= len(extracted_text_pages):
        selected_extracted_page = extracted_text_pages[
            st.session_state.selected_page - 1
        ]

    selected_ground_truth_page = ""
    if st.session_state.selected_page <= len(ground_truth_text_pages):
        selected_ground_truth_page = ground_truth_text_pages[
            st.session_state.selected_page - 1
        ]

    # Normalize text if toggle is enabled
    if st.session_state.normalization_enabled:
        from utils.text_utils import normalize_text

        normalized_extracted = normalize_text(selected_extracted_page)
        normalized_ground_truth = normalize_text(selected_ground_truth_page)
    else:
        normalized_extracted = selected_extracted_page
        normalized_ground_truth = selected_ground_truth_page

    # Calculate similarity score using difflib.SequenceMatcher
    similarity = difflib.SequenceMatcher(
        None, normalized_extracted, normalized_ground_truth
    )
    ratio = similarity.ratio()
    percentage = round(ratio * 100, 1)

    # Display similarity score
    st.subheader("Similarity Score")
    st.metric("Similarity Score", f"{percentage}% Match")

    # Generate HTML diff using normalized text
    html_diff = difflib.HtmlDiff()
    diff_html = html_diff.make_file(
        normalized_extracted.splitlines(),
        normalized_ground_truth.splitlines(),
        fromdesc="Extracted Output",
        todesc="Expected Output (Ground Truth)",
        context=False,
        numlines=5,
    )

    # Apply custom CSS to fix the width and improve readability
    # Uses LatLegal AI dark navy/gold theme colors
    custom_css = """
    <style>
    .diffTable {
        width: 100% !important;
        table-layout: fixed !important;
    }
    .diffHeader {
        font-weight: bold !important;
        background-color: #0D1020 !important;
        color: #FFD700 !important;
        padding: 4px !important;
    }
    .diffAdd {
        background-color: #0a2a0a !important;
        color: #2ecc71 !important;
    }
    .diffSub {
        background-color: #2a0a0a !important;
        color: #e74c3c !important;
    }
    .diffChange {
        background-color: #2a2a0a !important;
        color: #f59e0b !important;
    }
    .diffNext {
        color: #AAAAAA !important;
        background-color: #0C0F1A !important;
    }
    .diffRow {
        word-wrap: break-word !important;
        word-break: break-all !important;
        white-space: pre-wrap !important;
    }
    .diffContainer {
        max-height: 500px !important;
        overflow-y: auto !important;
        overflow-x: auto !important;
        border: 1px solid #1E2A5A !important;
        border-radius: 4px !important;
        background-color: #05070A !important;
    }
    table.diff {
        background-color: #05070A !important;
    }
    table.diff td {
        background-color: #0C0F1A !important;
        color: #FFFFFF !important;
    }
    </style>
    """

    # Display side-by-side comparison using columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Extracted Output")
        st.text_area("Extracted Text", selected_extracted_page, height=300)

    with col2:
        st.subheader("Expected Output (Ground Truth)")
        st.text_area(
            "Expected Output (Ground Truth)",
            selected_ground_truth_page,
            height=300,
        )

    # Display HTML diff with custom styling
    st.subheader("Difference Highlighting")
    styled_diff_html = custom_css + '<div class="diffContainer">' + diff_html + "</div>"
    components.html(styled_diff_html, height=550)
