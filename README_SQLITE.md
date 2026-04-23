# Vitis-AI Backend (SQLite Version)

Система оценки пригодности земель для виноделия с использованием SQLite вместо MongoDB.

## Особенности

- ✅ **SQLite** - легковесная БД, работает без отдельного сервера
- ✅ **GeoJSON поддержка** - хранение и экспорт геоданных
- ✅ **JWT аутентификация** - безопасный доступ к API
- ✅ **Кэширование** - ускорение повторных запросов
- ✅ **Windows совместимость** - локальный запуск без Linux сервера

## Требования

- Node.js 16+ ([скачать](https://nodejs.org/))
- npm (поставляется с Node.js)

## Установка на Windows

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd vitis-ai-backend
```

### 2. Установка зависимостей

```bash
npm install
```

### 3. Инициализация базы данных

```bash
npm run init-db
```

Это создаст файл базы данных `data/vitis_ai.db`.

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
PORT=3000
NODE_ENV=development
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRE=24h
DATABASE_PATH=./data/vitis_ai.db
FRONTEND_URL=http://localhost:8501
```

### 5. Запуск сервера

**Разработка:**
```bash
npm run dev
```

**Продакшн:**
```bash
npm start
```

Сервер запустится на `http://localhost:3000`

## API Endpoints

### Публичные маршруты

- `GET /` - Информация об API
- `GET /health` - Проверка здоровья сервера
- `POST /api/auth/register` - Регистрация пользователя
- `POST /api/auth/login` - Вход в систему

### Защищенные маршруты (требуется токен)

- `POST /api/evaluate` - Оценить участок
- `GET /api/evaluate/:id` - Получить оценку по ID
- `GET /api/evaluate/geojson` - Экспорт в GeoJSON
- `GET /api/user/history` - История оценок
- `GET /api/user/profile` - Профиль пользователя
- `PUT /api/user/profile` - Обновить профиль
- `DELETE /api/user/evaluation/:id` - Удалить оценку

## Примеры запросов

### Регистрация

```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"pass123\"}"
```

### Вход

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"pass123\"}"
```

### Оценка участка

```bash
curl -X POST http://localhost:3000/api/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"latitude\":45.0456,\"longitude\":38.9765,\"region\":\"Краснодарский край\"}"
```

### Экспорт в GeoJSON

```bash
curl -X GET http://localhost:3000/api/evaluate/geojson \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Структура проекта

```
vitis-ai-backend/
├── data/                    # База данных SQLite
│   └── vitis_ai.db
├── middleware/              # Express middleware
│   ├── auth.js
│   └── errorHandler.js
├── models/                  # Модели данных
│   ├── Evaluation.js
│   └── User.js
├── routes/                  # API маршруты
│   ├── auth.js
│   ├── evaluation.js
│   └── users.js
├── utils/                   # Утилиты
│   ├── database.js         # Обертка для SQLite
│   ├── init-db.js          # Скрипт инициализации БД
│   └── ee_wrapper.py       # Python wrapper для Google Earth Engine
├── .env                     # Переменные окружения
├── package.json
├── server.js               # Точка входа
└── README.md
```

## Модель данных

### Таблица users

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Первичный ключ |
| username | TEXT | Уникальное имя |
| email | TEXT | Уникальный email |
| password | TEXT | Хэш пароля |
| role | TEXT | Роль (user/admin) |
| full_name | TEXT | Полное имя |
| organization | TEXT | Организация |
| is_active | BOOLEAN | Активен ли аккаунт |
| evaluation_count | INTEGER | Количество оценок |

### Таблица evaluations

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Первичный ключ |
| user_id | INTEGER | Внешний ключ на users |
| location_type | TEXT | Point или Polygon |
| location_coords | TEXT | JSON координат |
| region | TEXT | Регион |
| suitability_score | REAL | Оценка пригодности (0-100) |
| category | TEXT | low/medium/high |
| features.* | REAL/TEXT | Признаки (климат, почва, рельеф) |
| shap_values | TEXT | JSON SHAP значений |
| risks | TEXT | JSON рисков |
| recommendations | TEXT | JSON рекомендаций |

## Работа с GeoJSON

База данных хранит координаты в JSON формате, что позволяет:
- Сохранять точки и полигоны
- Экспортировать данные в стандартном GeoJSON формате
- Интегрироваться с GIS системами

Пример экспорта:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [38.9765, 45.0456]
      },
      "properties": {
        "id": 1,
        "suitability_score": 75.5,
        "category": "high",
        "region": "Краснодарский край"
      }
    }
  ]
}
```

## Отличия от MongoDB версии

| MongoDB версия | SQLite версия |
|----------------|---------------|
| Требуется установка MongoDB Server | Не требуется внешний сервер БД |
| Mongoose ODM | better-sqlite3 + кастомные модели |
| $near для гео-запросов | Индексы по latitude/longitude |
| Поддержка репликации | Один файл БД |
| Ресурсоемкая | Легковесная |

## Решение проблем

### Ошибка при установке better-sqlite3

На Windows может потребоваться установить build tools:

```bash
npm install --global windows-build-tools
npm install
```

Или вручную установить Visual Studio Build Tools.

### Ошибка "Database locked"

Закройте все подключения к базе данных и перезапустите сервер.

### Порт уже занят

Измените PORT в файле `.env`:
```env
PORT=3001
```

## Лицензия

MIT
