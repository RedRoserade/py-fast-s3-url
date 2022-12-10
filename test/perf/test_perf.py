from __future__ import annotations
import secrets

from typing import TYPE_CHECKING, List
import pytest

from fast_s3_url import FastS3UrlSigner


if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client as Boto3S3Client
    from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore


pytestmark = [pytest.mark.benchmark(group="signed_url_generation")]


OBJECT_KEY_COUNT = [1, 8, 128, 512, 1024]


@pytest.mark.parametrize("object_key_count", OBJECT_KEY_COUNT)
def test_boto3(
    benchmark: BenchmarkFixture,
    boto3_client: Boto3S3Client,
    object_key_count: int,
) -> None:
    object_keys = [secrets.token_hex(16) for _ in range(object_key_count)]

    def sign_many():
        return [
            boto3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": "my-bucket", "Key": object_key},
            )
            for object_key in object_keys
        ]

    signed_urls: List[str] = benchmark(sign_many)

    assert len(signed_urls) == len(object_keys)


@pytest.mark.parametrize("object_key_count", OBJECT_KEY_COUNT)
def test_custom(
    benchmark: BenchmarkFixture,
    boto3_client: Boto3S3Client,
    object_key_count: int,
) -> None:
    object_keys = [secrets.token_hex(16) for _ in range(object_key_count)]

    sig = FastS3UrlSigner.from_boto3_client(boto3_client, "my-bucket")

    signed_urls: List[str] = benchmark(
        sig.generate_presigned_get_object_urls,
        object_keys,
    )

    assert len(signed_urls) == len(object_keys)
