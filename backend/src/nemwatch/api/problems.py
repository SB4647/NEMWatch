from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetail(BaseModel):
    code: str
    message: str
    fields: dict[str, str] | None = None


def problem(status_code: int, code: str, message: str, fields: dict[str, str] | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ProblemDetail(code=code, message=message, fields=fields).model_dump(exclude_none=True),
    )


def install_problem_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_problem(_request: Request, error: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for item in error.errors():
            location = ".".join(str(part) for part in item["loc"] if part not in {"body", "query", "path"})
            fields[location or "request"] = str(item["msg"])
        body: dict[str, Any] = {
            "detail": ProblemDetail(
                code="validation_error", message="Request validation failed", fields=fields
            ).model_dump(exclude_none=True)
        }
        return JSONResponse(status_code=422, content=body)
