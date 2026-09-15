"""Notify after CI finishes. Tokens are read only from environment variables."""
import json
import os
import urllib.request
import urllib.error

def fetch(url, token):
    request = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def main():
    required = ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'GH_TOKEN', 'REPOSITORY', 'RUN_ID', 'RUN_URL')
    if any(not os.environ.get(key) for key in required):
        raise SystemExit('Missing notification configuration')
    base = f"https://api.github.com/repos/{os.environ['REPOSITORY']}/actions/runs/{os.environ['RUN_ID']}/jobs"
    jobs = []
    page = 1
    while True:
        batch = fetch(f'{base}?per_page=100&page={page}', os.environ['GH_TOKEN'])['jobs']
        jobs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    lines = [f"CI · {os.environ['REPOSITORY']}"]
    lines.extend(f"{job['name']}: {job.get('conclusion') or job['status']}" for job in jobs)
    lines.extend(['Argo CD: статус фактического развёртывания отправляется отдельно.', os.environ['RUN_URL']])
    body = json.dumps({'chat_id': os.environ['TELEGRAM_CHAT_ID'], 'text': '\n'.join(lines)[:4000]}).encode()
    request = urllib.request.Request(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage", data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
        if not result.get('ok'):
            raise SystemExit('Telegram rejected the notification')
    except urllib.error.URLError:
        # Do not print exception URLs: Telegram embeds the secret in its URL.
        raise SystemExit('Telegram notification failed; check token, chat and network') from None

if __name__ == '__main__':
    main()
