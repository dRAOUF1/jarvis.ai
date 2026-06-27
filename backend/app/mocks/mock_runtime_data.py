"""Mock runtime data — canned demo responses."""

MOCK_RESPONSES: dict[str, str] = {
    "What was my last activity?": (
        "Your last activity was a 5km run completed in 25:00. "
        "That's a solid 5:00/km pace! Keep it up. 🏃"
    ),
    "hello": (
        "Hey there! I'm your personal sports coach. "
        "How are you feeling today? Ready to crush some goals?"
    ),
    "how am I doing?": (
        "Let me check your recent stats. You ran 5km yesterday in 25 minutes — "
        "great consistency! Your weekly volume is building nicely. "
        "I'd suggest adding a tempo run this week."
    ),
}

DEFAULT_RESPONSE = (
    "I'm your sports coach agent. I can help you analyze your activities, "
    "track progress, and plan your training. What would you like to know?"
)


def get_demo_response(message: str) -> str:
    """Return a canned response for the demo (no API key needed)."""
    return MOCK_RESPONSES.get(message, DEFAULT_RESPONSE)
