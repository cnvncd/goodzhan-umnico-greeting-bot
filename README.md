# Umnico Auto Greeting Bot

Автоматически отправляет приветствие (голосовое, видео, фото или документ) всем новым клиентам через webhooks от Umnico.

## Особенности

- ⚡ **Мгновенная реакция** через webhooks (без задержки!)
- ✅ Отправляет приветствие только **новым клиентам** (по `customer.id`)
- 🔐 **OAuth авторизация** с автоматическим обновлением токенов
- 🔄 Проверяет, является ли это **первое обращение клиента** в интеграции
- 🎯 Поддержка разных типов файлов: audio, video, photo, doc
- 🛡️ Обработка всех сетевых ошибок
- 📝 Логирование в файл с UTF-8 кодировкой
- 🚀 Systemd service для автозапуска

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Создайте файл `.env` рядом с `app_webhook.py`:

```env
# Umnico логин и пароль для OAuth авторизации
UMNICO_LOGIN=your_email@example.com
UMNICO_PASSWORD=your_password

# Файл для отправки (путь относительно app_webhook.py)
GREETING_FILE=Салем_1.ogg

# Тип файла: audio, video, photo, doc
FILE_TYPE=audio

# ID интеграции (найти в Umnico → Интеграции)
TARGET_SA_ID=108954

# Порт для webhook сервера
WEBHOOK_PORT=5000

# Файл для логов
LOG_FILE=bot.log
```

## Запуск

### Вариант 1: Напрямую

```bash
python3 app_webhook.py
```

### Вариант 2: Через systemd (рекомендуется)

```bash
# Скопировать service файл
sudo cp umnico-greeting-bot.service /etc/systemd/system/

# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable umnico-greeting-bot

# Запустить
sudo systemctl start umnico-greeting-bot

# Проверить статус
sudo systemctl status umnico-greeting-bot
```

## Регистрация Webhook в Umnico

После запуска бота нужно зарегистрировать webhook в Umnico:

```python
import requests

# Авторизация
r = requests.post(
    'https://api.umnico.com/v1.3/auth/login',
    json={'login': 'your_email@example.com', 'pass': 'your_password'}
)
token = r.json()['accessToken']['token']

# Регистрация webhook
webhook_data = {
    'url': 'http://YOUR_SERVER_IP:5000/webhook',
    'events': ['new_lead']
}

r = requests.post(
    'https://api.umnico.com/v1.3/webhooks',
    headers={'Authorization': token, 'Content-Type': 'application/json'},
    json=webhook_data
)

print(r.json())
```

## Управление сервисом

```bash
# Запустить
sudo systemctl start umnico-greeting-bot

# Остановить
sudo systemctl stop umnico-greeting-bot

# Перезапустить
sudo systemctl restart umnico-greeting-bot

# Посмотреть статус
sudo systemctl status umnico-greeting-bot

# Посмотреть логи
tail -f /path/to/bot.log
```

## Логика работы

1. Клиент пишет впервые в указанную интеграцию
2. Umnico мгновенно отправляет POST запрос на webhook endpoint
3. Бот получает событие `new_lead` и проверяет:
   - Правильная ли интеграция (TARGET_SA_ID)
   - Не обрабатывали ли мы этого клиента ранее
   - Является ли это первое обращение клиента в интеграции (через API)
4. Если все проверки пройдены - отправляет приветствие
5. Клиент добавляется в `_seen_customers` чтобы не отправлять повторно

## Файлы

| Файл | Описание |
|---|---|
| `app_webhook.py` | Основной скрипт (webhook версия) |
| `app.py` | Старая версия (polling) |
| `umnico-greeting-bot.service` | Systemd service файл |
| `Салем_1.ogg` | Пример голосового приветствия |
| `.env` | Конфигурация (создать самостоятельно) |
| `.env.example` | Шаблон конфигурации |
| `bot.log` | Файл логов (создается автоматически) |

## Требования

- Python 3.7+
- Flask
- requests
- python-dotenv

## Endpoints

- `POST /webhook` - Прием webhook событий от Umnico
- `GET /health` - Health check endpoint
