from flask import Flask, render_template, request
from google import genai
from groq import Groq
import os
import time

app = Flask(__name__)

# --- Configuration & Client Initialization ---
# Safely pulling keys from environment variables 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Fail-safe check to alert you in the logs if variables are completely missing
if not GEMINI_API_KEY or not GROQ_API_KEY:
    print("❌ [CRITICAL] Environmental API keys are missing! Check your configuration.")

# Native SDK Client Registrations
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# Native SDK Client Registrations
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# 3 Best Models Fleet: [Gemini Smartest Free -> Groq Flagship -> Groq High Volume]
MODELS_TO_TRY = [
    {"provider": "gemini", "model_name": "gemini-2.5-flash"},          # Tier 1: Gemini Balance & Intelligence
    {"provider": "groq", "model_name": "llama-3.3-70b-versatile"},     # Tier 2: Groq High-Performance Flagship
    {"provider": "groq", "model_name": "llama-3.1-8b-instant"}         # Tier 3: Groq Hyper-Speed & Volume Backup
]

def warmup_engines():
    """Warms up the AI fleet during server startup to prevent first-run lag."""
    print("🚀 [STARTUP] Initializing SentinelScan Multi-Provider AI Fleet...")
    
    # Warm up Gemini Primary
    try:
        gemini_client.models.generate_content(model=MODELS_TO_TRY[0]["model_name"], contents="ping")
        print(f"✅ [WARMUP] Gemini ({MODELS_TO_TRY[0]['model_name']}) is online.")
    except Exception as e:
        print(f"⚠️ [WARMUP] Gemini standby (Handshake pending): {str(e)[:40]}")
        
    # Warm up Groq Primary
    try:
        groq_client.chat.completions.create(
            model=MODELS_TO_TRY[1]["model_name"],
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print(f"✅ [WARMUP] Groq ({MODELS_TO_TRY[1]['model_name']}) is online.")
    except Exception as e:
        print(f"⚠️ [WARMUP] Groq standby (Handshake pending): {str(e)[:40]}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    url_to_scan = request.form.get('url')
    selected_tier = request.form.get('provider_tier') # 🎛️ Captures the user's dropdown choice
    start_time = time.time()
    
    prompt = (
        f"Analyze the URL: {url_to_scan}. Provide a highly structured security report. "
        "You must format the response exactly as follows, using the exact labels and <br> tags:\n\n"
        "RISK_SCORE: [Insert number only, 0-100]\n"
        "<br><br>\n"
        "SECURITY SUMMARY:\n"
        "- Phishing Analysis: [Your findings]<br>\n"
        "- Malware Detection: [Your findings]<br>\n"
        "- Domain Integrity: [Your findings]\n"
        "<br><br>\n"
        "CONCLUSION: [Your one-sentence conclusion]\n\n"
        "IMPORTANT: Do not use any markdown stars (**) or hashtags (###). Use plain text and the <br> tags exactly as requested."
    )

    # Re-order the fleet sequence based on what the user chose from the frontend
    ordered_fleet = []
    if selected_tier == "gemini":
        ordered_fleet = [MODELS_TO_TRY[0], MODELS_TO_TRY[1], MODELS_TO_TRY[2]]
    elif selected_tier == "groq-70b":
        ordered_fleet = [MODELS_TO_TRY[1], MODELS_TO_TRY[0], MODELS_TO_TRY[2]]
    elif selected_tier == "groq-8b":
        ordered_fleet = [MODELS_TO_TRY[2], MODELS_TO_TRY[0], MODELS_TO_TRY[1]]
    else:
        ordered_fleet = MODELS_TO_TRY # Standard fallback lineup default

    ai_output = ""
    used_model = ""

    # --- Intelligent Multi-Provider Fallback Routing Engine ---
    for item in ordered_fleet:
        provider = item["provider"]
        model_name = item["model_name"]
        
        try:
            print(f"📡 [USER ROUTE] Attempting analysis with {provider.upper()} ({model_name})...")
            
            if provider == "gemini":
                response = gemini_client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                ai_output = response.text
                
            elif provider == "groq":
                response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.choices[0].message.content
                
            used_model = f"{provider.capitalize()} ({model_name})"
            print(f"✔️ [SUCCESS] User request satisfied by {used_model}")
            break 
            
        except Exception as e:
            print(f"❌ [FALLBACK TRIGGERED] {provider.upper()} ({model_name}) error: {str(e)[:40]}...")
            ai_output = "System Overload: All multi-cloud AI engines are currently at capacity. Please retry shortly."
            used_model = "Maintenance Mode"

    # Performance monitoring execution log
    duration = round(time.time() - start_time, 2)
    print(f"⏱️ [PERF] Scan completed in {duration}s")

    analysis_result = {
        "url": url_to_scan,
        "status": "Analysis Complete",
        "risk_score": f"Verified by {used_model}",
        "details": ai_output
    }
    
    return render_template('result.html', result=analysis_result)

if __name__ == '__main__':
    # Initialize engines before the Flask server starts accepting traffic
    warmup_engines()
    # Optimized for OCI production performance execution
    app.run(host='0.0.0.0', port=5000, debug=False)
