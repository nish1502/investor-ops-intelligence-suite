import requests
import json

URL = "http://localhost:10000/chat"

def test_query(query):
    print(f"\nTESTING: {query}")
    try:
        response = requests.post(URL, json={"query": query}, timeout=10)
        data = response.json()
        print(f"ANSWER: {data['answer']}")
    except Exception as e:
        print(f"ERROR: {e}")

# Note: Ensure the API server is running on port 8000
# If not, this test will fail.
# I'll try to run the server in the background for a moment.

queries = [
    "SBI Long Term Equity exit load",   # Should PASS
    "SBI Infrastructure Fund exit load", # Should be blocked or global (no fund extracted)
    "HDFC Large Cap exit load"           # Should be blocked by guardrail
]

if __name__ == "__main__":
    for q in queries:
        test_query(q)
