import os
import sys
from dotenv import load_dotenv
import requests

# Ensure we're running from the project root so .env is found
project_root = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(project_root, ".env")

print(f"Looking for .env at: {env_path}")
print(f".env exists? {os.path.exists(env_path)}")

load_dotenv(env_path)

url = os.getenv("GITLAB_URL")
if url and url.count('/') > 2:
    parts = url.split('/')
    url = f"{parts[0]}//{parts[2]}"
token = os.getenv("GITLAB_PAT")
project_id = os.getenv("GITLAB_PROJECT_ID")

print("-" * 40)
print(f"GITLAB_URL: {url}")
print(f"GITLAB_PAT: {'[SET]' if token else '[MISSING]'}")
print(f"GITLAB_PROJECT_ID: {project_id}")
print("-" * 40)

if not all([url, token, project_id]):
    print("ERROR: Missing some credentials in .env file!")
    sys.exit(1)

print("Testing direct connection to GitLab API...")
base_url = f"{url}/api/v4/projects/{project_id}"
headers = {"PRIVATE-TOKEN": token}
try:
    r = requests.get(base_url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(f"SUCCESS: Connected to GitLab project!")
        print(f"Project Name: {data.get('name')}")
        print(f"Project Path: {data.get('path_with_namespace')}")
    else:
        print(f"FAILED to connect. Status: {r.status_code}")
        print(f"Response: {r.text}")
except Exception as e:
    print(f"ERROR connecting to GitLab: {e}")
