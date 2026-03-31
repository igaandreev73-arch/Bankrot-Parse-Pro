# Инструкция по выгрузке проекта на GitHub

## Предварительные требования

1. **Установите Git**:
   - Скачайте с [git-scm.com](https://git-scm.com/download/win)
   - Установите с настройками по умолчанию

2. **Создайте аккаунт на GitHub**:
   - Перейдите на [github.com](https://github.com)
   - Зарегистрируйтесь (если ещё нет аккаунта)

## Шаги для выгрузки проекта

### 1. Инициализация локального репозитория

Откройте терминал в папке проекта и выполните:

```bash
# Инициализация Git
git init

# Настройка пользователя
git config user.name "Ваше Имя"
git config user.email "ваш.email@example.com"
```

### 2. Добавление файлов и первый коммит

```bash
# Добавление всех файлов
git add .

# Проверка статуса
git status

# Создание коммита
git commit -m "feat: initial commit - парсер и анализатор лотов"
```

### 3. Создание репозитория на GitHub

1. Войдите в GitHub
2. Нажмите "+" в правом верхнем углу → "New repository"
3. Заполните:
   - Repository name: `bankrot-parser-pro`
   - Description: "Парсер и анализатор данных о банкротствах"
   - Public (рекомендуется)
   - Не добавляйте README, .gitignore или license (они уже есть)

4. Нажмите "Create repository"

### 4. Подключение к удалённому репозиторию

Скопируйте команды из созданного репозитория GitHub и выполните:

```bash
# Добавление удалённого репозитория
git remote add origin https://github.com/ваш-username/bankrot-parser-pro.git

# Проверка подключения
git remote -v
```

### 5. Отправка кода на GitHub

```bash
# Отправка кода
git push -u origin main

# Если ветка называется master:
git push -u origin master
```

## Настройки для работы с API

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
DEEPSEEK_API_KEY=ваш_ключ_глубокого_поиска
DATABASE_PATH=/data/bankrot.db
```

### Настройка секретов на GitHub (для CI/CD)

1. Перейдите в репозиторий на GitHub
2. Settings → Secrets and variables → Actions → New repository secret
3. Добавьте:
   - `DEEPSEEK_API_KEY` - ваш API ключ DeepSeek

## Деплой на Render

### 1. Подготовка файлов

Убедитесь, что в проекте есть:

- `Dockerfile` (создайте при необходимости)
- `render.yaml` (создайте при необходимости)
- `requirements.txt`

### 2. Создание сервиса на Render

1. Перейдите на [render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите репозиторий GitHub
4. Настройки:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python parser.py` (или ваш основной скрипт)
   - Добавьте persistent disk для `/data`

## Автоматизация

Для автоматического деплоя при пуше в GitHub добавьте файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
```

## Устранение проблем

### Ошибка: "git is not recognized"
- Убедитесь, что Git установлен и добавлен в PATH
- Перезапустите терминал

### Ошибка: "Permission denied"
- Проверьте правильность URL репозитория
- Используйте SSH ключи или Personal Access Token

### Ошибка: "API key not found"
- Убедитесь, что файл `.env` создан
- Проверьте, что `.env` добавлен в `.gitignore`