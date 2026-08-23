import requests
import json
import time

def test_endpoints():
    base_url = "http://127.0.0.1:8000"
    
    print("Testing /health...")
    r1 = requests.get(f"{base_url}/health")
    print(json.dumps(r1.json(), indent=2))
    
    print("\nTesting /memory-audit (This will load the models, so it may take a few seconds)...")
    t0 = time.time()
    r2 = requests.get(f"{base_url}/memory-audit")
    print(f"Time taken: {time.time()-t0:.2f}s")
    print(json.dumps(r2.json(), indent=2))
    
    print("\nTesting /query...")
    r3 = requests.post(f"{base_url}/query", json={"query": "heart rate"})
    print(json.dumps(r3.json(), indent=2))
    
if __name__ == "__main__":
    test_endpoints()
