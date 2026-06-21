#!/usr/bin/env python3
"""
Unit tests for the refactored markdown_parser.py (Natural Syntax with Smart Defaults).

Tests the new behavior:
- Smart Defaults (paragraphs, formulas, images, tables)
- Smart Caption Absorption (code blocks and tables)
- Natural image placeholders
- LaTeX formulas with optional captions
- Line breaks and page breaks
"""

import pytest
from pathlib import Path
from src.sdk.markdown_parser import parse_markdown_to_nodes


class TestSmartDefaults:
    """Test Smart Defaults behavior."""

    def test_paragraph_default_justify(self):
        """Paragraphs should default to align='justify'."""
        md = "Це звичайний абзац тексту."
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "paragraph"
        assert nodes[0]["text"] == "Це звичайний абзац тексту."
        assert nodes[0]["align"] == "justify"

    def test_formula_default_center(self):
        """Formulas should default to align='center'."""
        md = "$$E = mc^2$$ (1.1)"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "formula"
        assert nodes[0]["content"] == "E = mc^2"
        assert nodes[0]["caption"] == "(1.1)"
        assert nodes[0]["align"] == "center"

    def test_image_default_center_fit(self):
        """Images should default to align='center' and fit_to_page=True."""
        md = "![Рисунок 1.1 — Зображення](images/fig1.png)"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "image"
        assert nodes[0]["path"] == "images/fig1.png"
        assert nodes[0]["caption"] == "Рисунок 1.1 — Зображення"
        assert nodes[0]["align"] == "center"
        assert nodes[0]["fit_to_page"] is True

    def test_table_default_style_repeat(self):
        """Tables should default to style='Table Grid' and repeat_header=True."""
        md = """| Колонка 1 | Колонка 2 |
|-----------|-----------|
| Дані      | Дані      |"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "table"
        assert nodes[0]["style"] == "Table Grid"
        assert nodes[0]["repeat_header"] is True


class TestSmartCaptionAbsorption:
    """Test Smart Caption Absorption for code blocks and tables."""

    def test_listing_caption_absorption(self):
        """Italic caption before code block should be absorbed."""
        md = """*Лістинг 1.1 — Приклад коду*
```python
def hello():
    print("Hello")
```"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "code"
        assert nodes[0]["caption"] == "Лістинг 1.1 — Приклад коду"
        assert nodes[0]["language"] == "python"

    def test_listing_caption_with_path(self):
        """Italic caption with path should be absorbed."""
        md = """*Лістинг 2.1 — Конфігурація (config.yaml)*
```yaml
key: value
```"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "code"
        # The caption excludes the path
        assert nodes[0]["caption"] == "Лістинг 2.1 — Конфігурація"
        # The path is extracted separately
        assert nodes[0]["path"] == "config.yaml"

    def test_listing_caption_not_followed_by_code(self):
        """Italic caption not followed by code should become paragraph."""
        md = """*Лістинг 1.1 — Приклад коду*

Звичайний текст після."""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 2
        assert nodes[0]["type"] == "paragraph"
        # The caption should be stripped of asterisks
        assert "Лістинг 1.1 — Приклад коду" in nodes[0]["text"]
        assert nodes[1]["type"] == "paragraph"

    def test_table_caption_absorption(self):
        """Italic caption before table should be absorbed."""
        md = """*Таблиця 1.1 — Результати тестів*
| Тест | Результат |
|------|-----------|
| A    | Pass      |
| B    | Fail      |"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "table"
        assert nodes[0]["caption"] == "Таблиця 1.1 — Результати тестів"

    def test_table_caption_not_followed_by_table(self):
        """Italic table caption not followed by table should become paragraph."""
        md = """*Таблиця 1.1 — Результати тестів*

Звичайний текст після."""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 2
        assert nodes[0]["type"] == "paragraph"
        # The caption should be stripped of asterisks
        assert "Таблиця 1.1 — Результати тестів" in nodes[0]["text"]
        assert nodes[1]["type"] == "paragraph"


