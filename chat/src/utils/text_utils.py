def normalize_text(text: str) -> str:
    """
    Normalize text by performing the following steps:
    - Strip leading/trailing whitespace
    - Replace multiple internal spaces with a single space
    - Unify newlines (replace \\r\\n with \\n)
    - Convert text to lowercase
    - Remove non-printable characters
    - Ensure UTF-8 encoding

    Args:
        text: Input string to normalize

    Returns:
        Normalized string
    """
    import re

    if not isinstance(text, str):
        text = str(text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Unify newlines (replace \\r\\n with \\n, then \\r with \\n)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace multiple internal spaces with a single space
    text = re.sub(r" +", " ", text)

    # Remove non-printable characters (keep printable ASCII and common Unicode)
    text = "".join(char for char in text if char.isprintable() or char in "\n ")

    # Convert to lowercase
    text = text.lower()

    return text
