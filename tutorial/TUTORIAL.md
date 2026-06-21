# How to use AI to generate reports

This tutorial shows you how to use the **Markdown MCP Server** to automatically generate DSTU-compliant reports.

## Prerequisites

- Cursor or Claude Desktop installed
- Python 3.10+ with the project dependencies installed
- The reports-formater project cloned locally

## Step 1: Configure MCP Server

### For Cursor Users

1. Open Cursor Settings → Features → MCP
2. Click "Add MCP Server"
3. Configure the Markdown server:
   - **Name**: `reports-formater-markdown`
   - **Command**: `python`
   - **Arguments**: `-m src.mcp_server_markdown`
   - **Working Directory**: `/path/to/reports-formater`
4. Save the configuration

### For Claude Desktop Users

1. Open Claude Desktop settings
2. Navigate to the MCP configuration file
3. Add this configuration:

```json
{
  "mcpServers": {
    "reports-formater-markdown": {
      "command": "python",
      "args": ["-m", "src.mcp_server_markdown"],
      "cwd": "/path/to/reports-formater"
    }
  }
}
```

4. Restart Claude Desktop

## Step 2: Start a New Report Session

1. Open your AI assistant (Cursor or Claude Desktop)
2. The MCP server will automatically connect
3. Tell the AI:
   ```
   Please initialize a new report session for a laboratory work about Python programming.
   ```

The AI will call `init_report` automatically.

## Step 3: Solve Tasks and Generate Content

1. Open the file `tasks.txt` in this folder
2. Copy all 6 tasks
3. Paste them into your AI chat
4. Tell the AI:
   ```
   Please solve these 6 Python tasks and format them as a laboratory report.
   Include:
   - Title page with my name and group
   - Goal (Мета) and Topic (Тема)
   - Solutions with code blocks
   - Screenshots (use placeholders for now)
   - Conclusion (Висновок)
   
   Use the Markdown MCP tools to submit the content.
   ```

The AI will:
- Read `dstu://guidelines` to understand formatting rules
- Generate content in Markdown format
- Call `submit_markdown_chunk` to add content to the session
- Validate everything automatically

## Step 4: Finalize the Report

When the AI finishes adding all content, tell it:
```
Please finalize the report and save it as tutorial/my_report.docx
```

The AI will call `finalize_report` and generate the .docx file.

## Step 5: Review and Add Screenshots

1. Open `tutorial/my_report.docx`
2. Replace image placeholders with actual screenshots
3. Review formatting (everything should be DSTU-compliant)

## Done!

Your report is ready. The entire process was automated through the MCP protocol - no manual YAML editing required.

---

## Alternative: YAML Protocol

If you prefer structured YAML input, you can configure the YAML MCP server instead:

```json
{
  "mcpServers": {
    "reports-formater-yaml": {
      "command": "python",
      "args": ["-m", "src.mcp_server_yaml"],
      "cwd": "/path/to/reports-formater"
    }
  }
}
```

Then use `submit_chunk` instead of `submit_markdown_chunk`.

## Fallback: CLI Mode

If MCP is not available, you can still use the CLI:

1. Generate YAML manually or with AI assistance
2. Save to `report.yaml`
3. Run:
   ```bash
   python -m src.main tutorial/report.yaml --output tutorial/my_report.docx
   ```
