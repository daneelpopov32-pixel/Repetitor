from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import InvitationCodeCreate, InvitationCodeResponse
from app.services import auth as auth_service
from app.utils.deps import require_role
from app.models import User

router = APIRouter(prefix="/invitation-codes", tags=["Invitation Codes"])


@router.post("", response_model=InvitationCodeResponse)
async def create_code(
    data: InvitationCodeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    return await auth_service.generate_invitation_code(db, user.id, data.expires_in_days)
