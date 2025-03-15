from pathlib import Path

from src.build_processing import get_readme


def test_readme_html() -> None:
    """Ensure that markdown text is being converted to html."""
    with Path.open(Path(__file__).resolve().parent / "markdown_example/markdown.html", encoding="utf-8") as file:
        html = file.read()
    zip_path = Path(__file__).resolve().parent / "markdown_example/markdown.ext"
    assert f"{get_readme([zip_path])}\n" == html
