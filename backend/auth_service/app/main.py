import os
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE", "60"))

# In-memory user store (production: Amazon Cognito / RDS)
USERS = {
    "demo-user": {
        "user_id": "demo-user",
        "email": "demo@aura-commerce.local",
        "password_hash": "password",  # Plain for demo; use bcrypt in production
        "role": "customer"
    },
    "admin": {
        "user_id": "admin",
        "email": "admin@aura-commerce.local",
        "password_hash": "admin123",
        "role": "admin"
    }
}

app = FastAPI(title="Auth Service", version="2.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

security = HTTPBearer(auto_error=False)

class LoginRequest(BaseModel):
    user_id: str
    password: str

class RegisterRequest(BaseModel):
    user_id: str
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id or user_id not in USERS:
            raise HTTPException(status_code=401, detail="Invalid user")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "auth-service", "version": "2.0.0"}

@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(req: LoginRequest):
    user = USERS.get(req.user_id)
    if not user or user["password_hash"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user["user_id"], "email": user["email"], "role": user["role"]})
    logger.info(f"Login: user={req.user_id}, role={user['role']}")
    return TokenResponse(
        access_token=token,
        user_id=user["user_id"],
        email=user["email"],
        role=user["role"]
    )

@app.post("/auth/register", response_model=TokenResponse, tags=["auth"], status_code=201)
def register(req: RegisterRequest):
    if req.user_id in USERS:
        raise HTTPException(status_code=400, detail="User already exists")
    USERS[req.user_id] = {
        "user_id": req.user_id,
        "email": req.email,
        "password_hash": req.password,
        "role": "customer"
    }
    token = create_access_token({"sub": req.user_id, "email": req.email, "role": "customer"})
    logger.info(f"Registered: user={req.user_id}")
    return TokenResponse(
        access_token=token,
        user_id=req.user_id,
        email=req.email,
        role="customer"
    )

@app.get("/auth/verify", tags=["auth"])
def verify_token_route(payload: dict = Depends(verify_token)):
    user_id = payload.get("sub")
    user = USERS.get(user_id, {})
    return {
        "valid": True,
        "user_id": user_id,
        "email": user.get("email"),
        "role": user.get("role"),
        "exp": payload.get("exp"),
        "message": "Token verified successfully"
    }

@app.get("/auth/users", tags=["auth"])
def list_users():
    return {
        "users": [
            {"user_id": k, "email": v["email"], "role": v["role"]}
            for k, v in USERS.items()
        ],
        "note": "For demo purposes. Production uses Amazon Cognito User Pool."
    }
