"""Guard for the enforced CSP: it must not block the zone's inline JS-detections bootstrap."""

import unittest

import build_indexes as bi


def headers(enforced, report_only="script-src 'self' 'sha256-abc='"):
    return (f"/*\n  Content-Security-Policy: {enforced}\n"
            f"  Content-Security-Policy-Report-Only: {report_only}\n")


class EnforcedCspTest(unittest.TestCase):
    def test_real_headers_pass(self):
        self.assertEqual(bi.csp_enforced_problems(), [])

    def test_unsafe_inline_without_hash_passes(self):
        h = headers("default-src 'self'; script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com")
        self.assertEqual(bi.csp_enforced_problems(h), [])

    def test_hash_in_enforced_line_fails(self):
        h = headers("script-src 'self' 'unsafe-inline' 'sha256-abc='")
        self.assertEqual(len(bi.csp_enforced_problems(h)), 1)

    def test_nonce_in_enforced_line_fails(self):
        h = headers("script-src 'self' 'unsafe-inline' 'nonce-xyz'")
        self.assertEqual(len(bi.csp_enforced_problems(h)), 1)

    def test_missing_unsafe_inline_fails(self):
        h = headers("default-src 'self'; script-src 'self'")
        self.assertEqual(bi.csp_enforced_problems(h), ["script-src has no 'unsafe-inline'"])

    def test_hash_in_report_only_line_is_fine(self):
        h = headers("script-src 'self' 'unsafe-inline'", "script-src 'self' 'sha256-abc='")
        self.assertEqual(bi.csp_enforced_problems(h), [])


if __name__ == "__main__":
    unittest.main()
