import requests, pathlib

url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
db_path = pathlib.Path("./langchain_agents/sql/Chinook.db")

if not db_path.exists():
    print(f"Downloading file from {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        db_path.write_bytes(response.content)
        print(f"File downloaded and saved as {db_path}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")
