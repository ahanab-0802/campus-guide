"""
routes/auth.py
--------------
Handles user registration, login (JWT token), and profile management.
All password storage uses bcrypt hashing via passlib.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserOut, UserUpdate
from app.utils.auth import hash_password, verify_password, create_access_token, get_current_user_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - Checks for duplicate email
    - Hashes password with bcrypt
    - Stores user in database
    """
    # ── Duplicate email check ─────────────────────────────────────────────────
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    # ── Create user ───────────────────────────────────────────────────────────
    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        college=payload.college,
        graduation_year=payload.graduation_year
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return a JWT Bearer token.
    
    The token encodes the user's email as 'sub' (subject).
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/profile", response_model=UserOut)
def get_profile(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Return the authenticated user's profile."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.put("/profile/update", response_model=UserOut)
def update_profile(
    payload: UserUpdate,
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Update the authenticated user's profile fields.
    Partial updates are supported (only provided fields are changed).
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.name:            user.name            = payload.name
    if payload.phone:           user.phone           = payload.phone
    if payload.college:         user.college         = payload.college
    if payload.graduation_year: user.graduation_year = payload.graduation_year
    if payload.password:        user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return user
