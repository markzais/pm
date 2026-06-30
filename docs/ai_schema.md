# AI Structured-Output Schema

This document proposes a JSON schema for the AI responses that the backend will parse to optionally update the Kanban.

Top-level structure
{
  "response_text": "string",        // human-readable message to show in chat
  "actions": [                       // optional list of actions the AI wants applied
    {
      "action_type": "create|update|move|delete",
      "card": { /* card representation or partial patch */ },
      "target_column_id": number,    // for move or create
      "position": number             // optional ordering position
    }
  ],
  "suggestions": [ /* optional suggested new cards or text */ ],
  "metadata": { /* optional metadata e.g., confidence */ }
}

Examples
- Create card action:
  {
    "action_type": "create",
    "card": {"title": "New task", "description": "Details..."},
    "target_column_id": 2,
    "position": 0
  }

- Move card action:
  {
    "action_type": "move",
    "card": {"id": 12},
    "target_column_id": 3,
    "position": 1
  }

Parsing rules / safety
- Backend must validate each action before applying (IDs exist, user owns board).
- Treat AI-supplied IDs or positions as suggestions; enforce bounds and sanitize inputs.
- Apply actions transactionally; if any action fails, roll back and return an error plus partial diagnostics.

Testing & Success Criteria
- Unit tests parse sample AI responses and apply valid actions to a test DB.
- Simulate malformed AI output and confirm backend rejects it safely.
