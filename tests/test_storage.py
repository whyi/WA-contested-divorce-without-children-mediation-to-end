import unittest
from unittest.mock import Mock

from app.config import Settings
from app.storage import ObjectStorage


class ObjectStorageTests(unittest.TestCase):
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
