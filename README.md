# Job Hunter Bot 🚀

A modular job monitoring system that tracks career pages and sends notifications to Discord.

## Supported Platforms
- **Greenhouse** (API & HTML Fallback)
- **Lever** (API & HTML Fallback)
- **Workday** (API with custom headers)
- **SmartRecruiters** (Search API)
- **Generic HTML** (CSS Selector based)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create a `.env` file from the example:
   ```bash
   DISCORD_WEBHOOK_URL=your_webhook_url_here
   DB_PATH=data/jobs.db
   ```

3. **Configure Companies**
   Add target companies to `config/companies.yaml`.

## Usage

**Run standard scan:**
```bash
python -m app.main
```

**Run with Search Engine Discovery (find new boards):**
```bash
python -m app.main --discover
```

## example.env
```text
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DB_PATH=data/jobs.db
```
