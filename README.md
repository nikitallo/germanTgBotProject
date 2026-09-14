# germanTgBotProject

A Telegram bot for drilling German vocabulary: once a day it sends a new word,
and once a day it quizzes you on a word you've already seen (reply with the
translation and the bot tells you if you got it right). It only responds to a
predefined list of Telegram user IDs.

## Get the code

```bash
git clone https://github.com/nikitallo/germanTgBotProject.git
cd germanTgBotProject
```

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

`settings.json` is gitignored — it holds your bot token and user IDs and is
never committed or pulled from the repo.

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

## Bot commands

- `/word` — get a new word right now (also counts as introduced, same as the
  automatic daily send).
- `/check` — get a review quiz right now, picked from words you've already
  seen; reply with the translation to have it graded. If you haven't been
  sent any words yet, the bot tells you so instead of asking a question.
- `/stat` — your progress: how many words have been sent out of the total
  dictionary size, how many remain, and your quiz answer tally.
- `/help` — lists all commands and explains the daily flow.
- `/start` — greets you and confirms the bot can see you.

## Running

```bash
python -m bot.main
```

## Deploying on a VPS as a systemd service

1. On the server: install prerequisites, clone the repo, and follow **Setup**,
   **Configuration**, and **Dictionary** above.
   ```bash
   sudo apt update && sudo apt install -y git python3-venv python3-pip
   git clone https://github.com/nikitallo/germanTgBotProject.git
   cd germanTgBotProject
   ```
2. Edit `deploy/germantgbot.service`, replacing `REPLACE_WITH_YOUR_LINUX_USER`
   and `REPLACE_WITH_REPO_PATH` with real values (or generate it in one go):
   ```bash
   sed -e "s#REPLACE_WITH_YOUR_LINUX_USER#$(whoami)#g" \
       -e "s#REPLACE_WITH_REPO_PATH#$(pwd)#g" \
       deploy/germantgbot.service | sudo tee /etc/systemd/system/germantgbot.service
   ```
3. Install and enable the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now germantgbot
   ```
4. Check status and logs:
   ```bash
   systemctl status germantgbot
   journalctl -u germantgbot -f
   ```

### Updating after a fix

`settings.json`, `data/dictionary.json`, and `data/state.json` are gitignored,
so pulling never touches your token, dictionary, or progress:

```bash
cd germanTgBotProject
git pull
sudo systemctl restart germantgbot
```

## Project layout

```
bot/                 # bot source code
  config.py           # settings.json loader
  dictionary.py        # dictionary loader
  state.py              # per-user progress storage (data/state.json)
  quiz.py                # word selection and answer checking
  scheduler.py             # daily random send schedule + on-demand replies
  handlers.py               # commands, message handling, access control
  main.py                    # entry point
scripts/
  import_dictionary.py  # dictionary import from an external source
deploy/
  germantgbot.service    # systemd unit template
data/                     # dictionary.json and state.json — not in the repo
```
