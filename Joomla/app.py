from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:8888"}})


@app.route("/api/analyze", methods=["POST"])
def analyze_sentiment():
    data = request.get_json()
    if not data or 'review' not in data:
        return jsonify({"error": "No review text provided"}), 400

    review_text = data['review']
    blob = TextBlob(review_text)
    sentiment = blob.sentiment.polarity

    if sentiment > 0:
        sentiment_label = "Positive"
    elif sentiment < 0:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"

    result = {
        "sentiment_score": sentiment,
        "sentiment_label": sentiment_label
    }

    return jsonify(result), 200


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "Python Sentiment Analysis Service is running"}), 200


if __name__ == "__main__":
    from waitress import serve

    app.run(host="0.0.0.0", port=5001)

