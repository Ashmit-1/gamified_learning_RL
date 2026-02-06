import requests
import json
import time
import os

URL_START = "http://localhost:8000/start-quiz"
URL_SUBMIT = "http://localhost:8000/submit-answer"
TOPIC = "Uniqueness Test"
POOL_PATH = os.path.join("pools", "uniqueness_test.json")

def cleanup():
    if os.path.exists(POOL_PATH):
        os.remove(POOL_PATH)

def get_pool_count():
    if not os.path.exists(POOL_PATH):
        return None
    with open(POOL_PATH, 'r') as f:
        pool = json.load(f)
        total = sum(len(q_list) for q_list in pool.values())
        return total

print("--- STEP 1: CLEANUP ---")
cleanup()

print("\n--- STEP 2: START QUIZ (Generates Pool) ---")
res = requests.post(URL_START, json={"topic": TOPIC}, timeout=120)
if res.status_code != 200:
    print(f"Failed to start quiz: {res.text}")
    exit(1)

data = res.json()
session_id = data['session_id']
initial_count = get_pool_count()
print(f"Initial Pool Size (on disk): {initial_count}")
print(f"First Question: {data['question']['text'][:50]}...")

print("\n--- STEP 3: SUBMIT 3 ANSWERS ---")
for i in range(3):
    res = requests.post(URL_SUBMIT, json={
        "session_id": session_id,
        "answer": "dummy",
        "question_id": "dummy"
    })
    count = get_pool_count()
    print(f"Answer {i+1} submitted. Pool Size on disk: {count}")

print("\n--- STEP 4: VERIFY ---")
if initial_count is not None and count < initial_count:
    print(f"SUCCESS: Pool size decreased from {initial_count} to {count}")
    print("This confirms questions are being deleted from the persistent pool upon selection.")
else:
    print(f"FAILURE: Pool size did not decrease correctly. Current: {count}")
