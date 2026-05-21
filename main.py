import argparse
import json
import os
from datetime import datetime

import requests

from config.settings import Settings
from storage.db import Database

from collector.sources.rss import RSSCollector
from collector.sources.base import ArticleItem
from collector.scheduler import CollectorPipeline

from processor.processor import Processor

from cli.main import main as cli_main
from web.app import create_app


def sina_finance_fetch():
    """Fetch financial news from Sina finance API."""
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    resp = requests.get(
        "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=20",
        headers=headers, timeout=15,
    )
    data = resp.json()
    items = []
    for entry in data.get("result", {}).get("data", []):
        title = entry.get("title", "")
        url = entry.get("url", "") or entry.get("link", "")
        ctime = entry.get("ctime", "")
        pub_date = datetime.now()
        if ctime:
            try:
                pub_date = datetime.fromtimestamp(int(ctime))
            except (ValueError, OSError):
                pass
        if title and url:
            items.append(ArticleItem(
                title=title,
                url=url,
                source="新浪财经",
                category="#market",
                published_at=pub_date,
                summary=entry.get("intro", ""),
            ))
    return items


def run_collection():
    """Run one collection cycle."""
    settings = Settings()
    os.makedirs(settings.data_dir, exist_ok=True)
    db = Database(settings.database_path)
    db.initialize()

    processor = None
    if settings.anthropic_api_key:
        processor = Processor(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
            batch_size=settings.llm_batch_size,
        )

    pipeline = CollectorPipeline(db, processor=processor)
    pipeline.add_collector("sina", sina_finance_fetch)

    print(f"[fin-review] Starting collection...")
    saved = pipeline.run_collection()
    print(f"[fin-review] Saved {saved} new articles")
    db.close()


def run_web():
    """Start the web panel."""
    import uvicorn
    settings = Settings()
    os.makedirs(settings.data_dir, exist_ok=True)
    db = Database(settings.database_path)
    db.initialize()
    app = create_app(db)
    print(f"[fin-review] Web panel at http://{settings.web_host}:{settings.web_port}")
    uvicorn.run(app, host=settings.web_host, port=settings.web_port)


def run_scheduler_daemon():
    """Run scheduler in background, collecting periodically."""
    from apscheduler.schedulers.background import BackgroundScheduler
    import time

    settings = Settings()
    os.makedirs(settings.data_dir, exist_ok=True)

    scheduler = BackgroundScheduler()

    def job():
        db_local = Database(settings.database_path)
        db_local.initialize()
        processor = Processor(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
            batch_size=settings.llm_batch_size,
        ) if settings.anthropic_api_key else None
        pipeline = CollectorPipeline(db_local, processor=processor)
        pipeline.add_collector("sina", sina_finance_fetch)
        try:
            saved = pipeline.run_collection()
            print(f"[scheduler] Collected {saved} articles")
        except Exception as e:
            print(f"[scheduler] Error: {e}")
        db_local.close()

    scheduler.add_job(job, "interval", minutes=settings.collector_interval_minutes)
    scheduler.start()
    print(f"[fin-review] Scheduler running every {settings.collector_interval_minutes} minutes")
    print("[fin-review] Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        scheduler.shutdown()


def main():
    parser = argparse.ArgumentParser(prog="fin-review", description="投资信息聚合系统")
    parser.add_argument("command", nargs="?", default="cli",
                        choices=["collect", "web", "cli", "scheduler"])

    args = parser.parse_args()

    if args.command == "collect":
        run_collection()
    elif args.command == "web":
        run_web()
    elif args.command == "scheduler":
        run_scheduler_daemon()
    else:
        cli_main()


if __name__ == "__main__":
    main()
