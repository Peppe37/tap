from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.auth import TokenPair


def issue_token_pair(user: User) -> TokenPair:
    user_id = str(user.id)
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )
