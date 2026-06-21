"""
Unit tests for Markdown Transpiler Bridge (markdown_parser.py).

Tests all regex-parsing patterns and node generation for Pandoc-style
academic Markdown elements.
"""

import pytest
from src.sdk.markdown_parser import (
    parse_markdown_to_nodes,
    parse_attributes,
    _convert_value,
)


class TestAttributeParsing:
    """Test attribute parsing from key=value strings."""

    def test_parse_simple_string_attribute(self):
        """Parse unquoted string value."""
        result = parse_attributes('caption="Listing 1.1"')
        assert result == {"caption": "Listing 1.1"}

    def test_parse_quoted_string_with_spaces(self):
        """Parse quoted string with spaces."""
        result = parse_attributes('path="src/file.py"')
        assert result == {"path": "src/file.py"}

    def test_parse_float_attribute(self):
        """Parse float value."""
        result = parse_attributes('width=10.5')
        assert result == {"width": 10.5}

    def test_parse_integer_attribute(self):
        """Parse integer value."""
        result = parse_attributes('level=3')
        assert result == {"level": 3}

    def test_parse_boolean_true(self):
        """Parse boolean true."""
        result = parse_attributes('fit_to_page=true')
        assert result == {"fit_to_page": True}

    def test_parse_boolean_false(self):
        """Parse boolean false."""
        result = parse_attributes('placeholder=false')
        assert result == {"placeholder": False}

    def test_parse_multiple_attributes(self):
        """Parse multiple attributes in one string."""
        result = parse_attributes('width=17.0 fit_to_page=true caption="Рисунок 1.1"')
        assert result == {
            "width": 17.0,
            "fit_to_page": True,
            "caption": "Рисунок 1.1"
        }

    def test_parse_empty_string(self):
        """Parse empty attribute string."""
        result = parse_attributes('')
        assert result == {}


class TestHeadingParsing:
    """Test heading parsing."""

    def test_parse_level_1_heading(self):
        """Parse level 1 heading."""
        md = "# ВСТУП"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0] == {"type": "heading", "level": 1, "text": "ВСТУП"}

    def test_parse_level_2_heading(self):
        """Parse level 2 heading."""
        md = "## 1.1 Аналіз результатів"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0] == {"type": "heading", "level": 2, "text": "1.1 Аналіз результатів"}

    def test_parse_level_3_heading(self):
        """Parse level 3 heading."""
        md = "### 1.1.1 Детальний аналіз"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0] == {"type": "heading", "level": 3, "text": "1.1.1 Детальний аналіз"}

    def test_parse_heading_with_extra_spaces(self):
        """Parse heading with extra spaces."""
        md = "#   ВСТУП   "
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["text"] == "ВСТУП"


class TestCodeBlockParsing:
    """Test fenced code block parsing."""

    def test_parse_inline_code_block(self):
        """Parse inline code block with caption."""
        md = '''```python {caption="Лістинг 1.1 — Функція"}
def calculate(x):
    return x * 2
```'''
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "code"
        assert nodes[0]["language"] == "python"
        assert nodes[0]["caption"] == "Лістинг 1.1 — Функція"
        assert "def calculate(x):" in nodes[0]["code"]

    def test_parse_code_block_with_path(self):
        """Parse code block with file path."""
        md = '```python {caption="Лістинг 1.2" path="src/file.py"}\n```'
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "code"
        assert nodes[0]["path"] == "src/file.py"
        assert nodes[0]["caption"] == "Лістинг 1.2"
        assert "code" not in nodes[0] or nodes[0]["code"] == ""

    def test_parse_code_block_without_metadata(self):
        """Parse code block without metadata."""
        md = '''```python
print("hello")
```'''
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "code"
        assert nodes[0]["language"] == "python"
        assert "caption" not in nodes[0]


class TestImageParsing:
    """Test Pandoc-style image parsing."""

    def test_parse_image_with_all_attributes(self):
        """Parse image with all attributes."""
        md = '![Рисунок 1.1 — Головне вікно](images/screenshot.png){width=17.0 fit_to_page=true align=center}'
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "image"
        assert nodes[0]["path"] == "images/screenshot.png"
        assert nodes[0]["caption"] == "Рисунок 1.1 — Головне вікно"
        assert nodes[0]["width_cm"] == 17.0
        assert nodes[0]["fit_to_page"] == True
        assert nodes[0]["align"] == "center"

    def test_parse_image_with_placeholder(self):
        """Parse image with placeholder flag."""
        md = '![Рисунок 1.2](image.png){placeholder=true}'
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["placeholder"] == True

    def test_parse_image_without_caption(self):
        """Parse image without caption."""
        md = '![](image.png){width=10.0}'
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["caption"] is None
        assert nodes[0]["width_cm"] == 10.0


class TestFormulaParsing:
    """Test LaTeX formula parsing."""

    def test_parse_formula_with_caption(self):
        """Parse formula with caption."""
        md = '$$E_k = \\frac{m \\cdot v^2}{2}$$ (1.1)'
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "formula"
        assert nodes[0]["content"] == "E_k = \\frac{m \\cdot v^2}{2}"
        assert nodes[0]["caption"] == "(1.1)"

    def test_parse_formula_with_alignment(self):
        """Parse formula with alignment attribute."""
        md = '$$V = \\pi r^2 h$$ (1.2) {align=center}'
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["align"] == "center"
        assert nodes[0]["caption"] == "(1.2)"

    def test_parse_formula_without_caption(self):
        """Parse formula without caption."""
        md = '$$x = y + z$$'
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["type"] == "formula"
        assert nodes[0]["content"] == "x = y + z"
        assert "caption" not in nodes[0]


