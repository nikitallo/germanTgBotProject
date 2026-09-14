# germanTgBotProject

Telegram-бот для тренировки немецкой лексики: раз в день присылает новое слово,
раз в день — вопрос на повторение уже показанного слова (нужно написать перевод
в ответ, бот проверяет и говорит, правильно или нет). Работает только для
заранее указанных Telegram User ID.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Настройка

```bash
cp settings.example.json settings.json
```

Заполни `settings.json`:
- `bot_token` — токен бота от [@BotFather](https://t.me/BotFather).
- `allowed_user_ids` — список Telegram User ID, для которых бот будет работать
  (свой ID можно узнать, например, у [@userinfobot](https://t.me/userinfobot)).
- `timezone` — часовой пояс окна рассылки в формате IANA, например
  `Europe/Berlin` или `Europe/Moscow`.
- `send_window` — часы (`start_hour`/`end_hour`), внутри которых раз в день
  случайно выбирается время для нового слова и отдельно — для вопроса на
  повторение.
- `active_languages` — какие языки из словаря использовать (см. ниже).

## Словарь

`data/dictionary.json` не хранится в репозитории — его нужно сгенерировать
скриптом импорта:

```bash
python scripts/import_dictionary.py --url "https://poligloty.blogspot.com/2017/06/1000-nemeckih-slov.html" --lang de
```

Скрипт безопасно перезапускать: уже добавленные слова не дублируются.

### Добавление нового языка (например, английского)

1. Найди страницу-источник со словами и запусти импорт с другим кодом языка:
   ```bash
   python scripts/import_dictionary.py --url "<ссылка на источник>" --lang en
   ```
   Скрипт ожидает страницы вида Blogspot (`div.post-body.entry-content`) со
   строками `термин - перевод`; для источника с другой разметкой потребуется
   доработать `fetch_lines()` в `scripts/import_dictionary.py`.
2. Добавь `"en"` в `active_languages` в `settings.json`.

Код бота никаких изменений не требует — слова из всех языков, перечисленных в
`active_languages`, участвуют в рассылке и повторении на равных.

## Запуск

```bash
python -m bot.main
```

## Деплой на VPS как systemd-сервис

1. Скопируй проект на сервер, установи зависимости и настрой `settings.json` и
   словарь так же, как описано выше.
2. Отредактируй `deploy/germantgbot.service`, заменив
   `REPLACE_WITH_YOUR_LINUX_USER` и `REPLACE_WITH_REPO_PATH` на реальные
   значения.
3. Установи и включи сервис:
   ```bash
   sudo cp deploy/germantgbot.service /etc/systemd/system/germantgbot.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now germantgbot
   ```
4. Проверить статус и логи:
   ```bash
   systemctl status germantgbot
   journalctl -u germantgbot -f
   ```

## Структура проекта

```
bot/                 # код бота
  config.py           # загрузка settings.json
  dictionary.py        # загрузка словаря
  state.py              # хранение прогресса пользователей (data/state.json)
  quiz.py                # выбор слов и проверка ответа
  scheduler.py             # ежедневное случайное расписание рассылки
  handlers.py               # команды и обработка сообщений, контроль доступа
  main.py                    # точка входа
scripts/
  import_dictionary.py  # импорт словаря из внешнего источника
deploy/
  germantgbot.service    # шаблон systemd-юнита
data/                     # dictionary.json и state.json — не в репозитории
```
