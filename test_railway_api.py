import requests
import json
import time

BASE_URL = "https://appreviewinsightanalyzer-production.up.railway.app"

def test_config_endpoint():
    """Test if the backend is live and configuration is readable."""
    print("Testing /api/config endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/config", timeout=10)
        
        if response.status_code == 200:
            print("[SUCCESS] API is UP and Responding!")
            config_data = response.json()
            print("Configuration Data:", json.dumps(config_data, indent=2))
            
            if config_data.get("groq_api_key_set"):
                print("[SECURE] GROQ API KEY is configured securely.")
            else:
                print("[WARNING] GROQ API KEY is NOT set on Railway.")
                
            return True
        else:
            print(f"[FAILED] API responded with status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[FAILED] CONNECTION FAILED: The Railway instance is waking up, still building, or asleep.")
        return False
    except Exception as e:
        print(f"[ERROR] UNEXPECTED ERROR: {e}")
        return False

def test_fetch_trigger():
    """Test if we can trigger a very basic fetch API request (this doesn't require API keys yet)."""
    print("\nTesting /api/fetch endpoint... (This might take 10-30 seconds)")
    try:
        response = requests.post(f"{BASE_URL}/api/fetch", timeout=45)
        
        if response.status_code == 200:
            print("[SUCCESS] App Store and Google Play reviews fetched successfully!")
            data = response.json()
            print(f"Stats: Fetched {data.get('count')} total reviews "
                  f"({data.get('apple_count')} Apple, {data.get('google_count')} Google)")
        else:
            print(f"[FAILED] Fetch API responded with status code {response.status_code}")
            try:
                print("Error Details:", response.json())
            except:
                print("Response text:", response.text)
                
    except Exception as e:
        print(f"[ERROR] Fetch request failed: {e}")

if __name__ == "__main__":
    print(f"Ping targeting: {BASE_URL}\n")
    
    is_up = test_config_endpoint()
    
    # We can fetch reviews publicly without keys, so we try anyway to see backend pipeline performance
    if is_up:
        print("Waiting a second before deep test...")
        time.sleep(1)
        test_fetch_trigger()
    
    print("\nTest procedure completed.")
