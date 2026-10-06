# explore_feed.py
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict

load_dotenv()
API_KEY = os.environ["TRANSLINK_API_KEY"]
URL = "https://gtfsapi.translink.ca/v3/gtfsrealtime"

# TransLink's gateway returns 403 for the default python-requests User-Agent
HEADERS = {"User-Agent": "Mozilla/5.0"}

resp = requests.get(URL, params={"apikey": API_KEY}, headers=HEADERS, timeout=10)
# Don't print resp.url here: it contains the API key
if resp.status_code != 200:
    raise SystemExit(f"Request failed: HTTP {resp.status_code}\n{resp.text[:500]}")

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(resp.content)

print(f"Payload size: {len(resp.content) / 1024:.1f} KB")

ts_utc = datetime.fromtimestamp(feed.header.timestamp, tz=timezone.utc)
ts_van = ts_utc.astimezone(ZoneInfo("America/Vancouver"))
print(f"Feed timestamp (UTC):       {ts_utc:%Y-%m-%d %H:%M:%S %Z}")
print(f"Feed timestamp (Vancouver): {ts_van:%Y-%m-%d %H:%M:%S %Z}")

print(f"Entities: {len(feed.entity)}")

if feed.entity:
    print(MessageToDict(feed.entity[0]))
else:
    print("Feed has no entities")