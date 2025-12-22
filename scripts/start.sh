#!/bin/bash
# ==========================================
# Samsung AI Portal - 시작 스크립트 (Unix/Mac)
# ==========================================

set -e

# 스크립트 위치 기준으로 프로젝트 루트 찾기
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ==========================================
# 도움말 출력
# ==========================================
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --env, -e <ENV>     앱 환경 설정 (development|staging|production)"
    echo "  --port, -p <PORT>   서버 포트 (기본: 8000)"
    echo "  --host <HOST>       서버 호스트 (기본: 0.0.0.0)"
    echo "  --workers, -w <N>   워커 수 (production 모드, 기본: 1)"
    echo "  --mock-auth         인증 모킹 활성화 (SAML 우회, AUTH_MOCK_ENABLED=true)"
    echo "  --no-ssh            SSH 터널 비활성화"
    echo "  --help, -h          도움말 출력"
    echo ""
    echo "Examples:"
    echo "  $0                          # 기본 실행 (development)"
    echo "  $0 --env production         # production 모드"
    echo "  $0 --mock-auth              # 인증 모킹 활성화 (SAML 우회)"
    echo "  $0 --no-ssh --mock-auth     # SSH 없이 모킹 인증"
    echo "  $0 -e prod -p 9000          # production, 포트 9000"
    echo ""
    echo "Environment Variables:"
    echo "  APP_ENV, HOST, PORT, WORKERS, SSH_TUNNEL, AUTH_MOCK_ENABLED"
    exit 0
}

# ==========================================
# 플래그 파싱
# ==========================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --env|-e)
            APP_ENV="$2"
            shift 2
            ;;
        --port|-p)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --workers|-w)
            WORKERS="$2"
            shift 2
            ;;
        --mock-auth)
            AUTH_MOCK_ENABLED="true"
            shift
            ;;
        --no-ssh)
            SSH_TUNNEL="false"
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ==========================================
# 환경 변수 기본값 (플래그로 설정되지 않은 경우)
# ==========================================
APP_ENV=${APP_ENV:-development}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}
AUTH_MOCK_ENABLED=${AUTH_MOCK_ENABLED:-false}

# SSH 터널 설정
# SSH_TUNNEL: true(활성화) / false(비활성화)
SSH_TUNNEL=${SSH_TUNNEL:-true}

# ==========================================
# SSH 설정
# ==========================================
SSH_USER="samsung_ai_dbs"
SSH_KEY_FILE="$PROJECT_ROOT/.ssh/samsung_ai_portal_dbs"

# 외부용 (먼저 시도)
SSH_HOST_EXTERNAL="1.241.20.229"
SSH_PORT_EXTERNAL="2194"

# 내부용 (폴백)
SSH_HOST_INTERNAL="192.168.1.194"
SSH_PORT_INTERNAL="22"

# 포트 포워딩 설정
LOCAL_PG_PORT=${LOCAL_PG_PORT:-5432}
LOCAL_REDIS_PORT=${LOCAL_REDIS_PORT:-6379}
REMOTE_PG_PORT="5432"
REMOTE_REDIS_PORT="6379"

# SSH 터널 PID 저장
SSH_PG_PID=""
SSH_REDIS_PID=""

# 연결된 SSH 환경
CONNECTED_ENV=""

# ==========================================
# 함수 정의
# ==========================================

# 포트 사용 중인지 확인
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 포트 사용 중
    else
        return 1  # 포트 사용 안함
    fi
}

# SSH 터널 정리
cleanup_tunnels() {
    echo ""
    echo "Cleaning up SSH tunnels..."
    
    if [ -n "$SSH_PG_PID" ] && kill -0 "$SSH_PG_PID" 2>/dev/null; then
        kill "$SSH_PG_PID" 2>/dev/null || true
        echo "  - PostgreSQL tunnel (PID: $SSH_PG_PID) terminated"
    fi
    
    if [ -n "$SSH_REDIS_PID" ] && kill -0 "$SSH_REDIS_PID" 2>/dev/null; then
        kill "$SSH_REDIS_PID" 2>/dev/null || true
        echo "  - Redis tunnel (PID: $SSH_REDIS_PID) terminated"
    fi
}

# SSH 연결 테스트
test_ssh_connection() {
    local ssh_host=$1
    local ssh_port=$2
    local timeout_sec=5
    
    # SSH 키 파일로 연결 테스트 (타임아웃 적용)
    if ssh \
        -i "$SSH_KEY_FILE" \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=$timeout_sec \
        -o BatchMode=yes \
        -p "$ssh_port" \
        "$SSH_USER@$ssh_host" \
        "echo ok" >/dev/null 2>&1; then
        return 0  # 성공
    else
        return 1  # 실패
    fi
}

# 단일 SSH 터널 생성
create_single_tunnel() {
    local ssh_host=$1
    local ssh_port=$2
    local local_port=$3
    local remote_port=$4
    local service_name=$5
    
    # 포트 사용 중인지 확인
    if check_port "$local_port"; then
        echo "    - $service_name: Port $local_port already in use (skipping)"
        return 0
    fi
    
    ssh -f -N \
        -i "$SSH_KEY_FILE" \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o ServerAliveInterval=60 \
        -o ServerAliveCountMax=3 \
        -o ConnectTimeout=5 \
        -p "$ssh_port" \
        -L "$local_port:localhost:$remote_port" \
        "$SSH_USER@$ssh_host" 2>/dev/null
    
    # 터널 생성 확인 (최대 3초 대기)
    for i in {1..6}; do
        if check_port "$local_port"; then
            local pid=$(lsof -ti :$local_port -sTCP:LISTEN 2>/dev/null | head -1)
            echo "    ✓ $service_name tunnel (localhost:$local_port) - PID: $pid"
            echo "$pid"
            return 0
        fi
        sleep 0.5
    done
    
    return 1
}

