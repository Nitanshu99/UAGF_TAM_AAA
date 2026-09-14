"""A minimal in-process stand-in for ``minio.Minio``.

Implements only the five calls :class:`MinioBackend` uses, with the same
signatures as minio 7.2.20, so backend behaviour can be tested without a live
container.
"""
from __future__ import annotations

from typing import Any, Iterator


class _Obj:
    """One listed object, exposing ``object_name`` like the real SDK."""

    def __init__(self, object_name: str) -> None:
        self.object_name = object_name


class _Response:
    """Read-once response object mirroring the SDK's get_object result."""

    def __init__(self, body: bytes) -> None:
        self._body = body
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        """Return the whole object body."""
        return self._body

    def close(self) -> None:
        """Mark the response closed."""
        self.closed = True

    def release_conn(self) -> None:
        """Mark the pooled connection released."""
        self.released = True


class FakeMinio:
    """In-memory MinIO double recording buckets and objects."""

    def __init__(self) -> None:
        self.buckets: set[str] = set()
        self.objects: dict[tuple[str, str], bytes] = {}
        self.responses: list[_Response] = []

    def bucket_exists(self, bucket_name: str) -> bool:
        """Return whether *bucket_name* has been created."""
        return bucket_name in self.buckets

    def make_bucket(self, bucket_name: str) -> None:
        """Create *bucket_name*."""
        self.buckets.add(bucket_name)

    def put_object(self, bucket_name: str, object_name: str, data: Any,
                   length: int, content_type: str = "application/octet-stream") -> None:
        """Store the first *length* bytes of *data* under *object_name*."""
        del content_type
        self.objects[(bucket_name, object_name)] = data.read(length)

    def get_object(self, bucket_name: str, object_name: str) -> _Response:
        """Return a response for *object_name*, or raise if absent."""
        key = (bucket_name, object_name)
        if key not in self.objects:
            raise KeyError(f"NoSuchKey: {object_name}")
        response = _Response(self.objects[key])
        self.responses.append(response)
        return response

    def list_objects(self, bucket_name: str, prefix: str = "",
                     recursive: bool = False) -> Iterator[_Obj]:
        """Yield objects in *bucket_name* whose key starts with *prefix*."""
        del recursive
        for bucket, name in sorted(self.objects):
            if bucket == bucket_name and name.startswith(prefix):
                yield _Obj(name)
