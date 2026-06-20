"""
RailChart — Missing Trains Bulk Fetcher Utility

This script reads from 'backend/data/missing_trains.log', fetches the timetable 
details for each missing train using the modern 'google-genai' SDK with Google Search grounding,
and appends them to the static dataset 'backend/data/trains.json'.

Usage:
  1. Ensure GEMINI_API_KEY is set in your environment.
  2. Run the script:
     .venv\Scripts\python fetch_missing_trains.py
"""

import os
import sys
import json
from pathlib import Path
from google import genai
from google.genai import types

# Define paths
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "backend" / "data"
DATA_FILE = DATA_DIR / "trains.json"
LOG_FILE = DATA_DIR / "missing_trains.log"

def fetch_train_info(client: genai.Client, train_number: str) -> dict | None:
    train_number = train_number.strip()
    print(f"Fetching timetable for train {train_number}...")
    
    prompt = (
        f"Search the web for the official timetable details of Indian Railways train number '{train_number}'. "
        "Find its name, origin station code, origin station name, and its scheduled departure time from the origin station. "
        "Provide the output strictly as a single JSON object in the following format (no markdown code blocks, just raw JSON text): "
        "{\n"
        '  "train_number": "...",\n'
        '  "train_name": "...",\n'
        '  "origin_station_code": "...",\n'
        '  "origin_station_name": "...",\n'
        '  "departure_time": "HH:MM"\n'
        "}\n"
        "Ensure: \n"
        "- departure_time is in 24-hour HH:MM format.\n"
        "- train_name is in UPPERCASE.\n"
        "- origin_station_code is in UPPERCASE (e.g. MAS, NDLS).\n"
        "- origin_station_name is the proper name of the station.\n"
    )

    try:
        google_search_tool = types.Tool(google_search=types.GoogleSearch())
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                temperature=0.1
            )
        )
        response_text = response.text.strip()
        if not response_text:
            return None

        # Clean markdown wrappers if returned
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        data = json.loads(response_text)
        required = ["train_number", "train_name", "origin_station_code", "origin_station_name", "departure_time"]
        if not all(k in data for k in required):
            print(f"Skipping: Response missing required fields for train {train_number}")
            return None

        # Normalize format
        return {
            "train_number": str(data["train_number"]).strip(),
            "train_name": str(data["train_name"]).strip().upper(),
            "origin_station_code": str(data["origin_station_code"]).strip().upper(),
            "origin_station_name": str(data["origin_station_name"]).strip(),
            "departure_time": str(data["departure_time"]).strip()
        }
    except Exception as e:
        print(f"Failed to fetch train {train_number}: {e}")
        return None

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    if not LOG_FILE.exists():
        print(f"No missing trains log file found at {LOG_FILE}. Nothing to do.")
        return

    # Read missing trains
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        missing_trains = [line.strip() for line in f if line.strip()]

    if not missing_trains:
        print("No missing trains in log file.")
        return

    print(f"Found {len(missing_trains)} missing train(s) to fetch: {missing_trains}")
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    
    # Load current trains database
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            trains_db = json.load(f)
    else:
        trains_db = []

    # Map for easy updates/duplication check
    train_map = {t["train_number"]: t for t in trains_db}
    
    success_trains = []
    failed_trains = []

    for train_number in missing_trains:
        train_data = fetch_train_info(client, train_number)
        if train_data:
            train_map[train_data["train_number"]] = train_data
            success_trains.append(train_number)
            print(f"Successfully resolved and cached: {train_data['train_number']} - {train_data['train_name']}")
        else:
            failed_trains.append(train_number)

    # Save updated database
    if success_trains:
        updated_db = [train_map[k] for k in sorted(train_map.keys())]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_db, f, indent=2)
        print(f"Saved {len(success_trains)} new train(s) to {DATA_FILE}.")

    # Rewrite log file with only failed ones
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for train_number in failed_trains:
            f.write(f"{train_number}\n")

    print("\n--- Summary ---")
    print(f"Successfully processed: {len(success_trains)}")
    print(f"Failed / Retrying later: {len(failed_trains)}")

if __name__ == "__main__":
    main()
