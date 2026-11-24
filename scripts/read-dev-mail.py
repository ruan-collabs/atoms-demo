from pathlib import Path
import os

root = Path(__file__).resolve().parents[1]
path = root / '.runtime' / 'mailbox.jsonl'
if os.environ.get('APP_ENV') == 'production':
    raise SystemExit('Development mailbox unavailable in production')
if not path.exists():
    raise SystemExit('尚未收到开发邮件。请在本地登录页先发送验证码。')
# This CLI is for the developer to run locally, not an HTTP endpoint.
import json
entry = json.loads(path.read_text(encoding='utf-8').splitlines()[-1])
print(f"开发邮箱（不是真实邮件）: {entry['email']}\n验证码: {entry['code']}")
