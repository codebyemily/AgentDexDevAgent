#!/usr/bin/env python3
"""DevAgent — AI-powered developer task assistant registered in AgentDex."""

import json
import os
import sys
import time
from urllib.parse import urlparse

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

MODEL = "claude-sonnet-4-6"
LINE = "═" * 64


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.")
    except Exception:
        return url


def _get(obj, key: str, default=""):
    """Get a key from a dict or attribute from an object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def run(task: str) -> None:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": task}]

    session_start = time.time()
    all_sources: list = []          # {url, title, via}
    domains_hit: set = set()
    tool_calls: list = []           # {tool, input, elapsed}

    print(f"\n{LINE}")
    print(f"  DevAgent  —  session start  [{_ts(session_start)}]")
    print(f"  task   : {task}")
    print(f"  model  : {MODEL}")
    print(f"  tools  : web_search_20260209 · web_fetch_20260209")
    print(f"{LINE}\n")

    while True:
        # Per-stream block state
        cur_type: str = ""
        cur_name: str = ""    # name field on server_tool_use blocks
        cur_input: str = ""   # accumulated input_json_delta
        tool_start: float = 0.0

        with client.messages.stream(
            model=MODEL,
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            tools=TOOLS,
            messages=messages,
        ) as stream:
            for event in stream:
                etype = event.type

                # ── Block start ───────────────────────────────────────────────
                if etype == "content_block_start":
                    cb = getattr(event, "content_block", None)
                    cur_type = _get(cb, "type")
                    cur_name = _get(cb, "name")
                    cur_input = ""

                    if cur_type == "thinking":
                        print("\n[THINKING]", flush=True)

                    elif cur_type == "server_tool_use":
                        tool_start = time.time()
                        print(f"\n[TOOL ▶ {cur_name}]", flush=True)

                    elif cur_type == "web_search_tool_result":
                        # Search results arrive in the content list of this block
                        for item in (_get(cb, "content") or []):
                            url = _get(item, "url")
                            title = _get(item, "title")
                            if url:
                                d = _domain(url)
                                domains_hit.add(d)
                                all_sources.append({"url": url, "title": title, "via": "web_search"})
                                print(f"  ↳ [{d}]  {title}", flush=True)

                # ── Block delta ───────────────────────────────────────────────
                elif etype == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    dtype = _get(delta, "type")

                    if dtype == "text_delta":
                        print(_get(delta, "text"), end="", flush=True)

                    elif dtype == "thinking_delta":
                        print(_get(delta, "thinking"), end="", flush=True)

                    elif dtype == "input_json_delta":
                        cur_input += _get(delta, "partial_json")

                # ── Block stop ────────────────────────────────────────────────
                elif etype == "content_block_stop":
                    if cur_type == "thinking":
                        print()  # trailing newline after thinking block

                    elif cur_type == "server_tool_use":
                        elapsed = time.time() - tool_start
                        try:
                            inp = json.loads(cur_input) if cur_input else {}
                        except json.JSONDecodeError:
                            inp = {}

                        query_or_url = inp.get("query") or inp.get("url") or ""

                        # For web_fetch we capture the URL as a source here
                        if cur_name == "web_fetch" and inp.get("url"):
                            url = inp["url"]
                            d = _domain(url)
                            domains_hit.add(d)
                            all_sources.append({"url": url, "title": url, "via": "web_fetch"})
                            print(f"  ↳ fetching {d}", flush=True)

                        tool_calls.append({"tool": cur_name, "input": query_or_url, "elapsed": elapsed})
                        print(f"  [{elapsed:.1f}s]", flush=True)

            response = stream.get_final_message()

        if response.stop_reason == "end_turn":
            print()
            break
        elif response.stop_reason == "pause_turn":
            # Server-side tool loop hit iteration cap — resume without adding a new user turn
            messages.append({"role": "assistant", "content": response.content})
        else:
            print()
            break

    # ── Session summary ────────────────────────────────────────────────────────
    total = time.time() - session_start
    print(f"\n{LINE}")
    print(f"  Research complete  —  {total:.1f}s total")

    print(f"\n  Active MCP / server-side tools:")
    print(f"    · web_search_20260209  (Anthropic-hosted)")
    print(f"    · web_fetch_20260209   (Anthropic-hosted)")

    if tool_calls:
        print(f"\n  Tool calls ({len(tool_calls)}):")
        for t in tool_calls:
            print(f"    [{t['elapsed']:.1f}s]  {t['tool']:<12}  {t['input']}")

    if domains_hit:
        print(f"\n  Semantic domains hit ({len(domains_hit)}):")
        for d in sorted(domains_hit):
            print(f"    · {d}")

    if all_sources:
        seen: set = set()
        unique = []
        for s in all_sources:
            if s["url"] not in seen:
                seen.add(s["url"])
                unique.append(s)
        print(f"\n  Sources ({len(unique)}):")
        for s in unique:
            tag = "[search]" if s["via"] == "web_search" else "[fetch] "
            label = s["title"] if s["title"] and s["title"] != s["url"] else s["url"]
            print(f"    {tag}  {label}")
            if s["title"] and s["title"] != s["url"]:
                print(f"             {s['url']}")

    print(f"{LINE}\n")


def _ts(t: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S")


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
    run(task)


if __name__ == "__main__":
    main()
