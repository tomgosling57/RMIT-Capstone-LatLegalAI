from pathlib import Path
from typing import Optional
import uuid


class FileSaver:
    """
    Supports any binary-safe file type (txt, pdf, images, etc.).
    """

    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _generate_safe_filename(self, filename: str) -> str:
        ext = Path(filename).suffix  # includes dot, e.g. ".pdf"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        return unique_name

    def save_file(
        self, file_bytes: bytes, filename: str, subfolder: Optional[str] = None
    ) -> Path:
        # Build target directory
        target_dir = self.base_dir
        if subfolder:
            target_dir = target_dir / subfolder

        target_dir.mkdir(parents=True, exist_ok=True)

        safe_name = self._generate_safe_filename(filename)

        file_path = target_dir / safe_name

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return Path(file_path)

    def get_file_path(self, file_id: str) -> Optional[Path]:
        """
        Retrieve the file path for a given file_id by scanning the uploads directory.

        The ``file_id`` corresponds to the safe filename generated during save
        (e.g. ``"abc123def.pdf"``).  Returns ``None`` if no matching file is found.

        Args:
            file_id: The UUID-based filename (e.g. ``"abc123def456.pdf"``)

        Returns:
            Path to the file if found, ``None`` otherwise.
        """
        target: Path = self.base_dir / file_id
        if target.exists() and target.is_file():
            return target
        # Fallback: scan directory for a file whose name starts with file_id
        # (in case the extension was stripped or modified)
        for child in self.base_dir.iterdir():
            if child.is_file() and child.name == file_id:
                return child
        return None
