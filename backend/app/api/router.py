from fastapi import APIRouter

from app.api.routers import auth, carriers, packages, providers, shops

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(carriers.router)
api_router.include_router(shops.router)
api_router.include_router(providers.router)
api_router.include_router(packages.router)
