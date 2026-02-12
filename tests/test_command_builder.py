import unittest
import sys
import os

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ffuf_gui.runner import runner

class TestFfufCommandBuilder(unittest.TestCase):
    def test_basic_url(self):
        config = {"url": "http://example.com/FUZZ"}
        cmd = runner.build_command(config)
        self.assertIn("-u", cmd)
        self.assertIn("http://example.com/FUZZ", cmd)
        self.assertIn("-json", cmd)

    def test_wordlists(self):
        config = {
            "url": "http://example.com/FUZZ",
            "wordlists": [
                {"path": "/usr/share/wordlists/rockyou.txt", "keyword": "FUZZ"},
                {"path": "users.txt", "keyword": "USER"}
            ]
        }
        cmd = runner.build_command(config)
        self.assertIn("-w", cmd)
        self.assertIn("/usr/share/wordlists/rockyou.txt:FUZZ", cmd)
        self.assertIn("users.txt:USER", cmd)

    def test_http_options(self):
        config = {
            "url": "http://example.com/FUZZ",
            "method": "POST",
            "headers": ["Cookie: a=b", "Auth: Bearer 123"],
            "data": "user=admin"
        }
        cmd = runner.build_command(config)
        self.assertIn("-X", cmd)
        self.assertIn("POST", cmd)
        self.assertIn("-H", cmd)
        self.assertIn("Cookie: a=b", cmd)
        self.assertIn("-d", cmd)
        self.assertIn("user=admin", cmd)

    def test_filters_matchers(self):
        config = {
            "url": "http://example.com",
            "mc": "200",
            "fc": "404",
            "fs": "100"
        }
        cmd = runner.build_command(config)
        self.assertIn("-mc", cmd)
        self.assertIn("200", cmd)
        self.assertIn("-fc", cmd)
        self.assertIn("404", cmd)
        self.assertIn("-fs", cmd)
        self.assertIn("100", cmd)

    def test_recursion(self):
        config = {
            "url": "http://example.com/FUZZ",
            "recursion": True,
            "recursion_depth": 2
        }
        cmd = runner.build_command(config)
        self.assertIn("-recursion", cmd)
        self.assertIn("-recursion-depth", cmd)
        self.assertIn("2", cmd)

if __name__ == '__main__':
    unittest.main()
