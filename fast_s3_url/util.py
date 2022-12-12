from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Protocol

from fast_s3_url.credentials import Credentials, CredentialsWithToken


if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client as AioBotocoreS3Client
    from mypy_boto3_s3.client import S3Client as Boto3S3Client


__all__ = [
    "get_credentials_from_boto3_client",
    "get_credentials_from_aiobotocore_client",
]


def get_credentials_from_boto3_client(client: Boto3S3Client) -> Credentials:
    """
    Get credentials from a boto3 client.

    Note: This may cause the client to refresh its own credentials.
    """

    c: _Credentials = client._request_signer._credentials.get_frozen_credentials()  # type: ignore

    return _to_credentials(c)


async def get_credentials_from_aiobotocore_client(
    client: AioBotocoreS3Client,
) -> Credentials:
    """
    Get credentials from an aiobotocore client.

    Note: This may cause the client to refresh its own credentials.
    """

    c: _Credentials = await client._request_signer._credentials.get_frozen_credentials()  # type: ignore

    return _to_credentials(c)


class _Credentials(Protocol):
    access_key: str
    secret_key: str
    token: Optional[str]


def _to_credentials(c: _Credentials) -> Credentials:
    if c.token:
        return CredentialsWithToken(
            access_key=c.access_key,
            secret_key=c.secret_key,
            session_token=c.token,
        )

    return Credentials(
        access_key=c.access_key,
        secret_key=c.secret_key,
    )
