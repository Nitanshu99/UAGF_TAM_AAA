"""The browser session signs into the stack's own services with the .env credentials."""
from __future__ import annotations

from scripts.bootstrap.browser.login import sign_in_grafana, sign_in_langfuse, sign_in_minio
from scripts.bootstrap.browser.tabs import service_tabs


class _Reply:
    def __init__(self, ok: bool) -> None:
        self.ok = ok


class _Context:
    """Records the JSON logins posted on the shared cookie jar."""

    def __init__(self, ok: bool = True) -> None:
        self.posts: list[tuple[str, dict]] = []
        self.request = self
        self._ok = ok

    def post(self, url: str, data: dict) -> _Reply:
        self.posts.append((url, data))
        return _Reply(self._ok)


def test_minio_and_grafana_log_in_through_their_apis() -> None:
    ctx = _Context()
    assert sign_in_minio(ctx, "http://localhost:9001", "aaa-minio", "pw") is True
    assert sign_in_grafana(ctx, "http://localhost:3002", "admin-pw") is True
    assert ctx.posts == [
        ("http://localhost:9001/api/v1/login", {"accessKey": "aaa-minio", "secretKey": "pw"}),
        ("http://localhost:3002/login", {"user": "admin", "password": "admin-pw"}),
    ]


def test_a_refused_or_failing_login_is_reported_not_raised() -> None:
    assert sign_in_minio(_Context(ok=False), "http://localhost:9001", "u", "p") is False

    class _Broken(_Context):
        def post(self, url: str, data: dict) -> _Reply:
            raise ConnectionError("down")

    assert sign_in_grafana(_Broken(), "http://localhost:3002", "x") is False


def test_langfuse_without_credentials_asks_for_a_manual_sign_in() -> None:
    note = sign_in_langfuse(object(), {})
    assert "sign in by hand" in note


def test_langfuse_form_is_filled_and_the_sessions_page_opened() -> None:
    calls: list = []

    class _Locator:
        def __init__(self, name: str) -> None:
            self.name = name

        def fill(self, value: str) -> None:
            calls.append(("fill", self.name, value))

        def click(self) -> None:
            calls.append(("click", self.name))

    class _Page:
        url = "http://localhost:3003/auth/sign-in"

        def locator(self, selector: str) -> _Locator:
            found = _Locator("Email" if "email" in selector else "Password")
            found.first = found  # type: ignore[attr-defined]
            return found

        def get_by_role(self, role: str, name: str, exact: bool = False) -> _Locator:
            return _Locator(name)

        def wait_for_url(self, predicate, timeout: int) -> None:
            self.url = "http://localhost:3003/"
            assert predicate(self.url)

        def goto(self, url: str, **_: object) -> None:
            calls.append(("goto", url))

    env = {"LANGFUSE_INIT_USER_EMAIL": "admin@aaa.local", "LANGFUSE_INIT_USER_PASSWORD": "s3cret",
           "LANGFUSE_INIT_PROJECT_ID": "aaa-audit"}
    note = sign_in_langfuse(_Page(), env)
    assert calls == [("fill", "Email", "admin@aaa.local"), ("fill", "Password", "s3cret"),
                     ("click", "Sign in"), ("goto", "http://localhost:3003/project/aaa-audit/sessions")]
    assert note.startswith("signed in as admin@aaa.local")


def test_the_langfuse_tab_carries_the_sign_in_hook_and_minio_opens_the_browser() -> None:
    tabs = {t.name.split(" ·")[0]: t for t in service_tabs({})}
    assert tabs["Langfuse"].after is sign_in_langfuse
    assert tabs["MinIO"].url.endswith("/browser")
