# germanTgBotProject

A Telegram bot for drilling German vocabulary: once a day it sends a new word,
and once a day it quizzes you on a word you've already seen (reply with the
translation and the bot tells you if you got it right). It only responds to a
predefined list of Telegram user IDs.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

```bash
cp settings.example.json settings.json
```

Fill in `settings.json`:
- `bot_token` — bot token from [@BotFather](https://t.me/BotFather).
- `allowed_user_ids` — list of Telegram user IDs the bot will respond to (you
  can find your own ID via [@userinfobot](https://t.me/userinfobot)).
- `timezone` — IANA timezone name for the send window, e.g. `Europe/Berlin` or
  `Europe/Moscow`.
- `send_window` — hours (`start_hour`/`end_hour`) within which a random time
  is picked each day for the new word, and separately for the review quiz.
- `active_languages` — which dictionary languages to use (see below).

## Dictionary

`data/dictionary.json` isn't stored in the repo — generate it with the import
script:

```bash
python scripts/import_dictionary.py --url "https://poligloty.blogspot.com/2017/06/1000-nemeckih-slov.html" --lang de
```

The script is safe to rerun: already-added words are never duplicated.

### Adding a new language (e.g. English)

1. Find a source page with word lists and run the importer with a different
   language code:
   ```bash
   python scripts/import_dictionary.py --url "<source URL>" --lang en
   ```
   The script expects a Blogspot-style page (`div.post-body.entry-content`)
   with lines like `term - translation`; a source with different markup will
   need a small tweak to `fetch_lines()` in `scripts/import_dictionary.py`.
2. Add `"en"` to `active_languages` in `settings.json`.

No bot code changes are needed — words from every language listed in
`active_languages` are used equally for new-word sends and reviews.

## Running

```bash
python -m bot.main
```

## Deploying on a VPS as a systemd service

1. Copy the project to the server, install dependencies, and set up
   `settings.json` and the dictionary as described above.
2. Edit `deploy/germantgbot.service`, replacing `REPLACE_WITH_YOUR_LINUX_USER`
   and `REPLACE_WITH_REPO_PATH` with real values.
3. Install and enable the service:
   ```bash
   sudo cp deploy/germantgbot.service /etc/systemd/system/germantgbot.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now germantgbot
   ```
4. Check status and logs:
   ```bash
   systemctl status germantgbot
   journalctl -u germantgbot -f
   ```

## Project layout

```
bot/                 # bot source code
  config.py           # settings.json loader
  dictionary.py        # dictionary loader
  state.py              # per-user progress storage (data/state.json)
  quiz.py                # word selection and answer checking
  scheduler.py             # daily random send schedule
  handlers.py               # commands, message handling, access control
  main.py                    # entry point
scripts/
  import_dictionary.py  # dictionary import from an external source
deploy/
  germantgbot.service    # systemd unit template
data/                     # dictionary.json and state.json — not in the repo
```
