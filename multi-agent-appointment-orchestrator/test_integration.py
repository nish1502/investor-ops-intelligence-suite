import requests
import json

def test_book_call():
    url = "http://localhost:8000/book_call"
    payload = {
        "objective": "Test objective for automatic validation",
        "date": "2026-06-01",
        "urgency": "Priority (1-2 days)",
        "theme": "App Performance",
        "marketContext": "Testing automatic integration"
    }
    
    print(f"🚀 Testing POST {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200 and data.get("status") == "success":
            print("✅ Automatic Integration Test PASSED")
        else:
            print("❌ Automatic Integration Test FAILED")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_book_call()
