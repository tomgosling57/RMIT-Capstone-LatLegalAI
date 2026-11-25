"""Test the _resolve_logo_path function to validate logo path discovery.

Verifies:
- The function returns a valid path to an existing logo file.
- Candidate 3 is a dead path that should be removed.
"""

from pathlib import Path


class TestResolveLogoPath:
    """Tests for _resolve_logo_path."""

    def test_resolve_logo_returns_existing_path(self) -> None:
        """_resolve_logo_path should return an existing file path."""
        from pdf_export import _resolve_logo_path

        result = _resolve_logo_path()
        assert result is not None, "Expected a logo path, got None"
        assert Path(result).is_file(), f"Path does not exist: {result}"

    def test_candidate_one_is_correct(self) -> None:
        """Candidate 1: __file__/../public/logo_light.png should exist."""
        from pdf_export import _resolve_logo_path as _
        import pdf_export as m

        candidate = Path(m.__file__).resolve().parent.parent / "public" / "logo_light.png"
        assert candidate.is_file(), (
            f"Candidate 1 should exist: {candidate}"
        )

    def test_candidate_three_is_dead_path(self) -> None:
        """Candidate 3: __file__/./public/logo_light.png should NOT exist.

        This candidate resolves to chainlit/src/public/logo_light.png
        but the public/ directory is at chainlit/public/, not chainlit/src/public/.
        """
        import pdf_export as m

        candidate = Path(m.__file__).resolve().parent / "public" / "logo_light.png"
        assert not candidate.is_file(), (
            f"Candidate 3 should not exist (dead path): {candidate}"
        )

    def test_candidate_three_does_not_cause_error(self) -> None:
        """Even though candidate 3 is a dead path, _resolve_logo_path
        should still find the logo via candidate 1."""
        from pdf_export import _resolve_logo_path

        result = _resolve_logo_path()
        assert result is not None, "_resolve_logo_path should still return a valid path"
        # The returned path should end with public/logo_light.png
        assert "public" in result, f"Expected 'public' in path: {result}"
        assert "logo_light.png" in result, f"Expected 'logo_light.png' in path: {result}"
