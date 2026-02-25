from flask import Flask, render_template, request
import requests

app = Flask(__name__)
TOP_REPOS_LIMIT = 5
PER_PAGE = 100


def fetch_all_repositories(username):
    repos = []
    page = 1

    while True:
        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            timeout=10,
            params={"per_page": PER_PAGE, "page": page, "sort": "updated"},
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()

        page_items = response.json()
        if not page_items:
            break

        repos.extend(page_items)
        if len(page_items) < PER_PAGE:
            break

        page += 1

    return repos


@app.route("/", methods=["GET", "POST"])
def home():
    data = None
    repos = []
    repos_error = None
    orgs = []
    orgs_error = None
    error = None
    username = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            error = "Please enter a GitHub username."
        else:
            response = None
            try:
                response = requests.get(
                    f"https://api.github.com/users/{username}",
                    timeout=10,
                    headers={"Accept": "application/vnd.github+json"},
                )
                response.raise_for_status()
                data = response.json()

                try:
                    repos = fetch_all_repositories(username)

                    repos.sort(
                        key=lambda repo: (
                            repo.get("stargazers_count", 0),
                            repo.get("forks_count", 0),
                            repo.get("updated_at", ""),
                        ),
                        reverse=True,
                    )
                except requests.exceptions.RequestException as exc:
                    repos_error = f"Could not fetch repositories: {exc}"

                try:
                    orgs_response = requests.get(
                        f"https://api.github.com/users/{username}/orgs",
                        timeout=10,
                        headers={"Accept": "application/vnd.github+json"},
                    )
                    orgs_response.raise_for_status()
                    orgs = orgs_response.json()
                except requests.exceptions.RequestException as exc:
                    orgs_error = f"Could not fetch organizations: {exc}"
            except requests.exceptions.Timeout:
                error = "Request timed out. Please check your internet connection and try again."
            except requests.exceptions.ConnectionError:
                error = "Could not connect to the internet. Please try again."
            except requests.exceptions.HTTPError:
                status = response.status_code if response is not None else "unknown"
                if status == 404:
                    error = "User not found."
                elif status == 403:
                    error = "Access is restricted or rate limit exceeded."
                else:
                    error = f"HTTP error: {status}"
            except requests.exceptions.RequestException as exc:
                error = f"Request failed: {exc}"

    return render_template(
        "index.html",
        data=data,
        repos=repos,
        repos_error=repos_error,
        orgs=orgs,
        orgs_error=orgs_error,
        error=error,
        username=username,
        top_repos_limit=TOP_REPOS_LIMIT,
    )


if __name__ == "__main__":
    app.run(debug=True)
