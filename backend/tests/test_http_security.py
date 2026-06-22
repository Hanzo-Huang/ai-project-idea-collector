import socket
import unittest
from unittest.mock import patch

from app.services.http import validate_public_url


class PublicUrlValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_loopback_ip(self):
        with self.assertRaisesRegex(ValueError, "private network"):
            await validate_public_url("http://127.0.0.1/admin")

    async def test_rejects_localhost(self):
        with self.assertRaisesRegex(ValueError, "private network"):
            await validate_public_url("http://localhost:8000/api/settings")

    async def test_rejects_url_credentials(self):
        with self.assertRaisesRegex(ValueError, "credentials"):
            await validate_public_url("https://user:password@example.com")

    async def test_accepts_public_ip(self):
        self.assertEqual(await validate_public_url("https://8.8.8.8/example"), "https://8.8.8.8/example")

    async def test_rejects_hostname_with_private_dns_result(self):
        records = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.2", 443)),
        ]
        with patch("socket.getaddrinfo", return_value=records):
            with self.assertRaisesRegex(ValueError, "private network"):
                await validate_public_url("https://example.com")


if __name__ == "__main__":
    unittest.main()

