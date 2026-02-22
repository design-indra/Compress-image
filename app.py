from flask import Flask, render_template, request, send_file
import os
import io
import base64
from PIL import Image

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

MAX_SIZE = 10 * 1024 * 1024  # 10MB

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        file = request.files.get("image")
        quality = int(request.form.get("quality", 70))
        output_format = request.form.get("format", "auto")

        if not file or file.filename == "":
            error = "Pilih file gambar terlebih dahulu."
        elif not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            error = "Format tidak didukung. Gunakan PNG, JPG, atau WEBP."
        else:
            file_bytes = file.read()
            original_size = len(file_bytes)

            if original_size > MAX_SIZE:
                error = "Ukuran file terlalu besar. Maksimal 10MB."
            else:
                try:
                    img = Image.open(io.BytesIO(file_bytes))
                    orig_format = img.format or "JPEG"

                    # Tentukan format output
                    if output_format == "auto":
                        fmt = "JPEG" if orig_format in ("JPEG", "JPG") else orig_format
                    elif output_format == "jpg":
                        fmt = "JPEG"
                    elif output_format == "png":
                        fmt = "PNG"
                    elif output_format == "webp":
                        fmt = "WEBP"
                    else:
                        fmt = "JPEG"

                    # Convert RGBA ke RGB jika perlu
                    if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    buffer = io.BytesIO()
                    if fmt == "PNG":
                        img.save(buffer, format="PNG", optimize=True)
                    else:
                        img.save(buffer, format=fmt, quality=quality, optimize=True)

                    buffer.seek(0)
                    compressed_bytes = buffer.getvalue()
                    compressed_size = len(compressed_bytes)
                    saved_pct = round((1 - compressed_size / original_size) * 100, 1)

                    img_b64 = base64.b64encode(compressed_bytes).decode("utf-8")
                    ext = fmt.lower().replace("jpeg", "jpg")
                    mime = f"image/{ext}"

                    result = {
                        "image": img_b64,
                        "mime": mime,
                        "ext": ext,
                        "original_size": round(original_size / 1024, 1),
                        "compressed_size": round(compressed_size / 1024, 1),
                        "saved_pct": saved_pct,
                        "width": img.width,
                        "height": img.height,
                    }
                except Exception as e:
                    print(f"Compress error: {e}")
                    error = "Gagal memproses gambar. Coba dengan gambar lain."

    return render_template("index.html", result=result, error=error)

@app.route("/download", methods=["POST"])
def download():
    img_data = request.form.get("image_data")
    ext = request.form.get("ext", "jpg")
    if not img_data:
        return "Invalid", 400
    try:
        img_bytes = base64.b64decode(img_data)
        buffer = io.BytesIO(img_bytes)
        mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
        return send_file(buffer, mimetype=mime,
                         as_attachment=True, download_name=f"compressed.{ext}")
    except Exception as e:
        print(f"Download error: {e}")
        return "Error", 500

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    app.run(debug=True)
