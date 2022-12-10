from __future__ import annotations
import os

from typing import TYPE_CHECKING, Any, Dict
from unittest import mock

from aiobotocore.session import get_session
import boto3

import pytest

from fast_s3_url import FastS3UrlSigner

from botocore.config import Config

from test.util.url_comparison import assert_urls_match

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client as AioBotocoreS3Client
    from mypy_boto3_s3.client import S3Client as Boto3S3Client


pytestmark = [
    # Freeze time during test runs such that
    # the URLs are consistent (they have timestamps in them)
    pytest.mark.freeze_time,
]

OBJECT_KEYS = [
    "cat.jpg",
    "/my/image.png",
    "something/else.gif",
    "    ",
    "hello world.txt",
    "Scheiße.dat",
    "hello~world.txt",
    "abc..def.xyz",
]

EXPIRES_IN = [
    3600,
]


@pytest.mark.parametrize("object_key", OBJECT_KEYS)
@pytest.mark.parametrize("expires_in", EXPIRES_IN)
def test_generates_urls_like_boto(
    object_key: str, expires_in: int, boto3_client: Boto3S3Client
) -> None:
    # Arrange
    expected_url = boto3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": "bucket", "Key": object_key},
        ExpiresIn=expires_in,
    )

    sig = FastS3UrlSigner.from_boto3_client(boto3_client, "bucket")

    # Act
    actual_url, *_ = sig.generate_presigned_get_object_urls(
        [object_key], expires_in=expires_in
    )

    # Assert
    assert_urls_match(actual_url, expected_url)


@pytest.mark.asyncio
@pytest.mark.parametrize("object_key", OBJECT_KEYS)
@pytest.mark.parametrize("expires_in", EXPIRES_IN)
async def test_generates_urls_like_aiobotocore(
    object_key: str, expires_in: int, aio_s3_client: AioBotocoreS3Client
) -> None:
    # Arrange
    expected_url = await aio_s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": "test", "Key": object_key},
        ExpiresIn=expires_in,
    )

    sig = await FastS3UrlSigner.from_aiobotocore_client(aio_s3_client, "test")

    # Act
    actual_url, *_ = sig.generate_presigned_get_object_urls(
        [object_key], expires_in=expires_in
    )

    # Assert
    assert_urls_match(actual_url, expected_url)


_DUMMY_S3_CREDENTIALS = {
    "AWS_ACCESS_KEY_ID": "ACCESS",
    "AWS_SECRET_ACCESS_KEY": "SuperS3cret",
}

_DUMMY_S3_CREDENTIALS_WITH_TOKEN = {
    **_DUMMY_S3_CREDENTIALS,
    "AWS_SESSION_TOKEN": (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJjdXJpb3NpdHkiOiJLaWxsZWQgdGhlIGNhdCJ9."
        "Q1DwKcK9NBZdNxMj_BOeU1VFmjuisMKKtNgPVI1_Ie8"
    ),
}

_DUMMY_S3_CREDENTIALS_WITH_REGION = {
    **_DUMMY_S3_CREDENTIALS,
    "AWS_DEFAULT_REGION": "us-west-2",
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "credentials",
    [
        _DUMMY_S3_CREDENTIALS,
        _DUMMY_S3_CREDENTIALS_WITH_TOKEN,
        _DUMMY_S3_CREDENTIALS_WITH_REGION,
    ],
    ids=[
        "DUMMY",
        "DUMMY_WITH_TOKEN",
        "DUMMY_WITH_REGION",
    ],
)
async def test_generates_urls_like_aiobotocore_with_default_credentials(
    credentials: Dict[str, Any],
    s3_config: Config,
) -> None:
    # Arrange

    object_key = "cat.jpg"
    expires_in = 300
    bucket = "test"

    session = get_session()

    with mock.patch.dict(os.environ, credentials):
        aio_s3_client: AioBotocoreS3Client
        async with session.create_client("s3", config=s3_config) as aio_s3_client:  # type: ignore

            expected_url = await aio_s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_key},
                ExpiresIn=expires_in,
            )

            sig = await FastS3UrlSigner.from_aiobotocore_client(aio_s3_client, bucket)

            # Act
            actual_url, *_ = sig.generate_presigned_get_object_urls(
                [object_key], expires_in=expires_in
            )

    # Assert
    assert_urls_match(actual_url, expected_url)


@pytest.mark.parametrize(
    "credentials",
    [
        _DUMMY_S3_CREDENTIALS,
        _DUMMY_S3_CREDENTIALS_WITH_TOKEN,
        _DUMMY_S3_CREDENTIALS_WITH_REGION,
    ],
    ids=[
        "DUMMY",
        "DUMMY_WITH_TOKEN",
        "DUMMY_WITH_REGION",
    ],
)
def test_generates_urls_like_boto3_with_default_credentials(
    credentials: Dict[str, Any],
    s3_config: Config,
) -> None:
    # Arrange

    bucket = "test"
    object_key = "cat.jpg"
    expires_in = 300

    with mock.patch.dict(os.environ, credentials):
        boto3_client: Boto3S3Client = boto3.client("s3", config=s3_config)  # type: ignore

        expected_url = boto3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )

        sig = FastS3UrlSigner.from_boto3_client(boto3_client, bucket)

        # Act
        actual_url, *_ = sig.generate_presigned_get_object_urls(
            [object_key], expires_in=expires_in
        )

    # Assert
    assert_urls_match(actual_url, expected_url)
