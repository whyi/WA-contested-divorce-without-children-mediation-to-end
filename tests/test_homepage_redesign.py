import unittest

from fastapi.testclient import TestClient

from app.main import app


class HomepageRedesignTests(unittest.TestCase):
    def test_homepage_has_redesigned_hero_and_expectation_disclosure(self) -> None:
        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('id="hero-title">Clarity for the <em>next chapter.</em></h1>', page)
        self.assertIn('class="homepage-expectations"', page)
        self.assertIn("Structure, not legal strategy.", page)
        self.assertIn("pending qualified counsel review", page.lower())
        self.assertIn("not legal advice or representation", page.lower())
        self.assertIn("cannot guarantee correctness, fairness, acceptance", page.lower())

    def test_redesign_preserves_account_and_demo_entries(self) -> None:
        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('id="account-entry" href="#account"', page)
        self.assertIn('id="demo1-entry" href="/demo/start?source=demo1"', page)
        self.assertIn('id="demo2-entry" href="/demo/start?source=demo2"', page)


if __name__ == "__main__":
    unittest.main()
