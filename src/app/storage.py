from functools import cached_property

import boto3
from botocore.config import Config

from app.config import Settings, get_settings


class ObjectStorage:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @cached_property
    def client(self):
        options = {
            "region_name": self.settings.s3_region,
            "config": Config(s3={"addressing_style": "path"}),
        }
        if self.settings.s3_endpoint_url:
            options["endpoint_url"] = self.settings.s3_endpoint_url
        if self.settings.s3_access_key_id:
            options["aws_access_key_id"] = self.settings.s3_access_key_id
        if self.settings.s3_secret_access_key:
            options["aws_secret_access_key"] = self.settings.s3_secret_access_key
        return boto3.client("s3", **options)

    def check_ready(self) -> None:
        self.client.head_bucket(Bucket=self.settings.s3_bucket)

    def put(self, key: str, content: bytes, media_type: str) -> None:
        options = {
            "Bucket": self.settings.s3_bucket,
            "Key": key,
            "Body": content,
            "ContentType": media_type,
        }
        if not self.settings.s3_endpoint_url:
            options["ServerSideEncryption"] = "AES256"
        self.client.put_object(
            **options,
        )

    def get(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.settings.s3_bucket, Key=key)
        body = response["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.settings.s3_bucket, Key=key)
