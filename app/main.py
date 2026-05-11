from flask import Flask, render_template, request
from google import genai
import os

app = Flask(__name__)

# --- Configuration ---
GEMINI_API_KEY = "your_api_key"
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    url_to_scan = request.form.get('url')
    
    prompt = (
        f"Analyze the URL: {url_to_scan}. Provide a security report with: "
        "1. A Risk Score (0-100). "
        "2. Three bullet points covering Phishing, Malware, and Domain Integrity. "
        "3. A one-sentence final Conclusion. "
        "IMPORTANT: Do not use any markdown stars (**) or hashtags (###). "
        "Use plain text and start bullets with a simple dash (-)."
    )

    # Order of models: [Smartest (Low Limit) -> Smart (Medium) -> Efficient (High Limit)]
    models_to_try = [
        "gemini-3-flash-preview",     # The Apex model (20 RPD)
        "gemini-2.5-flash",           # The Ultra-stable (20 RPD)
        "gemini-3.1-flash-lite-preview" # The Workhorse (500 RPD)
        "gemini-1.5-flash-8b",           # The Ultimate backup (1500 RPD)
    ]

    ai_output = ""
    used_model = ""

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            ai_output = response.text
            used_model = model_name
            # If successful, break the loop and don't try the next models
            break 
        except Exception as e:
            # If it fails (like a 429 Rate Limit error), log it and move to next model
            print(f"Model {model_name} failed or limit reached. Trying next...")
            ai_output = f"Critical Error: All AI engines are currently at capacity. {str(e)}"
            used_model = "System Failure"

    analysis_result = {
        "url": url_to_scan,
        "status": "Analysis Complete",
        "risk_score": f"Engine: {used_model}",
        "details": ai_output
    }
    
    return render_template('result.html', result=analysis_result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
