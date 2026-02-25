from flask import Flask, render_template, request
import requests

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    data = None
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

    return render_template("index.html", data=data, error=error, username=username)


if __name__ == "__main__":
    app.run(debug=True)
