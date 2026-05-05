import sys
import os
from dotenv import load_dotenv

# Add Phase_8 to path
sys.path.insert(0, os.path.join(os.getcwd(), "mf-rag-faq-indmoney", "Phase_8"))

import api

load_dotenv("mf-rag-faq-indmoney/.env")

queries = [
    "SBI ELSS exit load",
    "SBI tax saver exit load",
    "SBI long term equity exit load",
    "SBI focused fund exit load"
]

print("--- RAG Retrieval & Cleaning Debug ---")
for q in queries:
    print(f"\nQUERY: {q}")
    contexts = api.retrieve_context(q)
    print(f"Number of contexts found: {len(contexts)}")
    if contexts:
        for i, c in enumerate(contexts[:3]):
            print(f"  [{i+1}] Title: {c['title']}")
            # Check for year prefix in content (should be removed)
            if any(year in c['content'][:10] for year in ["2006", "2007", "2024"]):
                 print(f"      [WARNING] Year prefix still present: {c['content'][:20]}")
            else:
                 print(f"      [OK] Content cleaned: {c['content'][:150]}...")
    else:
        print("  NO CONTEXTS FOUND")
