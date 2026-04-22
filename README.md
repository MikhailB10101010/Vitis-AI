# Vitis-AI — Система оценки пригодности земель для виноделия

## 🍇 О проекте

Vitis-AI — это ML-система для агроклиматического зонирования и выявления перспективных территорий под посадку виноградников на Юге России.

### Команда проекта
- Бакилин Михаил
- Саттаров Артем
- Хакимзянов Илья
- Елькин Лев
- Комаров Сергей

**Заказчик:** Сбербанк России, ПАО (филиал Уральский банк)

---

## 🏗️ Архитектура системы

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  Node.js Backend │────▶│   MongoDB       │
│   (Frontend)    │◀────│  (Express API)   │◀────│   (GeoJSON)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │  External APIs   │
                    │ - ERA5 (climate) │
                    │ - SRTM (relief)  │
                    │ - SoilGrids      │
                    │ - Sentinel-2     │
                    └──────────────────┘
```

---

## 🚀 Быстрый старт

### Предварительные требования

- Node.js >= 18.x
- Python >= 3.9
- MongoDB >= 6.0

### 1. Установка зависимостей

#### Backend (Node.js)
```bash
npm install
```

#### Frontend (Python/Streamlit)
```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

Скопируйте файл `.env.example` в `.env` и настройте переменные:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
PORT=3000
NODE_ENV=development

# MongoDB
MONGODB_URI=mongodb://localhost:27017/vitis-ai

# JWT Secret (обязательно измените для production!)
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRE=24h

# API Keys (добавьте ваши ключи)
GEE_API_KEY=your-google-earth-engine-api-key
```

### 3. Запуск MongoDB

```bash
# macOS (Homebrew)
brew services start mongodb-community

# Linux (systemd)
sudo systemctl start mongod

# Docker
docker run -d -p 27017:27017 --name vitis-mongo mongo:latest
```

### 4. Запуск Backend

```bash
npm start
```

Сервер запустится на `http://localhost:3000`

### 5. Запуск Frontend (Streamlit)

```bash
cd streamlit_app
streamlit run app.py
```

Интерфейс откроется на `http://localhost:8501`

---

## 📁 Структура проекта

```
/workspace
├── server.js                 # Основной сервер Node.js
├── package.json              # Зависимости Node.js
├── .env.example              # Шаблон переменных окружения
│
├── models/                   # MongoDB модели
│   ├── User.js               # Модель пользователя
│   └── Evaluation.js         # Модель оценки участка
│
├── routes/                   # API маршруты
│   ├── auth.js               # Аутентификация
│   ├── evaluation.js         # Оценка участков
│   └── users.js              # Профиль пользователя
│
├── middleware/               # Express middleware
│   ├── auth.js               # JWT аутентификация
│   └── errorHandler.js       # Обработка ошибок
│
├── streamlit_app/            # Streamlit интерфейс
│   └── app.py                # Основное приложение
│
├── docs/                     # Документация
│   ├── Vitis AI ТЗ 1.0.docx  # Техническое задание
│   └── just thinking.docx    # Исследовательские заметки
│
└── data/                     # Данные
    ├── vineyards Oliver Dressler/
    └── vineyard_OSM/
```

---

## 🔑 API Endpoints

### Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/auth/register` | Регистрация нового пользователя |
| POST | `/api/auth/login` | Вход в систему |
| GET | `/api/auth/me` | Получить текущий профиль |

### Оценка участков

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/evaluate` | Оценить пригодность участка |
| GET | `/api/evaluate/:id` | Получить результаты по ID |
| GET | `/api/evaluate/geojson` | Экспорт в GeoJSON |

### Пользователь

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/user/history` | История оценок |
| GET | `/api/user/profile` | Профиль пользователя |
| PUT | `/api/user/profile` | Обновить профиль |
| DELETE | `/api/user/evaluation/:id` | Удалить оценку |

---

## 📊 Пример запроса на оценку

```bash
curl -X POST http://localhost:3000/api/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "latitude": 45.0456,
    "longitude": 38.9765,
    "region": "Краснодарский край"
  }'
```

### Пример ответа

