from dataclasses import dataclass

__all__ = ["Credentials", "CredentialsWithToken"]


@dataclass(slots=True, frozen=True)
class Credentials:
    access_key: str
    """
    The Access Key ID. Usually mapped to the `AWS_ACCESS_KEY_ID` environment variable.
    """
    secret_key: str
    """
    The Secret Access Key. Usually mapped to the `AWS_SECRET_ACCESS_KEY` environment variable.
    """


@dataclass(slots=True, frozen=True)
class CredentialsWithToken(Credentials):
    session_token: str
    """
    An STS session token. Usually mapped to the `AWS_SESSION_TOKEN` environment variable.

    Note that these tokens usually expire, so you must refresh them yourself.
    """
