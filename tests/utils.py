"""Utility functions for displaying messages and prompts in Jupyter notebooks."""

import json

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_message_content(message):
    """Convert message content to displayable string."""
    parts = []
    tool_calls_processed = False

    # Handle main content
    if isinstance(message.content, str):
        parts.append(message.content)
    elif isinstance(message.content, list):
        # Handle complex content like tool calls (Anthropic format)
        for item in message.content:
            if item.get("type") == "text":
                parts.append(item["text"])
            elif item.get("type") == "tool_use":
                parts.append(f"\n🔧 Tool Call: {item['name']}")
                parts.append(f"   Args: {json.dumps(item['input'], indent=2, ensure_ascii=False)}")
                parts.append(f"   ID: {item.get('id', 'N/A')}")
                tool_calls_processed = True
    else:
        parts.append(str(message.content))

    # Handle tool calls attached to the message (OpenAI format) - only if not already processed
    if (
        not tool_calls_processed
        and hasattr(message, "tool_calls")
        and message.tool_calls
    ):
        for tool_call in message.tool_calls:
            parts.append(f"\n🔧 Tool Call: {tool_call['name']}")
            parts.append(f"   Args: {json.dumps(tool_call['args'], indent=2, ensure_ascii=False)}")
            parts.append(f"   ID: {tool_call['id']}")

    return "\n".join(parts)


def format_messages(messages):
    """Format and display a list of messages with Rich formatting."""
    for m in messages:
        msg_type = m.__class__.__name__.replace("Message", "")
        content = format_message_content(m)

        if msg_type == "Human":
            console.print(Panel(content, title="🧑 Human", border_style="blue"))
        elif msg_type == "Ai":
            console.print(Panel(content, title="🤖 Assistant", border_style="green"))
        elif msg_type == "Tool":
            console.print(Panel(content, title="🔧 Tool Output", border_style="yellow"))
        else:
            console.print(Panel(content, title=f"📝 {msg_type}", border_style="white"))


def format_message(messages):
    """Alias for format_messages for backward compatibility."""
    return format_messages(messages)


def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
    """Display a prompt with rich formatting and XML tag highlighting.

    Args:
        prompt_text: The prompt string to display
        title: Title for the panel (default: "Prompt")
        border_style: Border color style (default: "blue")
    """
    # Create a formatted display of the prompt
    formatted_text = Text(prompt_text)
    formatted_text.highlight_regex(r"<[^>]+>", style="bold blue")  # Highlight XML tags
    formatted_text.highlight_regex(
        r"##[^#\n]+", style="bold magenta"
    )  # Highlight headers
    formatted_text.highlight_regex(
        r"###[^#\n]+", style="bold cyan"
    )  # Highlight sub-headers

    # Display in a panel for better presentation
    console.print(
        Panel(
            formatted_text,
            title=f"[bold green]{title}[/bold green]",
            border_style=border_style,
            padding=(1, 2),
        )
    )

# more expressive runner
async def stream_agent(agent, query, config=None):
    async for graph_name, stream_mode, event in agent.astream(
        query,
        stream_mode=["updates", "values"], 
        subgraphs=True,
        config=config
    ):
        if stream_mode == "updates":
            print(f'Graph: {graph_name if len(graph_name) > 0 else "root"}')
            
            node, result = list(event.items())[0]
            print(f'Node: {node}')
            
            for key in result.keys():
                if "messages" in key:
                    # print(f"Messages key: {key}")
                    format_messages(result[key])
                    break
        elif stream_mode == "values":
            current_state = event

    return current_state


def check_validate_result(report_validate_markdown: str) -> str:
    """
    report_validate_markdown 문자열에서 검수 결과를 확인하는 함수
    
    Args:
        report_validate_markdown: 검수 보고서 마크다운 문자열
    
    Returns:
        'PASS', 'FAIL', 또는 'NOT_FOUND' 중 하나
    """
    if not report_validate_markdown:
        return 'NOT_FOUND'
    
    # 대소문자 구분 없이 검색
    report_upper = report_validate_markdown.upper()
    
    if 'VALIDATE_RESULT:PASS' in report_upper or 'VALIDATE RESULT : PASS' in report_upper:
        return 'PASS'
    elif 'VALIDATE_RESULT:FAIL' in report_upper or 'VALIDATE RESULT : FAIL' in report_upper:
        return 'FAIL'
    else:
        return 'NOT_FOUND'


# 또는 더 간단한 버전 (불리언 반환)
def has_validate_result(report_validate_markdown: str) -> bool:
    """
    report_validate_markdown 문자열에 검수 결과가 포함되어 있는지 확인
    
    Args:
        report_validate_markdown: 검수 보고서 마크다운 문자열
    
    Returns:
        True: PASS 또는 FAIL이 포함된 경우, False: 그 외
    """
    if not report_validate_markdown:
        return False
    
    report_upper = report_validate_markdown.upper()
    return 'VALIDATE_RESULT:PASS' in report_upper or 'VALIDATE_RESULT:FAIL' in report_upper


# 또는 정규식을 사용한 버전
import re

def extract_validate_result(report_validate_markdown: str) -> str:
    """
    report_validate_markdown 문자열에서 검수 결과를 추출하는 함수
    
    Args:
        report_validate_markdown: 검수 보고서 마크다운 문자열
    
    Returns:
        'PASS', 'FAIL', 또는 None
    """
    if not report_validate_markdown:
        return None
    
    # 다양한 형식 지원 (공백, 콜론 등)
    pattern = r'VALIDATE\s*RESULT\s*:?\s*(PASS|FAIL)'
    match = re.search(pattern, report_validate_markdown, re.IGNORECASE)
    
    if match:
        return match.group(1).upper()
    return None
