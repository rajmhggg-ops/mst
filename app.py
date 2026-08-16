from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageOps, ImageEnhance
import pytesseract, io, os, re

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

ALLOWED = {"image/jpeg", "image/png", "image/webp"}

def clean_text(t):
    t=(t or "").strip()
    t=re.sub(r"\s+", " ", t)
    return t

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/ocr")
def ocr():
    if "image" not in request.files:
        return jsonify(error="No image uploaded"), 400
    f=request.files["image"]
    if f.mimetype not in ALLOWED:
        return jsonify(error="Use JPG, PNG or WebP"), 400
    try:
        im=Image.open(f.stream).convert("RGB")
        # Upscale small images to improve OCR.
        if im.width < 1200:
            scale=min(3, 1200/im.width)
            im=im.resize((int(im.width*scale), int(im.height*scale)), Image.Resampling.LANCZOS)
        # Mild contrast/sharpness only; keep original coordinates in this working image.
        gray=ImageOps.grayscale(im)
        gray=ImageEnhance.Contrast(gray).enhance(1.25)
        gray=ImageEnhance.Sharpness(gray).enhance(1.2)

        data=pytesseract.image_to_data(
            gray,
            lang="eng",
            config="--psm 11",
            output_type=pytesseract.Output.DICT
        )
        words=[]
        for i,t in enumerate(data["text"]):
            t=clean_text(t)
            conf=float(data["conf"][i])
            if not t or conf < 35:
                continue
            x,y,w,h=(int(data[k][i]) for k in ("left","top","width","height"))
            # Normalize common currency OCR variants.
            t=re.sub(r"(?i)^inr(?=\s*\d)", "₹", t)
            t=re.sub(r"(?i)^rs\.?(?=\s*\d)", "₹", t)
            words.append({"text":t,"x":x,"y":y,"w":w,"h":h,"confidence":round(conf,1)})

        # De-duplicate heavily overlapping boxes.
        def area(a): return max(1,a["w"])*max(1,a["h"])
        def overlap(a,b):
            x=max(0,min(a["x"]+a["w"],b["x"]+b["w"])-max(a["x"],b["x"]))
            y=max(0,min(a["y"]+a["h"],b["y"]+b["h"])-max(a["y"],b["y"]))
            return x*y
        words.sort(key=lambda z:z["confidence"], reverse=True)
        clean=[]
        for w in words:
            if not any(overlap(w,q)/min(area(w),area(q)) > .65 for q in clean):
                clean.append(w)

        return jsonify(width=im.width,height=im.height,regions=clean[:250])
    except Exception as e:
        return jsonify(error=f"OCR failed: {e}"), 500

@app.get("/health")
def health():
    return jsonify(ok=True, ocr="tesseract-server")

@app.errorhandler(413)
def too_large(_):
    return jsonify(error="Image is too large. Maximum 12 MB."), 413

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
