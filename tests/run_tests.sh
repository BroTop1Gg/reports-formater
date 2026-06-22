#!/bin/bash
# ============================================================
# Reports-Formater Test Suite
# ============================================================
# Run all functional tests for the refactored codebase

set -e

cd "$(dirname "$0")/.."

echo "=== Reports-Formater Test Suite ==="
echo ""

# Activate virtual environment
source venv/bin/activate

# Clean output
rm -f tests/output/*.docx

# ------------------------------------------------------------
echo ">>> Test 1: Report WITH title page template (No Numbering)"
echo "    Template: tests/input/title_template.docx"
python -m src.main tests/input/test_with_title.yaml \
    --template tests/input/title_template.docx \
    --output tests/output/test_with_title.docx
echo "    ✓ Generated: tests/output/test_with_title.docx"
echo ""

# ------------------------------------------------------------
echo ">>> Test 2: Report WITHOUT title page (Header + Numbering)"
python -m src.main tests/input/test_without_title.yaml \
    --output tests/output/test_without_title.docx
echo "    ✓ Generated: tests/output/test_without_title.docx"
echo ""

# ------------------------------------------------------------
echo ">>> Test 3: Report WITH title page AND Numbering (Skip First Page)"
# This tests the logic that title page shouldn't have headers
python -m src.main tests/input/test_title_and_numbering.yaml \
    --template tests/input/title_template.docx \
    --output tests/output/test_title_and_numbering.docx
echo "    ✓ Generated: tests/output/test_title_and_numbering.docx"
echo ""

echo "=== All tests completed! ==="
echo ""
echo "Test files:"
ls -la tests/output/*.docx
echo ""
echo "Open the files in Word/LibreOffice to verify visually."
