import argparse
import os

from config.settings import Settings
from storage.db import Database

from collector.sources.rss import RSSCollector
from collector.scheduler import CollectorPipeline

from processor.processor import Processor

from cli.main import main as cli_main
from web.app import create_app


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
    pipeline.add_collector("cls_rss", RSSCollector(
        name="财联社", url="https://www.cls.cn/telegraph/rss",
        category="#market",
    ).fetch)
    pipeline.add_collector("wallstreet_rss", RSSCollector(
        name="华尔街见闻", url="https://wallstreetcn.com/rss",
        category="#market",
    ).fetch)

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
        pipeline.add_collector("cls_rss", RSSCollector(
            name="财联社", url="https://www.cls.cn/telegraph/rss",
            category="#market",
        ).fetch)
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
