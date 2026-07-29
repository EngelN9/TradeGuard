"""Content-addressed raw storage with no mutation or deletion surface."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
SHA256_LENGTH = 64


class ContentIntegrityError(RuntimeError):
    """Raised when content does not match its address."""


class StoredBlob(BaseModel):
    """Immutable receipt for one content-addressed blob."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    checksum: Checksum
    size_bytes: Annotated[int, Field(ge=0)]
    relative_path: str
    created: bool


class ContentAddressedStore:
    """Write-once SHA-256 storage.

    The API deliberately exposes no update or delete operation. Repeated writes
    of identical bytes are idempotent and never replace the stored object.
    """

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _path_for(self, checksum: str) -> Path:
        target = self._root / "blobs" / checksum[:2] / checksum[2:]
        if not target.resolve().is_relative_to(self._root):
            raise ContentIntegrityError("content address escaped the configured store")
        return target

    @staticmethod
    def checksum_bytes(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def put(self, content: bytes) -> StoredBlob:
        """Persist bytes once and return their stable content address."""

        checksum = self.checksum_bytes(content)
        target = self._path_for(checksum)
        target.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            with target.open("xb") as stream:
                stream.write(content)
            created = True
        except FileExistsError:
            existing = target.read_bytes()
            if self.checksum_bytes(existing) != checksum or existing != content:
                raise ContentIntegrityError(
                    "existing blob does not match its content address"
                ) from None

        relative_path = target.relative_to(self._root).as_posix()
        return StoredBlob(
            checksum=checksum,
            size_bytes=len(content),
            relative_path=relative_path,
            created=created,
        )

    def read(self, checksum: str) -> bytes:
        """Read and verify one blob by its expected checksum."""

        if len(checksum) != SHA256_LENGTH or any(
            character not in "0123456789abcdef" for character in checksum
        ):
            raise ValueError("checksum must be a lowercase SHA-256 value")
        content = self._path_for(checksum).read_bytes()
        if self.checksum_bytes(content) != checksum:
            raise ContentIntegrityError("stored blob checksum verification failed")
        return content
