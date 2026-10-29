import os, base64

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def get_icon(filename):
    path = os.path.join(BASE_DIR, "assets", filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
