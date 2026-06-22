#!/bin/bash
# ============================================================
# Reports-Formater Test Suite
# ============================================================
# Run all functional tests for the refactored codebase
# Generates both YAML and Markdown variants for visual comparison

set -e

cd "$(dirname "$0")/.."

echo "=== Reports-Formater Test Suite ==="
echo ""

# Activate virtual environment
source venv/bin/activate

# Clean output
rm -f tests/output/*.docx

# ============================================================
echo ">>> YAML Tests"
echo "============================================================"

# ------------------------------------------------------------
echo ""
echo ">>> Test 1 (YAML): Report WITH title page template (No Numbering)"
echo "    Template: tests/input/title_template.docx"
python -m src.main tests/input/test_with_title.yaml \
    --template tests/input/title_template.docx \
    --output tests/output/test_with_title.docx
echo "    ✓ Generated: tests/output/test_with_title.docx"

# ------------------------------------------------------------
echo ""
echo ">>> Test 2 (YAML): Report WITHOUT title page (Header + Numbering)"
python -m src.main tests/input/test_without_title.yaml \
    --output tests/output/test_without_title.docx
echo "    ✓ Generated: tests/output/test_without_title.docx"

# ------------------------------------------------------------
echo ""
echo ">>> Test 3 (YAML): Report WITH title page AND Numbering (Skip First Page)"
python -m src.main tests/input/test_title_and_numbering.yaml \
    --template tests/input/title_template.docx \
    --output tests/output/test_title_and_numbering.docx
echo "    ✓ Generated: tests/output/test_title_and_numbering.docx"

# ============================================================
echo ""
echo ">>> Markdown Tests"
echo "============================================================"

# ------------------------------------------------------------
echo ""
echo ">>> Test 4 (MD): Report WITH title page template (No Numbering)"
echo "    Template: tests/input/title_template.docx"
python -m src.main tests/input/test_with_title.md \
    --template tests/input/title_template.docx \
    --output tests/output/test_with_title_md.docx
echo "    ✓ Generated: tests/output/test_with_title_md.docx"

# ------------------------------------------------------------
echo ""
echo ">>> Test 5 (MD): Report WITHOUT title page (Header + Numbering)"
python -m src.main tests/input/test_without_title.md \
    --output tests/output/test_without_title_md.docx
echo "    ✓ Generated: tests/output/test_without_title_md.docx"

# ------------------------------------------------------------
echo ""
echo ">>> Test 6 (MD): Report WITH title page AND Numbering (Skip First Page)"
python -m src.main tests/input/test_title_and_numbering.md \
    --template tests/input/title_template.docx \
    --output tests/output/test_title_and_numbering_md.docx
echo "    ✓ Generated: tests/output/test_title_and_numbering_md.docx"

# ============================================================
echo ""
echo "=== All tests completed! ==="
echo ""
echo "Generated files (YAML vs Markdown for visual comparison):"
ls -la tests/output/*.docx
echo ""
echo "Compare pairs:"
echo "  test_with_title.docx          vs  test_with_title_md.docx"
echo "  test_without_title.docx       vs  test_without_title_md.docx"
echo "  test_title_and_numbering.docx vs  test_title_and_numbering_md.docx"
echo ""
echo "Open the files in Word/LibreOffice to verify visually."
