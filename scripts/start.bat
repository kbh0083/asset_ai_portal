@echo off
REM ==========================================
REM Samsung AI Portal - Windows 시작 스크립트
REM ==========================================

setlocal enabledelayedexpansion

REM ==========================================
REM 도움말 출력
REM ==========================================
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

REM ==========================================
REM 플래그 파싱
REM ==========================================
:parse_args
if "%1"=="" goto :done_parsing

if "%1"=="--env" (
    set APP_ENV=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="-e" (
    set APP_ENV=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--port" (
    set PORT=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="-p" (
    set PORT=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--host" (
    set HOST=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--workers" (
    set WORKERS=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="-w" (
    set WORKERS=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--mock-auth" (
    set AUTH_MOCK_ENABLED=true
    shift
    goto :parse_args
)
if "%1"=="--no-ssh" (
    set SSH_TUNNEL=false
    shift
    goto :parse_args
)

echo Unknown option: %1
echo Use --help for usage information
exit /b 1

:done_parsing

REM ==========================================
REM 환경 변수 기본값 (플래그로 설정되지 않은 경우)
REM ==========================================
if "%APP_ENV%"=="" set APP_ENV=development
if "%HOST%"=="" set HOST=0.0.0.0
if "%PORT%"=="" set PORT=8000
if "%WORKERS%"=="" set WORKERS=1
if "%AUTH_MOCK_ENABLED%"=="" set AUTH_MOCK_ENABLED=false
if "%SSH_TUNNEL%"=="" set SSH_TUNNEL=true

REM ==========================================
REM SSH 설정
REM ==========================================
set SSH_USER=samsung_ai_dbs
set SSH_KEY_FILE=%~dp0..\.ssh\samsung_ai_portal_dbs

REM 외부용 (먼저 시도)
set SSH_HOST_EXTERNAL=1.241.20.229
set SSH_PORT_EXTERNAL=2194

REM 내부용 (폴백)
set SSH_HOST_INTERNAL=192.168.1.194
set SSH_PORT_INTERNAL=22

REM 포트 포워딩 설정
if "%LOCAL_PG_PORT%"=="" set LOCAL_PG_PORT=5432
if "%LOCAL_REDIS_PORT%"=="" set LOCAL_REDIS_PORT=6379
set REMOTE_PG_PORT=5432
set REMOTE_REDIS_PORT=6379

REM 연결된 환경
set CONNECTED_ENV=

REM ==========================================
REM 메인 스크립트
REM ==========================================

echo ================================================
echo   Samsung AI Portal
echo   Environment: %APP_ENV%
echo   SSH Tunnel: %SSH_TUNNEL%
echo   Auth Mock: %AUTH_MOCK_ENABLED%
echo ================================================

REM PYTHONPATH 설정
set PYTHONPATH=%~dp0..\src

REM SSH 터널 비활성화 체크
if "%SSH_TUNNEL%"=="false" (
    echo.
    echo SSH tunnels disabled ^(SSH_TUNNEL=false^)
    goto :start_server
)

REM SSH 키 파일 존재 확인
if not exist "%SSH_KEY_FILE%" (
    echo.
    echo ================================================
    echo   ERROR: SSH Key File Not Found
    echo ================================================
    echo.
    echo   Expected path: %SSH_KEY_FILE%
    echo.
    echo   Please set up the SSH key file:
    echo     1. Create .ssh directory in project root
    echo     2. Copy your private key to: .ssh\samsung_ai_portal_dbs
    echo.
    echo ================================================
    exit /b 1
)

REM SSH 키 파일 권한 설정 (OpenSSH는 엄격한 권한 요구)
REM 현재 사용자만 읽을 수 있도록 PowerShell로 권한 설정 (BUILTIN\BUILTIN 완전 제거)
for /f %%a in ('whoami') do set CURRENT_USER=%%a
powershell -NoProfile -ExecutionPolicy Bypass -Command "$keyPath = '%SSH_KEY_FILE%'; $currentUser = '%CURRENT_USER%'; if (Test-Path $keyPath) { $file = Get-Item $keyPath; $acl = $file.GetAccessControl([System.Security.AccessControl.AccessControlSections]::Access); $acl.SetAccessRuleProtection($true, $false); $acl.Access | Where-Object { $_.IdentityReference.Value -ne $currentUser } | ForEach-Object { try { $acl.RemoveAccessRule($_) | Out-Null } catch {} }; $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, 'Read', 'Allow'); $acl.SetAccessRule($accessRule); $file.SetAccessControl($acl) }" >nul 2>&1

REM OpenSSH 클라이언트 확인
where ssh >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: ssh is not installed.
    echo   Please install OpenSSH Client from Windows Features
    echo   Or use WSL and run start.sh instead
    exit /b 1
)

echo.
echo Setting up SSH tunnels...
echo   User: %SSH_USER%
echo   Key: %SSH_KEY_FILE%
echo.

REM 1. 외부 IP 시도
echo   Trying External ^(%SSH_HOST_EXTERNAL%:%SSH_PORT_EXTERNAL%^)...
call :test_connection %SSH_HOST_EXTERNAL% %SSH_PORT_EXTERNAL%
if %ERRORLEVEL%==0 (
    call :create_tunnels %SSH_HOST_EXTERNAL% %SSH_PORT_EXTERNAL% External
    if %ERRORLEVEL%==0 (
        set CONNECTED_ENV=External
        echo.
        echo √ SSH tunnels established via External network
        goto :start_server
    )
)
echo     X Connection refused
echo.

REM 2. 내부 IP 시도 (폴백)
echo   Trying Internal ^(%SSH_HOST_INTERNAL%:%SSH_PORT_INTERNAL%^)...
call :test_connection %SSH_HOST_INTERNAL% %SSH_PORT_INTERNAL%
if %ERRORLEVEL%==0 (
    call :create_tunnels %SSH_HOST_INTERNAL% %SSH_PORT_INTERNAL% Internal
    if %ERRORLEVEL%==0 (
        set CONNECTED_ENV=Internal
        echo.
        echo √ SSH tunnels established via Internal network
        goto :start_server
    )
)
echo     X Connection refused

REM 3. 둘 다 실패
echo.
echo ================================================
echo   ERROR: Database Connection Failed
echo ================================================
echo.
echo   SSH tunnel could not be established.
echo   Tried:
echo     - External: %SSH_HOST_EXTERNAL%:%SSH_PORT_EXTERNAL%
echo     - Internal: %SSH_HOST_INTERNAL%:%SSH_PORT_INTERNAL%
echo.
echo   Please check:
echo     1. Network connectivity
echo     2. SSH server availability
echo     3. SSH key file: %SSH_KEY_FILE%
echo     4. User: %SSH_USER%
echo.
echo ================================================
exit /b 1

:start_server
echo.
echo Starting server...
if not "%CONNECTED_ENV%"=="" (
    echo   Database: via SSH ^(%CONNECTED_ENV%^)
)
if "%AUTH_MOCK_ENABLED%"=="true" (
    echo   Auth: Mock ^(SAML bypassed^)
)

REM 개발 환경
if "%APP_ENV%"=="development" (
    echo   Mode: Development ^(hot-reload enabled^)
    echo.
    uv run uvicorn app.main:app --host %HOST% --port %PORT% --reload --reload-dir src\app
) else (
    echo   Mode: Production ^(workers: %WORKERS%^)
    echo.
    uv run uvicorn app.main:app --host %HOST% --port %PORT% --workers %WORKERS%
)
goto :eof

REM ==========================================
REM 도움말
REM ==========================================
:show_help
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   --env, -e ^<ENV^>     앱 환경 설정 (development^|staging^|production)
echo   --port, -p ^<PORT^>   서버 포트 (기본: 8000)
echo   --host ^<HOST^>       서버 호스트 (기본: 0.0.0.0)
echo   --workers, -w ^<N^>   워커 수 (production 모드, 기본: 1)
echo   --mock-auth         인증 모킹 활성화 (SAML 우회, AUTH_MOCK_ENABLED=true)
echo   --no-ssh            SSH 터널 비활성화
echo   --help, -h          도움말 출력
echo.
echo Examples:
echo   %~nx0                          # 기본 실행 (development)
echo   %~nx0 --env production         # production 모드
echo   %~nx0 --mock-auth              # 인증 모킹 활성화 (SAML 우회)
echo   %~nx0 --no-ssh --mock-auth     # SSH 없이 모킹 인증
echo   %~nx0 -e prod -p 9000          # production, 포트 9000
echo.
echo Environment Variables:
echo   APP_ENV, HOST, PORT, WORKERS, SSH_TUNNEL, AUTH_MOCK_ENABLED
exit /b 0

REM ==========================================
REM 함수: SSH 연결 테스트
REM ==========================================
:test_connection
set TEST_HOST=%1
set TEST_PORT=%2

REM ssh로 연결 테스트 (SSH 키 파일 사용)
REM 디버그를 위해 오류 출력을 임시 파일로 저장
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p %TEST_PORT% -i "%SSH_KEY_FILE%" %SSH_USER%@%TEST_HOST% exit 2>%TEMP%\ssh_test_error.txt
if %ERRORLEVEL%==0 (
    echo     √ SSH connection OK
    del %TEMP%\ssh_test_error.txt >nul 2>&1
    exit /b 0
)
REM 오류가 있으면 출력 (권한 문제인지 확인)
type %TEMP%\ssh_test_error.txt 2>nul | findstr /i "permission" >nul
if %ERRORLEVEL%==0 (
    echo     X Connection failed: SSH key permissions issue
) else (
    type %TEMP%\ssh_test_error.txt 2>nul | findstr /i "refused\|timeout\|connection" >nul
    if %ERRORLEVEL%==0 (
        echo     X Connection refused/timeout
    )
)
del %TEMP%\ssh_test_error.txt >nul 2>&1
exit /b 1

REM ==========================================
REM 함수: SSH 터널 생성
REM ==========================================
:create_tunnels
set TUNNEL_HOST=%1
set TUNNEL_PORT=%2
set TUNNEL_ENV=%3

REM PostgreSQL 터널 (백그라운드, SSH 키 파일 사용)
echo     - Creating PostgreSQL tunnel ^(localhost:%LOCAL_PG_PORT%^)...
start /b ssh -N -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ConnectTimeout=5 -p %TUNNEL_PORT% -i "%SSH_KEY_FILE%" -L %LOCAL_PG_PORT%:localhost:%REMOTE_PG_PORT% %SSH_USER%@%TUNNEL_HOST% >nul 2>&1
timeout /t 2 /nobreak >nul
echo       √ PostgreSQL tunnel started

REM Redis 터널 (백그라운드, SSH 키 파일 사용)
echo     - Creating Redis tunnel ^(localhost:%LOCAL_REDIS_PORT%^)...
start /b ssh -N -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ConnectTimeout=5 -p %TUNNEL_PORT% -i "%SSH_KEY_FILE%" -L %LOCAL_REDIS_PORT%:localhost:%REMOTE_REDIS_PORT% %SSH_USER%@%TUNNEL_HOST% >nul 2>&1
timeout /t 2 /nobreak >nul
echo       √ Redis tunnel started

exit /b 0

endlocal
