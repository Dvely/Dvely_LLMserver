from typing import Literal

from pydantic import BaseModel


class ErrorBody(BaseModel):
    type: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class ModelInfo(BaseModel):
    id: str
    object: Literal["model"] = "model"
    owned_by: Literal["local"] = "local"


class ModelListResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelInfo]
