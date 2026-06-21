# DevAgent

A demo developer agent for AgentDex. 

## Context 

This dev agent queries AgentDex about a topic. While it gets a fast, structured answer for that topic, AgentDex in parallel researches semantically-adjacent topics — and has them ready as live MCP servers/APIs before the agent ever asks.

This agent uses Claude Sonnet 4.6 with live web search to browse the web, do research, make purchases, and manage legacy CRMs using AgentDex to speed up the research time. 

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
