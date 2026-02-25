import requests

username = input("enter username: ").strip()
print(username)

try:
    response = requests.get(
        f"https://api.github.com/users/{username}",
        timeout=10,
        headers={"Accept": "application/vnd.github+json"},
    )
    response.raise_for_status()
except requests.exceptions.Timeout:
    print("error: request timed out. check your internet connection and try again.")
except requests.exceptions.ConnectionError:
    print("error: failed to connect. check your internet connection and try again.")
except requests.exceptions.HTTPError:
    status = response.status_code if "response" in locals() else "unknown"
    if status == 404:
        print("error: user not found.")
    elif status == 403:
        print("error: access forbidden or rate limited by GitHub.")
    else:
        print(f"error: HTTP {status}.")
except requests.exceptions.RequestException as exc:
    print(f"error: request failed: {exc}")
else:
    data = response.json()
    for i in data:
        print(i, " : ", data[i])