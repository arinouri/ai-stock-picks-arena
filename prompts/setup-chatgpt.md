# ChatGPT: Codex app automation (on your Mac)

ChatGPT's own scheduled Tasks can't write files or push to GitHub; they only send a notification. So ChatGPT uses the Codex app, signed in with your ChatGPT account, which counts against your ChatGPT plan.

Codex automations run from your Mac, so the Mac needs to be awake around 8:45 PM.

## One-time setup

1. **Clone the repo somewhere Codex can work**, e.g. `~/Documents/GitHub/ai-stock-picks-arena`:
   - With GitHub Desktop: *File → Clone repository → arinouri/ai-stock-picks-arena*.
   - Or in Terminal: `git clone https://github.com/arinouri/ai-stock-picks-arena.git ~/Documents/GitHub/ai-stock-picks-arena`
2. **Make sure `git push` works from that folder** without a password prompt. GitHub Desktop or `gh auth login` sets this up.
3. **In the Codex app:**
   - Open that folder as the project.
   - Sign in with ChatGPT.
   - Turn on **web search**.
   - Allow network access for commands, so `git push` works.
4. **Create an automation** scheduled for **8:45 PM, Sunday to Thursday**, with the prompt below.
5. *(Optional)* Keep the Mac awake for it. Leave it plugged in with the lid open, or wake it on a schedule from Terminal: `sudo pmset repeat wakeorpoweron MTWRFSU 20:40:00`.

## Automation prompt

Paste the nightly prompt with `{NAME}` = ChatGPT and `{KEY}` = chatgpt, then add this:

---

**How to upload (Codex).** You are in a local clone of arinouri/ai-stock-picks-arena.

1. Run `git pull --rebase` and read `brief/chatgpt.json`.
2. Use web search for all research.
3. Write your file to `inbox/chatgpt/<tonight's date>.json` and check it with `python3 -m arena.schema inbox/chatgpt/<date>.json` (no installs needed). It lists any problems; fix them before uploading.
4. Run:
   ```
   git add inbox/chatgpt && git commit -m "ChatGPT picks <date>" && git pull --rebase && git push
   ```
5. Wait about 3 minutes, `git pull`, and check `brief/chatgpt.json` → `your_last_upload`. Fix and push again if needed.

Don't change any other files.

## If your Mac is often asleep at 8:45 PM

Grok Bot can act as ChatGPT's courier instead: a second Grok Bot routine opens chatgpt.com in its browser, pastes the nightly prompt for ChatGPT, copies the JSON answer word for word into `inbox/chatgpt/<date>.json`, and pushes it.

It works with your Mac off, but it depends on Grok Bot staying signed in to ChatGPT. Every raw upload is published on the site, so you can spot-check that nothing was changed.
