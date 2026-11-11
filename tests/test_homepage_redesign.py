import unittest

from fastapi.testclient import TestClient

from app.main import app


class HomepageRedesignTests(unittest.TestCase):
    def test_homepage_keeps_the_next_chapter_hero(self) -> None:
        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('id="hero-title">Clarity for the <em>next chapter.</em></h1>', page)
        self.assertIn("A guided workspace for organizing the details and questions that matter", page)

    def test_header_offers_distinct_login_and_signup_destinations(self) -> None:
        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('class="nav-cta auth-entry login-entry" id="login-entry" href="/?auth=login"', page)
        self.assertIn('class="nav-cta auth-entry" id="account-entry" href="/?auth=signup"', page)
        self.assertIn(">Log in</a>", page)
        self.assertIn(">Get started <span class=\"arrow\"", page)

    def test_public_home_is_limited_to_a_single_viewport_hero(self) -> None:
        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('dataset.publicLanding = "true"', page)
        self.assertIn('dataset.authView = "true"', page)
        self.assertIn("body[data-public-landing=\"true\"]:not(.authenticated-view) main > section:not(.hero)", page)
        self.assertIn('body[data-public-landing="true"]:not(.authenticated-view) .preview-bar', page)
        self.assertIn("<footer>", page)
        self.assertNotIn('body[data-public-landing="true"]:not(.authenticated-view) footer', page)
        self.assertIn("@media (max-width: 850px)", page)
        self.assertIn('body[data-public-landing="true"]:not(.authenticated-view) .visual-wrap', page)
        self.assertIn('href="/?auth=login"', page)
        self.assertIn('href="/?auth=signup"', page)

    def test_public_navigation_layout_is_selected_before_header_markup(self) -> None:
        client = TestClient(app)
        for path, marker in (
            ("/", 'document.body.dataset.publicLanding = "true"'),
            ("/pricing", 'document.body.dataset.pricingPage = "true"'),
        ):
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                page = response.text
                body = page.index("<body>")
                state = page.index(marker)
                header = page.index('<header class="topbar">')
                self.assertLess(body, state)
                self.assertLess(state, header)

    def test_auth_links_open_the_requested_form_without_changing_auth_endpoints(self) -> None:
        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('new URLSearchParams(window.location.search).get("auth")', page)
        self.assertIn('selectForm(requestedAuthView, false)', page)
        self.assertIn('"/api/auth/signup"', page)
        self.assertIn('"/api/auth/login"', page)

    def test_redesign_preserves_demo_entries_and_signed_in_case_entry(self) -> None:
        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('id="demo1-entry" href="/demo/start?source=demo1"', page)
        self.assertIn('id="demo2-entry" href="/demo/start?source=demo2"', page)
        self.assertIn('link.href = "/?view=case"', page)
        self.assertIn('await enterSignedInAccount(account)', page)


if __name__ == "__main__":
    unittest.main()
