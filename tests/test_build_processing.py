"""Tests for build_processing."""

import zipfile
from pathlib import Path

import pytest
from bs4 import BeautifulSoup, Tag

from src.build_processing import (
    apply_styles_to_table,
    get_build,
    get_readme,
    readme_html,
    replace_images_with_link,
)


class TestApplyStylesToTable:
    """Tests for apply_styles_to_table function."""

    def test_styles_applied_to_table_cells(self) -> None:
        """Test that td elements receive border and padding styles."""
        html = "<table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>"
        soup = BeautifulSoup(html, "html.parser")
        result = apply_styles_to_table(soup)

        cells = result.find_all("td")
        assert len(cells) == 2
        assert cells[0].get("style") == "border:1px solid #FFFFFF; padding:0.5em;"
        assert cells[1].get("style") == "border:1px solid #FFFFFF; padding:0.5em;"

    def test_styles_applied_to_table_rows(self) -> None:
        """Test that tr elements receive background color and border styles."""
        html = "<table><tr><td>Cell</td></tr><tr><td>Cell</td></tr></table>"
        soup = BeautifulSoup(html, "html.parser")
        result = apply_styles_to_table(soup)

        rows = result.find_all("tr")
        assert len(rows) == 2
        assert rows[0].get("style") == "background-color: #000000; border:1px solid #FFFFFF;"
        assert rows[1].get("style") == "background-color: #1C1C1E; border:1px solid #FFFFFF;"

    def test_alternating_row_colors(self) -> None:
        """Test that rows alternate between two background colors."""
        html = "<table><tr><td>1</td></tr><tr><td>2</td></tr><tr><td>3</td></tr></table>"
        soup = BeautifulSoup(html, "html.parser")
        result = apply_styles_to_table(soup)

        rows = result.find_all("tr")
        assert rows[0].get("style") == "background-color: #000000; border:1px solid #FFFFFF;"
        assert rows[1].get("style") == "background-color: #1C1C1E; border:1px solid #FFFFFF;"
        assert rows[2].get("style") == "background-color: #000000; border:1px solid #FFFFFF;"


class TestReplaceImagesWithLink:
    """Tests for replace_images_with_link function."""

    def test_image_replaced_with_link_using_src(self) -> None:
        """Test that image is replaced with link using img src attribute."""
        html = '<img src="image.png" alt="Test Image">'
        soup = BeautifulSoup(html, "html.parser")
        result = replace_images_with_link(soup, no_images=False)

        link = result.find("a")
        assert isinstance(link, Tag)
        assert link.get("href") == "image.png"
        assert link.string == "Test Image"

    def test_no_images_mode_empty_string(self) -> None:
        """Test that no_images=True results in empty link text."""
        html = '<img src="image.png" alt="Test Image">'
        soup = BeautifulSoup(html, "html.parser")
        result = replace_images_with_link(soup, no_images=True)

        link = result.find("a")
        assert isinstance(link, Tag)
        assert link.get("href") == "image.png"
        assert link.string == ""

    def test_image_replaced_with_link_using_parent_href(self) -> None:
        """Test that image is replaced with link using parent anchor href."""
        html = '<a href="page.html"><img src="image.png" alt="Test Image"></a>'
        soup = BeautifulSoup(html, "html.parser")
        result = replace_images_with_link(soup, no_images=False)

        link = result.find("a")
        assert isinstance(link, Tag)
        assert link.get("href") == "page.html"
        assert link.string == "Test Image"

    def test_missing_alt_attribute(self) -> None:
        """Test that missing alt attribute defaults to [IMG]."""
        html = '<a href="page.html"><img src="image.png"></a>'
        soup = BeautifulSoup(html, "html.parser")
        result = replace_images_with_link(soup, no_images=False)

        link = result.find("a")
        assert isinstance(link, Tag)
        assert link.get("href") == "page.html"
        assert link.string == "[IMG]"


