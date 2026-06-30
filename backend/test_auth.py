import unittest

from fastapi.testclient import TestClient

from backend.app import app


class AuthEndpointsTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_login_accepts_dummy_credentials(self):
        response = self.client.post(
            "/api/login",
            json={"username": "user", "password": "password"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"], "user")
        self.assertIn("token", data)

    def test_logout_invalidates_token(self):
        login_response = self.client.post(
            "/api/login",
            json={"username": "user", "password": "password"},
        )
        token = login_response.json()["token"]

        logout_response = self.client.post(
            "/api/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(logout_response.status_code, 200)

        me_response = self.client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me_response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
