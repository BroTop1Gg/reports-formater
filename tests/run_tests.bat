@echo off
REM ============================================================
REM Reports-Formater Test Suite (Windows)
REM ============================================================
REM Run all functional tests for the refactored codebase

echo === Reports-Formater Test Suite ===
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Clean output
if exist tests\output\*.docx del /Q tests\output\*.docx

REM ------------------------------------------------------------
echo ^>^>^> Test 1: Report WITH title page template (No Numbering)
echo     Template: tests\input\title_template.docx
python -m src.main tests\input\test_with_title.yaml ^
    --template tests\input\title_template.docx ^
    --output tests\output\test_with_title.docx
if errorlevel 1 goto :error
echo     [OK] Generated: tests\output\test_with_title.docx
echo.

REM ------------------------------------------------------------
echo ^>^>^> Test 2: Report WITHOUT title page (Header + Numbering)
python -m src.main tests\input\test_without_title.yaml ^
    --output tests\output\test_without_title.docx
if errorlevel 1 goto :error
echo     [OK] Generated: tests\output\test_without_title.docx
echo.

REM ------------------------------------------------------------
echo ^>^>^> Test 3: Report WITH title page AND Numbering (Skip First Page)
python -m src.main tests\input\test_title_and_numbering.yaml ^
    --template tests\input\title_template.docx ^
    --output tests\output\test_title_and_numbering.docx
if errorlevel 1 goto :error
echo     [OK] Generated: tests\output\test_title_and_numbering.docx
echo.

echo === All tests completed! ===
echo.
echo Test files:
dir /B tests\output\*.docx
echo.
echo Open the files in Word/LibreOffice to verify visually.
goto :eof

:error
echo.
echo [FAIL] Test failed with error code %errorlevel%
exit /b %errorlevel%
