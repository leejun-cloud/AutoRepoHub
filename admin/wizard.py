#!/usr/bin/env python3
"""
AutoRepo Hub — 최초 설정 마법사
실행: python wizard.py
"""
import os, json, sys
from pathlib import Path

# ── 색상 출력 ─────────────────────────────────────────────
def c(text, color):
    colors = {'green': '\033[92m', 'yellow': '\033[93m',
              'red': '\033[91m', 'cyan': '\033[96m',
              'bold': '\033[1m', 'reset': '\033[0m', 'muted': '\033[90m'}
    return f"{colors.get(color,'')}{text}{colors['reset']}"

def header(title):
    print(f"\n{c('━'*50, 'muted')}")
    print(f"  {c(title, 'bold')}")
    print(c('━'*50, 'muted'))

def ask(prompt, default='', secret=False):
    import getpass
    full = f"  {c('?', 'cyan')} {prompt}"
    if default:
        full += f" {c(f'[{default}]', 'muted')}"
    full += ': '
    if secret:
        val = getpass.getpass(full)
    else:
        val = input(full).strip()
    return val or default

def ask_yn(prompt, default='y'):
    val = input(f"  {c('?', 'cyan')} {prompt} [{c('y', 'green' if default=='y' else 'muted')}/{c('n', 'red' if default=='n' else 'muted')}]: ").strip().lower()
    return (val or default) == 'y'

ROOT = Path(__file__).parent.parent

# ── 메인 ──────────────────────────────────────────────────
def main():
    print(f"\n{c('🚀 AutoRepo Hub 설정 마법사', 'bold')}")
    print(c("  한 번만 실행하면 됩니다. API 키를 입력해주세요.", 'muted'))

    env_path      = ROOT / '.env'
    config_path   = ROOT / 'autorepo.json'

    # ── 1. GitHub Token ───────────────────────────────────
    header("1/3  GitHub Personal Access Token")
    print(f"""
  {c('발급 방법:', 'yellow')}
  1. https://github.com/settings/tokens/new 접속
  2. Note: AutoRepo Hub 입력
  3. Expiration: No expiration 선택
  4. Scopes: {c('repo', 'green')} (전체 체크) 체크
  5. Generate token 클릭 → 토큰 복사
    """)
    github_token = ask("GitHub Personal Access Token", secret=True)
    github_user  = ask("GitHub 사용자명 (예: lee)")

    if not github_token or not github_user:
        print(c("  ❌ GitHub Token과 사용자명은 필수입니다.", 'red'))
        sys.exit(1)

    # 토큰 유효성 간단 체크
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://api.github.com/user',
            headers={'Authorization': f'token {github_token}', 'User-Agent': 'AutoRepoHub'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            actual_user = data.get('login', '')
            print(f"  {c('✅ GitHub 연결 성공!', 'green')} 로그인: {c(actual_user, 'cyan')}")
    except Exception as e:
        print(f"  {c('⚠️  GitHub 연결 실패:', 'yellow')} {e}")
        if not ask_yn("  계속 진행할까요?", 'n'):
            sys.exit(1)

    # ── 2. Supabase ───────────────────────────────────────
    header("2/3  Supabase 설정 (DB + 인증)")
    print(f"""
  {c('발급 방법:', 'yellow')}
  1. https://supabase.com 에서 프로젝트 생성
  2. 좌측 Settings > API 클릭
  3. Project URL 복사
  4. anon public 키 복사
  5. supabase/schema.sql 을 SQL Editor에서 실행
    """)
    supabase_url  = ask("Supabase Project URL", "https://YOUR_PROJECT.supabase.co")
    supabase_anon = ask("Supabase anon public key", secret=True)
    supabase_service = ask("Supabase service_role key (서버용)", secret=True)

    # ── 3. Vercel ─────────────────────────────────────────
    header("3/3  Vercel 설정 (배포, 선택사항)")
    print(f"""
  {c('발급 방법:', 'yellow')}
  1. https://vercel.com/account/tokens 접속
  2. Create 클릭 → 이름 입력 → 생성
  3. 토큰 복사
    """)
    use_vercel = ask_yn("Vercel 배포 기능을 사용하시겠습니까?", 'y')
    vercel_token = ''
    if use_vercel:
        vercel_token = ask("Vercel Token", secret=True)

    # ── .env 파일 생성 ────────────────────────────────────
    header("설정 파일 생성")
    env_content = f"""# AutoRepo Hub 환경 변수
# ⚠️  이 파일은 절대 GitHub에 올리지 마세요!

# GitHub
GITHUB_TOKEN={github_token}
GITHUB_USER={github_user}

# Supabase
SUPABASE_URL={supabase_url}
SUPABASE_ANON_KEY={supabase_anon}
SUPABASE_SERVICE_KEY={supabase_service}

# Vercel (선택)
VERCEL_TOKEN={vercel_token}
"""
    env_path.write_text(env_content)
    print(f"  {c('✅ .env 파일 생성:', 'green')} {env_path}")

    # ── public/config.js 파일 생성 ────────────────────────
    config_js_path = ROOT / 'public' / 'config.js'
    config_js_content = f"""// AutoRepo Hub — Dynamic Client-side Configuration (Git-ignored)
window.SUPABASE_URL = "{supabase_url}";
window.SUPABASE_ANON_KEY = "{supabase_anon}";
"""
    config_js_path.write_text(config_js_content)
    print(f"  {c('✅ public/config.js 파일 생성:', 'green')} {config_js_path}")

    # ── autorepo.json 생성 (없으면) ───────────────────────
    if not config_path.exists():
        config = {"projects": [], "settings": {"default_branch": "main", "auto_gitignore": True}}
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2))
        print(f"  {c('✅ autorepo.json 생성:', 'green')} {config_path}")
    else:
        print(f"  {c('ℹ️  autorepo.json 이미 존재함 (유지)', 'muted')}")

    # ── 완료 ──────────────────────────────────────────────
    print(f"""
{c('━'*50, 'muted')}
{c('  🎉 설정 완료!', 'green')}
{c('━'*50, 'muted')}

  다음 명령어로 서버를 시작하세요:

    {c('cd admin && python server.py', 'cyan')}

  그런 다음 브라우저에서:

    {c('admin/dashboard.html', 'cyan')} — 관리자 대시보드
    {c('public/index.html', 'cyan')}   — 서비스 페이지 미리보기

  Supabase DB 설정 (아직 안 하셨다면):
    {c('supabase/schema.sql', 'cyan')} 을 Supabase SQL Editor에서 실행하세요.
""")

if __name__ == '__main__':
    main()
