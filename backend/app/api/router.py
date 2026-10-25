from fastapi import APIRouter

from app.api import attempts, auth, materials, tests

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(materials.router)
api_router.include_router(tests.router)
api_router.include_router(attempts.router)


@api_router.get("/health")
def health():
    return {"status": "ok"}
