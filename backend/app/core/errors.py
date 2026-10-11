from typing import Any, Dict, Optional, List
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def build_error_envelope(
    code: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        }
    }


def register_error_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_envelope(
                code=exc.code,
                message=exc.message,
                request_id=request_id,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        errors = []
        for err in exc.errors():
            loc = " -> ".join([str(x) for x in err.get("loc", [])])
            errors.append({"location": loc, "msg": err.get("msg")})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=build_error_envelope(
                code="validation_error",
                message="Request payload or parameters validation failed.",
                request_id=request_id,
                details={"fields": errors},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)
        code_map = {
            404: "not_found",
            403: "forbidden",
            401: "unauthorized",
            405: "method_not_allowed",
            413: "file_too_large",
            429: "rate_limited",
        }
        code = code_map.get(exc.status_code, "http_error")
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_envelope(
                code=code,
                message=str(exc.detail),
                request_id=request_id,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=build_error_envelope(
                code="internal_error",
                message="An unexpected server error occurred. Please contact support.",
                request_id=request_id,
            ),
        )
