import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("HF_TOKEN")
print("Token exists:", bool(token))

url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "x-wait-for-model": "true"
}

def get_embedding(text):
    payload = {"inputs": text}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res
    except Exception as e:
        print("Error:", e)
        return None

res_single = get_embedding("Hello world")
print("Single type:", type(res_single))
if isinstance(res_single, list):
    print("Single length:", len(res_single))
    print("Single first few elements:", res_single[:5])

res_multi = get_embedding(["Hello world", "Goodbye world"])
print("Multi type:", type(res_multi))
if isinstance(res_multi, list):
    print("Multi length:", len(res_multi))
    if len(res_multi) > 0:
        print("First element type:", type(res_multi[0]))
        print("First element length:", len(res_multi[0]))
        print("First element first few:", res_multi[0][:5])
