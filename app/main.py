import os
import time
from flask import Flask, render_template, request
import google.genai as genai  
from groq import Groq

app = Flask(__name__)

# --- Configuration & Client Initialization ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GEMINI_API_KEY or not GROQ_API_KEY:
    print("❌ [CRITICAL] Environmental API keys are missing! Check your configuration.")

# Native SDK Client Registrations
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# 3 Best Models Fleet
MODELS_TO_TRY = [
    {"provider": "gemini", "model_name": "gemini-2.5-flash"},          # Tier 1
    {"provider": "groq", "model_name": "llama-3.3-70b-versatile"},     # Tier 2
    {"provider": "groq", "model_name": "llama-3.1-8b-instant"}         # Tier 3
]

def warmup_engines():
    """Warms up the AI fleet safely without breaking boot sequence if keys are missing."""
    print("🚀 [STARTUP] Initializing SentinelScan Multi-Provider AI Fleet...")
    
    if gemini_client:
        try:
            gemini_client.models.generate_content(model=MODELS_TO_TRY[0]["model_name"], contents="ping")
            print(f"✅ [WARMUP] Gemini ({MODELS_TO_TRY[0]['model_name']}) is online.")
        except Exception as e:
            print(f"⚠️ [WARMUP] Gemini standby (Handshake pending): {str(e)[:40]}")
    
    if groq_client:
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
    selected_tier = request.form.get('provider_tier') 
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

    # Re-order the fleet sequence based on frontend dropdown choice
    if selected_tier == "gemini":
        ordered_fleet = [MODELS_TO_TRY[0], MODELS_TO_TRY[1], MODELS_TO_TRY[2]]
    elif selected_tier == "groq-70b":
        ordered_fleet = [MODELS_TO_TRY[1], MODELS_TO_TRY[0], MODELS_TO_TRY[2]]
    elif selected_tier == "groq-8b":
        ordered_fleet = [MODELS_TO_TRY[2], MODELS_TO_TRY[0], MODELS_TO_TRY[1]]
    else:
        ordered_fleet = MODELS_TO_TRY

    ai_output = ""
    used_model = "Maintenance Mode"
    audit_logs = []  # 📊 Dynamic list tracking execution path updates

    # --- Intelligent Multi-Provider Fallback Routing Engine ---
    for item in ordered_fleet:
        provider = item["provider"]
        model_name = item["model_name"]
        
        try:
            log_msg = f"📡 Dispatching runtime request payload to {provider.upper()} ({model_name})..."
            print(log_msg)
            audit_logs.append({"status": "attempt", "text": log_msg})
            
            if provider == "gemini" and gemini_client:
                response = gemini_client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                ai_output = response.text
                used_model = f"{provider.capitalize()} ({model_name})"
                
                success_msg = f"✅ Target resolution satisfied successfully via {used_model}."
                audit_logs.append({"status": "success", "text": success_msg})
                break
                
            elif provider == "groq" and groq_client:
                response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_output = response.choices[0].message.content
                used_model = f"{provider.capitalize()} ({model_name})"
                
                success_msg = f"✅ Target resolution satisfied successfully via {used_model}."
                audit_logs.append({"status": "success", "text": success_msg})
                break
                
        except Exception as e:
            error_preview = str(e)[:50]
            fail_msg = f"⚠️ Fallback Alert: {provider.upper()} ({model_name}) dropped connection ({error_preview}...). Bypassing layer..."
            print(f"❌ {fail_msg}")
            audit_logs.append({"status": "fail", "text": fail_msg})
            ai_output = "System Overload: All multi-cloud AI engines are currently at capacity. Please retry shortly."

    duration = round(time.time() - start_time, 2)
    print(f"⏱️ [PERF] Scan completed in {duration}s")

    analysis_result = {
        "url": url_to_scan,
        "status": "Analysis Complete",
        "risk_score": f"Verified by {used_model}",
        "details": ai_output,
        "logs": audit_logs  # Sending arrays out to your web view template
    }
    
    return render_template('result.html', result=analysis_result)

if __name__ == '__main__':
    warmup_engines()
    app.run(host='0.0.0.0', port=5000, debug=False)
