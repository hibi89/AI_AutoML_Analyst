"""ASGI request-envelope budget before FastAPI parses multipart file uploads.

Endpoint-level file.read(n + 1) runs AFTER Starlette has already accepted and
spooled a multipart body. Bound the received request envelope as well, including
streamed/chunked requests that lack Content-Length.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

# Individual file cap is 30 MiB on all four endpoints. Leave a modest
# allowance for multipart headers and additional short form fields.
MAX_MULTIPART_BODY_BYTES = 30 * 1024 * 1024 + 128 * 1024
UPLOAD_ENDPOINTS = frozenset({
    "/api/analyze",
    "/api/basic-report",
    "/api/standard-report",
    "/api/premium-report",
})


class _UploadEnvelopeTooLarge(Exception):
    """Internal control flow only; never echo upload contents."""


def _only_size_error(error: Exception) -> bool:
    """Starlette middleware may nest an ASGI receive error in a group."""
    if isinstance(error, _UploadEnvelopeTooLarge):
        return True
    if isinstance(error, ExceptionGroup):
        return bool(error.exceptions) and all(
            isinstance(item, Exception) and _only_size_error(item)
            for item in error.exceptions
        )
    return False


async def _reject(send: Callable[..., Awaitable[None]], status: int) -> None:
    description = ("Upload request exceeds body size limit."
                   if status == 413 else "Invalid Content-Length header.")
    body = ('{"detail":"' + description + '"}').encode("ascii")
    await send({
        "type": "http.response.start", "status": status,
        "headers": [(b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii"))],
    })
    await send({"type": "http.response.body", "body": body})


class UploadEnvelopeLimit:
    """Fail closed when the complete multipart request exceeds the budget."""

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive, send) -> None:
        if (scope["type"] != "http" or scope.get("method") != "POST"
                or scope.get("path") not in UPLOAD_ENDPOINTS):
            return await self.app(scope, receive, send)

        lengths = [value for key, value in scope.get("headers", [])
                   if key.lower() == b"content-length"]
        if len(lengths) > 1 or any(not raw.isdigit() for raw in lengths):
            return await _reject(send, 400)
        if lengths and int(lengths[0]) > MAX_MULTIPART_BODY_BYTES:
            return await _reject(send, 413)

        received_bytes = 0
        response_started = False

        async def checked_receive():
            nonlocal received_bytes
            message = await receive()
            if message["type"] == "http.request":
                received_bytes += len(message.get("body") or b"")
                if received_bytes > MAX_MULTIPART_BODY_BYTES:
                    raise _UploadEnvelopeTooLarge()
            return message

        async def checked_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, checked_receive, checked_send)
        except Exception as error:
            if not _only_size_error(error) or response_started:
                raise
            await _reject(send, 413)
