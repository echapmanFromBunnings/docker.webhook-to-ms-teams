
# webhook-to-ms-teams

Lightweight Python sender that forwards GitHub webhook events to a Microsoft Teams channel through a **Power Automate workflow**.

> ⚠️ **Important:** Microsoft retired Office 365 Connectors and legacy incoming webhooks. New connectors could not be created after **15 August 2024**, existing connectors must be migrated by **end of 2025**, and functionality will be fully disabled by **end of 2025**. The recommended replacement is a **Teams Power Automate workflow** using the template **"Post to a channel when a webhook request is received"**. This project has been updated to use that workflow.

## What changed

| Old approach | New approach |
| --- | --- |
| MS Teams **Incoming Webhook** connector | MS Teams **Workflows** app → Power Automate |
| `pymsteams` + MessageCard format | `requests` + Adaptive Card JSON payload |
| Webhook URL from channel connectors | Webhook URL from a Power Automate workflow trigger |

## Quick start (no Docker required)

1. Install Python 3.8+ and clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a Teams workflow:
   - In the target Teams channel, open the channel menu (`...`) and select **Workflows**.
   - Choose **Post to a channel when a webhook request is received**.
   - Copy the generated webhook URL.
4. Copy `.env.example` to `.env` and set `WORKFLOW_WEBHOOK_URL` to the URL from step 3.
5. Run locally with a sample event:
   ```bash
   python -m tests.local_send --event push --fixture push
   ```
   This starts a mock server and prints the JSON payload that would be sent to Teams.

## Send a real event locally

```bash
python -m src \
  --url "$WORKFLOW_WEBHOOK_URL" \
  --event push \
  --payload tests/fixtures/push.json
```

Or with GitHub Actions environment variables:

```bash
export WORKFLOW_WEBHOOK_URL="<your-workflow-url>"
export GITHUB_EVENT_NAME="push"
export GITHUB_EVENT_PATH="tests/fixtures/push.json"
python -m src
```

Use `--dry-run` to preview the payload without sending it.

### Message format

By default the sender posts an **Adaptive Card** (`--format adaptive`), which is
what the Teams workflow's "Post card in a chat or channel" action requires. The
payload is a `type: message` envelope containing an Adaptive Card whose content
has `"type": "AdaptiveCard"`. If your workflow instead posts plain text, use
`--format text` to send a simple `{"text": "..."}` body. Use `--format raw` to
forward the unmodified GitHub event JSON.

## Supported GitHub events

The formatter builds an Adaptive Card for these events:

- `push`
- `pull_request`
- `issues`
- `workflow_run`
- `release`

Unknown events are sent as a fallback card containing the raw event JSON.

## Usage in GitHub Actions

See `.github/workflows/example.yml`. Add your workflow URL as a repository secret named `TEAMS_WORKFLOW_WEBHOOK_URL`.

```yaml
      - name: Send GitHub event to Teams
        uses: docker://ghcr.io/echapmanfrombunnings/webhook-to-ms-teams:latest
        env:
          WORKFLOW_WEBHOOK_URL: ${{ secrets.TEAMS_WORKFLOW_WEBHOOK_URL }}
          GITHUB_EVENT_NAME: ${{ github.event_name }}
          GITHUB_EVENT_PATH: ${{ github.event_path }}
```

## Running tests

No Docker is needed for tests. A built-in mock HTTP server captures outbound requests.

On Windows, run everything with one PowerShell script:

```powershell
.\test.ps1                 # default: push event
.\test.ps1 -Event workflow_run -Fixture workflow_run
```

Or manually:

```bash
pip install -r requirements-dev.txt
pytest
python -m tests.local_send --event push --fixture push
```

To send a real event from PowerShell (set `WORKFLOW_WEBHOOK_URL` first):

```powershell
.\send.ps1 -Event push -Fixture push
.\send.ps1 -Event pull_request -Fixture pull_request -DryRun
```

## Building and running with Docker

```bash
docker build -t webhook-to-ms-teams .
docker run --rm \
  -e WORKFLOW_WEBHOOK_URL="<your-workflow-url>" \
  -e GITHUB_EVENT_NAME=push \
  -v "$PWD/tests/fixtures/push.json:/tmp/event.json" \
  -e GITHUB_EVENT_PATH=/tmp/event.json \
  webhook-to-ms-teams
```

## License

MIT License, see [LICENSE](LICENSE) file.