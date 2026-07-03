from fastapi import APIRouter

from app.api.v1 import auth, themes, tests, attempts, review, analytics, invitation_codes, content, fipi

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(themes.router)
router.include_router(tests.router)
router.include_router(attempts.router)
router.include_router(review.router)
router.include_router(analytics.router)
router.include_router(invitation_codes.router)
router.include_router(content.router)
router.include_router(fipi.router)
