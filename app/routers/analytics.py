from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def analytics_root():
    return {"message": "Analytics endpoints coming soon"}