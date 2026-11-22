import unittest
from unittest.mock import Mock, patch

from scrape import scrape_github_trending


class TrendingRequestTest(unittest.TestCase):
    @patch("scrape.requests.get")
    def test_filters_reach_github(self, get):
        get.return_value = Mock(text="<html></html>")

        scrape_github_trending(language="Python", spoken_lang="en", since="weekly")

        args, kwargs = get.call_args
        self.assertEqual(args[0], "https://github.com/trending/python")
        self.assertEqual(kwargs["params"], {"spoken_language_code": "en", "since": "weekly"})

    @patch("scrape.requests.get")
    def test_daily_uses_default_trending_page(self, get):
        get.return_value = Mock(text="<html></html>")

        scrape_github_trending()

        args, kwargs = get.call_args
        self.assertEqual(args[0], "https://github.com/trending")
        self.assertEqual(kwargs["params"], {})


if __name__ == "__main__":
    unittest.main()
