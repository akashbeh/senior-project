import re
import unittest

class TestRegexMatches(unittest.TestCase):
    def test_regex_matches(self):
        # Example: Match strings that look like an email
        ticker_regex = re.compile(r'(?<!\b[A-Z]{2}\s)(?<!\b[A-Z]{3}\s)(?<!\b[A-Z]{4}\s)(?<!\b[A-Z]{5}\s)(\b(?:\$[A-Z]{1,5}|[A-Z]{2,5})\b)(?!\s[A-Z]{2,}\b)')

        # Strings we expect to match
        should_match = [
            "I am an APPL. FAN",
            "I love APPL",
            "my_email123@sub.domain.org"
        ]

        # Strings we expect NOT to match
        should_not_match = [
            "plainaddress",
            "missing@domain",
            "@nouser.com",
            "user@.com"
        ]

        for s in should_match:
            self.assertIsNotNone(ticker_regex.search(s), f"Failed to match: {s}")

        for s in should_not_match:
            self.assertIsNone(ticker_regex.search(s), f"Incorrectly matched: {s}")

if __name__ == "__main__":
    unittest.main()