```json
{
  "success": true,
  "message": "Evaluation completed",
  "cached": false,
  "processing_time_ms": 1250,
  "data": {
    "_id": "...",
    "location": {
      "type": "Point",
      "coordinates": [38.9765, 45.0456]
    },
    "prediction": {
      "suitability_score": 78,
      "category": "high",
      "confidence": "high"
    },
    "recommendations": {
      "suitable_varieties": ["Саперави", "Красностоп", "Ркацители"],
      "planting_advice": "Отличные условия для коммерческого виноградарства"
    }
  }
}
```

---

## 🔧 Функциональные возможности

### Для пользователей (FR-001 — FR-034)

- ✅ Базовая аутентификация (логин/пароль)
- ✅ Две роли: Пользователь и Администратор
- ✅ Ввод координат участка вручную
- ✅ Отображение маркера на карте
- ✅ Получение данных рельефа (SRTM)
- ✅ Получение климатических данных (ERA5)
- ✅ Получение спутниковых данных (Sentinel-2)
- ✅ Расчет производных признаков (GDD, TPI, инсоляция)
- ✅ Предсказание вероятности пригодности (CatBoost)
- ✅ SHAP интерпретация предсказаний
- ✅ Интерактивная карта (Folium)
- ✅ Цветовая индикация результатов
- ✅ Генерация PDF-отчетов
- ✅ Подбор сортов винограда
- ✅ Кэширование запросов (TTL 24 часа)
- ✅ История оценок пользователя

---

## 🗄️ MongoDB Schema

### Collection: users

```javascript
{
  _id: ObjectId,
  username: String (unique),
  email: String (unique),
  password: String (hashed),
  role: String ('user' | 'admin'),
  fullName: String,
  organization: String,
  isActive: Boolean,
  evaluationCount: Number,
  createdAt: Date,
  updatedAt: Date
}
```

### Collection: evaluations

```javascript
{
  _id: ObjectId,
  user: ObjectId (ref: 'users'),
  location: {
    type: String ('Point' | 'Polygon'),
    coordinates: [Number]
  },
  features: {
    climate: { /* климатические данные */ },
    relief: { /* данные рельефа */ },
    soil: { /* данные почвы */ },
    satellite: { /* спутниковые данные */ }
  },
  prediction: {
    suitability_score: Number (0-100),
    category: String ('low' | 'medium' | 'high'),
    confidence: String,
    model_version: String
  },
  shap_values: [{
    feature_name: String,
    value: Number,
    impact: String
  }],
  recommendations: {
    suitable_varieties: [String],
    planting_advice: String
  },
  cached: Boolean,
  cache_expiry: Date,
  createdAt: Date,
  updatedAt: Date
}
```

**Geospatial Index:** `2dsphere` на поле `location`

---

## 🔒 Безопасность

- JWT токены для аутентификации
- Хеширование паролей (bcrypt)
- Rate limiting (100 запросов / 15 мин)
- Helmet.js для security headers
- HTTPS (требуется в production)
- Audit logging действий пользователей

---

## 📈 Производительность

- Время оценки одного участка: < 30 секунд
- Поддержка до 50 одновременных пользователей
- Кэширование запросов к внешним API (TTL 24 часа)
- Geospatial индексы для быстрых запросов

---

## 🛠️ Разработка

### Запуск в режиме разработки

```bash
# Backend с auto-reload
npm run dev

# Frontend
streamlit run streamlit_app/app.py
```

### Добавление новых источников данных

1. Создайте сервис в `utils/` (например, `geeService.js`)
2. Реализуйте методы получения данных
3. Интегрируйте в `routes/evaluation.js`

### Обучение ML модели

```python
# Пример обучения CatBoost модели
from catboost import CatBoostClassifier

model = CatBoostClassifier(
    iterations=1000,
    depth=6,
    learning_rate=0.1,
    loss_function='Logloss',
    verbose=True
)

model.fit(X_train, y_train)
model.save_model('model/catboost_model.pkl')
```

---

## 📝 Лицензия

Проект разработан в рамках проектного практикума УрФУ для Сбербанка России.

---

## 📞 Контакты

- **Техническая поддержка:** vitis-ai-support@example.com
- **Документация:** `/docs`
