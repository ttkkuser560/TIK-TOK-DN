from flask import Flask, request, send_file, after_this_request
from flask_cors import CORS
import instaloader
from instaloader import Post
import tempfile
import os
import re
import shutil

app = Flask(__name__)

# তোমার TikDown website-এর জন্য CORS
CORS(app)

L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=True,
    download_video_thumbnails=False,
    save_metadata=False
)

@app.route("/", methods=["GET"])
def home():
    return {
        "status": "online",
        "app": "TikDown Instagram API"
    }

@app.route("/download", methods=["POST"])
def download_video():

    data = request.get_json(silent=True)

    if not data or "url" not in data:
        return {"error": "Instagram URL is required"}, 400

    url = data["url"]

    # Instagram URL validation
    match = re.search(
        r"instagram\.com/(?:p|reel|tv)/([^/?]+)",
        url
    )

    if not match:
        return {"error": "Invalid Instagram URL"}, 400

    shortcode = match.group(1)
    temp_dir = tempfile.mkdtemp()

    try:
        # Load public post
        post = Post.from_shortcode(
            L.context,
            shortcode
        )

        if not post.is_video:
            return {"error": "No video found"}, 400

        # Download authorized public video
        L.download_post(
            post,
            target=temp_dir
        )

        video_file = next(
            (
                os.path.join(temp_dir, f)
                for f in os.listdir(temp_dir)
                if f.lower().endswith(".mp4")
            ),
            None
        )

        if not video_file:
            return {"error": "Video file not found"}, 404

        @after_this_request
        def cleanup(response):
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )
            return response

        return send_file(
            video_file,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="instagram_video.mp4"
        )

    except Exception:
        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        return {
            "error": "Unable to download. Post may be unavailable."
        }, 500

    return {"error": "Download failed"}, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port
)
