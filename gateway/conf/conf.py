import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ACCESS_TOKEN_DEFAULT_EXPIRE_MINUTES: int = 360
    MLDATASET_SERVICE_URL: str = "http://mldataset:8001"
    AUTH_SERVICE_URL: str = "http://auth:8002"
    WEBSOCKET_SERVICE_URL: str = "http://websocket:8003"
    GATEWAY_TIMEOUT: int = 59
settings = Settings()