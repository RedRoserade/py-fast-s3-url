from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import secrets
from urllib.parse import quote, urlparse, urlunparse

from typing import TYPE_CHECKING, List, Optional

from fast_s3_url.credentials import Credentials, CredentialsWithToken
from fast_s3_url.util import (
    get_credentials_from_aiobotocore_client,
    get_credentials_from_boto3_client,
)


if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client as AioBotocoreS3Client
    from mypy_boto3_s3.client import S3Client as Boto3S3Client

__all__ = ["FastS3UrlSigner"]


class FastS3UrlSigner:
    """
    Alternative signed URL generator for S3, compliant with the s3v4 format,
    and faster than (aio)botocore or boto3 implementations,
    for quickly generating lots of signed URLs at once.
    """

    def __init__(
        self,
        *,
        bucket_endpoint_url: str,
        credentials: Credentials,
        aws_region: Optional[str] = None,
    ) -> None:
        """
        Create an instance of this object with the specified parameters.

        :param bucket_endpoint_url: The URL to a bucket. Can be virtual-style, e.g.: 'https://my-bucket.s3.amazonaws.com/' or path-style, e.g.: 'https://s3.amazonaws.com/my-bucket/'.
        :param aws_region: The AWS region that will be used to generate URLs with. Defaults to 'us-east-1'.
        :param credentials: Credentials to the S3 bucket.
        :param session_token:
        """

        # Get the components from the bucket's endpoint URL.
        # The canonical path must include the bucket's name if we're using path-style URLs,
        # and we must ensure it's not repeated in the endpoint URL in these situations.
        parsed_bucket_url = urlparse(bucket_endpoint_url)

        self.canonical_uri_prefix = parsed_bucket_url.path.rstrip("/")
        self.endpoint_url = urlunparse(parsed_bucket_url._replace(path="/")).rstrip("/")
        self.bucket_host = parsed_bucket_url.netloc

        self.region = aws_region or "us-east-1"
        self.credentials = credentials

    @classmethod
    def from_boto3_client(
        cls,
        client: Boto3S3Client,
        bucket_name: str,
    ):
        """
        Create an instance from a boto3 S3 client, using its credentials.

        This method may, depending on how your client is configured, refresh its credentials.
        Bear in mind that the official clients may refresh their credentials when calling methods on them,
        but the created signer won't. This means that if the credentials are temporary (e.g., STS tokens),
        the generated URLs may suddently become invalid.

        For the sake of caution, these instances should, therefore, be short-lived
        (that is, create, use, and destroy).
        """

        # Generate a dummy URL to see how the client does it with the current configuration,
        # rather than reverse-engineering the logic.
        dummy_key = secrets.token_hex(8)

        dummy_url: str = client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": dummy_key}
        )
        bucket_endpoint_url = dummy_url[0 : dummy_url.index(dummy_key, 0)]

        # Get the client's current credentials.
        credentials = get_credentials_from_boto3_client(client)

        return cls(
            aws_region=client.meta.region_name,
            bucket_endpoint_url=bucket_endpoint_url,
            credentials=credentials,
        )

    @classmethod
    async def from_aiobotocore_client(
        cls,
        client: AioBotocoreS3Client,
        bucket_name: str,
    ):
        """
        Create an instance from an aiobotocore S3 client, using its credentials.

        This method may, depending on how your client is configured, refresh its credentials.
        Bear in mind that the official clients may refresh their credentials when calling methods on them,
        but the created signer won't. This means that if the credentials are temporary (e.g., STS tokens),
        the generated URLs may suddently become invalid.

        For the sake of caution, these instances should, therefore, be short-lived
        (that is, create, use, and destroy).
        """

        # Generate a dummy URL to see how the client does it with the current configuration,
        # rather than reverse-engineering the logic.
        dummy_key = secrets.token_hex(8)

        dummy_url: str = await client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": dummy_key}
        )
        bucket_endpoint_url = dummy_url[0 : dummy_url.index(dummy_key, 0)]

        # Get the client's current credentials.
        credentials = await get_credentials_from_aiobotocore_client(client)

        return cls(
            aws_region=client.meta.region_name,
            bucket_endpoint_url=bucket_endpoint_url,
            credentials=credentials,
        )

    def generate_presigned_get_object_urls(
        self,
        object_keys: List[str],
        *,
        expires_in: int = 3600,
    ) -> List[str]:
        """
        Generate presigned URLs for objects.

        :param object_keys: The object keys to sign.
        :param expires_in: The validity of the signed URLs, in seconds. Defaults to 3600 (1h).
        """

        if not object_keys:
            return []

        if any(not k for k in object_keys):
            raise ValueError("All 'object_keys' must be non-empty strings.")

        now = datetime.now(tz=timezone.utc)

        datestamp = now.strftime("%Y%m%d")
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")

        signing_key = _derive_signing_key(
            self.credentials.secret_key.encode(), datestamp, self.region, "s3"
        )

        canonical_headers = f"host:{self.bucket_host}\n"
        signed_headers = "host"

        algorithm = "AWS4-HMAC-SHA256"

        credential_scope = f"{datestamp}/{self.region}/s3/aws4_request"

        encoded_credential = quote(
            f"{self.credentials.access_key}/{credential_scope}", safe="~"
        )

        canonical_querystring_template_parts = [
            f"X-Amz-Algorithm={algorithm}",
            f"X-Amz-Credential={encoded_credential}",
            f"X-Amz-Date={amz_date}",
            f"X-Amz-Expires={expires_in}",
            f"X-Amz-SignedHeaders={signed_headers}",
        ]

        if isinstance(self.credentials, CredentialsWithToken):
            canonical_querystring_template_parts.append(
                f"X-Amz-Security-Token={quote(self.credentials.session_token, safe='~')}"
            )

        # The query string parameters must be sorted by their name.
        canonical_querystring_template = "&".join(
            sorted(canonical_querystring_template_parts)
        )

        payload = "UNSIGNED-PAYLOAD"

        signed_urls: List[str] = []

        for object_key in object_keys:
            # The object key must be URL encoded, where the only safe characters are
            # '/' and '~'.
            object_key = quote(object_key, safe="/~")

            canonical_uri = f"{self.canonical_uri_prefix}/{object_key}"

            canonical_request = "\n".join(
                (
                    "GET",
                    canonical_uri,
                    canonical_querystring_template,
                    canonical_headers,
                    signed_headers,
                    payload,
                )
            )

            string_to_sign = "\n".join(
                (
                    algorithm,
                    amz_date,
                    credential_scope,
                    hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
                )
            )

            signature = _hmac_hex(signing_key, string_to_sign.encode())

            qs_with_signature = (
                f"{canonical_querystring_template}&X-Amz-Signature={signature}"
            )

            signed_urls.append(
                f"{self.endpoint_url}{canonical_uri}?{qs_with_signature}"
            )

        return signed_urls


def _derive_signing_key(key: bytes, datestamp: str, region: str, service: str) -> bytes:
    k_date = _hmac_bytes(b"AWS4" + key, datestamp.encode("utf-8"))
    k_region = _hmac_bytes(k_date, region.encode("utf-8"))
    k_service = _hmac_bytes(k_region, service.encode("utf-8"))

    return _hmac_bytes(k_service, b"aws4_request")


def _hmac_bytes(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def _hmac_hex(key: bytes, data: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()
