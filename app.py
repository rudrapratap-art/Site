from flask import Flask, render_template, request, abort
import requests

app = Flask(__name__)

# ────────────────────────────────────────────────
# Custom Jinja filter (this was likely missing → causes 500 when template uses |format_number)
# ────────────────────────────────────────────────
def format_number(value):
    try:
        # Handle float/int/string safely
        num = float(value)
        return "{:,.0f}".format(num) if num.is_integer() else "{:,.2f}".format(num)
    except (ValueError, TypeError):
        return str(value) if value is not None else "0"

app.jinja_env.filters['format_number'] = format_number

# ────────────────────────────────────────────────
# API settings
# ────────────────────────────────────────────────
BASE_URL = "https://www.eporner.com/api/v2/video/search/"
VIDEO_DETAIL_URL = "https://www.eporner.com/api/v2/video/id/"

def fetch_videos(query="all", page=1, order="latest", per_page=24):
    params = {
        "query": query.strip() or "all",
        "page": max(1, page),
        "per_page": per_page,
        "order": order,
        "thumbsize": "big",
        "gay": 0,
        "lq": 1,
        "format": "json"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.eporner.com/",
        "Accept": "application/json, text/plain, */*"
    }

    try:
        resp = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("videos", []), data.get("total_count", 0), data.get("total_pages", 1)
    except Exception as e:
        print(f"Eporner API error: {e}")
        return [], 0, 1


def get_video_detail(video_id):
    if not video_id:
        return None

    params = {"id": video_id, "thumbsize": "big", "format": "json"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.eporner.com/",
        "Accept": "application/json, text/plain, */*"
    }

    try:
        resp = requests.get(VIDEO_DETAIL_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        print(f"Video detail error for {video_id}: {e}")
        return None


# ────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "all").strip()
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    order = request.args.get("order", "latest")
    if order not in ["latest", "most-popular", "top-rated", "longest"]:
        order = "latest"

    videos, total_count, total_pages = fetch_videos(
        query=query,
        page=page,
        order=order,
        per_page=24
    )

    # Safety: make sure page doesn't go beyond real total
    page = min(max(page, 1), max(total_pages, 1))

    return render_template(
        "index.html",
        videos=videos,
        query=query if query != "all" else "",
        page=page,
        total_pages=total_pages,
        order=order,
        total_count=total_count
    )


@app.route("/video/<video_id>")
def video_detail(video_id):
    video = get_video_detail(video_id)
    if not video:
        abort(404, description="Video not found or removed")

    return render_template("video.html", video=video)


# Optional: custom 404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404   # create simple 404.html if you want


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=True
    )