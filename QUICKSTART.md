# MENA Viral Tracker — Quick Start

## Setup

1. Copy and fill in your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # APIFY_API_TOKEN=your_token
   # GOOGLE_CREDENTIALS_PATH=/absolute/path/to/service-account.json
   # GOOGLE_SHEET_ID=your_sheet_id
   # DB_PATH=data/tracker.db
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   python -c "from db.database import Database; import config; Database(config.DB_PATH).init()"
   ```

## Running the Pipeline Manually

```bash
python pipeline/run.py
```

Logs appear in stdout. First run will scrape ~200 posts per platform and score them.

## Starting the Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at http://localhost:8501. Shows "No posts found" until first pipeline run completes.

## Setting Up Daily Cron (macOS)

Run once to configure:
```bash
crontab -e
```

Add this line (replace paths with your actual values):
```
0 7 * * * cd /Users/mt/Desktop/Work/Claude_Project/mena-viral-tracker && /usr/bin/python3 pipeline/run.py >> logs/run.log 2>&1
```

Verify it was saved:
```bash
crontab -l
```

To find your Python path: `which python3`

## Google Sheets Setup (one-time)

1. Go to console.cloud.google.com → create project "mena-tracker"
2. Enable **Google Sheets API** and **Google Drive API**
3. Create a Service Account → download JSON key
4. Save key to a safe path → set `GOOGLE_CREDENTIALS_PATH` in `.env`
5. Create a Google Sheet → copy its ID from the URL → set `GOOGLE_SHEET_ID` in `.env`
6. Share the sheet with the service account email (from the JSON key) as **Editor**

## Running Tests

```bash
pytest tests/ -v
```
