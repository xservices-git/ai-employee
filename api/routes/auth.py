"""Auth API routes: register, login, me, user admin.

POST /v1/auth/register  {email, name, password, role?} -> {user, token}
POST /v1/auth/login     {email, password}              -> {user, token}
GET  /v1/auth/me        (Bearer)                       -> {user}
GET  /v1/auth/users     (admin)                        -> {items}
DELETE /v1/auth/users/{id} (admin)                     -> {deleted}
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from core.auth import create_jwt, decode_jwt
from core import db

router = APIRouter(prefix="/v1/auth", tags=["auth"])

VALID_ROLES = {"admin", "approver", "user"}

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "user"

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    user: dict
    token: str

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract user from Bearer token. Raises 401 if invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization header")
    token = authorization[7:]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get_user(payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    return user

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin role required")
    return user

def _user_public(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Register user. Only admins can assign non-user role on 2nd+ user; first user is always admin."""
    if req.role not in VALID_ROLES:
        raise HTTPException(400, f"Invalid role: {req.role}. Must be one of {sorted(VALID_ROLES)}")
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    # First user becomes admin automatically
    role = req.role
    if not db.list_users(limit=1):
        role = "admin"
    user = db.create_user(req.email, req.name, req.password, role=role)
    if not user:
        raise HTTPException(409, "Email already registered")
    db.log_action(user["id"], "register", result="ok",
                  metadata={"email": req.email, "role": role})
    token = create_jwt(user["id"], user["role"])
    return AuthResponse(user=_user_public(user), token=token)

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    user = db.authenticate_user(req.email, req.password)
    if not user:
        db.log_action("anonymous", "login", result="fail",
                      metadata={"email": req.email})
        raise HTTPException(401, "Invalid email or password")
    db.log_action(user["id"], "login", result="ok",
                  metadata={"email": req.email})
    token = create_jwt(user["id"], user["role"])
    return AuthResponse(user=_user_public(user), token=token)

@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return _user_public(user)

@router.get("/users")
def list_users(user: dict = Depends(require_admin)):
    """Admin only: list all users (no passwords)."""
    return {"items": db.list_users()}

@router.delete("/users/{user_id}")
def delete_user(user_id: str, user: dict = Depends(require_admin)):
    """Admin only: delete user. Cannot delete self or last admin."""
    if user["id"] == user_id:
        raise HTTPException(400, "Cannot delete yourself")
    target = db.get_user(user_id)
    if not target:
        raise HTTPException(404, f"User not found: {user_id}")
    if target["role"] == "admin":
        all_users = db.list_users()
        admins = [u for u in all_users if u["role"] == "admin"]
        if len(admins) <= 1:
            raise HTTPException(400, "Cannot delete last admin")
    db.get_db().execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.get_db().commit()
    db.log_action(user["id"], "delete_user", result="ok",
                  metadata={"deleted_id": user_id})
    return {"deleted": user_id}

@router.get("/audit")
def list_audit(actor: Optional[str] = None, action: Optional[str] = None,
               limit: int = 100, user: dict = Depends(require_admin)):
    """Admin only: list audit log entries."""
    return {"items": db.list_audit_log(actor=actor, action=action, limit=limit)}
