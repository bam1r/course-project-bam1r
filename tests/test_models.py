from app.main import _has_active_checkout
from app.models.checkout import CheckoutStatus, can_transition
from app.main import _DB


class TestCheckoutLogic:
    """Тесты бизнес-логики аренд"""

    def test_can_transition_new_checkout(self):
        """Новая аренда может быть только active"""
        assert can_transition(None, CheckoutStatus.active) == True
        assert can_transition(None, CheckoutStatus.returned) == False
        assert can_transition(None, CheckoutStatus.overdue) == False

    def test_can_transition_active(self):
        """Из active можно перейти в returned или overdue"""
        assert can_transition(CheckoutStatus.active, CheckoutStatus.returned) == True
        assert can_transition(CheckoutStatus.active, CheckoutStatus.overdue) == True
        assert can_transition(CheckoutStatus.active, CheckoutStatus.active) == False

    def test_can_transition_overdue(self):
        """Из overdue можно перейти только в returned"""
        assert can_transition(CheckoutStatus.overdue, CheckoutStatus.returned) == True
        assert can_transition(CheckoutStatus.overdue, CheckoutStatus.active) == False
        assert can_transition(CheckoutStatus.overdue, CheckoutStatus.overdue) == False

    def test_can_transition_returned(self):
        """Returned - финальный статус, нельзя никуда перейти"""
        assert can_transition(CheckoutStatus.returned, CheckoutStatus.active) == False
        assert can_transition(CheckoutStatus.returned, CheckoutStatus.returned) == False
        assert can_transition(CheckoutStatus.returned, CheckoutStatus.overdue) == False


class TestHelperFunctions:
    """Тесты вспомогательных функций"""

    def test_has_active_checkout_empty(self):
        """Проверка на пустом списке аренд"""
        _DB["checkouts"] = []
        assert _has_active_checkout(1) == False

    def test_has_active_checkout_active(self):
        """Проверка при активной аренде"""
        _DB["checkouts"] = [
            {"asset_id": 1, "status": "active"},
            {"asset_id": 2, "status": "returned"}
        ]

        assert _has_active_checkout(1) == True
        assert _has_active_checkout(2) == False

    def test_has_active_checkout_overdue(self):
        """Проверка при просроченной аренде"""
        _DB["checkouts"] = [
            {"asset_id": 1, "status": "overdue"}
        ]
        assert _has_active_checkout(1) == True