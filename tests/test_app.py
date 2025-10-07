import sqlite3
import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create a Flask app instance configured to use a temporary SQLite DB and initialize schema."""
    app = create_app()
    db_path = tmp_path / "test.db"
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        DATABASE=str(db_path),
    )

    # Initialize schema with UNIQUE constraint on email to exercise IntegrityError handling
    conn = sqlite3.connect(app.config["DATABASE"])
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.commit()
    conn.close()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_index_returns_200_and_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    # Basic content checks from template
    assert b"Fullname" in resp.data
    assert b"Phone" in resp.data
    assert b"Email" in resp.data


def test_index_displays_contacts_from_db(app, client):
    # Seed a contact directly into the temp DB
    conn = sqlite3.connect(app.config["DATABASE"])
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


def test_add_contact_inserts_and_redirects(client, app):
    resp = client.post(
        "/add_contact",
        data={"fullname": "Bob", "phone": "111-222", "email": "bob@example.com"},
        follow_redirects=False,
    )
    # Should redirect back to index
    assert resp.status_code in (302, 303)

    # Verify it was inserted
    conn = sqlite3.connect(app.config["DATABASE"])
    cur = conn.cursor()
    cur.execute(
        "SELECT fullname, phone, email FROM contacts WHERE email=?",
        ("bob@example.com",),
    )
    row = cur.fetchone()
    conn.close()
    assert row == ("Bob", "111-222", "bob@example.com")


def test_add_contact_flashes_success_message(client):
    # Trigger the POST
    resp = client.post(
        "/add_contact",
        data={"fullname": "Carol", "phone": "222-333", "email": "carol@example.com"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)

    # Inspect session for flashed messages
    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
    # _flashes is a list of (category, message)
    assert any((cat == "success" and "Contact added successfully!" in msg) for cat, msg in flashes)


def test_add_contact_duplicate_email_flashes_error(client):
    # First insert
    client.post(
        "/add_contact",
        data={"fullname": "Dan", "phone": "333-444", "email": "dup@example.com"},
        follow_redirects=False,
    )
    # Attempt duplicate
    resp = client.post(
        "/add_contact",
        data={"fullname": "Dan 2", "phone": "555-666", "email": "dup@example.com"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)

    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
    assert any((cat == "error" and "This email already exists." in msg) for cat, msg in flashes)
