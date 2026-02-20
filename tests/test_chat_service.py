"""Tests for ChatService — Grapple AI chat session & message management."""

from rivaflow.core.services.chat_service import ChatService

# ---------------------------------------------------------------------------
# Session tests
# ---------------------------------------------------------------------------


def test_create_session(temp_db, test_user):
    """Creating a session returns a dict with an 'id' key."""
    svc = ChatService()
    result = svc.create_session(user_id=test_user["id"])

    assert isinstance(result, dict)
    assert "id" in result
    assert result["title"] == "New Chat"
    assert result["user_id"] == test_user["id"]


def test_create_session_with_title(temp_db, test_user):
    """Creating a session with a custom title stores it."""
    svc = ChatService()
    result = svc.create_session(user_id=test_user["id"], title="My Session")

    assert result["title"] == "My Session"


def test_get_session_by_id(temp_db, test_user):
    """Getting a session by ID returns the correct session."""
    svc = ChatService()
    created = svc.create_session(user_id=test_user["id"])

    fetched = svc.get_session_by_id(created["id"], test_user["id"])

    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["title"] == "New Chat"


def test_get_nonexistent_session_returns_none(temp_db, test_user):
    """Getting a non-existent session returns None."""
    svc = ChatService()
    result = svc.get_session_by_id("no-such-id", test_user["id"])

    assert result is None


def test_get_sessions_by_user(temp_db, test_user):
    """Listing sessions by user returns all created sessions."""
    svc = ChatService()
    svc.create_session(user_id=test_user["id"], title="A")
    svc.create_session(user_id=test_user["id"], title="B")
    svc.create_session(user_id=test_user["id"], title="C")

    sessions = svc.get_sessions_by_user(test_user["id"])

    assert len(sessions) == 3
    titles = {s["title"] for s in sessions}
    assert titles == {"A", "B", "C"}


def test_get_sessions_by_user_respects_limit(temp_db, test_user):
    """Listing sessions with limit returns at most that many."""
    svc = ChatService()
    for i in range(5):
        svc.create_session(user_id=test_user["id"], title=f"S{i}")

    sessions = svc.get_sessions_by_user(test_user["id"], limit=2)

    assert len(sessions) == 2


def test_update_session_stats(temp_db, test_user):
    """Updating session stats increments the counters."""
    svc = ChatService()
    created = svc.create_session(user_id=test_user["id"])

    ok = svc.update_session_stats(
        session_id=created["id"],
        message_count_delta=3,
        tokens_delta=150,
        cost_delta=0.005,
    )

    assert ok is True

    updated = svc.get_session_by_id(created["id"], test_user["id"])
    assert updated["message_count"] == 3
    assert updated["total_tokens"] == 150
    assert float(updated["total_cost_usd"]) > 0


def test_update_session_title(temp_db, test_user):
    """Updating a session title persists the new title."""
    svc = ChatService()
    created = svc.create_session(user_id=test_user["id"])

    ok = svc.update_session_title(created["id"], test_user["id"], "Renamed")
    assert ok is True

    fetched = svc.get_session_by_id(created["id"], test_user["id"])
    assert fetched["title"] == "Renamed"


def test_delete_session(temp_db, test_user):
    """Deleting a session removes it from the database."""
    svc = ChatService()
    created = svc.create_session(user_id=test_user["id"])

    ok = svc.delete_session(created["id"], test_user["id"])
    assert ok is True

    fetched = svc.get_session_by_id(created["id"], test_user["id"])
    assert fetched is None


def test_delete_nonexistent_session(temp_db, test_user):
    """Deleting a session that does not exist returns False."""
    svc = ChatService()
    ok = svc.delete_session("no-such-id", test_user["id"])

    assert ok is False


# ---------------------------------------------------------------------------
# Message tests
# ---------------------------------------------------------------------------


def test_create_message(temp_db, test_user):
    """Creating a message returns a dict with expected fields."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])

    msg = svc.create_message(
        session_id=session["id"],
        role="user",
        content="Hello, coach!",
        input_tokens=10,
        output_tokens=0,
        cost_usd=0.001,
    )

    assert isinstance(msg, dict)
    assert "id" in msg
    assert msg["role"] == "user"
    assert msg["content"] == "Hello, coach!"
    assert msg["input_tokens"] == 10


def test_get_messages_by_session(temp_db, test_user):
    """Getting messages returns them in chronological order."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])

    svc.create_message(session["id"], "user", "Question 1")
    svc.create_message(session["id"], "assistant", "Answer 1")
    svc.create_message(session["id"], "user", "Question 2")

    messages = svc.get_messages_by_session(session["id"])

    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["content"] == "Question 2"


def test_count_messages_by_session(temp_db, test_user):
    """Counting messages returns the correct number."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])

    assert svc.count_messages_by_session(session["id"]) == 0

    svc.create_message(session["id"], "user", "Msg 1")
    svc.create_message(session["id"], "assistant", "Msg 2")

    assert svc.count_messages_by_session(session["id"]) == 2


def test_get_recent_context(temp_db, test_user):
    """Recent context returns role/content dicts with expected keys."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])

    svc.create_message(session["id"], "user", "Q1")
    svc.create_message(session["id"], "assistant", "A1")
    svc.create_message(session["id"], "user", "Q2")

    context = svc.get_recent_context(session["id"], max_messages=2)

    assert len(context) == 2
    # Each item has only 'role' and 'content'
    for item in context:
        assert set(item.keys()) == {"role", "content"}
    # Roles should alternate (user/assistant or assistant/user)
    roles = [c["role"] for c in context]
    assert all(r in ("user", "assistant") for r in roles)


def test_get_recent_context_limits_results(temp_db, test_user):
    """Recent context respects max_messages limit."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])

    svc.create_message(session["id"], "user", "Q1")
    svc.create_message(session["id"], "assistant", "A1")
    svc.create_message(session["id"], "user", "Q2")
    svc.create_message(session["id"], "assistant", "A2")
    svc.create_message(session["id"], "user", "Q3")

    context = svc.get_recent_context(session["id"], max_messages=3)

    assert len(context) == 3
