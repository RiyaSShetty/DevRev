from flask import Flask, request, jsonify
from textblob import TextBlob  # Example NLP library for sentiment analysis
import requests

app = Flask(__name__)

# Threshold for frustration detection
FRUSTRATION_THRESHOLD = -0.3

# DevRev API token for authentication
DEVREV_API_TOKEN = "eyJhbGciOiJSUzI1NiIsImlzcyI6Imh0dHBzOi8vYXV0aC10b2tlbi5kZXZyZXYuYWkvIiwia2lkIjoic3RzX2tpZF9yc2EiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiamFudXMiXSwiYXpwIjoiZG9uOmlkZW50aXR5OmR2cnYtdXMtMTpkZXZvLzFxVUxZUlp1Tk46ZGV2dS8yIiwiZXhwIjoxODI3Mjk4MjQ2LCJodHRwOi8vZGV2cmV2LmFpL2F1dGgwX3VpZCI6ImRvbjppZGVudGl0eTpkdnJ2LXVzLTE6ZGV2by9zdXBlcjphdXRoMF91c2VyL2dvb2dsZS1vYXV0aDJ8MTAyOTk1OTY3MjcyMDg3NDk4NDc5IiwiaHR0cDovL2RldnJldi5haS9hdXRoMF91c2VyX2lkIjoiZ29vZ2xlLW9hdXRoMnwxMDI5OTU5NjcyNzIwODc0OTg0NzkiLCJodHRwOi8vZGV2cmV2LmFpL2Rldm9fZG9uIjoiZG9uOmlkZW50aXR5OmR2cnYtdXMtMTpkZXZvLzFxVUxZUlp1Tk4iLCJodHRwOi8vZGV2cmV2LmFpL2Rldm9pZCI6IkRFVi0xcVVMWVJadU5OIiwiaHR0cDovL2RldnJldi5haS9kZXZ1aWQiOiJERVZVLTIiLCJodHRwOi8vZGV2cmV2LmFpL2Rpc3BsYXluYW1lIjoicml5YXNoZXR0eTE1MTAiLCJodHRwOi8vZGV2cmV2LmFpL2VtYWlsIjoicml5YXNoZXR0eTE1MTBAZ21haWwuY29tIiwiaHR0cDovL2RldnJldi5haS9mdWxsbmFtZSI6IlJpeWEgUyBTaGV0dHkiLCJodHRwOi8vZGV2cmV2LmFpL2lzX3ZlcmlmaWVkIjp0cnVlLCJodHRwOi8vZGV2cmV2LmFpL3Rva2VudHlwZSI6InVybjpkZXZyZXY6cGFyYW1zOm9hdXRoOnRva2VuLXR5cGU6cGF0IiwiaWF0IjoxNzMyNjkwMjQ2LCJpc3MiOiJodHRwczovL2F1dGgtdG9rZW4uZGV2cmV2LmFpLyIsImp0aSI6ImRvbjppZGVudGl0eTpkdnJ2LXVzLTE6ZGV2by8xcVVMWVJadU5OOnRva2VuL2tCY0Y5S0Z6Iiwib3JnX2lkIjoib3JnX296QXdoaldKTllMUHMwN2EiLCJzdWIiOiJkb246aWRlbnRpdHk6ZHZydi11cy0xOmRldm8vMXFVTFlSWnVOTjpkZXZ1LzIifQ.Wn7cxTc0r5ZLIdMawUFQ8pmPegUQlNEdgoSsp2ykAtnu5UfvSX7Oa5MCZ2rZ0QU-PXpstv8X7NKZbotZklsnC2hr8TDD1xASUa-kWWvkBoq1IZHMEGBYkbmmceLcImgdVUcAmZ4WSOJ1QFrulyidttVHupzH4Td36tLiFPwq-YWKF-LROp8U5uE7bNx_dBn3RMPQP6K_YgTTkHy3Dvt3VdZ2Mx9ZEqNNlNtq7EnfeQf--0WjwG47JSsjaa18Vhrr6w5gznTPjku1rN9W9Nlqf-aDX08oIfIStWWgJbItiO02ejKff5CmV_SAGhn1ofqSuBfN5WEJCBDl0w0VnkBsww"
DEVREV_ALERT_URL = "https://api.devrev.ai/v1/alerts"  # Replace with the correct endpoint

@app.route('/webhook', methods=['POST'])
def analyze_message():
    """
    Webhook endpoint for Automatic Customer Reply or Slash Commands.
    Analyzes sentiment and triggers alerts if frustration is detected.
    """
    # Parse the incoming JSON payload
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid payload"}), 400

    message = data.get('message')  # Customer message
    customer_id = data.get('customer_id')  # Optional: Customer ID for tracking

    # Sentiment analysis
    sentiment = TextBlob(message).sentiment
    polarity = sentiment.polarity

    # Check for frustration
    if polarity < FRUSTRATION_THRESHOLD:
        # Trigger an alert via DevRev API
        alert_payload = {
            "title": "Customer Frustration Alert",
            "description": f"Customer ({customer_id}) appears frustrated. Message: {message}",
            "severity": "high",
            "custom_fields": {
                "customer_id": customer_id,
                "sentiment_score": polarity
            }
        }

        headers = {
            "Authorization": f"Bearer {DEVREV_API_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(DEVREV_ALERT_URL, json=alert_payload, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            return jsonify({"error": f"Failed to send alert: {str(e)}"}), 500

        return jsonify({"status": "Frustration alert triggered", "alert": alert_payload}), 200

    # No frustration detected
    return jsonify({"status": "No frustration detected", "sentiment_score": polarity}), 200

@app.route('/slash-analyze', methods=['POST'])
def slash_analyze():
    """
    Endpoint for Slash Command `/analyze`.
    Manually analyzes a message and provides immediate feedback.
    """
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid payload"}), 400

    message = data.get('message')
    sentiment = TextBlob(message).sentiment
    polarity = sentiment.polarity

    if polarity < FRUSTRATION_THRESHOLD:
        return jsonify({
            "response_type": "in_channel",
            "text": f"Frustration detected! Sentiment score: {polarity:.2f}",
        })

    return jsonify({
        "response_type": "in_channel",
        "text": f"No frustration detected. Sentiment score: {polarity:.2f}",
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Running", "message": "Customer Frustration Alerting System is healthy!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)







