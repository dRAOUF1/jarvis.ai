"""Compiler — ProjectSpec → ArtifactBundle.

AI fills only free-text fields (persona body, task descriptions).
Jinja2 templates produce all structure. Every AI output is validated
against the Pydantic schema; a hardcoded fallback fires on any failure.
"""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.contracts import ArtifactBundle, ProjectSpec, TaskItem, ToolRequirement
from app.control.llm import MODEL, get_client

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)

# ---------------------------------------------------------------------------
# Tool schema for forcing structured AI output
# ---------------------------------------------------------------------------

_GENERATE_CONTENT_TOOL = {
    "name": "generate_content",
    "description": "Generate the free-text content for the AI agent's profile files.",
    "input_schema": {
        "type": "object",
        "properties": {
            "persona_body": {
                "type": "string",
                "description": (
                    "2-3 paragraph rich description of the agent's personality, "
                    "expertise, tone, and communication style. Written in first person."
                ),
            },
            "task_descriptions": {
                "type": "object",
                "description": "Map of task title → 1-2 sentence expanded description.",
                "additionalProperties": {"type": "string"},
            },
            "user_md": {
                "type": "string",
                "description": "1-2 sentence description of the user and their context for USER.md.",
            },
        },
        "required": ["persona_body", "task_descriptions", "user_md"],
    },
}

_GENERATE_SPEC_TOOL = {
    "name": "generate_spec",
    "description": "Generate a complete ProjectSpec from a free-text description of what the user needs.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Short memorable agent name (2-4 words)"},
            "goal": {"type": "string", "description": "One clear purpose sentence"},
            "persona": {
                "type": "string",
                "description": "Personality traits and communication style (1-2 sentences)",
            },
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["title", "description"],
                },
                "minItems": 1,
                "description": "2-4 specific things the agent can do",
            },
            "tool_requirements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "app": {"type": "string"},
                        "reason": {"type": "string"},
                        "needed_scopes": {"type": "array", "items": {"type": "string"}},
                        "tool_subset": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["app", "reason"],
                },
                "description": "Apps to connect. Leave empty if no integrations are needed.",
            },
            "success_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "1-3 measurable outcomes",
            },
            "avatar_seed": {
                "type": "string",
                "description": "1-2 emoji that represent this agent",
            },
        },
        "required": ["name", "goal", "persona", "tasks", "success_criteria", "avatar_seed"],
    },
}


# ---------------------------------------------------------------------------
# Compiler class
# ---------------------------------------------------------------------------

class Compiler:
    async def compile(
        self,
        spec: ProjectSpec,
        project_id: str = "unknown",
        user_id: str = "demo-user",
    ) -> ArtifactBundle:
        """Compile a ProjectSpec into a complete ArtifactBundle.

        AI is called once for free-text fields only. Template rendering and
        all structural decisions are deterministic. Falls back to a hardcoded
        template on any AI failure so the provisioner always receives a valid bundle.
        """
        content = await self._generate_content(spec)

        soul_md = self._render_soul(spec, content)
        config_yaml = self._render_config()
        user_md = content.get("user_md", f"The user wants: {spec.goal}")
        memory_md = ""

        session_key = f"agent:{project_id}:user:{user_id}"

        bundle = ArtifactBundle(
            soul_md=soul_md,
            user_md=user_md,
            memory_md=memory_md,
            config_yaml=config_yaml,
            runtime_key="slot-a",
            session_key=session_key,
            tool_requirements=spec.tool_requirements,
        )
        return bundle

    async def generate_spec_from_need(self, need: str) -> ProjectSpec:
        """One Claude call: free-text need → complete ProjectSpec."""
        client = get_client()
        prompt = (
            f'Create a complete, practical project spec for this need: "{need}"\n\n'
            "Make the agent focused and useful. Be specific about tasks and success criteria."
        )
        try:
            resp = await client.messages.create(
                model=MODEL,
                max_tokens=2048,
                tools=[_GENERATE_SPEC_TOOL],
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": prompt}],
            )
            for block in resp.content:
                if block.type == "tool_use" and block.name == "generate_spec":
                    raw = block.input
                    raw.setdefault("tool_requirements", [])
                    return ProjectSpec(**raw)
        except Exception:
            pass

        return self._fallback_spec(need)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _generate_content(self, spec: ProjectSpec) -> dict:
        client = get_client()
        prompt = (
            f"Generate rich profile content for an AI agent:\n"
            f"Name: {spec.name}\n"
            f"Goal: {spec.goal}\n"
            f"Persona hint: {spec.persona}\n"
            f"Tasks: {json.dumps([t.model_dump() for t in spec.tasks], indent=2)}\n\n"
            "Write vivid, specific content that makes the agent feel distinct and useful."
        )
        try:
            resp = await client.messages.create(
                model=MODEL,
                max_tokens=1024,
                tools=[_GENERATE_CONTENT_TOOL],
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": prompt}],
            )
            for block in resp.content:
                if block.type == "tool_use" and block.name == "generate_content":
                    return block.input
        except Exception:
            pass

        return self._fallback_content(spec)

    def _render_soul(self, spec: ProjectSpec, content: dict) -> str:
        tmpl = _jinja_env.get_template("soul.md.j2")
        task_descriptions: dict[str, str] = content.get("task_descriptions", {})
        return tmpl.render(
            name=spec.name,
            goal=spec.goal,
            persona_body=content.get("persona_body", spec.persona),
            tasks=spec.tasks,
            task_descriptions=task_descriptions,
            success_criteria=spec.success_criteria,
        )

    def _render_config(self) -> str:
        tmpl = _jinja_env.get_template("config.yaml.j2")
        return tmpl.render()

    @staticmethod
    def _fallback_content(spec: ProjectSpec) -> dict:
        return {
            "persona_body": (
                f"I am {spec.name}. {spec.persona} "
                f"My purpose is to help you {spec.goal.lower()}."
            ),
            "task_descriptions": {t.title: t.description for t in spec.tasks},
            "user_md": f"The user is working on: {spec.goal}",
        }

    @staticmethod
    def _fallback_spec(need: str) -> ProjectSpec:
        return ProjectSpec(
            name=need[:40].strip(),
            goal=need,
            persona="Helpful, clear, and professional",
            tasks=[TaskItem(title="Main task", description=need)],
            tool_requirements=[],
            success_criteria=["Completes the task accurately"],
            avatar_seed="🤖",
        )
