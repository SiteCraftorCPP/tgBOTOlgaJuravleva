# SCN Bot (Telegram)

Бот для чата: начисление/списание SCN коинов админами, рейтинг участников, отложенная рассылка по МСК.

## Быстрый старт (локально)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate
pip install -r requirements.txt
# Создайте .env из .env.example при необходимости
python bot.py
```

## Пуш в GitHub и загрузка на VPS

### 1. Пуш в репозиторий (с локальной машины)

Из папки проекта:

```bash
git init
git add .
git commit -m "SCN Bot: конфиг, два админа, рассылка дата+время"
git branch -M main
git remote add origin https://github.com/SiteCraftorCPP/tgBOTOlgaJuravleva.git
git push -u origin main
```

Если репо уже есть и в нём есть файлы:

```bash
git remote add origin https://github.com/SiteCraftorCPP/tgBOTOlgaJuravleva.git
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### 2. Загрузка и запуск на VPS (не трогая другие проекты)

Подключитесь по SSH. Все команды выполняются в **отдельной папке** только для этого бота.

```bash
# Перейти в домашнюю директорию (или туда, где у вас лежат проекты)
cd ~

# Отдельная папка только для этого бота — другие проекты не затрагиваются
mkdir -p bots
cd bots
git clone https://github.com/SiteCraftorCPP/tgBOTOlgaJuravleva.git
cd tgBOTOlgaJuravleva
```

Создать виртуальное окружение и зависимости **внутри этой папки**:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Создать `.env` с реальными данными (токен уже в коде по умолчанию, но лучше хранить в .env):

```bash
nano .env
```

Содержимое (при необходимости поправьте):

```
BOT_TOKEN=8689285232:AAFE_tjFWwtTEmvPrfgd281y69W-IvOAjUM
CHAT_ID=-1003786647693
ADMIN_IDS=480110890,6933111964
```

Запуск в фоне (через `screen` или `tmux`, чтобы не убивалось при отключении SSH):

```bash
# Вариант 1: screen
screen -S scnbot
source venv/bin/activate
python bot.py
# Отключиться: Ctrl+A, затем D
# Вернуться: screen -r scnbot

# Вариант 2: nohup
nohup venv/bin/python bot.py >> bot.log 2>&1 &
```

Конфиг в репозитории уже настроен на прод: токен, Chat id и два админа (480110890, 6933111964). На VPS достаточно создать `.env` при первом деплое (или положиться на дефолты из `config.py`).

---

## Обновление (команды для обновы)

### Локально: отправить изменения в GitHub

Из папки проекта на своём ПК:

```bash
cd "C:\Users\MOD PC COMPANY\Desktop\tgBOTOlgaJuravleva"
git add .
git commit -m "описание правок"
git push origin main
```

### На VPS: подтянуть обновления и перезапустить бота

```bash
cd ~/bots/tgBOTOlgaJuravleva
git pull origin main
# Перезапустить бота:
# Если через screen:
screen -r scnbot
# В сессии: Ctrl+C (остановить бота), затем снова:
# source venv/bin/activate
# python bot.py
# Отключиться: Ctrl+A, D

# Если через nohup — найти процесс, убить, запустить заново:
# pkill -f "python bot.py"
# nohup venv/bin/python bot.py >> bot.log 2>&1 &
```
