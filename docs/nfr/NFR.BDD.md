## NFR-002: Авторизация по ролям

```gherkin
Feature: Авторизация по ролям

  Scenario: Студент не может изменять чужой checkout
    Given система Equipment Checkout запущена
    And существует пользователь "student1@example.com" с ролью "student"
    And существует пользователь "student2@example.com" с ролью "student"
    And checkout с ID 1 принадлежит "student1@example.com"
    And "student2@example.com" аутентифицирован
    When "student2@example.com" отправляет PUT запрос на "/checkouts/1"
    Then ответ имеет статус код 403
    And в ответе содержится ошибка "forbidden: owner_only"

  Scenario: Администратор может изменять любой checkout
    Given система Equipment Checkout запущена
    And существует пользователь "admin@example.com" с ролью "admin"
    And существует checkout с ID 1
    And "admin@example.com" аутентифицирован
    When "admin@example.com" отправляет PUT запрос на "/checkouts/1"
    Then ответ имеет статус код 200
```

## NFR-003: Валидация входных данных

```gherkin
Feature: Валидация входных данных

  Scenario: Создание asset с невалидными данными отклоняется
    Given система Equipment Checkout запущена
    And пользователь аутентифицирован
    When пользователь отправляет POST запрос на "/assets" с телом:
      """
      {
        "title": "",
        "inv_id": null
      }
      """
    Then ответ имеет статус код 422
    And в ответе содержится информация о полях с ошибками валидации
    And поле "title" имеет ошибку "field required" или "string too short"
    And поле "inv_id" имеет ошибку "field required"

  Scenario: Создание checkout с несуществующим asset_id отклоняется
    Given система Equipment Checkout запущена
    And пользователь аутентифицирован
    And asset с ID 999 не существует
    When пользователь отправляет POST запрос на "/checkouts" с телом:
      """
      {
        "asset_id": 999,
        "due_at": "2025-12-31T23:59:59Z"
      }
      """
    Then ответ имеет статус код 404
    And в ответе содержится ошибка "Asset not found"
```

## NFR-006: Валидация статуса checkout

```gherkin
Feature: Валидация статуса checkout

  Scenario: Статус checkout может изменяться только по правилам
    Given система Equipment Checkout запущена
    And существует checkout с ID 1 и статусом "returned"
    And пользователь аутентифицирован
    When пользователь пытается изменить статус на "active"
    Then запрос отклоняется с кодом 400
    And в ответе содержится ошибка "invalid_status_transition"
    And статус checkout остаётся "returned"

  Scenario: Валидный переход статуса выполняется успешно
    Given система Equipment Checkout запущена
    And существует checkout с ID 1 и статусом "active"
    And дата возврата "due_at" прошла
    And пользователь аутентифицирован
    When пользователь изменяет статус на "returned"
    Then ответ имеет статус код 200
    And статус checkout обновлён на "returned"
```
