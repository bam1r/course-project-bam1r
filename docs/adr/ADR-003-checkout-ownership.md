# ADR-003: Checkout Ownership & State Machine

- **Status**: Accepted

## Context
- Требование NFR-006 требует строгой валидации статусов checkout и owner-only доступа.
- В исходной реализации checkout не содержал владельца и позволял обновлять статус без ограничений, что нарушало угрозы STRIDE (F7-E/T).

## Decision
- Расширили модель `Checkout`/`CheckoutOut` полем `owner_id`; значение присваивается только на сервере из `CurrentUser`.
- Добавлен state machine (`can_transition`) с разрешёнными переходами (active → returned/overdue, overdue → returned).
- CRUD-эндпойнты для checkout:
  - фильтруют выдачу по владельцу (кроме админа),
  - проверяют `ensure_owner_or_admin` перед чтением/изменением/удалением,
  - отклоняют невалидные переходы с кодом `400 invalid_status_transition`.

## Consequences
- **Плюсы**: предотвращено повышение привилегий и нарушения бизнес-правил; требования NFR-002/NFR-006 и угрозы STRIDE F7 (Tampering/Elevation) закрыты.
- **Минусы**: усложнился in-memory слой и тестовые сценарии; потребуется миграция данных при переходе на реальную БД.

## Links
- **NFR**: NFR-002, NFR-006
- **Threat Model**: STRIDE_TABLE (F7-T/E),
- **Code**: `app/models/checkout.py`, `app/main.py` (раздел Checkouts)
