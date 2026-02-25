from io import BytesIO
from flask import Flask, render_template, request, send_file
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


def fetch_user_orgs(username):
    response = requests.get(
        f"https://api.github.com/users/{username}/orgs",
        timeout=10,
        headers={"Accept": "application/vnd.github+json"},
    )
    response.raise_for_status()
    return response.json()


def fetch_user_bundle(username):
    data = None
    repos = []
    repos_error = None
    orgs = []
    orgs_error = None
    error = None
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
            orgs = fetch_user_orgs(username)
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

    return data, repos, repos_error, orgs, orgs_error, error


def sanitize_pdf_text(value):
    text = str(value or "N/A")
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", "replace").decode("latin-1")


def build_simple_pdf(lines):
    page_width = 612
    page_height = 792
    left = 40
    top = 760
    line_height = 14
    max_lines = 50
    font_size = 11

    chunks = []
    for i in range(0, len(lines), max_lines):
        chunks.append(lines[i : i + max_lines])
    if not chunks:
        chunks = [[]]

    objects = {}
    font_obj_num = 3
    objects[font_obj_num] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    page_refs = []
    next_obj_num = 4

    for chunk in chunks:
        stream_lines = [
            "BT",
            f"/F1 {font_size} Tf",
            f"{left} {top} Td",
            f"{line_height} TL",
        ]
        first = True
        for line in chunk:
            safe = sanitize_pdf_text(line)
            if first:
                stream_lines.append(f"({safe}) Tj")
                first = False
            else:
                stream_lines.append("T*")
                stream_lines.append(f"({safe}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("latin-1")

        content_obj_num = next_obj_num
        page_obj_num = next_obj_num + 1
        next_obj_num += 2

        objects[content_obj_num] = (
            b"<< /Length " + str(len(stream)).encode("latin-1") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        objects[page_obj_num] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> /Contents {content_obj_num} 0 R >>"
        ).encode("latin-1")
        page_refs.append(page_obj_num)

    kids = " ".join(f"{ref} 0 R" for ref in page_refs)
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[2] = (
        b"<< /Type /Pages /Kids ["
        + kids.encode("latin-1")
        + b"] /Count "
        + str(len(page_refs)).encode("latin-1")
        + b" >>"
    )

    buffer = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    max_obj_num = max(objects.keys())
    offsets = {0: 0}

    for idx in range(1, max_obj_num + 1):
        obj = objects[idx]
        offsets[idx] = len(buffer)
        buffer.extend(f"{idx} 0 obj\n".encode("latin-1"))
        buffer.extend(obj)
        buffer.extend(b"\nendobj\n")

    xref_start = len(buffer)
    buffer.extend(f"xref\n0 {max_obj_num + 1}\n".encode("latin-1"))
    buffer.extend(b"0000000000 65535 f \n")
    for idx in range(1, max_obj_num + 1):
        off = offsets[idx]
        buffer.extend(f"{off:010d} 00000 n \n".encode("latin-1"))

    buffer.extend(
        (
            f"trailer\n<< /Size {max_obj_num + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("latin-1")
    )
    return bytes(buffer)


def build_report_lines(username, data, repos, orgs):
    lines = [
        f"GitHub Profile Report - {username}",
        "",
        "Profile",
        f"Name: {data.get('name') or 'N/A'}",
        f"Username: {data.get('login') or 'N/A'}",
        f"Profile URL: {data.get('html_url') or 'N/A'}",
        f"Bio: {data.get('bio') or 'N/A'}",
        f"Location: {data.get('location') or 'N/A'}",
        f"Company: {data.get('company') or 'N/A'}",
        f"Blog/Website: {data.get('blog') or 'N/A'}",
        f"Public Repos: {data.get('public_repos')}",
        f"Followers: {data.get('followers')}",
        f"Following: {data.get('following')}",
        "",
        f"Repositories ({len(repos)})",
    ]

    if repos:
        for index, repo in enumerate(repos, start=1):
            lines.extend(
                [
                    f"{index}. {repo.get('name')}",
                    f"   Description: {repo.get('description') or 'N/A'}",
                    f"   Language: {repo.get('language') or 'N/A'}",
                    f"   Stars: {repo.get('stargazers_count', 0)} | Forks: {repo.get('forks_count', 0)} | Open Issues: {repo.get('open_issues_count', 0)}",
                    f"   URL: {repo.get('html_url') or 'N/A'}",
                ]
            )
    else:
        lines.append("No repositories found.")

    lines.extend(["", f"Organizations ({len(orgs)})"])
    if orgs:
        for index, org in enumerate(orgs, start=1):
            lines.append(f"{index}. {org.get('login')} - https://github.com/{org.get('login')}")
    else:
        lines.append("No organizations found.")

    return lines


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
            data, repos, repos_error, orgs, orgs_error, error = fetch_user_bundle(username)

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


@app.route("/download-report/<username>")
def download_pdf_report(username):
    username = (username or "").strip()
    if not username:
        return "Username is required.", 400

    data, repos, _, orgs, _, error = fetch_user_bundle(username)
    if error or not data:
        message = error or "User not found."
        return message, 404

    lines = build_report_lines(username, data, repos, orgs)
    pdf_bytes = build_simple_pdf(lines)
    filename = f"github-report-{username}.pdf"
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(debug=True)
