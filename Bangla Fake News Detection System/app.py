import subprocess  # Used to run the scraper script
from flask import Flask, request, render_template
import pandas as pd
import re
import io
import base64
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)

# === Normalize URLs (Remove tracking parameters) ===
def normalize_url(url):
    return re.sub(r'\?.*$', '', url.strip())

# === Load CSV Data (with links and titles) ===
def load_verified_data():
    try:
        df = pd.read_csv("data/data.csv")
        links = set()
        titles = set()

        for _, row in df.iterrows():
            if pd.notna(row['news_link']):
                links.add(normalize_url(row['news_link']))
            if pd.notna(row['text']):
                titles.add(row['text'].strip().lower())

        return links, titles
    except Exception as e:
        print("⚠ Error loading CSV:", e)
        return set(), set()

# === Generate Confusion Matrix Image ===
def generate_confusion_matrix_image(is_real):
    colors = ["red", "green"] if is_real else ["green", "red"]  # Fake -> Green, Real -> Red
    matrix = [[1, 0], [0, 1]] if is_real else [[0, 1], [1, 0]]

    fig, ax = plt.subplots(figsize=(4, 3))
    sns.heatmap(matrix, annot=True, fmt="d", cmap=sns.color_palette(colors),
                xticklabels=["Fake", "Real"], yticklabels=["Real", "Fake"])  # Labels remain unchanged
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix - Real vs Fake")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

# === Home Page ===
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    matrix_img = None

    # Load verified links/titles from CSV
    verified_links, verified_titles = load_verified_data()

    if request.method == "POST":
        user_input = request.form["news_input"].strip().lower()
        normalized_input = normalize_url(user_input)

        # Verify by headline or URL
        is_real = any(title in user_input for title in verified_titles) or \
                  any(normalized_input in link for link in verified_links)

        result = "✅ Verified News - Found in trusted sources!" if is_real else \
                 "⚠ Fake News - Not found in trusted sources!"

        matrix_img = generate_confusion_matrix_image(is_real)

    return render_template("index.html", result=result, matrix_img=matrix_img)

# === Refresh News Data (Styled Like True News) ===
@app.route("/refresh", methods=["GET"])
def refresh_data():
    try:
        subprocess.run(["python", "scraper.py"], check=True)  # Run scraper.py to update CSV
        update_message = '''
        <div style="text-align:center; padding:20px; background:#e6f4ea; color:#1b5e20; 
                    border-radius:6px; font-size:1.2rem; font-weight:600;">
            ✅ News data updated successfully!
        </div>
        '''
    except subprocess.CalledProcessError:
        update_message = '''
        <div style="text-align:center; padding:20px; background:#ffebee; color:#b71c1c; 
                    border-radius:6px; font-size:1.2rem; font-weight:600;">
            ⚠ Error updating news data! Try again later.
        </div>
        '''

    return render_template("index.html", result=update_message, matrix_img=None)

# === Run the Flask App ===
if __name__ == "__main__":
    app.run(debug=True)
