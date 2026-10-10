import unittest

from lan_proxy import _client_ip, _forward_headers


class LanProxyTests(unittest.TestCase):
    def test_client_ip_normalizes_ipv4_mapped_ipv6(self):
        self.assertEqual(_client_ip("::ffff:192.0.2.15"), "192.0.2.15")

    def test_forward_headers_overwrites_untrusted_forwarded_addresses(self):
        headers = {
            "Accept": "application/json",
            "Connection": "keep-alive, X-Trace",
            "Content-Length": "999",
            "Forwarded": "for=198.51.100.2",
            "X-Forwarded-For": "198.51.100.3",
            "X-Forwarded-Host": "attacker.example",
            "X-Trace": "private-hop",
        }

        forwarded = _forward_headers(headers, "192.0.2.15", 12)

        self.assertEqual(forwarded["Accept"], "application/json")
        self.assertEqual(forwarded["Content-Length"], "12")
        self.assertEqual(forwarded["X-Forwarded-For"], "192.0.2.15")
        self.assertEqual(forwarded["X-Real-IP"], "192.0.2.15")
        self.assertNotIn("Forwarded", forwarded)
        self.assertNotIn("X-Forwarded-Host", forwarded)
        self.assertNotIn("X-Trace", forwarded)


if __name__ == "__main__":
    unittest.main()
