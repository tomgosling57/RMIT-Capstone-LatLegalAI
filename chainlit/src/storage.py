"""Local filesystem storage client for Chainlit (demo prototype).

Implements BaseStorageClient so uploaded file elements (PDFs, images, etc.)
are persisted on disk rather than lost when no cloud storage is configured.
Files are served through Nginx via a shared Docker volume at ``/chat/uploads/``.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from chainlit import make_async
from chainlit.data.storage_clients.base import BaseStorageClient


class LocalStorageClient(BaseStorageClient):
    """Stores uploaded blobs on the local filesystem.

    Parameters
    ----------
    storage_path : str
        Directory on disk where blobs are saved. Created automatically if it
        does not exist.  Defaults to ``./.files``.
    base_url : str
        HTTP URL prefix that Nginx uses to serve files from the shared
        ``chainlit_data`` volume.  Defaults to ``/chat/uploads``.  Must not
        have a trailing slash.
    """

    def __init__(
        self, storage_path: str = "./.files", base_url: str = "/chat/uploads"
    ) -> None:
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Synchronous helpers (wrapped via make_async for the async interface)
    # ------------------------------------------------------------------

    def _sync_upload_file(
        self,
        object_key: str,
        data: Union[bytes, str],
        mime: str = "application/octet-stream",
        overwrite: bool = True,
        content_disposition: Optional[str] = None,
    ) -> Dict[str, Any]:
        dest = self._path / object_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(dest, mode) as f:
            f.write(data)  # type: ignore[arg-type]
        url = f"{self._base_url}/{object_key}"
        return {"object_key": object_key, "url": url}

    def _sync_delete_file(self, object_key: str) -> bool:
        dest = self._path / object_key
        if dest.exists():
            dest.unlink()
            return True
        return False

    # ------------------------------------------------------------------
    # Async interface (required by BaseStorageClient)
    # ------------------------------------------------------------------

    async def upload_file(
        self,
        object_key: str,
        data: Union[bytes, str],
        mime: str = "application/octet-stream",
        overwrite: bool = True,
        content_disposition: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await make_async(self._sync_upload_file)(
            object_key,
            data,
            mime,
            overwrite,
            content_disposition,
        )

    async def delete_file(self, object_key: str) -> bool:
        return await make_async(self._sync_delete_file)(object_key)

    async def get_read_url(self, object_key: str) -> str:
        dest = self._path / object_key
        if dest.exists():
            return f"{self._base_url}/{object_key}"
        return ""

    async def close(self) -> None:
        """No-op — local filesystem client has no connections to close."""
        return
