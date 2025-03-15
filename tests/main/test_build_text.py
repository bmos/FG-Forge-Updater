from pathlib import Path

from src.build_processing import get_readme


def test_readme_html() -> None:
    """Ensure that markdown text is being converted to html."""
    html = (Path(__file__).parent / "markdown_example/markdown.html").read_text(encoding="utf-8")
    zip_path = Path(__file__).parent / "markdown_example/markdown.ext"
    assert f"{get_readme([zip_path])}\n" == html
