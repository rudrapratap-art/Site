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
        "gay": 0,     # change to 1 or 2 if needed
        "lq": 1,
        "format": "json"
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        videos = data.get("videos", [])
        total_count = data.get("total_count", 0)
        total_pages = data.get("total_pages", 1)

        return videos, total_count, total_pages

    except requests.RequestException as e:
        print(f"API fetch error: {e}")
        return [], 0, 1
    except ValueError:
        print("API returned invalid JSON")
        return [], 0, 1


def get_video_detail(video_id):
    if not video_id:
        return None

    params = {
        "id": video_id,
        "thumbsize": "big",
        "format": "json"
    }

    try:
        resp = requests.get(VIDEO_DETAIL_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Video detail error ({video_id}): {e}")
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