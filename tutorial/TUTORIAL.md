# How to use AI to generate reports

Follow these simple steps to try this tool.

### Step 1: Solve the tasks
1. Open the file `tasks.txt`.
2. Copy all 6 tasks.
3. Paste them into your AI chat.
4. Tell the AI: "Please solve these 6 Python tasks."

### Step 2: Format the report
1. Open the file `../familiarization/ai_system_prompt.md`.
2. Copy all the text from that file.
3. Paste it into the same AI chat.
4. Tell the AI: "Now use this instruction to format a report for the tasks you just solved. Add a Title, Goal (Мета), Topic (Тема), Conclusion (Висновок), and Code blocks. Use placeholders for images."

### Step 3: Create the Word file
1. Copy the YAML code that the AI generated (use `Copy` button at top of YAML container).
2. Open the file `report.yaml` in this folder.
3. Delete everything in `report.yaml` and paste the new code.
4. Save the file.
5. Open your terminal in the main folder (`reports-formater`).
6. Activate `venv` if you use it, or, if not, just run a command below.
7. Run this command:
   ```bash
   python -m src.main tutorial/report.yaml --output tutorial/my_report.docx
   ```

### Done!
Your report is now ready in the `tutorial/my_report.docx` file. You can open it and add your screenshots to the image placeholders.
