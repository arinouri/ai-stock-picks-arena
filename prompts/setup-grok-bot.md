# Grok: Grok Bot routine

Grok Bot runs on xAI's cloud computer, so your Mac can be off.

## One-time setup

1. **Create a GitHub token that can only touch this repo.** Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.
   - Repository access: *Only select repositories* → `ai-stock-picks-arena`.
   - Permissions → Repository permissions → **Contents: Read and write**. Leave everything else as no access.
   - Expiration: 1 year. Copy the token.
2. **Give the token to Grok Bot** in its credentials/secrets settings as `GITHUB_TOKEN`. If Grok Bot has a built-in GitHub connector you can use that instead. Never paste the token into a chat message or a prompt.
3. **Create a routine** scheduled for **8:45 PM Eastern, Sunday to Thursday**, with the prompt below.

## Routine prompt

Paste the nightly prompt with `{NAME}` = Grok and `{KEY}` = grok, then add this:

---

**How to upload (Grok Bot).** In your terminal, clone the repo with the stored token:

```
git clone https://x-access-token:$GITHUB_TOKEN@github.com/arinouri/ai-stock-picks-arena.git arena
cd arena
```

(If it's already cloned, run `cd arena && git pull`.) Read `brief/grok.json`.

Write your file to `inbox/grok/<tonight's date>.json`, then run:

```
git config user.name "Grok Bot"
git config user.email "grok-bot@users.noreply.github.com"
git add inbox/grok && git commit -m "Grok picks <date>" && git pull --rebase && git push
```

Wait about 3 minutes, `git pull`, and check `brief/grok.json` → `your_last_upload`. Fix and push again if needed.

Use X search as well as web search for sentiment and breaking news, but confirm anything you act on with a real news source.
