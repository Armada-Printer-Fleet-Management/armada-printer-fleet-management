"""Reads and clears the stack's bucket directly, below the app."""

from botocore.client import BaseClient


def stored_object_count(client: BaseClient, bucket: str) -> int:
    count: int = client.list_objects_v2(Bucket=bucket)["KeyCount"]
    return count


def empty_bucket(client: BaseClient, bucket: str) -> None:
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
        for stored in page.get("Contents", []):
            client.delete_object(Bucket=bucket, Key=stored["Key"])
