from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from storage.db import Database
import os


def create_app(db: Database) -> FastAPI:
    app = FastAPI(title="FinReview")

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = Jinja2Templates(directory=template_dir)

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        today = datetime.now().strftime("%Y-%m-%d")
        articles = db.get_articles_by_date(today)
        high = [a for a in articles if a.importance >= 8]
        medium = [a for a in articles if 5 <= a.importance < 8]
        low = [a for a in articles if a.importance < 5]
        return templates.TemplateResponse(
            request, "index.html",
            {
                "high": high, "medium": medium, "low": low,
                "today": today, "total": len(articles),
            },
        )

    @app.get("/article/{article_id}", response_class=HTMLResponse)
    async def article_detail(request: Request, article_id: int):
        article = db.get_article(article_id)
        if not article:
            return HTMLResponse("Not Found", status_code=404)
        return templates.TemplateResponse(
            request, "article.html", {"a": article},
        )

    @app.get("/api/today")
    async def api_today():
        today = datetime.now().strftime("%Y-%m-%d")
        articles = db.get_articles_by_date(today)
        return {"articles": [vars(a) for a in articles]}

    @app.get("/api/search")
    async def api_search(q: str = Query(""), category: str = Query(""),
                         source: str = Query(""), min_imp: int = Query(1),
                         date: str = Query("")):
        if date:
            articles = db.get_articles_by_date(
                date, category=category or None,
                source=source or None, min_importance=min_imp,
            )
        else:
            articles = db.search_articles(q)
            if category:
                articles = [a for a in articles if a.category == category]
        return {"articles": [vars(a) for a in articles]}

    return app