class TestReadmeHtml:
    """Tests for readme_html function."""

    def test_markdown_converted_to_html(self) -> None:
        """Test that markdown text is converted to HTML."""
        markdown_text = "# Header\n\nParagraph text."
        result = readme_html(markdown_text)
        soup = BeautifulSoup(result, "html.parser")

        h1 = soup.find("h1")
        assert h1 is not None
        assert h1.get_text() == "Header"

        p = soup.find("p")
        assert p is not None
        assert p.get_text() == "Paragraph text."

    def test_relative_image_references_removed(self) -> None:
        """Test that relative image references are stripped out."""
        markdown_text = "Text ![](../images/pic.png) more text"
        result = readme_html(markdown_text)
        soup = BeautifulSoup(result, "html.parser")

        assert soup.get_text() == "Text more text"
        assert soup.find("img") is None
        assert "../images/pic.png" not in result

    def test_images_replaced_with_links(self) -> None:
        """Test that images in markdown are converted to links."""
        markdown_text = "![alt text](image.png)"
        result = readme_html(markdown_text, no_images=False)
        soup = BeautifulSoup(result, "html.parser")

        link = soup.find("a")
        assert isinstance(link, Tag)
        assert link.get("href") == "image.png"
        assert link.get_text() == "alt text"
        assert soup.find("img") is None


class TestGetReadme:
    """Tests for get_readme function."""

    @pytest.fixture
    def temp_zip_with_readme(self, tmp_path: Path) -> Path:
        """Create a temporary zip file containing a README.md."""
        zip_path = tmp_path / "test.zip"
        readme_content = b"# Test README\n\nThis is a test."

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("README.md", readme_content)

        return zip_path

    @pytest.fixture
    def temp_zip_without_readme(self, tmp_path: Path) -> Path:
        """Create a temporary zip file without a README.md."""
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("other_file.txt", b"Some content")

        return zip_path

    def test_readme_extracted_from_zip(self, temp_zip_with_readme: Path) -> None:
        """Test that README is successfully extracted and converted."""
        result = get_readme([temp_zip_with_readme])

        soup = BeautifulSoup(result, "html.parser")
        h1 = soup.find("h1")
        assert h1 is not None
        assert h1.get_text() == "Test README"
        assert "This is a test." in soup.get_text()

    def test_raises_error_when_no_readme_found(self, temp_zip_without_readme: Path) -> None:
        """Test that FileNotFoundError is raised when no README exists."""
        with pytest.raises(FileNotFoundError, match="No README file found"):
            get_readme([temp_zip_without_readme])

    def test_searches_multiple_files(self, temp_zip_without_readme: Path, temp_zip_with_readme: Path) -> None:
        """Test that function searches through multiple zip files."""
        result = get_readme([temp_zip_without_readme, temp_zip_with_readme])

        soup = BeautifulSoup(result, "html.parser")
        h1 = soup.find("h1")
        assert h1 is not None
        assert h1.get_text() == "Test README"

    def test_custom_readme_name(self, tmp_path: Path) -> None:
        """Test that custom README filename can be specified."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("CUSTOM.md", b"# Custom README")

        result = get_readme([zip_path], readme_name="CUSTOM.md")

        soup = BeautifulSoup(result, "html.parser")
        h1 = soup.find("h1")
        assert h1 is not None
        assert h1.get_text() == "Custom README"


class TestGetBuild:
    """Tests for get_build function."""

    def test_returns_path_when_file_exists(self, tmp_path: Path) -> None:
        """Test that Path is returned when file exists."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = get_build(tmp_path, "test.txt")

        assert result == test_file
        assert result.is_file()

    def test_raises_error_when_file_not_found(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="is not found"):
            get_build(tmp_path, "nonexistent.txt")

    def test_combines_path_correctly(self, tmp_path: Path) -> None:
        """Test that PurePath and filename are combined correctly."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("content")

        result = get_build(subdir, "test.txt")

        assert result.parent == subdir
        assert result.name == "test.txt"
