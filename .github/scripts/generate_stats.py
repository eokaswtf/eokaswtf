from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

user = os.environ["GITHUB_USER"]
token = os.environ["GITHUB_STATS_TOKEN"]
end = datetime.now(timezone.utc).replace(microsecond=0)
start = end - timedelta(days=365)

query = """
query ($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalRepositoriesWithContributedCommits
    }
  }
}
"""
payload = {
    "query": query,
    "variables": {
        "login": user,
        "from": start.isoformat().replace("+00:00", "Z"),
        "to": end.isoformat().replace("+00:00", "Z"),
    },
}
request = Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "eokaswtf-profile-stats",
    },
)
with urlopen(request, timeout=30) as response:
    result = json.load(response)
if result.get("errors"):
    raise RuntimeError(json.dumps(result["errors"], ensure_ascii=False))

stats = result["data"]["user"]["contributionsCollection"]
metrics = [
    ("⌘", "Commits (last year)", stats["totalCommitContributions"]),
    ("↗", "Pull requests", stats["totalPullRequestContributions"]),
    ("!", "Issues", stats["totalIssueContributions"]),
    ("▦", "Repos with commits", stats["totalRepositoriesWithContributedCommits"]),
]
rows = []
for index, (icon, label, value) in enumerate(metrics):
    y = 96 + index * 43
    rows.append(
        f'<rect x="38" y="{y - 22}" width="32" height="32" rx="12" fill="#fce6ff"/>'
        f'<text x="54" y="{y}" text-anchor="middle" font-size="17" fill="#bb55bb">{icon}</text>'
        f'<text x="86" y="{y}" font-size="16" font-weight="600" fill="#615365">{label}</text>'
        f'<text x="625" y="{y}" text-anchor="end" font-size="16" font-weight="700" fill="#615365">{value}</text>'
    )

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="660" height="285" viewBox="0 0 660 285" fill="none">
<title>eokaswtf's GitHub Stats</title>
<rect x="4" y="4" width="652" height="277" rx="32" fill="#fff7ff"/>
<text x="38" y="48" font-family="Arial, sans-serif" font-size="23" font-weight="700" fill="#bb55bb">eokaswtf's GitHub Stats</text>
{''.join(rows)}
<text x="38" y="263" font-family="Arial, sans-serif" font-size="12" fill="#9d8a9f">{os.getenv("GITHUB_STATS_VISIBILITY", "Public only")} · Last 365 days · Updated {end:%Y-%m-%d}</text>
</svg>
"""
output = Path("profile/stats.svg")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(svg, encoding="utf-8")
