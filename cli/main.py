import argparse
from datetime import datetime
from storage.db import Database
from storage.models import Article
from config.settings import Settings
from rich.console import Console
from rich.panel import Panel
from rich import box


console = Console()


def format_importance_badge(score: int) -> str:
    """Return colored importance badge."""
    if score >= 8:
        return f"[bold red]{score}[/bold red]"
    elif score >= 5:
        return f"[bold yellow]{score}[/bold yellow]"
    else:
        return f"[dim]{score}[/dim]"


def format_article_line(article: Article, show_link: bool = True) -> str:
    """Format one article as a rich console line."""
    badge = format_importance_badge(article.importance)
    line = f"  [{badge}] {article.title}"
    line += f"\n       [cyan]{article.source}[/cyan] · {article.summary}"
    if article.tags:
        tags = " ".join(f"[green]{t}[/green]" for t in article.tags)
        line += f"\n       {tags}"
    if show_link and article.url:
        line += f"\n       [blue underline]{article.url}[/blue underline]"
    return line


def cmd_today(db: Database):
    """Display today's briefing."""
    today = datetime.now().strftime("%Y-%m-%d")
    articles = db.get_articles_by_date(today)

    console.print(Panel(
        f"[bold]\U0001f4ca 今日投资简报[/bold]  {today}",
        box=box.ROUNDED,
    ))
    console.print(f"共 {len(articles)} 条\n")

    high = [a for a in articles if a.importance >= 8]
    medium = [a for a in articles if 5 <= a.importance < 8]
    low = [a for a in articles if a.importance < 5]

    sections = [
        ("\U0001f534 高重要性 (8-10)", high, "bold red"),
        ("\U0001f7e1 中重要性 (5-7)", medium, "bold yellow"),
        ("⚪ 一般 (1-4)", low, "dim"),
    ]

    for title, items, style in sections:
        if not items:
            continue
        console.print(f"\n[bold {style}]{title}[/bold {style}]")
        for art in items:
            console.print(format_article_line(art))
            console.print()


def cmd_top(db: Database, n: int = 10):
    """Display top N important articles from today."""
    today = datetime.now().strftime("%Y-%m-%d")
    articles = db.get_articles_by_date(today, min_importance=7, limit=n)
    console.print(f"[bold]\U0001f3c6 今日精选 Top {len(articles)}[/bold]\n")
    for art in articles:
        console.print(format_article_line(art))
        console.print()


def cmd_history(db: Database, date_str: str, category: str = "",
                source: str = "", min_imp: int = 1):
    articles = db.get_articles_by_date(
        date_str, category=category or None,
        source=source or None, min_importance=min_imp,
    )
    console.print(f"[bold]\U0001f4c5 {date_str}[/bold] 共 {len(articles)} 条\n")
    for art in articles:
        console.print(format_article_line(art))
        console.print()


def cmd_search(db: Database, keyword: str):
    articles = db.search_articles(keyword)
    console.print(f"[bold]\U0001f50d 搜索 \"{keyword}\"[/bold] 找到 {len(articles)} 条\n")
    for art in articles:
        console.print(format_article_line(art))
        console.print()


def main():
    settings = Settings()
    db = Database(settings.database_path)
    db.initialize()

    parser = argparse.ArgumentParser(prog="fin-review", description="投资信息聚合")
    sub = parser.add_subparsers(dest="command")

    p_today = sub.add_parser("today", help="今日简报")

    p_top = sub.add_parser("top", help="今日精选")
    p_top.add_argument("-n", type=int, default=10)

    p_hist = sub.add_parser("history", help="按日期查看")
    p_hist.add_argument("--date", required=True)
    p_hist.add_argument("--category")
    p_hist.add_argument("--source")
    p_hist.add_argument("--min-importance", type=int, default=1)

    p_search = sub.add_parser("search", help="搜索")
    p_search.add_argument("keyword")

    args = parser.parse_args()
    if args.command == "today":
        cmd_today(db)
    elif args.command == "top":
        cmd_top(db, args.n)
    elif args.command == "history":
        cmd_history(db, args.date, args.category or "",
                    args.source or "", args.min_importance)
    elif args.command == "search":
        cmd_search(db, args.keyword)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
