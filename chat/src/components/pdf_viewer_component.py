import streamlit as st
from streamlit_pdf_viewer import pdf_viewer


def pdf_viewer_component(
    pdf_bytes: bytes, page_number: int = None, total_pages: int = None
):
    """
    A reusable Streamlit component for displaying PDF files with pagination support.

    Args:
        pdf_bytes: The PDF file content as bytes.
        page_number: Optional page number to display. If None, all pages are shown.
        total_pages: Optional total number of pages for pagination controls. If None,
                     the component will attempt to determine it automatically.

    Returns:
        The selected page number if pagination is used, otherwise None.
    """
    # Display the PDF viewer with specific page if provided
    if page_number is not None:
        pdf_viewer(pdf_bytes, pages_to_render=[page_number])
    else:
        pdf_viewer(pdf_bytes)

    # If pagination info is provided, show pagination controls
    if total_pages is not None and total_pages > 1:
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if page_number is None:
                page_number = 1

            selected_page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=page_number,
                step=1,
                key="pdf_page_selector",
            )

            st.caption(f"of {total_pages} pages")
            return selected_page

    return None
