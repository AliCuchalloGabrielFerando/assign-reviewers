# Slack PR Reviewer Bot

Slack bot that assigns GitHub PR reviewers via a slash command.

```
/assign-reviewers https://github.com/acme/api/pull/42 octocat hubot
```

Also supports team reviewers with the `team:` prefix:

```
/assign-reviewers https://github.com/acme/api/pull/42 octocat team:frontend
```

## Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name it (e.g., `PR Reviewer Bot`) and select your workspace
3. Go to **Slash Commands** → **Create New Command**:
   - Command: `/assign-reviewers`
   - Request URL: `https://<your-domain>/slack/events` (fill in after deploy)
   - Short Description: `Assign reviewers to a GitHub PR`
   - Usage Hint: `<PR_URL> <reviewer1> [reviewer2] ...`
4. Go to **OAuth & Permissions** → add Bot Token Scope: `commands`
5. **Install to Workspace** and copy the **Bot User OAuth Token** (`xoxb-...`)
6. Go to **Basic Information** and copy the **Signing Secret**

### 2. Create a GitHub Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens) → **Fine-grained tokens** → **Generate new token**
2. Select the repositories you need access to
3. Under **Repository permissions**, set **Pull requests** to **Read and write**
4. Copy the token

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your tokens
```

### 4. Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# For local dev, use ngrok to expose your local server:
# ngrok http 3000
# Then update the Slash Command Request URL in Slack App settings

source .env
python app.py
```

### 5. Deploy to AWS Lambda (optional)

```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements

# Set env vars in your shell or use a .env plugin
export SLACK_BOT_TOKEN=xoxb-...
export SLACK_SIGNING_SECRET=...
export GITHUB_TOKEN=ghp_...

serverless deploy
```

After deploy, update the Slash Command Request URL to the Lambda endpoint shown in the deploy output.

## Usage

```
/assign-reviewers <PR_URL> <reviewer1> [reviewer2] [team:team-slug]
/assign-reviewers help
```

### Examples

```
/assign-reviewers https://github.com/acme/api/pull/42 octocat
/assign-reviewers https://github.com/acme/api/pull/42 octocat hubot
/assign-reviewers https://github.com/acme/api/pull/42 octocat team:backend
```

## Project Structure

```
app.py              - Slack Bolt app + slash command handler + Lambda entry point
github_client.py    - GitHub API client (parse PR URLs, assign reviewers)
requirements.txt    - Python dependencies
serverless.yml      - AWS Lambda deploy config
.env.example        - Environment variable template
```