class TestNaturalImages:
    """Test natural image syntax with placeholder detection."""

    def test_natural_image(self):
        """Standard image syntax."""
        md = "![Рисунок 1.1 — Скріншот](screenshots/ui.png)"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "image"
        assert nodes[0]["path"] == "screenshots/ui.png"
        assert nodes[0]["caption"] == "Рисунок 1.1 — Скріншот"
        assert nodes[0]["align"] == "center"
        assert nodes[0]["fit_to_page"] is True

    def test_placeholder_detection(self):
        """Image with path='placeholder' should be rewritten and marked as placeholder."""
        md = "![Рисунок 1.2 — Місце для скріншоту](placeholder)"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "image"
        # Parser rewrites "placeholder" to "images/placeholder.png"
        assert nodes[0]["path"] == "images/placeholder.png"
        assert nodes[0]["placeholder"] is True
        assert nodes[0]["caption"] == "Рисунок 1.2 — Місце для скріншоту"

    def test_image_without_caption(self):
        """Image without caption text."""
        md = "![](images/fig.png)"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "image"
        assert nodes[0]["path"] == "images/fig.png"
        # Empty caption string becomes None
        assert nodes[0]["caption"] is None


class TestFormulas:
    """Test LaTeX formula parsing."""

    def test_formula_with_caption(self):
        """Formula with caption in parentheses."""
        md = "$$E = mc^2$$ (1.1)"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "formula"
        assert nodes[0]["content"] == "E = mc^2"
        assert nodes[0]["caption"] == "(1.1)"
        assert nodes[0]["align"] == "center"

    def test_formula_without_caption(self):
        """Formula without caption."""
        md = "$$x = y + z$$"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "formula"
        assert nodes[0]["content"] == "x = y + z"
        assert "caption" not in nodes[0]

    def test_complex_formula(self):
        """Complex LaTeX formula."""
        md = r"$$\int_0^1 x^2 dx = \frac{1}{3}$$ (2.1)"
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "formula"
        assert r"\int_0^1 x^2 dx = \frac{1}{3}" in nodes[0]["content"]
        assert nodes[0]["caption"] == "(2.1)"


class TestLineBreaks:
    """Test line break parsing."""

    def test_simple_br(self):
        """Simple <br> tag."""
        md = "Перший рядок.<br>Другий рядок."
        nodes = parse_markdown_to_nodes(md)
        # Should be one paragraph with newline
        assert len(nodes) == 1
        assert nodes[0]["type"] == "paragraph"
        assert "Перший рядок.\nДругий рядок." in nodes[0]["text"]

    def test_br_with_count(self):
        """<br> with count parameter."""
        md = "Текст<br count=3>Більше тексту."
        nodes = parse_markdown_to_nodes(md)
        # Should be one paragraph with the raw <br> tag preserved
        assert len(nodes) == 1
        assert nodes[0]["type"] == "paragraph"
        # The <br count=3> tag is preserved as-is in the text
        assert "<br count=3>" in nodes[0]["text"]


class TestPageBreaks:
    """Test page break parsing."""

    def test_hr_break(self):
        """Horizontal rule as page break."""
        md = """Розділ 1.

---

Розділ 2."""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 3
        assert nodes[0]["type"] == "paragraph"
        # --- creates a break node with style="page"
        assert nodes[1]["type"] == "break"
        assert nodes[1]["style"] == "page"
        assert nodes[2]["type"] == "paragraph"


class TestHeadings:
    """Test heading parsing."""

    def test_heading_levels(self):
        """All heading levels."""
        md = """# Заголовок 1
## Заголовок 2
### Заголовок 3
#### Заголовок 4"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 4
        assert nodes[0]["level"] == 1
        assert nodes[1]["level"] == 2
        assert nodes[2]["level"] == 3
        assert nodes[3]["level"] == 4


class TestLists:
    """Test list parsing."""

    def test_bullet_list(self):
        """Bullet list with dashes."""
        md = """- Пункт 1
