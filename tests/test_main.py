from datetime import datetime, timedelta


class TestHealthEndpoint:
    """Тесты health-check эндпоинта"""

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestUserCRUD:
    """Тесты CRUD операций для пользователей"""

    def test_create_user_as_admin(self, client, admin_headers, test_user_data):
        """Админ может создать пользователя"""
        response = client.post("/users", json=test_user_data, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_user_data["name"]
        assert data["email"] == test_user_data["email"]
        assert "id" in data

    def test_create_user_duplicate_email(self, client, admin_headers, test_user_data):
        """Нельзя создать пользователя с существующим email"""
        # Первый пользователь
        client.post("/users", json=test_user_data, headers=admin_headers)

        # Второй с тем же email
        response = client.post("/users", json=test_user_data, headers=admin_headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_user_as_non_admin(self, client, user_headers, test_user_data):
        """Не-админ не может создать пользователя"""
        response = client.post("/users", json=test_user_data, headers=user_headers)
        assert response.status_code == 403

    def test_get_users_as_admin(self, client, admin_headers, test_user_data):
        """Админ может получить список пользователей"""
        # Создаем пользователя
        client.post("/users", json=test_user_data, headers=admin_headers)

        # Получаем список
        response = client.get("/users", headers=admin_headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) > 0
        assert users[0]["email"] == test_user_data["email"]

    def test_get_users_as_user(self, client, user_headers):
        """Не-админ не может получить список пользователей"""
        response = client.get("/users", headers=user_headers)
        assert response.status_code == 403


    def test_get_nonexistent_user(self, client, admin_headers):
        """Получение несуществующего пользователя"""
        response = client.get("/users/999", headers=admin_headers)
        assert response.status_code == 404


class TestAssetCRUD:
    """Тесты CRUD операций для активов"""

    def test_create_asset_as_admin(self, client, admin_headers, test_asset_data):
        """Админ может создать актив"""
        response = client.post("/assets", json=test_asset_data, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_asset_data["title"]
        assert "id" in data

    def test_create_asset_as_user(self, client, user_headers, test_asset_data):
        """Не-админ не может создать актив"""
        response = client.post("/assets", json=test_asset_data, headers=user_headers)
        assert response.status_code == 403

    def test_get_assets_no_auth(self, client, test_asset_data):
        """Получение активов не требует аутентификации"""
        # Сначала создаем актив (нужен админ)
        client.post("/assets", json=test_asset_data, headers={"X-User-Id": "1", "X-User-Role": "admin"})

        # Получаем без аутентификации
        response = client.get("/assets")
        assert response.status_code == 200
        assets = response.json()
        assert len(assets) > 0

    def test_get_asset_by_id(self, client, test_asset_data):
        """Получение актива по ID"""
        # Создаем
        create_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = create_response.json()["id"]

        # Получаем
        response = client.get(f"/assets/{asset_id}")
        assert response.status_code == 200
        assert response.json()["id"] == asset_id

    def test_delete_asset(self, client, admin_headers, test_asset_data):
        """Удаление актива"""
        # Создаем
        create_response = client.post("/assets", json=test_asset_data, headers=admin_headers)
        asset_id = create_response.json()["id"]

        # Удаляем
        response = client.delete(f"/assets/{asset_id}", headers=admin_headers)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]

        # Проверяем, что удален
        get_response = client.get(f"/assets/{asset_id}")
        assert get_response.status_code == 404


class TestCheckoutCRUD:
    """Тесты CRUD операций для аренд"""

    def setup_method(self):
        """Настройка тестовых данных перед каждым тестом"""
        # Очищаем базу данных
        from app.main import _DB
        _DB["assets"].clear()
        _DB["checkouts"].clear()
        _DB["users"].clear()

    def test_create_checkout(self, client, user_headers, test_asset_data, test_checkout_data):
        """Создание аренды"""
        # Создаем актив (нужен админ)
        asset_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = asset_response.json()["id"]

        # Создаем аренду
        test_checkout_data["asset_id"] = asset_id
        response = client.post("/checkouts", json=test_checkout_data, headers=user_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["asset_id"] == asset_id
        assert data["status"] == "active"
        assert data["owner_id"] == 2  # ID из user_headers

    def test_create_checkout_duplicate_asset(self, client, user_headers, test_asset_data, test_checkout_data):
        """Нельзя создать две активные аренды на один актив"""
        # Создаем актив
        asset_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = asset_response.json()["id"]

        # Первая аренда
        test_checkout_data["asset_id"] = asset_id
        response1 = client.post("/checkouts", json=test_checkout_data, headers=user_headers)
        assert response1.status_code == 201

        # Вторая аренда на тот же актив
        response2 = client.post("/checkouts", json=test_checkout_data, headers=user_headers)
        assert response2.status_code == 409
        assert "already checked out" in response2.json()["detail"]

    def test_create_checkout_invalid_status(self, client, user_headers, test_asset_data):
        """Нельзя создать аренду с невалидным статусом"""
        # Создаем актив
        asset_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = asset_response.json()["id"]

        # Пробуем создать с возвращенным статусом (нельзя)
        invalid_checkout = {
            "asset_id": asset_id,
            "due_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "returned"  # нельзя начинать с returned
        }

        response = client.post("/checkouts", json=invalid_checkout, headers=user_headers)
        assert response.status_code == 400

    def test_create_checkout_nonexistent_asset(self, client, user_headers, test_checkout_data):
        """Нельзя создать аренду на несуществующий актив"""
        test_checkout_data["asset_id"] = 999  # несуществующий ID

        response = client.post("/checkouts", json=test_checkout_data, headers=user_headers)
        assert response.status_code == 404

    def test_get_my_checkouts(self, client, user_headers, test_asset_data, test_checkout_data):
        """Пользователь видит только свои аренды"""
        # Создаем актив
        asset_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = asset_response.json()["id"]

        # Создаем аренду от пользователя 2
        test_checkout_data["asset_id"] = asset_id
        client.post("/checkouts", json=test_checkout_data, headers=user_headers)

        # Создаем аренду от другого пользователя
        other_user_headers = {"X-User-Id": "3", "X-User-Role": "student"}
        client.post("/checkouts", json=test_checkout_data, headers=other_user_headers)

        # Пользователь 2 получает свои аренды
        response = client.get("/checkouts", headers=user_headers)
        assert response.status_code == 200
        checkouts = response.json()
        assert len(checkouts) == 1
        assert checkouts[0]["owner_id"] == 2


    def test_get_checkout_by_id(self, client, user_headers, test_asset_data, test_checkout_data):
        """Получение аренды по ID"""
        # Создаем актив
        asset_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = asset_response.json()["id"]

        # Создаем аренду
        test_checkout_data["asset_id"] = asset_id
        create_response = client.post("/checkouts", json=test_checkout_data, headers=user_headers)
        checkout_id = create_response.json()["id"]

        # Получаем по ID
        response = client.get(f"/checkouts/{checkout_id}", headers=user_headers)
        assert response.status_code == 200
        assert response.json()["id"] == checkout_id

    def test_get_other_users_checkout(self, client, user_headers, test_asset_data, test_checkout_data):
        """Нельзя получить чужую аренду"""
        # Создаем актив
        asset_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = asset_response.json()["id"]

        # Создаем аренду от пользователя 3
        test_checkout_data["asset_id"] = asset_id
        create_response = client.post(
            "/checkouts",
            json=test_checkout_data,
            headers={"X-User-Id": "3", "X-User-Role": "student"}
        )
        checkout_id = create_response.json()["id"]

        # Пользователь 2 пытается получить аренду пользователя 3
        response = client.get(f"/checkouts/{checkout_id}", headers=user_headers)
        assert response.status_code == 403

    def test_update_checkout_status(self, client, user_headers, test_asset_data):
        """Обновление статуса аренды"""
        # Создаем актив
        asset_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = asset_response.json()["id"]

        # Создаем аренду
        checkout_data = {
            "asset_id": asset_id,
            "due_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "active"
        }
        create_response = client.post("/checkouts", json=checkout_data, headers=user_headers)
        checkout_id = create_response.json()["id"]

        # Обновляем на returned
        update_data = {
            "asset_id": asset_id,
            "due_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "returned"
        }
        response = client.put(f"/checkouts/{checkout_id}", json=update_data, headers=user_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "returned"

    def test_update_to_invalid_status(self, client, user_headers, test_asset_data):
        """Нельзя обновить на невалидный статус"""
        # Создаем актив
        asset_response = client.post(
            "/assets",
            json=test_asset_data,
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        asset_id = asset_response.json()["id"]

        # Создаем аренду
        checkout_data = {
            "asset_id": asset_id,
            "due_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "active"
        }
        create_response = client.post("/checkouts", json=checkout_data, headers=user_headers)
        checkout_id = create_response.json()["id"]

        # Пробуем обновить на active (повторно) - нельзя
        update_data = {
            "asset_id": asset_id,
            "due_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "active"
        }
        response = client.put(f"/checkouts/{checkout_id}", json=update_data, headers=user_headers)
        assert response.status_code == 400