# fast_s3_url

An S3 URL generator that's (much) faster than boto3/aiobotocore's, while being compliant with the s3v4 signed URL format. How much faster? [See below](#benchmarks).

Largely based upon: https://github.com/WeTransfer/wt_s3_signer.

## Important notice

This library, much like the one it's based upon, skips several steps that boto3 and aiobotocore do. As a result, this library should be used one very specific use case only -- when you need to generate thousands of signed URLs fast, and most importantly, when you control the object keys themselves.

For any other use case scenario, please use boto3 or aiobotocore instead.

## Installation

After making sure this is for you, with your favourite package manager (e.g., pip):

```shell
pip install fast-s3-url
```

## Recommended reading

- [Speeding up S3 URL generation in ruby](https://bibwild.wordpress.com/2020/08/26/speeding-up-s3-url-generation-in-ruby/)
- [Super fast signing of S3 URLs](https://wetransfer.com/engineering/super-fast-signing-of-s3-urls)
- [Authenticating Requests: Using Query Parameters (AWS Signature Version 4)](https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-query-string-auth.html)

## Usage

Note: This library does not depend on boto3 or aiobotocore explicitly. If you want to use it without them, you can create an instance directly (see below).

### With boto3

Use `FastS3UrlSigner.from_boto3_client` to create an instance from an existing (and properly configured) client.

```python
client = boto3.client("s3") 

signer = FastS3UrlSigner.from_boto3_client(client, bucket="test")

object_keys = ["cat.jpg", ...]

signed_urls = signer.generate_presigned_get_object_urls(object_keys, expires_in=3600)
```

### With aiobotocore

Use `FastS3UrlSigner.from_aiobotocore_client` to create an instance from an existing (and properly configured) client. Note that unlike the boto3 variant, this method needs to be `await`ed.

```python
session = get_session()

async with session.create_client("s3") as client:
    signer = await FastS3UrlSigner.from_aiobotocore_client(client, "test")

    object_keys = ["cat.jpg", ...]

    signed_urls = signer.generate_presigned_get_object_urls(object_keys, expires_in=3600)
```

### Manually creating an object

The following example assumes you have a [MinIO](https://min.io/) instance running on http://localhost:9000 with default settings. 

Note that you shouldn't hardcode credentials, this is merely for illustration purposes.

```python
signer = FastS3UrlSigner(
    bucket_endpoint_url="http://localhost:9000/my-bucket/",
    aws_region="us-east-1",
    access_key_id="minioadmin",
    secret_access_key="minioadmin",
)
```

## Local development

This project uses [Poetry](https://python-poetry.org/) for dependency management. Make sure you have it installed.

You can then create a Virtual Environment with it (any Python version >= 3.8 will do), and set up a shell. See Poetry's documentation for tutorials on how to do this.

### Running tests

If you have `make` installed, the following targets are set up for you:

- `unit-test`: Runs unit tests. Doesn't require any S3 instance.
- `integration-test`: Runs integration tests. Requires an S3 instance running on `http://localhost:9000`. You can use MinIO to create one.

Note: These targets assume you are running a shell with a Poetry Virtual Environment set up. They do not spawn a shell for running the commands.

## Benchmarks

The following results are from Python 3.11 on Fedora 37 running on a Lenovo ThinkPad L390, with an Intel Core i7 8565U and 16 GB RAM. Turbo Boost was disabled because it quickly causes throttling and it can skew results.

As shown below, depending on the number of URLs to generate, this library can be 6 times faster than the official libraries when generating a single URL, and over 30 times faster when generating 100 or more URLs.

You can run the following to run the benchmarks with pytest-benchmark:

```
make benchmark
```

```text
---------------------------------------------------------------- benchmark 'signed_url_generation object_key_count=1': 2 tests ----------------------------------------------------------------
Name (time in us)          Min                 Max                Mean            StdDev              Median                IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_custom[1]         55.5300 (1.0)      103.7830 (1.0)       57.4275 (1.0)      2.1685 (1.0)       56.8480 (1.0)       0.6910 (1.0)     1187;1741       17.4133 (1.0)       16791           1
test_boto3[1]         355.7460 (6.41)     492.3180 (4.74)     367.2364 (6.39)     6.9269 (3.19)     364.7620 (6.42)     10.6518 (15.41)      659;13        2.7230 (0.16)       2621           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------ benchmark 'signed_url_generation object_key_count=1024': 2 tests -----------------------------------------------------------
Name (time in ms)          Min                 Max                Mean            StdDev              Median               IQR            Outliers      OPS            Rounds  Iterations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_custom[1024]      11.3772 (1.0)       11.5678 (1.0)       11.4341 (1.0)      0.0283 (1.0)       11.4352 (1.0)      0.0308 (1.0)          19;2  87.4577 (1.0)          88           1
test_boto3[1024]      427.2083 (37.55)    429.6503 (37.14)    427.9307 (37.43)    0.9811 (34.63)    427.6766 (37.40)    0.7958 (25.81)         1;1   2.3368 (0.03)          5           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------- benchmark 'signed_url_generation object_key_count=128': 2 tests -----------------------------------------------------------
Name (time in ms)         Min                Max               Mean            StdDev             Median               IQR            Outliers       OPS            Rounds  Iterations
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_custom[128]       1.4635 (1.0)       1.6152 (1.0)       1.4895 (1.0)      0.0110 (1.0)       1.4889 (1.0)      0.0114 (1.0)        131;11  671.3848 (1.0)         665           1
test_boto3[128]       53.6779 (36.68)    55.7975 (34.54)    54.3269 (36.47)    0.6903 (63.01)    53.9923 (36.26)    0.9660 (85.04)         4;0   18.4071 (0.03)         19           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------ benchmark 'signed_url_generation object_key_count=512': 2 tests -------------------------------------------------------------
Name (time in ms)          Min                 Max                Mean            StdDev              Median               IQR            Outliers       OPS            Rounds  Iterations
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_custom[512]        5.7369 (1.0)        5.8751 (1.0)        5.8002 (1.0)      0.0266 (1.0)        5.8028 (1.0)      0.0361 (1.0)          53;1  172.4078 (1.0)         172           1
test_boto3[512]       215.7762 (37.61)    219.7181 (37.40)    217.4519 (37.49)    1.6630 (62.51)    217.8732 (37.55)    2.6384 (73.16)         2;0    4.5987 (0.03)          5           1
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------- benchmark 'signed_url_generation object_key_count=8': 2 tests --------------------------------------------------------------------
Name (time in us)            Min                   Max                  Mean             StdDev                Median                IQR            Outliers         OPS            Rounds  Iterations
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_custom[8]          133.2900 (1.0)        189.1850 (1.0)        137.3525 (1.0)       3.2919 (1.0)        136.2515 (1.0)       1.6770 (1.0)     1137;1124  7,280.5388 (1.0)        7182           1
test_boto3[8]         2,829.3420 (21.23)    4,067.5490 (21.50)    2,869.7947 (20.89)    82.0675 (24.93)    2,854.3680 (20.95)    13.6910 (8.16)        16;43    348.4570 (0.05)        349           1
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
```
