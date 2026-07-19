"""Auth API routes: register, login, me.

POST /v1/auth/register  {email, name, password} -> {user, token}
POST /v1/auth/login     {email, password}       -> {user, token}
GET  /v1/auth/me         (Bearer)                -> {user}
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from core.auth import create_jwt, decode_jwt
from core import db

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


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


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    user = db.create_user(req.email, req.name, req.password, role="user")
    if not user:
        raise HTTPException(409, "Email already registered")
    token = create_jwt(user["id"], user["role"])
    return AuthResponse(user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}, token=token)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    user = db.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(401, "Invalid email or password")
    token = create_jwt(user["id"], user["role"])
    return AuthResponse(user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}, token=token)


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
