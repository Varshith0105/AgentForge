from typing import Optional
from pydantic import BaseModel


class GitHubRepoRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"
    access_token: Optional[str] = None


class GitHubOAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None
