"""Utility for automatically liking tweets from accounts you follow.

This module provides a small scheduler that can be executed as a script. It
periodically fetches tweets from the authenticated user's following list and
likes the newest ones. A simple JSON file is used to keep track of tweets that
were already processed so we don't try to like them repeatedly across runs.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence, Set

import tweepy

import environment as env


LOGGER = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration options that control how likes are scheduled."""

    max_users: Optional[int] = None
    tweets_per_user: int = 2
    interval_minutes: float = 30.0
    min_delay_seconds: float = 30.0
    max_delay_seconds: float = 90.0
    state_file: Path = Path("liked_tweets_state.json")

    def __post_init__(self) -> None:
        if self.min_delay_seconds < 0 or self.max_delay_seconds < 0:
            raise ValueError("Delay values must be non-negative")
        if self.min_delay_seconds > self.max_delay_seconds:
            raise ValueError("min_delay_seconds cannot be greater than max_delay_seconds")
        if self.tweets_per_user < 1:
            raise ValueError("tweets_per_user must be at least 1")


class LikeState:
    """Manages persistence of tweet IDs that were already liked."""

    def __init__(self, path: Path):
        self._path = path
        self._liked_ids: Set[int] = self._load()

    def __contains__(self, tweet_id: int) -> bool:
        return tweet_id in self._liked_ids

    def add(self, tweet_id: int) -> None:
        self._liked_ids.add(tweet_id)
        self._save()

    def _load(self) -> Set[int]:
        if not self._path.exists():
            return set()
        try:
            data = json.loads(self._path.read_text())
        except json.JSONDecodeError:
            LOGGER.warning("Could not decode state file %s, starting fresh", self._path)
            return set()
        if not isinstance(data, Sequence):
            LOGGER.warning("State file %s had unexpected format, starting fresh", self._path)
            return set()
        try:
            return {int(item) for item in data}
        except (TypeError, ValueError):
            LOGGER.warning("State file %s had invalid tweet IDs, starting fresh", self._path)
            return set()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as handle:
            json.dump(sorted(self._liked_ids), handle)