class TestTableParsing:
    """Test pipe table parsing."""

    def test_parse_table_with_caption_above(self):
        """Parse table with caption above."""
        md = '''Table: Таблиця 1.1 — Параметри
| Назва | Значення |
|-------|----------|
| Порт  | 8080     |'''
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "table"
        assert nodes[0]["caption"] == "Таблиця 1.1 — Параметри"
        assert len(nodes[0]["rows"]) == 2

    def test_parse_table_with_caption_below(self):
        """Parse table with caption below."""
        md = '''| Колонка 1 | Колонка 2 |
|-----------|-----------|
| Дані      | Дані      |
: Таблиця 1.2 — Назва'''
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["caption"] == "Таблиця 1.2 — Назва"

    def test_parse_table_with_br_tags(self):
        """Parse table with <br> tags in cells."""
        md = '''| Текст |
|-------|
| Рядок 1<br>Рядок 2 |'''
        nodes = parse_markdown_to_nodes(md)
        assert "Рядок 1\nРядок 2" in nodes[0]["rows"][1][0]

    def test_parse_table_with_attributes(self):
        """Parse table with style attributes."""
        md = '''Table: Таблиця 1.3 {style="Table Grid" repeat_header=false}
| A | B |
|---|---|
| 1 | 2 |'''
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["style"] == "Table Grid"
        assert nodes[0]["repeat_header"] == False


class TestListParsing:
    """Test list parsing."""

    def test_parse_bullet_list(self):
        """Parse bullet list."""
        md = '''- перший елемент;
- другий елемент;
- останній елемент.'''
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "list"
        assert nodes[0]["style"] == "bullet"
        assert len(nodes[0]["items"]) == 3

    def test_parse_numbered_list(self):
        """Parse numbered list."""
        md = '''1. перший крок;
2. другий крок;
3. останній крок.'''
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["style"] == "numbered"
        assert len(nodes[0]["items"]) == 3

    def test_parse_alpha_cyrillic_list(self):
        """Parse Cyrillic alpha list."""
        md = '''а) перший варіант;
б) другий варіант.'''
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["style"] == "alpha_cyrillic"

    def test_parse_alpha_latin_list(self):
        """Parse Latin alpha list."""
        md = '''a) first item;
b) second item.'''
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["style"] == "alpha_latin"

    def test_parse_nested_list(self):
        """Parse nested list with indentation."""
        md = '''- перший рівень;
  - другий рівень;
  - ще один елемент;
- останній елемент.'''
        nodes = parse_markdown_to_nodes(md)
        # Should create three list nodes (level 1, level 2, level 1)
        assert len(nodes) == 3
        assert nodes[0]["level"] == 1
        assert nodes[0]["items"] == ["перший рівень;"]
        assert nodes[1]["level"] == 2
        assert nodes[1]["items"] == ["другий рівень;", "ще один елемент;"]
        assert nodes[2]["level"] == 1
        assert nodes[2]["items"] == ["останній елемент."]


class TestParagraphParsing:
    """Test paragraph parsing."""

    def test_parse_simple_paragraph(self):
        """Parse simple paragraph."""
        md = "Це звичайний абзац тексту."
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "paragraph"
        assert nodes[0]["text"] == "Це звичайний абзац тексту."

    def test_parse_paragraph_with_alignment(self):
        """Parse paragraph with alignment attribute."""
        md = "Текст з вирівнюванням. {align=center}"
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0]["align"] == "center"
        assert nodes[0]["text"] == "Текст з вирівнюванням."

    def test_parse_multiline_paragraph(self):
        """Parse paragraph with multiple lines."""
        md = '''Перший рядок.
Другий рядок.
Третій рядок.'''
        nodes = parse_markdown_to_nodes(md)
        assert "Перший рядок." in nodes[0]["text"]
        assert "Другий рядок." in nodes[0]["text"]


class TestPageBreakParsing:
    """Test page break parsing."""

    def test_parse_page_break_dashes(self):
        """Parse page break with dashes."""
        md = "---"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0] == {"type": "break", "style": "page"}

    def test_parse_page_break_asterisks(self):
        """Parse page break with asterisks."""
        md = "***"
        nodes = parse_markdown_to_nodes(md)
        assert nodes[0] == {"type": "break", "style": "page"}


class TestComplexDocuments:
    """Test parsing of complex multi-element documents."""

    def test_parse_mixed_content(self):
        """Parse document with multiple element types."""
        md = '''# ВСТУП

Це вступний абзац.

## 1.1 Аналіз

![Рисунок 1.1](image.png){width=10.0}

$$E = mc^2$$ (1.1)

- елемент 1;
- елемент 2.'''
        nodes = parse_markdown_to_nodes(md)
        
        # Should have: heading, paragraph, heading, image, formula, list
        types = [n["type"] for n in nodes]
        assert "heading" in types
        assert "paragraph" in types
        assert "image" in types
        assert "formula" in types
        assert "list" in types

    def test_parse_empty_document(self):
        """Parse empty document."""
        md = ""
        nodes = parse_markdown_to_nodes(md)
        assert nodes == []

    def test_parse_only_whitespace(self):
        """Parse document with only whitespace."""
        md = "   \n\n   \n"
        nodes = parse_markdown_to_nodes(md)
        assert nodes == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
