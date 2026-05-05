import os
import sys
import json
import re
import time
from groq import Groq

# --- M1 (RAG FAQ) Integration ---
def get_m1_faq_answer(query):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    m1_path = os.path.join(base_dir, "mf-rag-faq-indmoney")
    m1_api_path = os.path.join(m1_path, "Phase_8")
    
    if m1_api_path not in sys.path:
        sys.path.insert(0, m1_api_path)
    
    # Load environment for M1
    from dotenv import load_dotenv
    load_dotenv(os.path.join(m1_path, ".env"))
    
    # Import M1 functions
    from api import retrieve_context, generate_answer
    
    print(f">>> 🔍 Querying M1 RAG System: '{query}'...")
    contexts = retrieve_context(query)
    
    if not contexts:
        return "I do not have the factual information for this specific request.", []
    
    # Use only top context as per M1 requirement
    answer = generate_answer(query, contexts[:1])
    sources = [c['url'] for c in contexts[:1]]
    
    return answer, sources

# --- M2 (Pulse/Fee) Integration ---
def get_m2_pulse_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    m2_output_path = os.path.join(base_dir, "indmoney-pulse", "output")
    trends_file = os.path.join(m2_output_path, "v3_trends.json")
    report_file = os.path.join(m2_output_path, "v3_weekly_pulse.md")
    
    top_theme = "Unknown"
    summary = "No summary available."
    
    if os.path.exists(trends_file):
        with open(trends_file, 'r') as f:
            trends = json.load(f)
            if trends:
                top_theme = max(trends.items(), key=lambda x: x[1].get('current_pct', 0))[0]
    
    if os.path.exists(report_file):
        with open(report_file, 'r') as f:
            content = f.read()
            if "### Action Ideas" in content:
                summary = content.split("### Action Ideas")[-1].strip().split("\n")[0] # First action idea
            elif "### User Voices" in content:
                summary = content.split("### User Voices")[-1].split("###")[0].strip().split("\n")[0]

    return top_theme, summary

def get_m2_fee_explainer():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    m2_output_path = os.path.join(base_dir, "indmoney-pulse", "output")
    fee_file = os.path.join(m2_output_path, "v5_fee_explanation.json")
    
    if not os.path.exists(fee_file):
        fee_file = os.path.join(base_dir, "indmoney-pulse", "backend", "output", "v5_fee_explanation.json")

    if os.path.exists(fee_file):
        with open(fee_file, 'r') as f:
            data = json.load(f)
            explanation = data.get("explanation", "")
            bullets = [line.strip("- ").strip() for line in explanation.split("\n") if line.strip().startswith("-")]
            return bullets[:3], data.get("source_links", [])
    return [], []

# --- M3 (Orchestrator) Integration ---
def get_m3_response(user_query, top_theme):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    m3_path = os.path.join(base_dir, "multi-agent-appointment-orchestrator", "production_app")
    if m3_path not in sys.path:
        sys.path.insert(0, m3_path)
    
    from dotenv import load_dotenv
    load_dotenv(os.path.join(m3_path, ".env"))
    
    from orchestrator import Orchestrator, NLUEngine
    from session import SessionContext
    
    api_key = os.getenv("GROQ_API_KEY")
    nlu = NLUEngine(api_key=api_key)
    orch = Orchestrator(nlu)
    ctx = SessionContext(session_id="integrated_user_123")
    
    modified_input = f"{user_query}. Current user issue trend: {top_theme}. Mention this naturally."
    m3_response = orch.handle_message(modified_input, ctx)
    
    client = Groq(api_key=api_key)
    res = client.chat.completions.create(
        messages=[{"role": "user", "content": f"M3 State Response: {m3_response}\nTrend: {top_theme}\nUser Input: {user_query}\n\nCombine naturally into a single response mentioning the trend:"}],
        model="llama-3.3-70b-versatile"
    )
    return res.choices[0].message.content.strip()

# --- Main App Logic ---
def main():
    start_time = time.time()
    
    print("\n" + "="*60)
    print("🧪 FULL SYSTEM INTEGRATION TEST")
    print("="*60)

    # TEST 1: M2 Test (Pulse)
    print("\n[TEST 1: M2 Pulse]")
    top_theme, m2_summary = get_m2_pulse_data()
    print(f"Top Theme: {top_theme}")
    print(f"Summary: {m2_summary}")

    # TEST 2: M3 Test (Voice Agent)
    print("\n[TEST 2: M3 Voice Agent]")
    user_query_m3 = "I want to book a call"
    m3_response = get_m3_response(user_query_m3, top_theme)
    print(f"User Input: {user_query_m3}")
    print(f"Top Theme: {top_theme}")
    print(f"M3 Response: {m3_response}")

    # TEST 3: M1 + M2 Test (Smart-Sync)
    print("\n[TEST 3: M1 + M2 Smart-Sync]")
    user_query_m1 = "What is exit load for ELSS and why was I charged it?"
    m1_answer, m1_sources = get_m1_faq_answer(user_query_m1)
    clean_m1_text = m1_answer.split("Source:")[0].strip()
    m1_bullets = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_m1_text) if s.strip()]
    while len(m1_bullets) < 3: m1_bullets.append("N/A")
    m1_bullets = m1_bullets[:3]
    
    m2_bullets, m2_sources = get_m2_fee_explainer()
    while len(m2_bullets) < 3: m2_bullets.append("N/A")
    m2_bullets = m2_bullets[:3]
    
    combined_bullets = m1_bullets + m2_bullets
    print(f"Query: {user_query_m1}")
    print("Combined 6-Bullet Response:")
    for i, b in enumerate(combined_bullets):
        print(f"{i+1}. {b}")
    print("Sources:")
    for s in list(set(m1_sources + m2_sources)):
        print(f"- {s}")

    end_time = time.time()
    duration = end_time - start_time
    print(f"\n[PERFORMANCE] Total Execution Time: {duration:.2f} seconds")
    print("="*60)

if __name__ == "__main__":
    main()