# SSH 터널 생성 시도
try_create_tunnels() {
    local ssh_host=$1
    local ssh_port=$2
    local env_name=$3
    
    echo "  Trying $env_name ($ssh_host:$ssh_port)..."
    
    # SSH 연결 테스트
    if ! test_ssh_connection "$ssh_host" "$ssh_port"; then
        echo "    ✗ Connection refused"
        return 1
    fi
    
    echo "    ✓ SSH connection OK"
    
    # PostgreSQL 터널
    local pg_result
    pg_result=$(create_single_tunnel "$ssh_host" "$ssh_port" "$LOCAL_PG_PORT" "$REMOTE_PG_PORT" "PostgreSQL")
    if [ $? -ne 0 ]; then
        echo "    ✗ Failed to create PostgreSQL tunnel"
        return 1
    fi
    SSH_PG_PID="$pg_result"
    
    # Redis 터널
    local redis_result
    redis_result=$(create_single_tunnel "$ssh_host" "$ssh_port" "$LOCAL_REDIS_PORT" "$REMOTE_REDIS_PORT" "Redis")
    if [ $? -ne 0 ]; then
        echo "    ✗ Failed to create Redis tunnel"
        # PostgreSQL 터널 정리
        if [ -n "$SSH_PG_PID" ]; then
            kill "$SSH_PG_PID" 2>/dev/null || true
            SSH_PG_PID=""
        fi
        return 1
    fi
    SSH_REDIS_PID="$redis_result"
    
    CONNECTED_ENV="$env_name"
    return 0
}

# SSH 터널 자동 설정 (외부 → 내부 폴백)
setup_ssh_tunnels() {
    # SSH 키 파일 존재 확인
    if [ ! -f "$SSH_KEY_FILE" ]; then
        echo ""
        echo "================================================"
        echo "  ERROR: SSH Key File Not Found"
        echo "================================================"
        echo ""
        echo "  Expected path: $SSH_KEY_FILE"
        echo ""
        echo "  Please set up the SSH key file:"
        echo "    1. Create .ssh directory: mkdir -p $PROJECT_ROOT/.ssh"
        echo "    2. Copy your private key to: $SSH_KEY_FILE"
        echo "    3. Set permissions: chmod 600 $SSH_KEY_FILE"
        echo ""
        echo "================================================"
        exit 1
    fi
    
    # SSH 키 파일 권한 설정 (600)
    chmod 600 "$SSH_KEY_FILE" 2>/dev/null || true
    
    echo ""
    echo "Setting up SSH tunnels..."
    echo "  User: $SSH_USER"
    echo "  Key: $SSH_KEY_FILE"
    echo ""
    
    # 1. 외부 IP 시도
    if try_create_tunnels "$SSH_HOST_EXTERNAL" "$SSH_PORT_EXTERNAL" "External"; then
        echo ""
        echo "✓ SSH tunnels established via External network"
        return 0
    fi
    
    echo ""
    
    # 2. 내부 IP 시도 (폴백)
    if try_create_tunnels "$SSH_HOST_INTERNAL" "$SSH_PORT_INTERNAL" "Internal"; then
        echo ""
        echo "✓ SSH tunnels established via Internal network"
        return 0
    fi
    
    # 3. 둘 다 실패
    echo ""
    echo "================================================"
    echo "  ERROR: Database Connection Failed"
    echo "================================================"
    echo ""
    echo "  SSH tunnel could not be established."
    echo "  Tried:"
    echo "    - External: $SSH_HOST_EXTERNAL:$SSH_PORT_EXTERNAL"
    echo "    - Internal: $SSH_HOST_INTERNAL:$SSH_PORT_INTERNAL"
    echo ""
    echo "  Please check:"
    echo "    1. Network connectivity"
    echo "    2. SSH server availability"
    echo "    3. SSH key file: $SSH_KEY_FILE"
    echo "    4. User: $SSH_USER"
    echo ""
    echo "================================================"
    exit 1
}

# ==========================================
# 메인 스크립트
# ==========================================

echo "================================================"
echo "  Samsung AI Portal"
echo "  Environment: $APP_ENV"
echo "  SSH Tunnel: $SSH_TUNNEL"
echo "  Auth Mock: $AUTH_MOCK_ENABLED"
echo "  Project Root: $PROJECT_ROOT"
echo "================================================"

# 종료 시 터널 정리 (trap)
trap cleanup_tunnels EXIT INT TERM

# SSH 터널 설정
if [ "$SSH_TUNNEL" = "true" ]; then
    setup_ssh_tunnels
else
    echo ""
    echo "SSH tunnels disabled (SSH_TUNNEL=false)"
fi

# 환경변수 export
export PYTHONPATH="$PROJECT_ROOT/src"
export APP_ENV="$APP_ENV"
export AUTH_MOCK_ENABLED="$AUTH_MOCK_ENABLED"

# 프로젝트 루트로 이동
cd "$PROJECT_ROOT"

echo ""
echo "Starting server..."
if [ -n "$CONNECTED_ENV" ]; then
    echo "  Database: via SSH ($CONNECTED_ENV)"
fi
if [ "$AUTH_MOCK_ENABLED" = "true" ]; then
    echo "  Auth: Mock (SAML bypassed)"
fi

# 개발 환경
if [ "$APP_ENV" = "development" ]; then
    echo "  Mode: Development (hot-reload enabled)"
    echo ""
    uv run uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --reload-dir src/app

# 운영 환경
else
    echo "  Mode: Production (workers: $WORKERS)"
    echo ""
    uv run uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --no-access-log
fi
