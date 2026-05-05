import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from production.orchestrator import Orchestrator, MockNLUEngine
from production.nlu_engine import NLUEngine
from production.session import SessionContext, State
from dotenv import load_dotenv
import os

# Find the absolute path to the .env file in the production directory
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path) 

app = FastAPI()

# 1. Security (CORS) - Allows your website to talk to your server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup the Brain
try:
    nlu = NLUEngine()
    print("✅ Real NLU Engine Started (Groq)")
except Exception as e:
    print(f"⚠️ NLU Startup Warning: {e}. Using Mock AI Engine.")
    nlu = MockNLUEngine()

orch = Orchestrator(nlu)

# 3. Simple in-memory storage for User Sessions
# (In a big app, we would use a Database like Redis)
sessions = {}

def get_top_theme():
    """Reads the latest top theme from M2 output (v3_trends.json)."""
    try:
        # Use relative path or environment variable for production flexibility
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_path = os.path.join(current_dir, "../../indmoney-pulse/backend/output/v3_trends.json")
        file_path = os.getenv("TRENDS_FILE_PATH", default_path)
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                if not data:
                    return None
                
                # Find the theme with the highest current_pct
                top_theme = None
                max_pct = -1.0
                
                for theme, stats in data.items():
                    current_pct = stats.get("current_pct", 0)
                    if current_pct > max_pct:
                        max_pct = current_pct
                        top_theme = theme
                
                return top_theme
    except Exception as e:
        print(f"⚠️ Error reading trends for greeting: {e}")
    return None

@app.get("/greeting")
async def get_greeting():
    """Returns a theme-aware greeting with actionable guidance based on M2 Pulse data."""
    theme = get_top_theme()
    
    # Contextual Guidance Mapping
    guidance_map = {
        "Trading Features": "I see many users are facing issues related to Trading Features. Would you like help with order execution issues, transaction failures, or feature configuration?",
        "Payment Issues": "I see users are facing payment-related issues. I can help you schedule a session for failed transactions or refund tracking.",
        "Payments & Rewards": "I see users are facing payment-related issues. I can help you schedule a session for failed transactions or refund tracking.",
        "App Performance": "I see users are reporting performance issues. I can help you schedule a session for app lag, crash analysis, or loading delays.",
        "Account Issues": "I see a trend in account-related queries. I can help you with login verification, profile synchronization, or security settings.",
        "High Charges": "I see users are concerned about platform charges. I can help you schedule a session for fee transparency or billing disputes."
    }

    if theme and theme in guidance_map:
        response = guidance_map[theme]
    elif theme:
        response = f"I see many users are currently facing issues related to {theme}. I can help you schedule a strategy session for that."
    else:
        response = "I can help you schedule a strategy session based on your needs."
    
    return JSONResponse(content={"response": response, "theme": theme})

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serves the main website."""
    # Find the absolute path to static/index.html
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "static", "index.html")
    
    print(f"🔍 DEBUG: Attempting to serve index from: {index_path}")
    
    if not os.path.exists(index_path):
        print(f"❌ ERROR: index.html NOT FOUND at {index_path}")
        return HTMLResponse(content="<h1>Error: Home page file not found.</h1>", status_code=404)
        
    try:
        with open(index_path, "r") as f:
            return f.read()
    except Exception as e:
        print(f"❌ ERROR: Could not read index.html: {e}")
        return HTMLResponse(content=f"<h1>Internal Error: {str(e)}</h1>", status_code=500)

@app.post("/chat")
async def chat(request: Request):
    """Receives user input from the website and returns AI response."""
    data = await request.json()
    user_text = data.get("text")
    session_id = data.get("session_id", "default")

    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = SessionContext(session_id=session_id)
    
    ctx = sessions[session_id]
    
    # Process message through our existing Orchestrator!
    res_dict = orch.handle_message(user_text, ctx)
    
    return {
        "response": res_dict["response"],
        "state": res_dict["state"],
        "date": res_dict.get("date")
    }

@app.post("/book_call")
async def book_call(request: Request):
    """Triggers the real booking flow: Calendar + Docs + Gmail."""
    data = await request.json()
    objective = data.get("objective")
    date_str = data.get("date")
    urgency = data.get("urgency")
    theme = data.get("theme")
    market_context = data.get("marketContext")

    from production.booking_logic import BookingCodeGenerator
    from production.mcp_server import calendar_create_hold, docs_append_prebooking, gmail_create_draft
    
    # Use provided booking_id if available, otherwise generate new one
    booking_code = data.get("booking_id") or BookingCodeGenerator.generate()
    
    # 1. Create Calendar Hold (Assuming 10 AM UTC for the requested date for demo)
    # In a real app, we'd parse the date_str and find a real slot
    start_time = f"{date_str}T10:00:00Z" 
    try:
        cal_res = calendar_create_hold(start_time, f"{theme} Strategy Session", booking_code)
    except Exception as e:
        cal_res = f"⚠️ Calendar Hold skipped: {str(e)}"
    
    # 2. Log in Docs
    try:
        doc_res = docs_append_prebooking(booking_code, theme, f"{date_str} (via Dashboard)")
    except Exception as e:
        doc_res = f"⚠️ Doc logging skipped: {str(e)}"
    
    # 3. Create Gmail Draft
    subject = f"ACTION REQUIRED: {theme} Strategy Session ({booking_code})"
    body = f"""
Hello,

A new strategy session has been approved via the Intelligence Dashboard.

Objective: {objective}
Requested Date: {date_str}
Urgency: {urgency}
Market Context: {market_context}

System Traceability:
- Theme: {theme}
- Booking Code: {booking_code}

Please review and confirm with the client.
    """
    try:
        gmail_res = gmail_create_draft("advisor@example.com", subject, body)
    except Exception as e:
        gmail_res = f"⚠️ Gmail draft skipped: {str(e)}"
    
    return {
        "status": "success",
        "booking_id": booking_code,
        "calendar": cal_res,
        "docs": doc_res,
        "gmail": gmail_res
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
