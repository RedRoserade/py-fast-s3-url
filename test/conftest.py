from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterable
import pytest
import pytest_asyncio

import boto3

from aiobotocore.session import get_session

from botocore.config import Config

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client as AioBotocoreS3Client
    from mypy_boto3_s3.client import S3Client as Boto3S3Client


@pytest.fixture
def s3_config() -> Config:
    """
    S3 configuration to ensure signed URLs use the s3v4 format,
    regardless of region (some default to v2 format).
    """
    return Config(
        signature_version="s3v4",
    )


@pytest_asyncio.fixture  # type: ignore
async def aio_s3_client(s3_config: Config) -> AsyncIterable[AioBotocoreS3Client]:
    session = get_session()

    endpoint_url = "http://localhost:9000"

    access_key_id = "minioadmin"
    secret_key = "minioadmin"

    async with session.create_client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_key,
        config=s3_config,
    ) as client:
        yield client  # type: ignore


@pytest.fixture
def boto3_client(s3_config: Config) -> Boto3S3Client:
    endpoint_url = "http://localhost:9000"

    access_key_id = "minioadmin"
    secret_key = "minioadmin"

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_key,
        config=s3_config,
    )

    return client  # type: ignore
