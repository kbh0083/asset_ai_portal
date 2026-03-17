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


def visualize_res_result(res: Dict[str, Any]):
    """
    extract_one_file의 결과값 res를 테이블 형태로 시각화하는 함수
    
    Args:
        res: extract_one_file 함수의 반환값 (file, db_rows, ingest_issues, extract_issues, validation_report 포함)
    """
    if not res:
        print("res 변수가 비어있습니다.")
        return
    
    # 파일 정보 표시
    print("=" * 80)
    print(f"📄 파일: {res.get('file', 'N/A')}")
    print("=" * 80)
    print()
    
    # db_rows 테이블 생성
    if res.get('db_rows'):
        db_rows_data = []
        for idx, row in enumerate(res['db_rows'], 1):
            row_data = {'Row #': idx}
            # 각 행의 모든 키-값을 추가
            for key, value in row.items():
                # date와 Decimal 타입을 문자열로 변환
                if isinstance(value, date):
                    row_data[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_data[key] = str(value)
                else:
                    row_data[key] = value
            db_rows_data.append(row_data)
        
        if db_rows_data:
            df_db_rows = pd.DataFrame(db_rows_data)
            print("=" * 80)
            print("📊 DB 행 데이터")
            print("=" * 80)
            # 모든 행과 열을 표시하도록 pandas 옵션 설정
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None, 'display.max_colwidth', None):
                display(df_db_rows)
            print()
    else:
        print("=" * 80)
        print("📊 DB 행 데이터: 없음")
        print("=" * 80)
        print()
    
    # ingest_issues 표시
    if res.get('ingest_issues'):
        print("=" * 80)
        print("⚠️  Ingest 이슈")
        print("=" * 80)
        for idx, issue in enumerate(res['ingest_issues'], 1):
            print(f"{idx}. {issue}")
        print()
    else:
        print("=" * 80)
        print("✅ Ingest 이슈 없음")
        print("=" * 80)
        print()
    
    # extract_issues 표시
    if res.get('extract_issues'):
        print("=" * 80)
        print("⚠️  Extract 이슈")
        print("=" * 80)
        for idx, issue in enumerate(res['extract_issues'], 1):
            print(f"{idx}. {issue}")
        print()
    else:
        print("=" * 80)
        print("✅ Extract 이슈 없음")
        print("=" * 80)
        print()
    
    # validation_report 표시
    validation_report = res.get('validation_report', '')
    print("=" * 80)
    print("🔍 검증 리포트")
    print("=" * 80)
    if validation_report:
        print(validation_report)
    else:
        print("검증 리포트 없음")
    print()