class TweetLikeScheduler:
    """Coordinates fetching and liking tweets for followed accounts."""

    def __init__(self, client: tweepy.Client, config: SchedulerConfig):
        self._client = client
        self._config = config
        self._state = LikeState(config.state_file)
        self._me_id: Optional[int] = None

    def run(self, run_once: bool = False) -> None:
        """Start the scheduler.

        Args:
            run_once: When True the scheduler processes one pass and exits. When
                False the scheduler will run forever and sleep between passes.
        """

        LOGGER.info("Starting tweet like scheduler%s",
                    " (single run)" if run_once else "")
        try:
            while True:
                liked = self._run_once()
                LOGGER.info("Finished pass - liked %d tweets", liked)
                if run_once:
                    return
                sleep_seconds = max(self._config.interval_minutes, 0) * 60
                LOGGER.info("Sleeping for %.1f seconds", sleep_seconds)
                time.sleep(sleep_seconds)
        except KeyboardInterrupt:
            LOGGER.info("Scheduler interrupted by user")

    def _run_once(self) -> int:
        user_id = self._get_me_id()
        following_ids = list(self._get_following_ids(user_id))
        if not following_ids:
            LOGGER.info("No accounts found in the following list")
            return 0

        random.shuffle(following_ids)
        if self._config.max_users is not None:
            following_ids = following_ids[: self._config.max_users]

        total_liked = 0
        for target_id in following_ids:
            try:
                total_liked += self._process_user(target_id)
            except tweepy.TooManyRequests:
                LOGGER.warning("Stopping current pass early due to rate limits")
                break
        return total_liked

    def _get_me_id(self) -> int:
        if self._me_id is None:
            response = self._client.get_me()
            if response.data is None:
                raise RuntimeError("Unable to determine the authenticated user")
            self._me_id = int(response.data.id)
            LOGGER.debug("Authenticated as user id %s", self._me_id)
        return self._me_id

    def _get_following_ids(self, user_id: int) -> Iterable[int]:
        pagination_token: Optional[str] = None
        fetched = 0
        max_users = self._config.max_users

        while True:
            limit = 1000
            if max_users is not None:
                remaining = max_users - fetched
                if remaining <= 0:
                    break
                limit = max(1, min(limit, remaining))
            response = self._client.get_users_following(
                id=user_id, pagination_token=pagination_token, max_results=limit
            )
            if response.data:
                for user in response.data:
                    fetched += 1
                    yield int(user.id)
            if not response.meta or "next_token" not in response.meta:
                break
            pagination_token = response.meta["next_token"]

    def _process_user(self, target_user_id: int) -> int:
        tweets_response = self._client.get_users_tweets(
            id=target_user_id,
            max_results=min(10, max(self._config.tweets_per_user * 3, 5)),
            exclude=["retweets", "replies"],
            tweet_fields=["created_at"],
        )
        tweets = list(tweets_response.data or [])
        if not tweets:
            LOGGER.debug("No tweets available for user %s", target_user_id)
            return 0

        def _sort_key(tweet: tweepy.Tweet) -> float:
            created_at = getattr(tweet, "created_at", None)
            if created_at is None:
                return 0.0
            if isinstance(created_at, datetime):
                return created_at.timestamp()
            try:
                return float(created_at)
            except (TypeError, ValueError):
                return 0.0

        tweets.sort(key=_sort_key, reverse=True)
        liked_this_user = 0
        for tweet in tweets:
            if liked_this_user >= self._config.tweets_per_user:
                break
            tweet_id = int(tweet.id)
            if tweet_id in self._state:
                continue
            try:
                result = self._try_like_tweet(tweet_id)
            except tweepy.TooManyRequests:
                LOGGER.error(
                    "Rate limit reached while liking tweet %s; ending current pass",
                    tweet_id,
                )
                raise

            if result == "liked":
                liked_this_user += 1
                self._state.add(tweet_id)
                delay = self._compute_delay()
                LOGGER.debug("Sleeping %.2f seconds before next like", delay)
                time.sleep(delay)
            elif result == "forbidden":
                # Tweet cannot be liked (possibly already liked). Record it so we
                # do not retry on subsequent passes.
                self._state.add(tweet_id)
        return liked_this_user

    def _try_like_tweet(self, tweet_id: int) -> str:
        try:
            self._client.like(tweet_id)
            LOGGER.info("Liked tweet %s", tweet_id)
            return "liked"
        except tweepy.Forbidden as exc:  # type: ignore[attr-defined]
            codes = getattr(exc, "api_codes", None)
            response_text = getattr(getattr(exc, "response", None), "text", "")
            LOGGER.warning(
                "Forbidden when liking tweet %s (codes=%s): %s",
                tweet_id,
                codes,
                response_text or exc,
            )
            return "forbidden"
        except tweepy.TooManyRequests:
            LOGGER.error("Rate limit reached while trying to like tweet %s", tweet_id)
            raise
        except tweepy.TweepyException as exc:
            LOGGER.exception("Unexpected Tweepy error while liking tweet %s: %s", tweet_id, exc)
        return "error"

    def _compute_delay(self) -> float:
        if self._config.min_delay_seconds == self._config.max_delay_seconds:
            return self._config.min_delay_seconds
        return random.uniform(self._config.min_delay_seconds, self._config.max_delay_seconds)


def _configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Like tweets from accounts you follow")
    parser.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Minutes to wait between scheduler passes (default: 30)",
    )
    parser.add_argument(
        "--tweets-per-user",
        type=int,
        default=2,
        help="Maximum number of tweets to like per user each pass (default: 2)",
    )
    parser.add_argument(
        "--max-users",
        type=int,
        default=None,
        help="Optional limit on how many followed accounts to process per pass",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=30.0,
        help="Minimum seconds to wait between likes (default: 30)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=90.0,
        help="Maximum seconds to wait between likes (default: 90)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path("liked_tweets_state.json"),
        help="Path to the JSON file storing tweet IDs that were already liked",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Process one pass and exit instead of running continuously",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (use -vv for debug logs)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    _configure_logging(args.verbose)

    config = SchedulerConfig(
        max_users=args.max_users,
        tweets_per_user=args.tweets_per_user,
        interval_minutes=args.interval,
        min_delay_seconds=args.min_delay,
        max_delay_seconds=args.max_delay,
        state_file=args.state_file,
    )

    client = tweepy.Client(
        consumer_key=env.consumer_key,
        consumer_secret=env.consumer_secret,
        access_token=env.access_token,
        access_token_secret=env.access_token_secret,
        wait_on_rate_limit=True,
    )

    scheduler = TweetLikeScheduler(client=client, config=config)
    scheduler.run(run_once=args.run_once)


if __name__ == "__main__":
    main(sys.argv[1:])
