import httpx
import uuid
from datetime import datetime, timedelta, timezone
import psycopg2
import sys

def main():
    API_URL = "http://localhost:8000"
    
    admin_email = f"live_admin_{uuid.uuid4().hex[:6]}@test.com"
    print(f"Registering {admin_email}...")
    
    res = httpx.post(f"{API_URL}/auth/register", json={
        "username": f"LiveAdmin_{uuid.uuid4().hex[:4]}",
        "email": admin_email,
        "password": "password123"
    })
    res.raise_for_status()
    
    # Make admin
    print("Upgrading user to admin role...")
    conn = psycopg2.connect("postgresql://promptrank:promptrank@db:5432/promptrank")
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = 'admin' WHERE email = %s", (admin_email,))
    conn.commit()
    cur.close()
    conn.close()

    # Login
    print("Logging in...")
    login_res = httpx.post(f"{API_URL}/auth/login", json={"email": admin_email, "password": "password123"})
    login_res.raise_for_status()
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Contest
    print("Creating contest...")
    now = datetime.now(timezone.utc)
    contest_res = httpx.post(f"{API_URL}/admin/contest", json={
        "name": f"Live Browser Test Contest",
        "start_time": (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S"),
        "end_time": (now + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S"),
        "submission_limit": 10,
        "allowed_model": "gpt-4o-mini",
        "temperature": 0.0,
        "seed_base": 42
    }, headers=headers)
    contest_res.raise_for_status()
    contest_id = contest_res.json()["id"]

    # Create Problem
    print("Creating problem...")
    prob_res = httpx.post(f"{API_URL}/admin/problem", json={
        "title": "Extract Animal Facts",
        "statement": "You are a zoologist. Extract the animal name, its habitat, and diet from the given text.",
        "schema_json": {
            "animal": "string",
            "habitat": "string",
            "diet": "string"
        },
        "time_limit_sec": 30,
        "scoring_config_json": {},
        "contest_id": contest_id
    }, headers=headers)
    prob_res.raise_for_status()
    prob_id = prob_res.json()["id"]

    # Create Testcase
    print("Creating testcase...")
    tc_res = httpx.post(f"{API_URL}/admin/testcases", json={
        "problem_id": prob_id,
        "input_blob": "The majestic Bengal tiger lives in the dense forests of India. It feeds primarily on large ungulates like deer and wild boar.",
        "expected_output_blob": '{"animal": "Bengal tiger", "habitat": "dense forests of India", "diet": "deer and wild boar"}',
        "is_adversarial": False
    }, headers=headers)
    tc_res.raise_for_status()

    # Create a Player account for the browser to log into
    player_email = f"live_player_{uuid.uuid4().hex[:6]}@test.com"
    httpx.post(f"{API_URL}/auth/register", json={
        "username": f"LivePlayer_{uuid.uuid4().hex[:4]}",
        "email": player_email,
        "password": "password123"
    })

    print(f"\nSUCCESS!")
    print(f"Contest ID: {contest_id}")
    print(f"Player Email: {player_email}")
    print(f"Player Password: password123")
    print(f"Contest URL: http://localhost:3000/contests/{contest_id}")

if __name__ == "__main__":
    main()
