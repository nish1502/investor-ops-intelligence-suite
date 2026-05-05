from fastapi import FastAPI, HTTPException, Request
from datetime import datetime
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import psycopg2
import re
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import torch
from groq import Groq
from dotenv import load_dotenv

# --- Configuration & Initialization ---
# Load .env from the root directory relative to this file
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

app = FastAPI()

@app.get("/metadata")
async def get_metadata():
    return {
        "data_last_updated": datetime.now().strftime("%d %B %Y, %I:%M %p")
    }

@app.post("/test")
async def test_endpoint():
    print("TEST ENDPOINT CALLED")
    return {"status": "ok"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"DEBUG: Incoming Request {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"DEBUG: Request {request.method} {request.url.path} - Result: {response.status_code}")
    return response

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# Initialize local SentenceTransformer model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_query_embedding(text: str) -> Optional[list[float]]:
    """Generates embedding vector using local sentence-transformers model."""
    try:
        print(f"DEBUG: Generating local embedding for: {text[:50]}...")
        # Ensure we're in eval mode and no grad for speed/memory
        embedding_model.eval()
        with torch.no_grad():
            vector = embedding_model.encode(text).tolist()
        return vector
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return None

# Standardized Model Constants
# Using local all-MiniLM-L6-v2 model (384 dimensions)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
# LLaMA model from Groq
GROQ_MODEL = "llama-3.1-8b-instant"

# Data Freshness
DATA_LAST_UPDATED = "05-03-2026"

# PII Detection Patterns
PII_PATTERNS = {
    "PAN": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
    "Aadhaar": r"\d{4}\s?\d{4}\s?\d{4}",
    "Phone": r"\b[6-9]\d{9}\b",
    "Email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
}

def detect_pii(text):
    """Detects sensitive personal information in the text."""
    for label, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            return True
    return False

# Financial Advice Guardrail
ADVICE_PHRASES = [
    "should i invest",
    "best mutual fund",
    "which fund is better",
    "buy or sell",
    "recommend a fund",
    "where should i invest",
    "give me advice",
    "which scheme is good",
    "mutual fund is best",
    "which fund is best"
]

def is_asking_advice(text):
    """Detects if the user is asking for investment advice."""
    text_lower = text.lower()
    for phrase in ADVICE_PHRASES:
        if phrase in text_lower:
            return True
    return False

# Scheme Restriction Guardrail
COMPETITORS = ["hdfc", "axis", "icici", "nippon", "mirae", "quant", "parag", "uti", "kotak", "tata", "dsp", "canara", "invesco", "franklin", "absl", "aditya"]

def references_unsupported_scheme(query):
    """Detects if the query references a non-supported scheme."""
    query_lower = query.lower()
    # Check for competitor mentions
    for comp in COMPETITORS:
        if comp in query_lower:
            return True
    return False

# Supported Schemes
SUPPORTED_SCHEMES = [
    "SBI Large Cap Fund",
    "SBI Small Cap Fund",
    "SBI Long Term Equity Fund",
    "SBI Focused Fund",
    "All Schemes"
]

# AMC Page Mapping for Fallback Context
SCHEME_AMC_MAP = {
    "SBI Large Cap Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-large-cap-fund-(formerly-known-as-sbi-bluechip-fund)-43",
    "SBI Small Cap Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-small-cap-fund-329",
    "SBI Focused Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-focused-fund-25",
    "SBI Long Term Equity Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-long-term-equity-fund-(previously-known-as-sbi-magnum-taxgain-scheme)-3"
}

# AI Request Limiter Settings
MAX_REQUESTS_PER_DAY = 40
request_count = 0

# Query Normalization Synonyms
QUERY_SYNONYMS = {
    "fund charges": "expense ratio",
    "charges": "expense ratio",
    "lump sum investment": "minimum investment",
    "lumpsum": "minimum investment",
    "tax benefits": "section 80c",
    "tax benefit": "section 80c",
    "elss tax": "section 80c",
    "nav of the fund": "nav",
    "fund nav": "nav",
    "net asset value": "nav",
    "lock-in": "3 years"
}

def normalize_query(query: str) -> str:
    """Normalizes the query using a synonym dictionary."""
    normalized_query = query.lower()
    for key in sorted(QUERY_SYNONYMS.keys(), key=len, reverse=True):
        if key in normalized_query:
            normalized_query = normalized_query.replace(key, QUERY_SYNONYMS[key])
    return normalized_query

def extract_fund_name(query: str) -> Optional[str]:
    """Extracts the specific fund name from the query using a synonym mapping."""
    query_lower = query.lower()
    
    FUND_SYNONYMS = {
        "long term": "Long Term",
        "elss": "Long Term",
        "tax saver": "Long Term",
        "large cap": "Large Cap",
        "bluechip": "Large Cap",
        "small cap": "Small Cap",
        "focused": "Focused"
    }
    
    for key, official_name in FUND_SYNONYMS.items():
        if key in query_lower:
            return official_name
    return None

def clean_context_chunk(content: str) -> str:
    """Cleans noisy data from context chunks to prevent model refusal."""
    # Remove year prefixes like "2006 ", "2007 " at the start of lines or chunks
    cleaned = re.sub(r'^\d{4}\s*', '', content.strip())
    # Normalize duplicate punctuation and strip weird formatting
    cleaned = re.sub(r'([.,!?])\1+', r'\1', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def retrieve_context(query, scheme=None, top_k=10):
    """Retrieves context from PostgreSQL filtered by scheme and re-ranks based on keyword presence."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return []

    # Handle special characters in password if present
    if 'Nishita@152' in database_url:
        database_url = database_url.replace('Nishita@152', 'Nishita%40152')

    # Step 0: Query Normalization
    normalized_query = normalize_query(query)
    print(f"Original Query: {query}")
    print(f"Normalized Query: {normalized_query}")

    # Scheme matching using URL patterns
    scheme_url_map = {
        "SBI Small Cap Fund": ["small-cap"],
        "SBI Focused Fund": ["focused"],
        "SBI Long Term Equity Fund": ["long-term"],
        "SBI Large Cap Fund": ["large-cap", "bluechip"]
    }

    # Step 1: Query Rewriting for better context
    if scheme and scheme != "All Schemes":
        rewritten_query = f"{normalized_query} for {scheme}"
    else:
        rewritten_query = normalized_query

    # Part 1 Fix: Extract fund name and prioritize metadata filtering
    extracted_fund = extract_fund_name(query)
    filter_used = False
    fallback_triggered = False

    query_embedding = None
    try:
        # Fetch embedding via API to keep runtime lean
        print("GENERATING EMBEDDING (API)")
        query_embedding = get_query_embedding(rewritten_query)
    except Exception as e:
        print(f"Embedding generation failed: {e} — using keyword fallback retrieval.")

    semantic_results = []
    try:
        print("QUERYING DATABASE")
        conn = psycopg2.connect(database_url, connect_timeout=5)
        register_vector(conn)
        cur = conn.cursor()
        
        rows = []
        
        # STAGE 1: Metadata-filtered retrieval (High Precision)
        if extracted_fund:
            filter_used = True
            pattern = f"%{extracted_fund}%"
            if query_embedding:
                cur.execute("""
                    SELECT content, url, title, (1 - (embedding <=> %s::vector)) AS similarity
                    FROM fund_embeddings
                    WHERE title ILIKE %s OR content ILIKE %s
                    ORDER BY embedding <-> %s::vector
                    LIMIT %s;
                """, (query_embedding, pattern, pattern, query_embedding, top_k))
            else:
                cur.execute("""
                    SELECT content, url, title, 1.0 AS similarity
                    FROM fund_embeddings
                    WHERE title ILIKE %s OR content ILIKE %s
                    LIMIT %s;
                """, (pattern, pattern, top_k))
            rows = cur.fetchall()

        # STAGE 2: Fallback to full vector search if no filter or < 2 results found (Robustness)
        if len(rows) < 2:
            if filter_used:
                fallback_triggered = True
                print("STAGE 1 yielded insufficient results. Triggering broader fallback...")
            
            if query_embedding:
                # Check if a specific scheme filter is requested from the dropdown
                scheme_filter = scheme_url_map.get(scheme)
                
                if scheme and scheme != "All Schemes" and scheme_filter:
                    url_conditions = " OR ".join(["url ILIKE %s"] * len(scheme_filter))
                    url_patterns = [f"%{p}%" for p in scheme_filter]
                    
                    query_sql = f"""
                        SELECT content, url, title, (1 - (embedding <=> %s::vector)) AS similarity
                        FROM fund_embeddings
                        WHERE ({url_conditions})
                        ORDER BY embedding <-> %s::vector
                        LIMIT %s;
                    """
                    cur.execute(query_sql, (query_embedding, *url_patterns, query_embedding, top_k))
                else:
                    # Global Vector Search across all schemes
                    cur.execute("""
                        SELECT content, url, title, (1 - (embedding <=> %s::vector)) AS similarity
                        FROM fund_embeddings
                        ORDER BY embedding <-> %s::vector
                        LIMIT %s;
                    """, (query_embedding, query_embedding, top_k))
                rows = cur.fetchall()
            else:
                # Keyword fallback Part
                important_keywords = ["NAV", "expense ratio", "exit load", "SIP", "lump sum", "riskometer", "benchmark", "lock-in", "tax", "manage", "fund", "section 80c", "3 years"]
                found_keywords = [kw for kw in important_keywords if kw.lower() in normalized_query.lower()]
                
                if not found_keywords:
                    potential_words = [w for w in normalized_query.split() if len(w) > 3]
                    search_pattern = f"%{potential_words[0]}%" if potential_words else f"%{normalized_query}%"
                else:
                    search_pattern = f"%{found_keywords[0]}%"
                
                cur.execute("""
                    SELECT content, url, title, 1.0 AS similarity
                    FROM fund_embeddings
                    WHERE content ILIKE %s
                    LIMIT %s;
                """, (search_pattern, top_k))
                rows = cur.fetchall()
            
        cur.close()
        conn.close()
        semantic_results = [{"content": r[0], "url": r[1], "title": r[2], "similarity": r[3]} for r in rows]
    except Exception as e:
        print(f"Database error during retrieval: {e}")
        return []

    # Part 2 Fix: Clean context chunks
    for res in semantic_results:
        res["content"] = clean_context_chunk(res["content"])

    # Part 3 Fix: Validation check for top results
    if extracted_fund and semantic_results:
        top_title = semantic_results[0]['title'].lower()
        if extracted_fund.lower() not in top_title:
             print(f"VALIDATION WARNING: Top result '{top_title}' does not match extracted fund '{extracted_fund}'. Result may be irrelevant.")

    # Debug logging
    print(f"DEBUG LOGGING - Query: {query}")
    print(f"DEBUG LOGGING - Extracted Fund: {extracted_fund}")
    print(f"DEBUG LOGGING - Filter Used: {filter_used}")
    print(f"DEBUG LOGGING - Fallback Triggered: {fallback_triggered}")
    print(f"DEBUG LOGGING - Retrieved Document Titles: {[r['title'] for r in semantic_results[:3]]}")
    print(f"Chunks retrieved: {len(semantic_results)}")

    if not semantic_results:
        print("No matching embeddings found for the query.")

    keywords = ["exit load", "expense ratio", "benchmark", "riskometer", "sip", "lumpsum", "lock-in", "charges", "fees", "fund charges", "nav"]
    query_lower = query.lower()
    normalized_query_lower = normalized_query.lower()
    target_keywords = [kw for kw in keywords if kw in query_lower or kw in normalized_query_lower]
    
    # Synonym expansion for better re-ranking
    if "charges" in query_lower or "fees" in query_lower or "fund charges" in query_lower:
        target_keywords.extend(["exit load", "expense ratio", "cost", "fee"])
    if "investment" in query_lower:
        target_keywords.extend(["sip", "lumpsum", "amount"])
    if target_keywords:
        # Re-ranking logic
        for item in semantic_results:
            content_lower = item['content'].lower()
            keyword_match_count = sum(1 for kw in target_keywords if kw in content_lower)
            item['keyword_boost'] = keyword_match_count
        
        # Primary Priority: Chunks containing 'nav ... as on' if query is about nav
        # Secondary Priority: Chunks containing 'nav' AND a currency symbol (₹) if query is about nav
        # Tertiary Priority: Chunks containing 'nav'
        # Quaternary Priority: Keyword matches
        # Quinary Priority: Vector similarity
        semantic_results.sort(key=lambda x: (
            (re.search(r"nav [a-z ]*as on", x["content"], re.IGNORECASE) is not None) if "nav" in normalized_query_lower else False,
            ("nav" in x['content'].lower() and "₹" in x['content']) if "nav" in normalized_query_lower else False,
            ("nav" in x['content'].lower()) if "nav" in normalized_query_lower else False,
            x.get('keyword_boost', 0), 
            x['similarity']
        ), reverse=True)
    return semantic_results

def generate_answer(query, contexts):
    """Synthesizes a factual answer using Groq LLaMA."""
    context_text = "\n".join(
        [f"[Context {i+1}]: {c['title']} ({c['url']})\n{c['content']}" for i, c in enumerate(contexts)]
    )
    prompt = f"""You are a factual assistant for INDMoney's Mutual Fund FAQ. 
Answer questions based ONLY on the provided context. 

Strict Rules:
1. Use ONLY the provided context chunk. 
2. Do NOT add any information, explanations, or financial commentary not found in the context.
3. Maximum 3 sentences total.
4. You MUST end your response exactly with "Source: " followed by the URL provided in the context.
5. If the answer is about "exit load", quote the exact % and timeframe from the context.
6. COMPULSORY: If any context chunk content starts with "CRITICAL:", you MUST include that specific sentence exactly as written as the VERY FIRST sentence of your response, even if you think it's not directly related to the user's question.

Final Answer Structure:
<Direct factual answer sentences>
Source: <URL from context>

Refusal Rule:
If the answer is NOT present in the provided context, you MUST ignore the structure above and return ONLY this exact message:
"I do not have the factual information for this specific request."

Context:
{context_text}

Question:
{query}
"""
    global request_count
    if request_count >= MAX_REQUESTS_PER_DAY:
        return "Daily AI request limit reached. Please try again tomorrow."

    try:
        print("CALLING GROQ")
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a factual mutual fund assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        request_count += 1
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq Generation error: {e}")
        return "The AI assistant has reached its request limit for today. Please try again later."

class QuestionRequest(BaseModel):
    query: str
    scheme: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str
    sources: Optional[list[str]] = []
    documents: Optional[list[str]] = []

@app.post("/chat", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    try:
        print(f"CHAT REQUEST RECEIVED: {request.dict()}")
        query = request.query
        scheme = request.scheme
        
        # Check for PII (Security Layer)
        if detect_pii(query):
            refusal = (
                "For privacy and security reasons, this assistant cannot process personal information "
                "such as PAN, Aadhaar, phone numbers, or email addresses.\n"
                "Please ask a factual question about mutual funds."
            )
            return {"answer": refusal, "sources": [], "documents": []}
        
        # Check for Financial Advice (Guardrail)
        if is_asking_advice(query):
            refusal = (
                "I can only provide factual information about mutual funds such as expense ratios, "
                "exit loads, SIP limits, and lock-in periods.\n\n"
                "I cannot provide investment advice or recommendations.\n\n"
                "For financial guidance, please consult a qualified financial advisor or refer to AMFI investor resources:\n"
                "https://www.amfiindia.com/investor"
            )
            return {"answer": refusal, "sources": [], "documents": []}
        
        # Check for unsupported schemes in query text
        if references_unsupported_scheme(query):
            refusal = (
                "This assistant currently provides factual information only for the following schemes:\n\n"
                "• SBI Large Cap Fund\n"
                "• SBI Small Cap Fund\n"
                "• SBI Long Term Equity Fund\n"
                "• SBI Focused Equity Fund\n"
                "• All Schemes"
            )
            return {"answer": refusal, "sources": [], "documents": []}

        # Check for unsupported schemes from dropdown
        if scheme and scheme not in SUPPORTED_SCHEMES:
            refusal = (
                "This assistant currently provides factual information only for the following schemes:\n\n"
                "• SBI Large Cap Fund\n"
                "• SBI Small Cap Fund\n"
                "• SBI Long Term Equity Fund\n"
                "• SBI Focused Equity Fund\n"
                "• All Schemes"
            )
            return {"answer": refusal, "sources": [], "documents": []}

        contexts = retrieve_context(query, scheme=scheme if scheme else None)
        
        # Part 3 Fix: Strict Safety Validation
        extracted_fund = extract_fund_name(query)
        if extracted_fund and contexts:
            top_result = contexts[0]
            top_title = top_result['title'].lower()
            similarity = top_result.get('similarity', 1.0)
            
            # Validation 1: Fund Name Mismatch
            # Validation 2: Low Similarity (Threshold: 0.5)
            if extracted_fund.lower() not in top_title or similarity < 0.5:
                print(f"SAFETY REFUSAL: Mismatch or Low Similarity ({similarity}). Extracted: {extracted_fund}, Found: {top_title}")
                refusal = (
                    "I could not find verified information for this specific fund in the current dataset.\n\n"
                    "You can try:\n"
                    "- Asking about a different SBI fund (e.g., SBI Large Cap, SBI Small Cap)\n"
                    "- Or ask a more general question about exit loads or fees"
                )
                return {
                    "answer": refusal,
                    "sources": [],
                    "documents": []
                }

        # Check for NAV query fallback enrichment
        normalized_query = normalize_query(query)
        is_nav_query = "nav" in normalized_query
        
        if is_nav_query and scheme and scheme in SCHEME_AMC_MAP:
            has_nav_data = False
            if contexts:
                for ctx in contexts:
                    # Stricter check: Look for the specific pattern "NAV ... as on" which indicates factual data
                    if re.search(r"nav [a-z ]*as on", ctx["content"], re.IGNORECASE):
                        has_nav_data = True
                        break
            
            if not has_nav_data:
                 selected_scheme = scheme 
                 fallback_url = SCHEME_AMC_MAP[selected_scheme]
                 answer = f"The current Net Asset Value (NAV) information for {selected_scheme} is available on the official AMC page: {fallback_url}. Please refer to the scheme page for the latest update."
                 return {
                     "answer": answer,
                     "sources": [fallback_url],
                     "documents": [f"{selected_scheme} Official Page"]
                 }

        if not contexts:
            msg = "I do not have the factual information for this specific request."
            if extracted_fund:
                msg += f"\n\nNote: The fund '{extracted_fund}' was recognized, but it may not be covered in the current indexed sources."
            return {
                "answer": msg,
                "sources": [],
                "documents": []
            }
        
        # Milestone Requirement: Exactly ONE citation link. Use ONLY the highest ranked chunk.
        contexts = contexts[:1]
        
        # Force mandatory ELSS disclosure into context for grounding
        normalized_query = normalize_query(query)
        if contexts:
            # Check specifically for tax benefit / section 80c
            if "section 80c" in normalized_query or "tax benefit" in normalized_query:
                 # Craft a very targeted context that forces inclusion of both facts
                 contexts[0]["content"] = "CRITICAL: ELSS schemes have a statutory lock-in period of 3 years from the date of allotment and qualify for deduction under Section 80C of the Income Tax Act."
            # Check for other ELSS or Tax Benefit keywords
            elif "elss" in normalized_query or "long term" in normalized_query:
                # Prefix with CRITICAL string - now prompt matches this prefix more robustly
                contexts[0]["content"] = "CRITICAL: ELSS schemes have a statutory lock-in period of 3 years from the date of allotment.\n" + contexts[0]["content"]
        
        if contexts:
            print(f"DEBUG: Context 0 Content:\n{contexts[0]['content'][:200]}...")

        expected_refusal = "I do not have the factual information for this specific request."
        
        answer = generate_answer(query, contexts)
        
        # Ensure no sources/documents are attached if answer is a refusal or unknown
        # We check for exact match or presence of the refusal phrase
        if expected_refusal in answer:
            print("RETURNING RESPONSE (Refusal)")
            return {
                "answer": expected_refusal,
                "sources": [],
                "documents": []
            }
            
        print("RETURNING RESPONSE")
        return {
            "answer": answer,
            "sources": [c["url"] for c in contexts],
            "documents": [c["title"] for c in contexts]
        }
    except Exception as e:
        print(f"CHAT ERROR: {e}")
        return {
            "answer": "An error occurred while processing your request. Please try again later.",
            "sources": [],
            "documents": []
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