- Пункт 2
- Пункт 3"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "list"
        assert nodes[0]["style"] == "bullet"
        assert len(nodes[0]["items"]) == 3

    def test_numbered_list(self):
        """Numbered list."""
        md = """1. Перший
2. Другий
3. Третій"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "list"
        assert nodes[0]["style"] == "numbered"
        assert len(nodes[0]["items"]) == 3

    def test_alpha_cyrillic_list(self):
        """Cyrillic alphabetic list."""
        md = """а) Пункт а
б) Пункт б
в) Пункт в"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "list"
        assert nodes[0]["style"] == "alpha_cyrillic"

    def test_alpha_latin_list(self):
        """Latin alphabetic list."""
        md = """a) Item a
b) Item b
c) Item c"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "list"
        assert nodes[0]["style"] == "alpha_latin"


class TestTables:
    """Test table parsing."""

    def test_simple_table(self):
        """Simple table without caption."""
        md = """| A | B | C |
|---|---|---|
| 1 | 2 | 3 |
| 4 | 5 | 6 |"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "table"
        assert len(nodes[0]["rows"]) == 3  # header + 2 data rows
        assert nodes[0]["style"] == "Table Grid"
        assert nodes[0]["repeat_header"] is True

    def test_table_with_br_in_cells(self):
        """Table with <br> tags in cells."""
        md = """| Колонка |
|---------|
| Рядок 1<br>Рядок 2 |"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "table"
        # Check that <br> was converted to newline
        cell_content = nodes[0]["rows"][1][0]
        assert "\n" in cell_content


class TestCodeBlocks:
    """Test code block parsing."""

    def test_code_block_with_language(self):
        """Code block with language specified."""
        md = """```python
def hello():
    print("Hello")
```"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "code"
        assert nodes[0]["language"] == "python"
        assert "def hello():" in nodes[0]["code"]

    def test_code_block_without_language(self):
        """Code block without language."""
        md = """```
some code here
```"""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "code"
        assert "language" not in nodes[0]


class TestComplexDocument:
    """Test parsing of complex documents with multiple element types."""

    def test_mixed_content(self):
        """Document with headings, paragraphs, lists, code, images, formulas."""
        md = """# ВСТУП

Це вступний текст.

## 1.1 Основна частина

*Лістинг 1.1 — Приклад*
```python
print("Hello")
```

*Таблиця 1.1 — Дані*
| A | B |
|---|---|
| 1 | 2 |

![Рисунок 1.1](images/fig.png)

$$E = mc^2$$ (1.1)

- Пункт 1
- Пункт 2"""
        nodes = parse_markdown_to_nodes(md)
        
        # Check we got all expected types
        types = [n["type"] for n in nodes]
        assert "heading" in types
        assert "paragraph" in types
        assert "code" in types
        assert "table" in types
        assert "image" in types
        assert "formula" in types
        assert "list" in types
        
        # Check caption absorption worked
        code_node = next(n for n in nodes if n["type"] == "code")
        assert code_node["caption"] == "Лістинг 1.1 — Приклад"
        
        table_node = next(n for n in nodes if n["type"] == "table")
        assert table_node["caption"] == "Таблиця 1.1 — Дані"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_document(self):
        """Empty document should return empty list."""
        nodes = parse_markdown_to_nodes("")
        assert nodes == []

    def test_whitespace_only(self):
        """Whitespace-only document should return empty list."""
        nodes = parse_markdown_to_nodes("   \n\n   \n")
        assert nodes == []

    def test_consecutive_empty_lines(self):
        """Multiple empty lines should be ignored."""
        md = """Текст 1.



Текст 2."""
        nodes = parse_markdown_to_nodes(md)
        assert len(nodes) == 2
        assert all(n["type"] == "paragraph" for n in nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
