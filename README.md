# TLDR Today

## Features
- Multi-source scraping: Collects news from leading tech and financial websites, including CNN, Bloomberg, TechCrunch, and more.
- Real-time updates: Scrapes news every hour to ensure the latest news is published promptly.
- Platform integration: Publishes news on Twitter, websites, and other customizable platforms.
- Customizable filters: Allows users to filter news by keywords, categories, and sources.
- Social engagement scheduler: Automatically likes recent tweets from the accounts you follow on a configurable cadence.

## Requirements

```
git clone https://github.com/becloudready/tldr-today.git
pip install -r requirements.txt
```
Configure Credentials
```
~/tldr_app_config.ini
```
## Usage

### Publish curated news tweets
```
./run.sh
```

### Automatically like tweets from followed accounts
Run the scheduler with your preferred cadence. By default it processes every 30
minutes, liking up to two recent tweets per followed account and recording
already-liked tweets in `liked_tweets_state.json` so they are not processed
again.

```
python like_following_scheduler.py --interval 45 --tweets-per-user 1 --max-users 50
```

Useful flags:

- `--run-once` – perform a single pass and exit.
- `--min-delay` / `--max-delay` – control the random pause between likes to
  mimic organic behaviour.
- `--state-file` – change where the scheduler stores tweet IDs it has already
  processed.
