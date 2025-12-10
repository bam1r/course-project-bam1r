# Equipment checkout

#### Учёт выдачи оборудования

### Основные сущности:

| Сущность | Описание             | Пример                         |
|----------|----------------------|--------------------------------|
| **User** | Пользователь системы | Сотрудник компании             |
| **Asset** | Оборудование         | Проектор, переговорка, ноутбук |
| **Checkout** | Бронирование         | Бронирование проектора         |

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <ссылка на репозиторий>
cd <папка-проекта>
```

### 2. Создание виртуального окружения (рекомендуется)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Запуск сервера
```bash
# Режим разработки
uvicorn app.main:app --reload
```

Сервер будет доступен по адресу: http://localhost:8000

### 5. Документация API
После запуска откройте:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Использование API

### Примеры запросов

#### 1. Создание пользователя
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "string",
    "email": "user@example.com",
    "password": "stringst2",
    "role": "student"
  }'
```

#### 2. Создание оборудования
```bash
curl -X POST "http://localhost:8000/assets" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "string",
    "inv_id": "string"
  }'
```

#### 3. Бронирование оборудования
```bash
curl -X POST "http://localhost:8000/checkouts" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -H "X-User-Role: user" \
  -d '{
    "asset_id": 1,
    "due_at": "2025-12-10T16:30:36.056Z",
    "status": "active"
  }'
```

#### 4. Получение всех активных аренд
```bash
curl -X GET "http://localhost:8000/checkouts" \
  -H "X-User-Id: 1" \
  -H "X-User-Role: admin"
```

## Основные эндпоинты

### Пользователи (`/users`)
- `GET /users` - список всех пользователей
- `GET /users/{id}` - информация о пользователе
- `POST /users` - создание пользователя
- `PUT /users/{id}` - обновление пользователя
- `DELETE /users/{id}` - удаление пользователя

### Активы (`/assets`)
- `GET /assets` - список оборудования
- `GET /assets/{id}` - информация об оборудовании
- `POST /assets` - создание оборудования
- `PUT /assets/{id}` - обновление оборудования
- `DELETE /assets/{id}` - удаление оборудования

### Аренды (`/checkouts`)
- `GET /checkouts` - мои аренды
- `GET /checkouts/{id}` - информация об аренде
- `POST /checkouts` - создание аренды
- `PUT /checkouts/{id}` - обновление аренды
- `DELETE /checkouts/{id}` - удаление аренды

## Роли пользователей

- **user** - обычный пользователь, может:
  - Просматривать свои аренды
  - Создавать новые аренды
  - Просматривать доступное оборудование

- **admin** - администратор, дополнительно может:
  - Управлять пользователями
  - Управлять оборудованием
  - Просматривать все аренды

## Тестирование
Проект включает набор тестов для обеспечения качества кода и правильной работы всех компонентов системы.

### Типы тестов
#### 1. Unit-тесты (tests/test_models.py). Тестирование бизнес-логики и моделей данных

#### 2. Integration-тесты (tests/test_main.py). End-to-end тестирование API эндпоинтов

#### 3. API-тесты. Тестирование через HTTP-запросы с использованием TestClient

## Валидация и ошибки

Система возвращает стандартизированные ошибки:

```json
{
  "error": {
    "code": "not_found",
    "message": "Resource not found",
    "details": {
      "resource_type": "asset",
      "resource_id": 999
    }
  }
}
```

### Основные коды ошибок:
- `400` - Неверный запрос
- `401` - Требуется аутентификация
- `403` - Доступ запрещен
- `404` - Ресурс не найден
- `409` - Конфликт (например, дублирующий email)
- `422` - Ошибка валидации данных
- `500` - Внутренняя ошибка сервера