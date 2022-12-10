from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Iterable, Tuple
import requests

import pytest

from fast_s3_url import FastS3UrlSigner


if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client as Boto3S3Client


@pytest.fixture
def bucket(boto3_client: Boto3S3Client) -> Iterable[str]:
    bucket_name = f"test-{secrets.token_hex(4)}"

    try:
        boto3_client.create_bucket(Bucket=bucket_name)
        yield bucket_name
    finally:
        boto3_client.delete_bucket(Bucket=bucket_name)


@pytest.fixture
def object_with_contents(
    boto3_client: Boto3S3Client, bucket: str
) -> Iterable[Tuple[str, bytes]]:
    object_key = f"test/object/{secrets.token_hex(16)}.txt"
    contents = secrets.token_bytes(64)

    try:
        boto3_client.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=contents,
        )

        yield (object_key, contents)
    finally:
        boto3_client.delete_object(
            Bucket=bucket,
            Key=object_key,
        )


def test_integration(
    boto3_client: Boto3S3Client, bucket: str, object_with_contents: Tuple[str, bytes]
):
    # Arrange
    signer = FastS3UrlSigner.from_boto3_client(boto3_client, bucket)

    object_key, expected_contents = object_with_contents

    # Act
    signed_url, *_ = signer.generate_presigned_get_object_urls([object_key])

    # Assert
    # The URL must be valid and points to the actual object
    response = requests.get(signed_url)

    response.raise_for_status()

    assert response.content == expected_contents
