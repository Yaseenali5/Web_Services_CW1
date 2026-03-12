from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from ..security import authenticate_user, create_access_token

router = APIRouter()


@router.post("/token")
def issue_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(
        subject=user["username"],
        role=user["role"],
        scopes=user["scopes"],
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": " ".join(user["scopes"]),
        "role": user["role"],
    }
