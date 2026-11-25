"""
File validation utilities using magic number (libmagic) detection.

**Deprecation notice:** The core detection logic has moved to
``shared/file_validation.py`` so it can be reused across services.
This module now re-exports from the shared utility for backward
compatibility.  New code should import from ``shared.file_validation``
directly.
"""

import os
import uuid
import warnings
from typing import Optional

from fastapi import UploadFile, File, HTTPException  # type: ignore

# Re-export from the shared utility.
from shared.file_validation import (  # noqa: F401
    detect_file_type_bytes,
    detect_file_type_from_path,
    extension_matches,
    is_pdf,
    is_docx,
    is_txt,
    is_png,
    is_jpg,
    is_supported,
)

warnings.warn(
    "backend.src.utilities.magicNums is deprecated. "
    "Import from shared.file_validation instead.",
    DeprecationWarning,
    stacklevel=2,
)


class FileValidator:
    """Legacy file validator — kept for backward compatibility."""

    # Private function to check if a given ID is unique in the storage directory
    @staticmethod
    def __is_id_unique(id: str) -> bool:
        base_path = os.path.dirname(__file__)
        storage_dir = os.path.normpath(
            os.path.join(base_path, "..", "..", "tests", "frontend")
        )
        # Strip extensions from existing filenames before comparing against bare ID
        existing_ids = {os.path.splitext(f)[0] for f in os.listdir(storage_dir)}
        return id not in existing_ids

    # Generate a unique alphanumeric file _ID using uuid4, retrying until unique
    @staticmethod
    def assign_file_id() -> str:
        while True:
            # uuid4 uses letters, digits, and hyphens by default
            # strip hyphens for clean output
            raw_id = str(uuid.uuid4()).replace("-", "")
            if FileValidator._FileValidator__is_id_unique(raw_id):
                return raw_id

    # Use Magic Numbers to detect file type and validate against allowed types
    @staticmethod
    def map_mime_to_ext(mime: str) -> Optional[str]:
        """Map a MIME type to a file extension.

        Deprecated: use ``shared.file_validation.MIME_TO_EXT`` instead.
        """
        from shared.file_validation import MIME_TO_EXT

        return MIME_TO_EXT.get(mime)

    # Give each file a unique name using UUIDs to prevent overwriting
    @staticmethod
    def generate_uuid_filename(extension: str) -> str:
        return f"{uuid.uuid4()}.{extension}"

    # Print Final file name and type for debugging purposes
    @staticmethod
    def print_file_info(filename: str, filetype: str):
        print(f"Validated file: {filename} (type: {filetype})")

    # Print Final File results to put in validate-tests endpoint
    @staticmethod
    def print_validation_results(
        file_path: str,
        valid: bool,
        detected_type: Optional[str],
        uuid_filename: Optional[str],
    ):
        print(f"File: {file_path}")
        print(f"  Valid: {valid}")
        print(f"  Detected Type: {detected_type}")
        print(f"  UUID Filename: {uuid_filename}")


def grab_files():
    test_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "tests", "frontend")
    )
    return [os.path.join(test_dir, f) for f in os.listdir(test_dir)]


async def validate_upload(file: UploadFile = File(...)):
    contents = await file.read(2048)
    file.file.seek(0)

    detected_type = detect_file_type_bytes(contents)

    if detected_type is None:
        raise HTTPException(status_code=400, detail="Unsupported or invalid file type")

    # Prevent extension spoofing
    if not extension_matches(file.filename, detected_type):
        raise HTTPException(
            status_code=400, detail="File extension does not match file content"
        )

    return file


def validate_file_path(file_path: str):
    detected_type = detect_file_type_from_path(file_path)

    return {
        "file": file_path,
        "valid": detected_type is not None,
        "detected_type": detected_type,
        "uuid_filename": (
            FileValidator.generate_uuid_filename(detected_type)
            if detected_type
            else None
        ),
    }


if __name__ == "__main__":
    files = grab_files()
    print(f"\nFound {len(files)} files in tests folder\n")

    for file in files:
        print(f"Testing file: {file}")

        file_type = detect_file_type_from_path(file)
        if file_type:
            print(f"  -> File type: {file_type}")
        else:
            print("  -> Invalid file type")

        print()
