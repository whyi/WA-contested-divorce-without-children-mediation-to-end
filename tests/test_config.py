import unittest

from app.config import Settings


class SettingsTests(unittest.TestCase):
    def test_bedrock_configuration_is_optional(self) -> None:
        settings = Settings()

        self.assertIsNone(settings.bedrock_model_id)
        self.assertIsNone(settings.bedrock_region)

    def test_bedrock_model_and_region_can_be_configured(self) -> None:
        settings = Settings(
            bedrock_model_id="us.amazon.nova-lite-v1:0",
            bedrock_region="us-west-2",
        )

        self.assertEqual(settings.bedrock_model_id, "us.amazon.nova-lite-v1:0")
        self.assertEqual(settings.bedrock_region, "us-west-2")

if __name__ == "__main__":
    unittest.main()
