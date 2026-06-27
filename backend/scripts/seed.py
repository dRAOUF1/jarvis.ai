"""Reset DB to known demo state.

Creates the demo user if it doesn't exist.
Run against a running Supabase instance.
"""

from app.config import settings
from app.db.client import get_supabase


def seed() -> None:
    db = get_supabase()

    # Create / update demo user
    db.table("users").upsert({
        "id": settings.demo_user_id,
        "name": "Demo User",
        "email": "demo@jarvis.ai",
    }).execute()

    print(f"Seeded demo user: {settings.demo_user_id}")


if __name__ == "__main__":
    seed()
