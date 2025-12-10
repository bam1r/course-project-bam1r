from app.main import _DB, _has_active_checkout
from app.models.checkout import CheckoutStatus, can_transition


class TestCheckoutLogic:
    """Тесты бизнес-логики аренд"""

    def test_can_transition_new_checkout(self):
        """Новая аренда может быть только active"""
        assert can_transition(None, CheckoutStatus.active)
        assert not can_transition(None, CheckoutStatus.returned)
        assert not can_transition(None, CheckoutStatus.overdue)

    def test_can_transition_active(self):
        """Из active можно перейти в returned или overdue"""
        assert can_transition(CheckoutStatus.active, CheckoutStatus.returned)
        assert can_transition(CheckoutStatus.active, CheckoutStatus.overdue)
        assert not can_transition(CheckoutStatus.active, CheckoutStatus.active)

    def test_can_transition_overdue(self):
        """Из overdue можно перейти только в returned"""
        assert can_transition(CheckoutStatus.overdue, CheckoutStatus.returned)
        assert not can_transition(CheckoutStatus.overdue, CheckoutStatus.active)
        assert not can_transition(CheckoutStatus.overdue, CheckoutStatus.overdue)

    def test_can_transition_returned(self):
        """Returned - финальный статус, нельзя никуда перейти"""
        assert not can_transition(CheckoutStatus.returned, CheckoutStatus.active)
        assert not can_transition(CheckoutStatus.returned, CheckoutStatus.returned)
        assert not can_transition(CheckoutStatus.returned, CheckoutStatus.overdue)


class TestHelperFunctions:
    """Тесты вспомогательных функций"""

    def test_has_active_checkout_empty(self):
        """Проверка на пустом списке аренд"""
        _DB["checkouts"] = []
        assert not _has_active_checkout(1)

    def test_has_active_checkout_active(self):
        """Проверка при активной аренде"""
        _DB["checkouts"] = [
            {"asset_id": 1, "status": "active"},
            {"asset_id": 2, "status": "returned"},
        ]

        assert _has_active_checkout(1)
        assert not _has_active_checkout(2)

    def test_has_active_checkout_overdue(self):
        """Проверка при просроченной аренде"""
        _DB["checkouts"] = [{"asset_id": 1, "status": "overdue"}]
        assert _has_active_checkout(1)
