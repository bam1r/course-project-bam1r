# ADR-002: Input Validation and Normalization

- **Status**: Accepted

## Context
- Текущие модели Pydantic имеют минимальную валидацию (только типы)
- Нет нормализации входных данных (trim, case conversion, whitespace handling)
- Нет проверки длин, форматов, бизнес-правил
- NFR-003 требует валидацию всех входных данных
- STRIDE-T (Tampering) угроза требует защиты от некорректных данных

## Decision
- Добавить строгую валидацию во все модели создания (UserCreate, AssetCreate, CheckoutCreate, EquipmentCreate)
- Реализовать нормализацию данных (trim, case conversion, whitespace collapse)
- Добавить проверки длин через `Field` с `min_length`/`max_length`
- Добавить кастомные валидаторы через `@field_validator` и `@model_validator`
- Использовать UTC для всех datetime значений
- Валидировать бизнес-правила (например, due_at должен быть в будущем для active checkout)

### Детали реализации:

#### User:
- **name**: 1-100 символов, только буквы/цифры/пробелы/дефисы/апострофы/точки, trim и collapse whitespace
- **email**: нормализация (lowercase, trim) через EmailStr
- **password**: 8-128 символов, минимум одна буква и одна цифра

#### Asset:
- **title**: 1-200 символов, trim и collapse whitespace
- **inv_id**: 3-50 символов, только uppercase буквы/цифры/дефисы/подчёркивания, автоматический uppercase

#### Checkout:
- **asset_id**: положительное число (gt=0)
- **due_at**: нормализация к UTC, проверка что для active checkout дата в будущем

#### Equipment:
- **title**: 1-200 символов, trim и collapse whitespace
- **description**: 1-1000 символов, trim и normalize whitespace (сохраняя переносы строк)

## Consequences
- **Плюсы**:
  - Защита от некорректных данных на уровне модели
  - Автоматическая нормализация (меньше проблем с регистром, пробелами)
  - Улучшенная безопасность (валидация паролей, форматов)
  - Соответствие NFR-003
  - Защита от STRIDE-T (Tampering)
- **Минусы**:
  - Дополнительная сложность в моделях
  - Возможные breaking changes для клиентов, которые полагались на отсутствие валидации
  - Небольшое влияние на производительность (валидация выполняется для каждого запроса)
- **Нейтрально**:
  - Все ошибки валидации возвращаются в формате RFC 7807
  - Не требуются изменения БД

## Implementation
- Обновлены все модели создания с валидаторами
- Добавлены `Field` с ограничениями длин
- Реализованы `@field_validator` для нормализации и проверки
- Добавлены `@model_validator` для бизнес-правил
- Созданы comprehensive тесты (`tests/test_validation.py`) - 25+ тестов

## Links
- **NFR**: NFR-003 (Input Validation)
- **Threat Model**: STRIDE-T (Tampering) - валидация предотвращает изменение данных
- **RFC 7807**: Ошибки валидации возвращаются в стандартном формате
