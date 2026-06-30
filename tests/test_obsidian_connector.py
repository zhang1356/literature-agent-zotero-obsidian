import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from connectors.obsidian_connector import ObsidianConnector


def test_safe_filename_removes_windows_invalid_characters(tmp_path):
    connector = ObsidianConnector(str(tmp_path), "Literature Notes")

    filename = connector.safe_filename('A/B:C*D?E"F<G>H|I')

    assert filename == "A_B_C_D_E_F_G_H_I"
    assert all(char not in filename for char in '<>:"/\\|?*')


def test_write_note_writes_markdown_and_deduplicates_name(tmp_path):
    connector = ObsidianConnector(str(tmp_path), "Literature Notes")

    first_path = Path(connector.write_note("Paper: One", "# Paper One"))
    second_path = Path(connector.write_note("Paper: One", "# Paper One Again"))

    assert first_path.exists()
    assert first_path.read_text(encoding="utf-8") == "# Paper One"
    assert second_path.exists()
    assert second_path.name == "Paper_ One-1.md"
    assert second_path.read_text(encoding="utf-8") == "# Paper One Again"


def test_search_notes_returns_filename_path_and_snippet(tmp_path):
    connector = ObsidianConnector(str(tmp_path), "Literature Notes")
    connector.write_note(
        "Multimodal RAG",
        "# Multimodal RAG\n\nThis note discusses retrieval augmented generation.",
    )
    connector.write_note("Unrelated", "# Unrelated\n\nNothing to see here.")

    results = connector.search_notes("retrieval")

    assert len(results) == 1
    assert results[0]["filename"] == "Multimodal RAG.md"
    assert results[0]["path"].endswith("Multimodal RAG.md")
    assert "retrieval" in results[0]["snippet"].lower()
