"""Application settings — reads .env / environment variables."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Required — match .env.local names
    anthropic_api_key: str
    supabase_service_role_key: str

    # Supabase URL — accepts either SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL
    supabase_url: str = ""

    # Runtime / provisioner mode toggles
    runtime_mode: Literal["hermes", "mock"] = "mock"
    provisioner_mode: Literal["warmpool", "modal"] = "warmpool"

    # Integrations
    composio_api_key: str = ""

    # Demo / dev
    demo_user_id: str = "demo-user"

    # Hermes gateway pool (match .env.local names)
    hermes_jobcoach_url: str = ""
    hermes_jobcoach_key: str = ""
    hermes_interview_url: str = ""
    hermes_interview_key: str = ""
    # Aliases used by factory / provisioning
    hermes_a_url: str = ""
    hermes_a_key: str = ""
    hermes_b_url: str = ""
    hermes_b_key: str = ""
    hermes_pool_urls: str = ""   # comma-separated
    hermes_pool_keys: str = ""

    def model_post_init(self, __context) -> None:
        # Fallback: use NEXT_PUBLIC_SUPABASE_URL if supabase_url not set
        if not self.supabase_url:
            import os
            self.supabase_url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
        # Alias Hermes A = jobcoach, B = interview
        if not self.hermes_a_url:
            self.hermes_a_url = self.hermes_jobcoach_url
        if not self.hermes_a_key:
            self.hermes_a_key = self.hermes_jobcoach_key
        if not self.hermes_b_url:
            self.hermes_b_url = self.hermes_interview_url
        if not self.hermes_b_key:
            self.hermes_b_key = self.hermes_interview_key


settings = Settings()
