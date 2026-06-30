from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import prisma
from app.core.security import hash_password, verify_password, create_access_token
from app.models.schemas import UserRegister, UserLogin, TokenResponse
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister):
    """Create a new user account and return a JWT."""
    existing = await prisma.user.find_unique(where={"username": body.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = await prisma.user.create(
        data={"username": body.username, "password_hash": hash_password(body.password)}
    )
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return a JWT."""
    user = await prisma.user.find_unique(where={"username": form_data.username})
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)
