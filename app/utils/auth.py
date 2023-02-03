from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import HTTPException, status, Request
from typing import Optional, Dict, Literal

# Securing JWT token with http-only cookie
class OAuth2PasswordBearerWithCookie(OAuth2):
    '''
        Access token schema or refresh token schema
    '''
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
        token_type: Literal['access_token', 'refresh_token'] = 'access_token'
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )
        self.token_type = token_type

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.cookies.get(self.token_type) # changed to accept access token from httpOnly Cookie
        print(f'{self.token_type} is: {authorization}')

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


async def RefreshWithCookie(request: Request) -> Optional[str]:
    authorization = request.cookies.get('refresh_token') # changed to accept access token from httpOnly Cookie
    print(f'refresh_token is: {authorization}')

    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return param
