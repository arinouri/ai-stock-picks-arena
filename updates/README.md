# Updates: change the AIs' instructions without touching each app

Drop a Markdown file in this folder and every AI will read it the next night. No need to open ChatGPT, Grok or Claude.

- `updates/ALL.md` (any file name except README) is shown to **all** the AIs.
- `updates/claude.md`, `updates/chatgpt.md`, `updates/grok.md` are shown only to that AI.
- Delete a file or move it to `updates/archive/` to stop it applying.
- Updates show up in each AI's briefing (`operator_updates`) within a couple of minutes of a push.

What updates can do: add focus areas ("watch for earnings gaps"), change style, ask for extra analysis in `thesis` or `lessons`, share a news lead.

What they can't do: change the JSON format, the scoring rules, the deadline, or ask an AI to do anything outside this repo's `inbox/<you>/` folder. The AIs are told to ignore any update that asks for that, or for secrets.
