#!/usr/bin/env python3
"""DevAgent — AI-powered developer task assistant registered in AgentDex."""

import os
import sys
import anthropic


SYSTEM_PROMPT = """You are DevAgent, a specialized AI assistant registered in AgentDex — \
a curated registry of AI agents built for developers.

Your role is to help developers complete technical tasks by:
- Searching the web for up-to-date documentation, tutorials, and best practices
- Fetching content from specific URLs for detailed API references and guides
- Finding relevant packages, libraries, GitHub repos, and code examples
- Researching new technologies, frameworks, and tooling
- Looking up error messages and debugging solutions
- Summarizing technical articles and release notes

When handling a developer task:
1. Search for the most current and authoritative information available
2. Synthesize findings into clear, actionable answers
3. Cite sources (URLs) when referencing specific documentation
4. Prefer official documentation and recent sources over older blog posts
5. Be technically precise and concise — developers value accuracy over padding"""


TOOLS = [
    {"type": "web_search_20260209", "name": "web_search"},
    {"type": "web_fetch_20260209", "name": "web_fetch"},
]


def run(task: str) -> None:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": task}]

    while True:
        with client.messages.stream(
            model="claude-opus-4-8",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            for event in stream:
                if (
                    event.type == "content_block_start"
                    and hasattr(event, "content_block")
                    and getattr(event.content_block, "type", None) == "server_tool_use"
                ):
                    name = getattr(event.content_block, "name", "")
                    if name == "web_search":
                        print("\n[Searching the web...]", flush=True)
                    elif name == "web_fetch":
                        print("\n[Fetching content...]", flush=True)
                elif (
                    event.type == "content_block_delta"
                    and hasattr(event, "delta")
                    and event.delta.type == "text_delta"
                ):
                    print(event.delta.text, end="", flush=True)

            response = stream.get_final_message()

        if response.stop_reason == "end_turn":
            print()
            break
        elif response.stop_reason == "pause_turn":
            # Server-side tool loop hit iteration limit — resume without adding a new user turn
            messages.append({"role": "assistant", "content": response.content})
        else:
            print()
            break


def main() -> None:
    if len(sys.argv) < 2:
        print("DevAgent — AI-powered developer task assistant")
        print("\nUsage: python agent.py '<task>'")
        print("\nExamples:")
        print("  python agent.py 'What are the new features in Python 3.13?'")
        print("  python agent.py 'How do I deploy a Node.js app to Railway?'")
        print("  python agent.py 'Latest stable version of FastAPI and its changelog'")
        sys.exit(0)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    print(f"Task: {task}\n{'─' * 60}")
    run(task)


if __name__ == "__main__":
    main()
