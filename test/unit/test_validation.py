from __future__ import annotations


import pytest

from fast_s3_url import FastS3UrlSigner


@pytest.mark.parametrize(
    "invalid_object_key",
    [
        None,
        "",
    ],
)
def test_validates_parameters(invalid_object_key: str):
    # Arrange
    sig = FastS3UrlSigner(
        bucket_endpoint_url="http://localhost:9000/my-bucket/",
        access_key_id="minioadmin",
        secret_access_key="minioadmin",
    )

    # Act / Assert
    with pytest.raises(ValueError):
        sig.generate_presigned_get_object_urls([invalid_object_key])
