# ADR-001: Header-Derived Auth Context

- **Status**: Accepted

## Context
- MVP не содержит полноценного AuthN сервиса, но NFR-001/NFR-002 требуют, чтобы каждый защищённый запрос имел контекст пользователя и роли.
- В модели угроз (STRIDE F1-S) подмена пользователя и обход owner-only считаются критичными.
- Нужно быстро получить проверяемый контур безопасности, чтобы тесты могли симулировать разные роли.

## Decision
- Ввели лёгкий слой `app/security.py`, который извлекает `X-User-Id` и `X-User-Role` из заголовков и превращает их в `CurrentUser`.
- Все CRUD-эндпойнты (кроме `/health`) требуют `Depends(get_current_user)`; операции, требующие прав администратора, вызывают `require_admin`.
- Ошибки аутентификации/авторизации нормализуются в единый JSON-формат, что облегчает проверку и логирование.

## Consequences
- **Плюсы**: Быстрое покрытие требований AuthN/AuthZ, возможность писать тесты без реального Identity-провайдера, соответствие NFR-001/002 и STRIDE угрозам F1/F4.
- **Минусы**: Заголовки легко подделать, поэтому решение подходит только для dev/test окружений; для production потребуется полноценный JWT/OPA слой (см. follow-up tasks в NFR_TRACEABILITY).

## Links
- **NFR**: NFR-001, NFR-002 (`docs/security-nfr/NFR.md`)
- **Threat Model**: STRIDE_TABLE (потоки F1/F4)
- **Code**: `app/security.py`, `app/main.py` (все эндпойнты c `Depends(get_current_user)`)
