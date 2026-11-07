# trysac-a2a-agent-card

Build and validate A2A protocol Agent Cards against the v1.0.0 field rules, with JSON-path issues, media type and URL checks and the well-known discovery URL.

## Installation

```bash
pip install trysac-a2a-agent-card
```

## Usage Example

```python
from a2a_agent_card import Interface, Skill, build_card, validate_card, well_known_url

card = build_card(
    name="SearchAgent",
    description="Finds documents and code",
    version="1.0.0",
    interfaces=[Interface("https://agent.example.com/a2a", "JSONRPC", "1.0")],
    skills=[Skill("search", "Search", "Search docs", ("docs", "kb"))],
)
assert validate_card(card) == []
assert (
    well_known_url("https://agent.example.com/base/")
    == "https://agent.example.com/.well-known/agent-card.json"
)
```

## CLI

Validate an agent card JSON file:

```bash
python -m a2a_agent_card validate /path/to/agent-card.json
```
