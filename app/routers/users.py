from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserResponse
from app.db.database import supabase

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    """Creates a new user in Supabase Auth."""
    try:
        # Supabase handles password hashing and storage automatically
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {"data": {"role": user.role}}
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Signup failed.")

        return {
            "id": response.user.id,
            "email": response.user.email,
            "role": user.role,
            "access_token": response.session.access_token if response.session else "Check Email for Verification"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=UserResponse)
async def login(user: UserCreate):
    """Authenticates a user and returns a session token."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        
        return {
            "id": response.user.id,
            "email": response.user.email,
            "role": response.user.user_metadata.get("role"),
            "access_token": response.session.access_token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password.")