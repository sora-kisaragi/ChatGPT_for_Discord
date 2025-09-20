import pytest

from src.conversation_manager import ConversationManager


def test_add_and_trim_history():
    cm = ConversationManager(max_history=5)
    ch = 123

    # set system setting and add many messages
    cm.set_system_setting(ch, "system prompt")
    for i in range(10):
        cm.add_message(ch, "user" if i % 2 == 0 else "assistant", f"m{i}")

    messages = cm.get_messages(ch)
    # total length should not exceed max_history, but include the system message
    assert len(messages) <= 5
    # system message must be preserved as first item
    assert messages[0]["role"] == "system"


def test_reset_conversation_with_setting():
    cm = ConversationManager(max_history=3)
    ch = 456

    cm.set_system_setting(ch, "sys")
    cm.add_message(ch, "user", "hello")
    cm.reset_conversation(ch, "new_sys")
    msgs = cm.get_messages(ch)
    assert len(msgs) == 1
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "new_sys"
