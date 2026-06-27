# hermes/ — Claude Code local rules

This folder holds the template profile, Composio MCP snippet, and gateway run/warm scripts. Profiles
are stamped per project by `app/provisioning/hermes_writer.py`. Pin the Hermes version; disable
self-update. Tool calls run on the gateway host — MCP binaries must be on its PATH. Model is set in
`config.yaml` (Claude Sonnet 4.6), not in the request.
