import os
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def format_brief_for_slack(brief_text, analyses):
    high_importance = [a for a in analyses if a["importance"] >= 4]
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Competitive Intelligence Brief — {datetime.now().strftime('%d %b %Y')}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{len(analyses)} signals detected* across {len(set(a['competitor'] for a in analyses))} competitors. *{len(high_importance)} high importance* (4+/5)."
            }
        },
        {"type": "divider"},
    ]

    for analysis in high_importance[:5]:
        importance_bar = "🔴" if analysis["importance"] == 5 else "🟡"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{importance_bar} *{analysis['competitor']}* — "
                    f"`{analysis['event_type']}` — importance {analysis['importance']}/5\n"
                    f"{analysis['summary'][:200]}..."
                )
            }
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Full brief:*\n```{brief_text[:2000]}```"
        }
    })
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"Generated at {datetime.now().strftime('%I:%M %p IST')} by Competitive Intel Agent"
        }]
    })

    return blocks

async def send_to_slack(brief_text, analyses):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

    if not webhook_url:
        print("No Slack webhook URL set — skipping Slack delivery.")
        return False

    blocks = format_brief_for_slack(brief_text, analyses)

    payload = {
        "text": f"Competitive Intelligence Brief — {datetime.now().strftime('%d %b %Y')}",
        "blocks": blocks
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code == 200:
                print("Brief sent to Slack successfully.")
                return True
            else:
                print(f"Slack returned status {response.status_code}: {response.text}")
                return False
    except Exception as e:
        print(f"Failed to send to Slack: {e}")
        return False