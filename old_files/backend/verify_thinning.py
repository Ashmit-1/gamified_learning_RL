import asyncio
import httpx
import json
import os

URL = "http://localhost:8000/start-quiz"
TOPIC = "Python"
POOL_PATH = os.path.join("pools", "python.json")

async def get_pool_count():
    if not os.path.exists(POOL_PATH):
        return 0
    with open(POOL_PATH, 'r') as f:
        pool = json.load(f)
        return sum(len(q_list) for q_list in pool.values())

async def main():
    initial_count = await get_pool_count()
    print(f"Pool size before start: {initial_count}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"Sending request for topic: {TOPIC}...")
        try:
            res = await client.post(URL, json={"topic": TOPIC})
            print(f"Response Status: {res.status_code}")
            if res.status_code == 200:
                print("Success! Checking pool size...")
                after_count = await get_pool_count()
                print(f"Pool size after start: {after_count}")
                if after_count < initial_count:
                    print("VERIFIED: Question was successfully thinned from pool.")
                else:
                    print("FAILED: Pool size did not change.")
            else:
                print(f"Error: {res.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
