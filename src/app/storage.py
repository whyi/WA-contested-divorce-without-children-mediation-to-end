from functools import cached_property
import json
from urllib.parse import urlparse

import boto3
from botocore.config import Config

from app.config import Settings, get_settings


class ObjectStorage:
    DELETION_LEDGER_PREFIX = "casework-deletions/v1/"
    DELETION_LEDGER_MARKER = f"{DELETION_LEDGER_PREFIX}initialized.json"

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
        if self.settings.case_data_enabled:
            self.check_deletion_ledger_ready()

    def check_deletion_ledger_ready(self) -> None:
        self.client.head_bucket(Bucket=self.settings.deletion_ledger_bucket)
        versioning = self.client.get_bucket_versioning(
            Bucket=self.settings.deletion_ledger_bucket
        )
        if versioning.get("Status") != "Enabled":
            raise RuntimeError("The permanent-deletion ledger bucket must have versioning enabled.")
        if not self.deletion_ledger_initialized():
            raise RuntimeError("The permanent-deletion ledger has not been initialized.")

    def deletion_ledger_initialized(self) -> bool:
        try:
            self.client.head_object(
                Bucket=self.settings.deletion_ledger_bucket,
                Key=self.DELETION_LEDGER_MARKER,
            )
        except self.client.exceptions.ClientError as error:
            if error.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise
        return True

    def initialize_deletion_ledger(self, entries: list[dict[str, object]]) -> None:
        self.client.head_bucket(Bucket=self.settings.deletion_ledger_bucket)
        versioning = self.client.get_bucket_versioning(
            Bucket=self.settings.deletion_ledger_bucket
        )
        if versioning.get("Status") != "Enabled":
            raise RuntimeError("The permanent-deletion ledger bucket must have versioning enabled.")
        try:
            self.client.head_object(
                Bucket=self.settings.deletion_ledger_bucket,
                Key=self.DELETION_LEDGER_MARKER,
            )
        except self.client.exceptions.ClientError as error:
            if error.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 404:
                raise
        else:
            raise RuntimeError("The permanent-deletion ledger is already initialized.")
        for entry in entries:
            self.record_deletion_tombstone(
                entry["scope_type"],
                entry["scope_id"],
                entry["initiated_by"],
                entry.get("object_keys", []),
                require_initialized=False,
            )
        self._put_ledger_object(
            self.DELETION_LEDGER_MARKER,
            json.dumps({"schema_version": 1}, separators=(",", ":")).encode(),
        )

    def record_deletion_tombstone(
        self,
        scope_type: str,
        scope_id: str,
        initiated_by: str,
        object_keys: list[str] | None = None,
        *,
        require_initialized: bool = True,
    ) -> None:
        if require_initialized and not self.deletion_ledger_initialized():
            raise RuntimeError("The permanent-deletion ledger has not been initialized.")
        key = f"{self.DELETION_LEDGER_PREFIX}entries/{scope_type}/{scope_id}.json"
        payload = {
            "schema_version": 1,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "initiated_by": initiated_by,
            "object_keys": object_keys or [],
        }
        try:
            body = self.client.get_object(
                Bucket=self.settings.deletion_ledger_bucket,
                Key=key,
            )["Body"]
        except self.client.exceptions.ClientError as error:
            if error.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 404:
                raise
        else:
            try:
                existing = json.loads(body.read())
            finally:
                body.close()
            if any(
                existing.get(key) != payload.get(key)
                for key in (
                    "schema_version",
                    "scope_type",
                    "scope_id",
                    "initiated_by",
                    "object_keys",
                )
            ):
                raise RuntimeError("The permanent-deletion ledger entry conflicts with this request.")
            return
        self._put_ledger_object(
            key,
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
        )

    def read_deletion_tombstones(self) -> list[dict[str, object]]:
        self.check_deletion_ledger_ready()
        prefix = f"{self.DELETION_LEDGER_PREFIX}entries/"
        entries: list[dict[str, object]] = []
        continuation_token = None
        while True:
            request = {
                "Bucket": self.settings.deletion_ledger_bucket,
                "Prefix": prefix,
            }
            if continuation_token is not None:
                request["ContinuationToken"] = continuation_token
            page = self.client.list_objects_v2(**request)
            for item in page.get("Contents", []):
                body = self.client.get_object(
                    Bucket=self.settings.deletion_ledger_bucket,
                    Key=item["Key"],
                )["Body"]
                try:
                    entry = json.loads(body.read())
                finally:
                    body.close()
                entries.append(entry)
            if not page.get("IsTruncated"):
                return entries
            continuation_token = page.get("NextContinuationToken")
            if not continuation_token:
                raise RuntimeError("The permanent-deletion ledger returned an invalid continuation token.")

    def _put_ledger_object(self, key: str, content: bytes) -> None:
        options = {
            "Bucket": self.settings.deletion_ledger_bucket,
            "Key": key,
            "Body": content,
            "ContentType": "application/json",
        }
        if not self.settings._uses_local_s3_endpoint():
            if not (self.settings.s3_kms_key_id or "").strip():
                raise RuntimeError("S3_KMS_KEY_ID is required for the permanent-deletion ledger.")
            options["ServerSideEncryption"] = "aws:kms"
            options["SSEKMSKeyId"] = self.settings.s3_kms_key_id
        self.client.put_object(**options)

    def put(self, key: str, content: bytes, media_type: str) -> None:
        options = {
            "Bucket": self.settings.s3_bucket,
            "Key": key,
            "Body": content,
            "ContentType": media_type,
        }
        local_endpoint = False
        if self.settings.s3_endpoint_url:
            endpoint = urlparse(self.settings.s3_endpoint_url)
            local_endpoint = (
                endpoint.scheme == "http"
                and endpoint.hostname is not None
                and endpoint.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
            )
        if not local_endpoint:
            if not (self.settings.s3_kms_key_id or "").strip():
                raise RuntimeError("S3_KMS_KEY_ID is required for encrypted object storage.")
            options["ServerSideEncryption"] = "aws:kms"
            options["SSEKMSKeyId"] = self.settings.s3_kms_key_id
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

    def delete_all_versions(self, key: str) -> None:
        versions = []
        key_marker = None
        version_id_marker = None
        while True:
            request = {
                "Bucket": self.settings.s3_bucket,
                "Prefix": key,
            }
            if key_marker is not None:
                request["KeyMarker"] = key_marker
            if version_id_marker is not None:
                request["VersionIdMarker"] = version_id_marker
            page = self.client.list_object_versions(**request)
            versions.extend(
                {"Key": item["Key"], "VersionId": item["VersionId"]}
                for item in page.get("Versions", [])
                if item.get("Key") == key
            )
            versions.extend(
                {"Key": item["Key"], "VersionId": item["VersionId"]}
                for item in page.get("DeleteMarkers", [])
                if item.get("Key") == key
            )
            if not page.get("IsTruncated"):
                break
            key_marker = page.get("NextKeyMarker")
            version_id_marker = page.get("NextVersionIdMarker")
            if key_marker is None:
                raise RuntimeError("S3 object-version listing returned an invalid continuation marker.")

        for offset in range(0, len(versions), 1000):
            response = self.client.delete_objects(
                Bucket=self.settings.s3_bucket,
                Delete={"Objects": versions[offset : offset + 1000], "Quiet": True},
            )
            if response.get("Errors"):
                raise RuntimeError("S3 object version purge failed.")

        remaining = self.client.list_object_versions(
            Bucket=self.settings.s3_bucket,
            Prefix=key,
        )
        if any(item.get("Key") == key for item in remaining.get("Versions", [])) or any(
            item.get("Key") == key for item in remaining.get("DeleteMarkers", [])
        ):
            raise RuntimeError("S3 object version purge could not be verified.")
