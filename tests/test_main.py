import importlib.util
import sys
import types
import unittest
from pathlib import Path


def load_main_with_stubs():
    sys.modules["loguru"] = types.SimpleNamespace(logger=types.SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        success=lambda *args, **kwargs: None,
    ))
    sys.modules["DrissionPage"] = types.SimpleNamespace(
        ChromiumOptions=object,
        Chromium=object,
    )
    sys.modules["tabulate"] = types.SimpleNamespace(tabulate=lambda *args, **kwargs: "")
    sys.modules["curl_cffi"] = types.SimpleNamespace(requests=types.SimpleNamespace(Session=object))
    sys.modules["bs4"] = types.SimpleNamespace(BeautifulSoup=object)
    sys.modules["notify"] = types.SimpleNamespace(NotificationManager=object)

    module_path = Path(__file__).resolve().parents[1] / "main.py"
    spec = importlib.util.spec_from_file_location("main_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CookieJar:
    def __init__(self):
        self.cleared = False

    def clear(self):
        self.cleared = True


class LoginFallbackTests(unittest.TestCase):
    def test_cookie_failure_clears_session_cookies_before_password_login(self):
        main = load_main_with_stubs()
        main.COOKIES = "stale=cookie"
        main.BROWSE_ENABLED = False

        class Browser(main.LinuxDoBrowser):
            def __init__(self):
                self.session = types.SimpleNamespace(cookies=CookieJar())
                self.page = types.SimpleNamespace(close=lambda: None)
                self.browser = types.SimpleNamespace(quit=lambda: None)
                self.clear_seen_by_login = None

            def login_with_cookies(self, cookie_str):
                return False

            def login(self):
                self.clear_seen_by_login = self.session.cookies.cleared
                return True

            def print_connect_info(self):
                pass

            def send_notifications(self, browse_enabled):
                pass

        browser = Browser()

        self.assertTrue(browser.run())
        self.assertTrue(browser.clear_seen_by_login)

    def test_does_not_browse_when_all_login_methods_fail(self):
        main = load_main_with_stubs()
        main.COOKIES = "stale=cookie"
        main.BROWSE_ENABLED = True

        class Browser(main.LinuxDoBrowser):
            def __init__(self):
                self.session = types.SimpleNamespace(cookies=CookieJar())
                self.page = types.SimpleNamespace(close=lambda: None)
                self.browser = types.SimpleNamespace(quit=lambda: None)
                self.browsed = False

            def login_with_cookies(self, cookie_str):
                return False

            def login(self):
                return False

            def click_topic(self):
                self.browsed = True
                return True

        browser = Browser()

        self.assertFalse(browser.run())
        self.assertFalse(browser.browsed)


if __name__ == "__main__":
    unittest.main()
