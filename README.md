# DevAgent

A developer-task AI agent registered in [AgentDex](https://github.com/codebyemily/AgentDexDevAgent) — a curated registry of AI agents built for developers.

DevAgent uses Claude Opus 4.8 with live web search to answer developer questions with up-to-date information: docs, package versions, API references, debugging help, and more.

## Usage

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python agent.py '<task>'
```

### Examples

```bash
python agent.py 'What are the new features in Python 3.13?'
python agent.py 'How do I deploy a Node.js app to Railway?'
python agent.py 'Latest stable version of FastAPI and its breaking changes'
python agent.py 'What is the difference between React Server Components and Client Components?'
```

## What it does

- Searches the web for current documentation and best practices
- Fetches specific URLs for detailed API references
- Streams output in real-time as the agent thinks and searches
- Handles multi-step searches automatically (continues if search hits iteration limits)

## Architecture

```
agent.py
└── Anthropic SDK (claude-opus-4-8)
    ├── web_search_20260209  — live web search (server-side)
    └── web_fetch_20260209   — fetch specific URLs (server-side)
```

The agent runs an agentic loop: Claude decides when to search, the Anthropic API executes the searches on its infrastructure, and Claude synthesizes the results into a final answer.

## Claude Code integration

A Claude Code subagent definition is included at `.claude/agents/dev-agent.md`. Within a Claude Code session you can invoke it with:

```
/agent:dev-agent <task>
```

## Roadmap

- [ ] Deploy as an MCP server to Railway for use across any MCP-compatible client
- [ ] Register in the AgentDex platform registry
