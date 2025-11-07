"""Application factory for the online textbook search site."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, abort, current_app, render_template, request
from bs4 import BeautifulSoup

from search_engine import retrieve, load_stopwords


BASE_DIR = Path(__file__).resolve().parent.parent


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Flask application factory.

    Parameters
    ----------
    config:
        Optional configuration overrides. Keys include `HTMLS_DIR`,
        `STOPWORDS_PATH`, and `INDEX_PATH`.
    """

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    default_config = {
        "HTMLS_DIR": str(Path(os.getenv("HTMLS_DIR", BASE_DIR / "htmls"))),
        "STOPWORDS_PATH": str(Path(os.getenv("STOPWORDS_PATH", BASE_DIR / "data" / "stopwords.txt"))),
        "INDEX_PATH": str(Path(os.getenv("INDEX_PATH", BASE_DIR / "bm25_index.pkl"))),
        "TOP_K": int(os.getenv("TOP_K", "10")),
    }

    app.config.update(default_config)

    if config:
        app.config.update(config)

    _ensure_runtime_assets(app)
    _register_routes(app)
    _register_error_handlers(app)

    return app


def _ensure_runtime_assets(app: Flask) -> None:
    htmls_dir = Path(app.config["HTMLS_DIR"])
    if not htmls_dir.exists():
        app.logger.warning("HTML目录 %s 不存在，正在创建", htmls_dir)
        htmls_dir.mkdir(parents=True, exist_ok=True)

    index_path = Path(app.config["INDEX_PATH"])
    if not index_path.exists():
        app.logger.warning("索引文件 %s 不存在，请先构建BM25索引", index_path)

    stopwords_path = Path(app.config["STOPWORDS_PATH"])
    if stopwords_path.exists():
        try:
            load_stopwords(str(stopwords_path))
        except ValueError:
            app.logger.warning("无法加载停用词文件：%s", stopwords_path)
    else:
        app.logger.warning("停用词文件 %s 不存在", stopwords_path)


def _get_html_title(doc_id: int) -> str:
    htmls_dir = Path(current_app.config["HTMLS_DIR"])
    html_file = htmls_dir / f"{doc_id}.html"

    if not html_file.exists():
        return f"文档{doc_id}"

    soup = _load_html_soup(html_file)
    return soup.title.get_text(strip=True) if soup.title else f"文档{doc_id}"


def _load_html_soup(html_file: Path) -> BeautifulSoup:
    try:
        with html_file.open("r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "lxml")
    except UnicodeDecodeError:
        with html_file.open("r", encoding="gbk", errors="ignore") as f:
            return BeautifulSoup(f.read(), "lxml")


def _register_routes(app: Flask) -> None:
    @app.get("/")
    def search_page():
        return render_template("search.html")

    @app.post("/search")
    def handle_search():
        query = request.form.get("query", "").strip()
        if not query:
            return render_template("search.html", error="请输入检索词")

        try:
            raw_results = retrieve(
                query=query,
                index_path=current_app.config["INDEX_PATH"],
                stopwords_path=current_app.config["STOPWORDS_PATH"],
                top_n=current_app.config.get("TOP_K", 10),
            )
        except ValueError as exc:
            current_app.logger.exception("检索失败：%s", exc)
            return render_template("search.html", error=str(exc))
        except Exception as exc:  # noqa: BLE001
            current_app.logger.exception("检索发生异常")
            return render_template("search.html", error=f"检索出错：{exc}")

        results_with_title = [
            (doc_id, score, _get_html_title(doc_id))
            for doc_id, score in raw_results
        ]

        return render_template(
            "results.html",
            query=query,
            results=results_with_title,
            total=len(results_with_title),
        )

    @app.get("/doc/<int:doc_id>")
    def show_document(doc_id: int):
        htmls_dir = Path(current_app.config["HTMLS_DIR"])
        html_file = htmls_dir / f"{doc_id}.html"

        if not html_file.exists():
            abort(404, description=f"文档 {doc_id} 不存在")

        soup = _load_html_soup(html_file)
        current_title = soup.title.get_text(strip=True) if soup.title else f"文档{doc_id}"

        related_items = []
        if current_title:
            try:
                related_docs = retrieve(
                    query=current_title,
                    index_path=current_app.config["INDEX_PATH"],
                    stopwords_path=current_app.config["STOPWORDS_PATH"],
                    top_n=5,
                )
            except Exception:  # noqa: BLE001
                related_docs = []

            for rel_doc_id, _ in related_docs:
                if rel_doc_id == doc_id:
                    continue

                rel_html_path = htmls_dir / f"{rel_doc_id}.html"
                if not rel_html_path.exists():
                    continue

                rel_soup = _load_html_soup(rel_html_path)
                rel_title = rel_soup.title.get_text(strip=True) if rel_soup.title else f"文档{rel_doc_id}"
                rel_p_tags = rel_soup.find_all("p")
                rel_desc = (
                    rel_p_tags[0].get_text(strip=True)[:20] + "..."
                    if rel_p_tags
                    else ""
                )

                related_items.append(
                    {
                        "url": f"/doc/{rel_doc_id}",
                        "text": rel_title,
                        "desc": rel_desc,
                    }
                )

        related_container = soup.find("div", class_="related-container")
        if related_container is not None:
            related_container.clear()
            for item in related_items:
                item_div = soup.new_tag("div", attrs={"class": "related-item"})
                a_tag = soup.new_tag("a", attrs={"href": item["url"]})
                a_tag.string = item["text"]
                p_tag = soup.new_tag("p")
                p_tag.string = item["desc"]
                item_div.append(a_tag)
                item_div.append(p_tag)
                related_container.append(item_div)

        return str(soup)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def page_not_found(error):  # type: ignore[override]
        return render_template("error.html", code=404, message=error.description), 404

    @app.errorhandler(500)
    def internal_error(error):  # type: ignore[override]
        message = getattr(error, "description", "服务器发生错误")
        return render_template("error.html", code=500, message=message), 500

