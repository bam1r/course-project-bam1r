from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException
from starlette import status

from app.models.asset import AssetCreate, AssetOut

# fmt: off
from app.models.checkout import CheckoutCreate, CheckoutOut, CheckoutStatus, can_transition
from app.models.user import UserCreate, UserOut, UserRole
from app.security import CurrentUser, ensure_owner_or_admin, get_current_user, require_admin

# fmt: on

app = FastAPI(title="Equipment Checkout", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


_DB: Dict[str, List[Dict]] = {
    "users": [],
    "assets": [],
    "checkouts": [],
    "equipment": [],
}


def _get_record(bucket: str, entity_id: int, message: str) -> Dict:
    if entity_id < 1 or entity_id > len(_DB[bucket]):
        raise HTTPException(404, message)

    return _DB[bucket][entity_id - 1]


def _reindex(bucket: str) -> None:
    for idx, record in enumerate(_DB[bucket], start=1):
        record["id"] = idx


def _serialize_checkout(data: Dict) -> CheckoutOut:
    return CheckoutOut(**data)


def _visible_checkouts(current_user: CurrentUser) -> List[Dict]:
    if current_user.role == UserRole.admin:
        return _DB["checkouts"]
    return [c for c in _DB["checkouts"] if c["owner_id"] == current_user.id]


def _has_active_checkout(asset_id: int) -> bool:
    active_statuses = ["active", "overdue"]  # статусы, когда asset занят

    for checkout in _DB["checkouts"]:
        if (
            checkout.get("asset_id") == asset_id
            and checkout.get("status") in active_statuses
        ):
            return True

    return False


# Users CRUD
@app.get("/users", response_model=List[UserOut])
def get_users(current_user: CurrentUser = Depends(get_current_user)):
    require_admin(current_user)
    return [UserOut(**user) for user in _DB["users"]]


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_user: CurrentUser = Depends(get_current_user)):
    require_admin(current_user)
    return _get_record("users", user_id, "User not found")


@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate, current_user: CurrentUser = Depends(get_current_user)
):
    require_admin(current_user)
    for u in _DB["users"]:
        if u.get("email") == user.email:
            raise HTTPException(400, "User with this email already exists")

    user_data = {"id": len(_DB["users"]) + 1, **user.dict()}
    _DB["users"].append(user_data)
    return UserOut(**user_data)


@app.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user: UserCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    require_admin(current_user)
    _ = _get_record("users", user_id, "User not found")

    for idx, existing in enumerate(_DB["users"]):
        if existing.get("email") == user.email and idx != user_id - 1:
            raise HTTPException(400, "User with this email already exists")

    _DB["users"][user_id - 1] = {"id": user_id, **user.dict()}
    return UserOut(**_DB["users"][user_id - 1])


@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: CurrentUser = Depends(get_current_user)):
    require_admin(current_user)
    _get_record("users", user_id, "User not found")
    deleted = _DB["users"].pop(user_id - 1)
    _reindex("users")
    return {"message": f"User {deleted['name']} deleted"}


# Assets CRUD
@app.get("/assets", response_model=List[AssetOut])
def get_assets():
    return [AssetOut(**asset) for asset in _DB["assets"]]


@app.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int):
    return _get_record("assets", asset_id, "Asset not found")


@app.post("/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset: AssetCreate, current_user: CurrentUser = Depends(get_current_user)
):
    require_admin(current_user)
    asset_data = {"id": len(_DB["assets"]) + 1, **asset.dict()}
    _DB["assets"].append(asset_data)
    return asset_data


@app.put("/assets/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: int,
    asset: AssetCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    require_admin(current_user)
    _get_record("assets", asset_id, "Asset not found")
    _DB["assets"][asset_id - 1] = {"id": asset_id, **asset.dict()}
    return _DB["assets"][asset_id - 1]


@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, current_user: CurrentUser = Depends(get_current_user)):
    require_admin(current_user)
    _get_record("assets", asset_id, "Asset not found")
    deleted_asset = _DB["assets"].pop(asset_id - 1)
    _reindex("assets")
    return {"message": f"Asset {deleted_asset['title']} deleted"}


# Checkouts CRUD
@app.get("/checkouts", response_model=List[CheckoutOut])
def get_checkouts(current_user: CurrentUser = Depends(get_current_user)):
    return [_serialize_checkout(co) for co in _visible_checkouts(current_user)]


@app.get("/checkouts/{checkout_id}", response_model=CheckoutOut)
def get_checkout(
    checkout_id: int, current_user: CurrentUser = Depends(get_current_user)
):
    checkout = _get_record("checkouts", checkout_id, "Checkout not found")
    ensure_owner_or_admin(checkout["owner_id"], current_user)
    return _serialize_checkout(checkout)


@app.post("/checkouts", response_model=CheckoutOut, status_code=status.HTTP_201_CREATED)
def create_checkout(
    checkout: CheckoutCreate, current_user: CurrentUser = Depends(get_current_user)
):
    _get_record("assets", checkout.asset_id, "Asset not found")

    if _has_active_checkout(checkout.asset_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Asset is already checked out"
        )

    if not can_transition(None, checkout.status):
        raise HTTPException(400, "Cannot create checkout with this status")

    checkout_data = {
        "id": len(_DB["checkouts"]) + 1,
        "asset_id": checkout.asset_id,
        "due_at": checkout.due_at,
        "status": checkout.status.value,
        "owner_id": current_user.id,
    }

    _DB["checkouts"].append(checkout_data)
    return _serialize_checkout(checkout_data)


@app.put("/checkouts/{checkout_id}", response_model=CheckoutOut)
def update_checkout(
    checkout_id: int,
    checkout: CheckoutCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    existing = _get_record("checkouts", checkout_id, "Checkout not found")
    ensure_owner_or_admin(existing["owner_id"], current_user)
    _get_record("assets", checkout.asset_id, "Asset not found")

    current_status = CheckoutStatus(existing["status"])
    if not can_transition(current_status, checkout.status):
        raise HTTPException(400, "Cannot create checkout with this status")

    existing.update(
        {
            "asset_id": checkout.asset_id,
            "due_at": checkout.due_at,
            "status": checkout.status.value,
        }
    )
    return _serialize_checkout(existing)


@app.delete("/checkouts/{checkout_id}")
def delete_checkout(
    checkout_id: int, current_user: CurrentUser = Depends(get_current_user)
):
    checkout = _get_record("checkouts", checkout_id, "Checkout not found")
    ensure_owner_or_admin(checkout["owner_id"], current_user)
    deleted_checkout = _DB["checkouts"].pop(checkout_id - 1)
    _reindex("checkouts")
    return {"message": f"Checkout {deleted_checkout['id']} deleted"}
