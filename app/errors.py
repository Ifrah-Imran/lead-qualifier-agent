"""Map external service failures to clear HTTP errors."""

from fastapi import HTTPException
from openai import APIConnectionError, APIError, APITimeoutError, OpenAIError


def openai_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, APITimeoutError):
        return HTTPException(status_code=504, detail=f"OpenAI request timed out: {exc}")
    if isinstance(exc, APIConnectionError):
        return HTTPException(status_code=503, detail=f"OpenAI service unavailable: {exc}")
    if isinstance(exc, APIError):
        return HTTPException(status_code=502, detail=f"OpenAI API error: {exc}")
    if isinstance(exc, OpenAIError):
        return HTTPException(status_code=502, detail=f"OpenAI error: {exc}")
    return HTTPException(status_code=502, detail=f"Unexpected OpenAI failure: {exc}")


def chroma_http_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=503, detail=f"ChromaDB unavailable: {exc}")
