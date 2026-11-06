import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

from botocore.exceptions import ClientError

from app.config import Settings
from app.storage import ObjectStorage


class ObjectStorageTests(unittest.TestCase):
    def test_deletion_ledger_requires_separate_versioned_bucket_and_marker(self) -> None:
        storage = ObjectStorage(
            Settings(
                auth_enabled=True,
                auth_jwt_secret="test-ledger-settings-secret-that-is-long-enough",
                case_data_enabled=True,
                s3_endpoint_url="http://localhost:5000",
            )
        )
        storage.client = Mock()
        storage.client.get_bucket_versioning.return_value = {"Status": "Enabled"}

        storage.check_deletion_ledger_ready()

        storage.client.head_bucket.assert_called_once_with(
            Bucket="mediation-deletion-ledger"
        )
        storage.client.head_object.assert_called_once_with(
            Bucket="mediation-deletion-ledger",
            Key=storage.DELETION_LEDGER_MARKER,
        )

    def test_ready_check_rejects_missing_ledger_initialization_marker(self) -> None:
        storage = ObjectStorage(
            Settings(
                auth_enabled=True,
                auth_jwt_secret="test-ledger-settings-secret-that-is-long-enough",
                case_data_enabled=True,
                s3_endpoint_url="http://localhost:5000",
            )
        )
        storage.client = Mock()
        storage.client.exceptions = SimpleNamespace(ClientError=ClientError)
        storage.client.get_bucket_versioning.return_value = {"Status": "Enabled"}
        storage.client.head_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
            "HeadObject",
        )

        with self.assertRaisesRegex(RuntimeError, "not been initialized"):
            storage.check_deletion_ledger_ready()

    def test_write_deletion_tombstone_is_immutable_and_uses_ledger_bucket(self) -> None:
        storage = ObjectStorage(Settings(s3_endpoint_url="http://localhost:5000"))
        storage.client = Mock()
        storage.client.exceptions = SimpleNamespace(ClientError=ClientError)
        storage.client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
            "GetObject",
        )

        storage.record_deletion_tombstone(
            "case",
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            require_initialized=False,
        )

        request = storage.client.put_object.call_args.kwargs
        self.assertEqual(request["Bucket"], "mediation-deletion-ledger")
        self.assertEqual(
            request["Key"],
            "casework-deletions/v1/entries/case/00000000-0000-0000-0000-000000000001.json",
        )
        self.assertEqual(
            request["Body"],
            b'{"initiated_by":"00000000-0000-0000-0000-000000000002","object_keys":[],"schema_version":1,"scope_id":"00000000-0000-0000-0000-000000000001","scope_type":"case"}',
        )

    def test_write_deletion_tombstone_rejects_changed_object_keys(self) -> None:
        storage = ObjectStorage(Settings(s3_endpoint_url="http://localhost:5000"))
        storage.client = Mock()
        storage.client.exceptions = SimpleNamespace(ClientError=ClientError)
        storage.client.get_object.return_value = {
            "Body": BytesIO(
                b'{"schema_version":1,"scope_type":"case",'
                b'"scope_id":"00000000-0000-0000-0000-000000000001",'
                b'"initiated_by":"00000000-0000-0000-0000-000000000002",'
                b'"object_keys":["case/old.pdf"]}'
            )
        }

        with self.assertRaisesRegex(RuntimeError, "conflicts"):
            storage.record_deletion_tombstone(
                "case",
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002",
                ["case/new.pdf"],
                require_initialized=False,
            )

        storage.client.put_object.assert_not_called()

    def test_ledger_initialization_writes_marker_only_after_backfill(self) -> None:
        storage = ObjectStorage(Settings(s3_endpoint_url="http://localhost:5000"))
        storage.client = Mock()
        storage.client.exceptions = SimpleNamespace(ClientError=ClientError)
        storage.client.get_bucket_versioning.return_value = {"Status": "Enabled"}
        missing_marker = ClientError(
            {"Error": {"Code": "NoSuchKey"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
            "HeadObject",
        )
        storage.client.head_object.side_effect = missing_marker
        storage.client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
            "GetObject",
        )

        storage.initialize_deletion_ledger(
            [
                {
                    "scope_type": "case",
                    "scope_id": "00000000-0000-0000-0000-000000000001",
                    "initiated_by": "00000000-0000-0000-0000-000000000002",
                    "object_keys": ["opaque/document.pdf"],
                }
            ]
        )

        requests = storage.client.put_object.call_args_list
        self.assertEqual(len(requests), 2)
        self.assertIn("entries/case/", requests[0].kwargs["Key"])
        self.assertEqual(requests[1].kwargs["Key"], storage.DELETION_LEDGER_MARKER)

    def test_read_deletion_tombstones_paginates_and_closes_response_bodies(self) -> None:
        storage = ObjectStorage(
            Settings(
                auth_enabled=True,
                auth_jwt_secret="test-ledger-settings-secret-that-is-long-enough",
                case_data_enabled=True,
                s3_endpoint_url="http://localhost:5000",
            )
        )
        storage.client = Mock()
        storage.client.get_bucket_versioning.return_value = {"Status": "Enabled"}
        first_body = BytesIO(b'{"schema_version":1}')
        second_body = BytesIO(b'{"schema_version":1}')
        storage.client.list_objects_v2.side_effect = [
            {
                "Contents": [{"Key": "entry-1"}],
                "IsTruncated": True,
                "NextContinuationToken": "next",
            },
            {"Contents": [{"Key": "entry-2"}], "IsTruncated": False},
        ]
        storage.client.get_object.side_effect = [
            {"Body": first_body},
            {"Body": second_body},
        ]

        entries = storage.read_deletion_tombstones()

        self.assertEqual(entries, [{"schema_version": 1}, {"schema_version": 1}])
        first_body.close()
        second_body.close()
        self.assertEqual(
            storage.client.list_objects_v2.call_args_list[1].kwargs["ContinuationToken"],
            "next",
        )

    def test_production_upload_requests_kms_encryption(self) -> None:
        storage = ObjectStorage(Settings(s3_kms_key_id="arn:aws:kms:us-west-2:123:key/test"))
        client = Mock()
        storage.client = client

        storage.put("case/document.pdf", b"private", "application/pdf")

        client.put_object.assert_called_once_with(
            Bucket="mediation-documents",
            Key="case/document.pdf",
            Body=b"private",
            ContentType="application/pdf",
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId="arn:aws:kms:us-west-2:123:key/test",
        )

    def test_local_loopback_upload_does_not_require_or_send_kms(self) -> None:
        storage = ObjectStorage(Settings(s3_endpoint_url="http://localhost:5000"))
        client = Mock()
        storage.client = client

        storage.put("case/document.pdf", b"private", "application/pdf")

        client.put_object.assert_called_once_with(
            Bucket="mediation-documents",
            Key="case/document.pdf",
            Body=b"private",
            ContentType="application/pdf",
        )

    def test_upload_fails_closed_without_a_kms_key(self) -> None:
        storage = ObjectStorage(Settings())
        storage.client = Mock()

        with self.assertRaisesRegex(RuntimeError, "S3_KMS_KEY_ID"):
            storage.put("case/document.pdf", b"private", "application/pdf")

        storage.client.put_object.assert_not_called()

    def test_read_closes_the_storage_response_body(self) -> None:
        storage = ObjectStorage(Settings())
        body = Mock()
        body.read.return_value = b"private"
        storage.client = Mock()
        storage.client.get_object.return_value = {"Body": body}

        content = storage.get("case/document.pdf")

        self.assertEqual(content, b"private")
        body.close.assert_called_once()

    def test_delete_uses_only_the_configured_bucket_and_object_key(self) -> None:
        storage = ObjectStorage(Settings())
        storage.client = Mock()

        storage.delete("case/document.pdf")

        storage.client.delete_object.assert_called_once_with(
            Bucket="mediation-documents",
            Key="case/document.pdf",
        )

    def test_delete_all_versions_removes_versions_and_delete_markers(self) -> None:
        storage = ObjectStorage(Settings())
        storage.client = Mock()
        storage.client.list_object_versions.side_effect = [
            {
                "Versions": [
                    {"Key": "case/document.pdf", "VersionId": "v2"},
                    {"Key": "case/document.pdf-extra", "VersionId": "other"},
                ],
                "DeleteMarkers": [
                    {"Key": "case/document.pdf", "VersionId": "marker"},
                ],
                "IsTruncated": False,
            },
            {"Versions": [], "DeleteMarkers": [], "IsTruncated": False},
        ]
        storage.client.delete_objects.return_value = {"Deleted": []}

        storage.delete_all_versions("case/document.pdf")

        self.assertEqual(storage.client.list_object_versions.call_count, 2)
        storage.client.delete_objects.assert_called_once_with(
            Bucket="mediation-documents",
            Delete={
                "Objects": [
                    {"Key": "case/document.pdf", "VersionId": "v2"},
                    {"Key": "case/document.pdf", "VersionId": "marker"},
                ],
                "Quiet": True,
            },
        )
        storage.client.delete_object.assert_not_called()

    def test_delete_all_versions_follows_all_version_pages(self) -> None:
        storage = ObjectStorage(Settings())
        storage.client = Mock()
        storage.client.list_object_versions.side_effect = [
            {
                "Versions": [{"Key": "case/document.pdf", "VersionId": "v2"}],
                "IsTruncated": True,
                "NextKeyMarker": "case/document.pdf",
                "NextVersionIdMarker": "v2",
            },
            {
                "Versions": [{"Key": "case/document.pdf", "VersionId": "v1"}],
                "DeleteMarkers": [{"Key": "case/document.pdf", "VersionId": "marker"}],
                "IsTruncated": False,
            },
            {"Versions": [], "DeleteMarkers": [], "IsTruncated": False},
        ]
        storage.client.delete_objects.return_value = {"Deleted": []}

        storage.delete_all_versions("case/document.pdf")

        self.assertEqual(storage.client.list_object_versions.call_count, 3)
        second_request = storage.client.list_object_versions.call_args_list[1].kwargs
        self.assertEqual(second_request["KeyMarker"], "case/document.pdf")
        self.assertEqual(second_request["VersionIdMarker"], "v2")
        self.assertEqual(
            storage.client.delete_objects.call_args.kwargs["Delete"]["Objects"],
            [
                {"Key": "case/document.pdf", "VersionId": "v2"},
                {"Key": "case/document.pdf", "VersionId": "v1"},
                {"Key": "case/document.pdf", "VersionId": "marker"},
            ],
        )

    def test_delete_all_versions_fails_when_version_purge_is_incomplete(self) -> None:
        storage = ObjectStorage(Settings())
        storage.client = Mock()
        storage.client.list_object_versions.return_value = {
            "Versions": [{"Key": "case/document.pdf", "VersionId": "v1"}],
            "IsTruncated": False,
        }
        storage.client.delete_objects.return_value = {
            "Errors": [{"Key": "case/document.pdf", "VersionId": "v1", "Code": "AccessDenied"}]
        }
        storage.client.list_object_versions.side_effect = [
            {
                "Versions": [{"Key": "case/document.pdf", "VersionId": "v1"}],
                "IsTruncated": False,
            }
        ]

        with self.assertRaisesRegex(RuntimeError, "version purge"):
            storage.delete_all_versions("case/document.pdf")


if __name__ == "__main__":
    unittest.main()
