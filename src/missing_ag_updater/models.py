from typing import Optional

from pydantic import BaseModel


class Release(BaseModel):
    version: str
    execution_id: str


class CliManifest(BaseModel):
    version: str
    url: str
    sha512: Optional[str] = None
