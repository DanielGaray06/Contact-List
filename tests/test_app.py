import os
import sqlite3
import types
import pytest

import app as app_module
from app import app as flask_app


@pytest.fixture
def app_tmp_db(tmp_path, monkeypatch):
    """Configure the Flask app to use a temporary SQLite DB and initialize schema."""
    db_path = tmp_path / "test.db"
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        DATABASE=str(db_path),
    )

    # Initialize schema
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

    yield flask_app


@pytest.fixture
def client(app_tmp_db):
    return app_tmp_db.test_client()


def test_index_returns_200_and_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    # Basic content checks from template
    assert b"Fullname" in resp.data
    assert b"Phone" in resp.data
    assert b"Email" in resp.data


def test_index_displays_contacts_from_db(client, app_tmp_db):
    # Seed a contact directly into the temp DB
    conn = sqlite3.connect(app_tmp_db.config["DATABASE"])
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO contacts (fullname, phone, email) VALUES (?, ?, ?)",
        ("Alice", "123-456", "alice@example.com"),
    )
    conn.commit()
    conn.close()

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Alice" in resp.data
    assert b"123-456" in resp.data
    assert b"alice@example.com" in resp.data


def test_add_contact_inserts_and_redirects(client, app_tmp_db):
    resp = client.post(
        "/add_contact",
        data={"fullname": "Bob", "phone": "111-222", "email": "bob@example.com"},
        follow_redirects=False,
    )
    # Should redirect back to index
    assert resp.status_code in (302, 303)

    # Verify it was inserted
    conn = sqlite3.connect(app_tmp_db.config["DATABASE"])
    cur = conn.cursor()
    cur.execute(
        "SELECT fullname, phone, email FROM contacts WHERE fullname=?",
        ("Bob",),
    )
    row = cur.fetchone()
    conn.close()
    assert row == ("Bob", "111-222", "bob@example.com")


def test_add_contact_flashes_success_message(client):
    # Trigger the POST
    resp = client.post(
        "/add_contact",
        data={"fullname": "Carol", "phone": "222-333", "email": "carol@example.com"},
    )
    assert resp.status_code in (302, 303)

    # Inspect session for flashed messages
    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
    # _flashes is a list of (category, message)
    assert any("Contacts added successfully" in msg for _cat, msg in flashes)


class _FakeCursor:
    def execute(self, *args, **kwargs):
        return None

    def fetchall(self, *args, **kwargs):
        return []


class _FakeConn:
    def __init__(self):
        self.closed = False
        self.committed = False

    def cursor(self):
        return _FakeCursor()

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def test_index_closes_connection(monkeypatch, app_tmp_db):
    fake = _FakeConn()
    monkeypatch.setattr(app_module, "get_db_connection", lambda: fake)

    client = app_tmp_db.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    # Expect connection to be closed by the route handler
    assert fake.closed is True


def test_add_commits_and_closes(monkeypatch, app_tmp_db):
    fake = _FakeConn()
    monkeypatch.setattr(app_module, "get_db_connection", lambda: fake)

    client = app_tmp_db.test_client()
    resp = client.post(
        "/add_contact",
        data={"fullname": "Zed", "phone": "999-000", "email": "zed@example.com"},
    )
    assert resp.status_code in (302, 303)
    assert fake.committed is True
    assert fake.closed is True
