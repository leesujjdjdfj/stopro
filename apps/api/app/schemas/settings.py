from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    defaultExchangeRate: Optional[str] = None
    cacheTTLSeconds: Optional[str] = None
