"""Reads and clears the stack's bucket directly, below the app."""

from types_boto3_s3.client import S3Client


def stored_object_count(client: S3Client, bucket: str) -> int:
    return client.list_objects_v2(Bucket=bucket)["KeyCount"]


def empty_bucket(client: S3Client, bucket: str) -> None:
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
        for stored in page.get("Contents", []):
            if "Key" in stored:
                client.delete_object(Bucket=bucket, Key=stored["Key"])
