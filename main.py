from io import BytesIO
import os
import textwrap
import zlib
from flask import Flask, render_template, request, send_file
import requests

app = Flask(__name__)
TOP_REPOS_LIMIT = 5
PER_PAGE = 100
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")


def github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def github_get(path, params=None):
    return requests.get(
        f"{GITHUB_API_BASE}{path}",
        timeout=10,
        params=params,
        headers=github_headers(),
    )


def fetch_all_repositories(username):
    repos = []
    page = 1

    while True:
        response = github_get(
            f"/users/{username}/repos",
            params={"per_page": PER_PAGE, "page": page, "sort": "updated"},
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
    response = github_get(f"/users/{username}/orgs")
    response.raise_for_status()
    return response.json()


def map_http_error(response):
    status = response.status_code if response is not None else "unknown"
    if status == 404:
        return "User not found."
    if status == 401:
        return "Invalid GitHub token. Please check GITHUB_TOKEN."
    if status == 403:
        remaining = response.headers.get("X-RateLimit-Remaining", "")
        if remaining == "0":
            return "GitHub API rate limit exceeded. Add GITHUB_TOKEN to increase limits."
        return "Access is restricted or rate limit exceeded."
    return f"HTTP error: {status}"


def fetch_profile_with_orgs(username):
    data = None
    orgs = []
    orgs_error = None
    error = None
    response = None

    try:
        response = github_get(f"/users/{username}")
        response.raise_for_status()
        data = response.json()

        try:
            orgs = fetch_user_orgs(username)
        except requests.exceptions.RequestException as exc:
            orgs_error = f"Could not fetch organizations: {exc}"
    except requests.exceptions.Timeout:
        error = "Request timed out. Please check your internet connection and try again."
    except requests.exceptions.ConnectionError:
        error = "Could not connect to the internet. Please try again."
    except requests.exceptions.HTTPError:
        error = map_http_error(response)
    except requests.exceptions.RequestException as exc:
        error = f"Request failed: {exc}"

    return data, orgs, orgs_error, error


def fetch_user_bundle(username):
    data = None
    repos = []
    repos_error = None
    orgs = []
    orgs_error = None
    error = None
    response = None

    try:
        response = github_get(f"/users/{username}")
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
        error = map_http_error(response)
    except requests.exceptions.RequestException as exc:
        error = f"Request failed: {exc}"

    return data, repos, repos_error, orgs, orgs_error, error


def sanitize_pdf_text(value):
    text = str(value or "N/A")
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", "replace").decode("latin-1")


def wrap_pdf_text(value, width):
    text = str(value or "N/A")
    parts = []
    for paragraph in text.splitlines() or [""]:
        wrapped = textwrap.wrap(paragraph.strip(), width=width)
        parts.extend(wrapped or [""])
    return parts or ["N/A"]


def build_simple_pdf(username, blocks):
    page_width = 612
    page_height = 792
    left = 48
    right = 48
    header_height = 82
    top_content = page_height - header_height - 28
    bottom_content = 56
    usable_width = page_width - left - right

    styles = {
        "section": {"font": "F2", "size": 13, "leading": 19, "color": (0.11, 0.18, 0.34), "indent": 0, "wrap": 60},
        "label": {"font": "F2", "size": 10, "leading": 14, "color": (0.18, 0.18, 0.18), "indent": 0, "wrap": 96},
        "text": {"font": "F1", "size": 10, "leading": 14, "color": (0.24, 0.24, 0.24), "indent": 12, "wrap": 92},
        "item": {"font": "F2", "size": 11, "leading": 16, "color": (0.15, 0.15, 0.15), "indent": 0, "wrap": 90},
    }

    pages = []
    page_number = 0

    def add_rect(commands, x, y, width, height, color):
        commands.append(
            f"q {color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg {x:.2f} {y:.2f} {width:.2f} {height:.2f} re f Q"
        )

    def add_text(commands, x, y, text, font, size, color):
        safe = sanitize_pdf_text(text)
        commands.append(
            f"BT /{font} {size} Tf {color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg 1 0 0 1 {x:.2f} {y:.2f} Tm ({safe}) Tj ET"
        )

    def new_page():
        nonlocal page_number
        page_number += 1
        commands = []
        add_rect(commands, 0, page_height - header_height, page_width, header_height, (0.09, 0.15, 0.32))
        add_text(commands, left, page_height - 38, "GitHub Profile Report", "F2", 18, (1.0, 1.0, 1.0))
        add_text(commands, left, page_height - 58, f"@{username}", "F1", 10, (0.86, 0.91, 1.0))
        commands.append(f"0.82 0.85 0.91 RG 0.8 w {left:.2f} 45 m {page_width - right:.2f} 45 l S")
        add_text(commands, left, 30, "Generated by GitHub Profile Analyser", "F1", 8, (0.40, 0.40, 0.40))
        add_text(commands, page_width - right - 58, 30, f"Page {page_number}", "F1", 8, (0.40, 0.40, 0.40))
        return {"commands": commands, "y": top_content}

    current = new_page()

    def ensure_space(height_needed):
        nonlocal current
        if current["y"] - height_needed < bottom_content:
            pages.append(current["commands"])
            current = new_page()

    for block in blocks:
        if block["kind"] == "spacer":
            space = block.get("space", 10)
            ensure_space(space)
            current["y"] -= space
            continue

        style = styles[block["kind"]]
        lines = wrap_pdf_text(block["text"], style["wrap"])
        for line in lines:
            ensure_space(style["leading"])
            x = min(left + style.get("indent", 0), left + usable_width - 20)
            add_text(current["commands"], x, current["y"], line, style["font"], style["size"], style["color"])
            current["y"] -= style["leading"]

    pages.append(current["commands"])

    objects = {}
    font_regular_obj_num = 3
    font_bold_obj_num = 4
    objects[font_regular_obj_num] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects[font_bold_obj_num] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"

    page_refs = []
    next_obj_num = 5

    for page_commands in pages:
        stream = "\n".join(page_commands).encode("latin-1")
        compressed_stream = zlib.compress(stream, level=6)

        content_obj_num = next_obj_num
        page_obj_num = next_obj_num + 1
        next_obj_num += 2

        objects[content_obj_num] = (
            b"<< /Filter /FlateDecode /Length "
            + str(len(compressed_stream)).encode("latin-1")
            + b" >>\nstream\n"
            + compressed_stream
            + b"\nendstream"
        )
        objects[page_obj_num] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {font_regular_obj_num} 0 R /F2 {font_bold_obj_num} 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>"
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
    blocks = [
        {"kind": "section", "text": "Profile Summary"},
        {"kind": "label", "text": "Name"},
        {"kind": "text", "text": data.get("name") or "N/A"},
        {"kind": "label", "text": "Username"},
        {"kind": "text", "text": data.get("login") or username},
        {"kind": "label", "text": "Profile URL"},
        {"kind": "text", "text": data.get("html_url") or "N/A"},
        {"kind": "label", "text": "Bio"},
        {"kind": "text", "text": data.get("bio") or "N/A"},
        {"kind": "label", "text": "Location / Company / Blog"},
        {"kind": "text", "text": f"{data.get('location') or 'N/A'} | {data.get('company') or 'N/A'} | {data.get('blog') or 'N/A'}"},
        {"kind": "label", "text": "Public Repos / Followers / Following"},
        {"kind": "text", "text": f"{data.get('public_repos', 0)} / {data.get('followers', 0)} / {data.get('following', 0)}"},
        {"kind": "spacer", "space": 12},
        {"kind": "section", "text": f"Repositories ({len(repos)})"},
    ]

    if repos:
        for index, repo in enumerate(repos, start=1):
            blocks.extend(
                [
                    {"kind": "item", "text": f"{index}. {repo.get('name') or 'N/A'}"},
                    {"kind": "text", "text": f"Description: {repo.get('description') or 'N/A'}"},
                    {"kind": "text", "text": f"Language: {repo.get('language') or 'N/A'}"},
                    {
                        "kind": "text",
                        "text": (
                            f"Stars: {repo.get('stargazers_count', 0)} | "
                            f"Forks: {repo.get('forks_count', 0)} | "
                            f"Open Issues: {repo.get('open_issues_count', 0)}"
                        ),
                    },
                    {"kind": "text", "text": f"URL: {repo.get('html_url') or 'N/A'}"},
                    {"kind": "spacer", "space": 8},
                ]
            )
    else:
        blocks.append({"kind": "text", "text": "No repositories found."})

    blocks.extend([{"kind": "spacer", "space": 8}, {"kind": "section", "text": f"Organizations ({len(orgs)})"}])
    if orgs:
        for index, org in enumerate(orgs, start=1):
            org_login = org.get("login") or "N/A"
            blocks.append({"kind": "item", "text": f"{index}. {org_login}"})
            blocks.append({"kind": "text", "text": f"https://github.com/{org_login}"})
            blocks.append({"kind": "spacer", "space": 6})
    else:
        blocks.append({"kind": "text", "text": "No organizations found."})

    return blocks


@app.route("/", methods=["GET", "POST"])
def home():
    # Profile tab state
    data = None
    repos = []
    repos_error = None
    orgs = []
    orgs_error = None
    error = None
    username = ""

    # Compare tab state
    compare_left_username = ""
    compare_right_username = ""
    compare_left_data = None
    compare_right_data = None
    compare_left_orgs = []
    compare_right_orgs = []
    compare_left_orgs_error = None
    compare_right_orgs_error = None
    compare_error = None
    active_tab = "profile"

    if request.method == "POST":
        form_type = request.form.get("form_type", "profile").strip()

        if form_type == "compare":
            active_tab = "compare"
            compare_left_username = request.form.get("compare_left_username", "").strip()
            compare_right_username = request.form.get("compare_right_username", "").strip()

            if not compare_left_username or not compare_right_username:
                compare_error = "Please enter both GitHub usernames to compare."
            else:
                (
                    compare_left_data,
                    compare_left_orgs,
                    compare_left_orgs_error,
                    left_error,
                ) = fetch_profile_with_orgs(compare_left_username)
                (
                    compare_right_data,
                    compare_right_orgs,
                    compare_right_orgs_error,
                    right_error,
                ) = fetch_profile_with_orgs(compare_right_username)

                errors = []
                if left_error:
                    errors.append(f"{compare_left_username}: {left_error}")
                if right_error:
                    errors.append(f"{compare_right_username}: {right_error}")
                if errors:
                    compare_error = " | ".join(errors)
        else:
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
        active_tab=active_tab,
        compare_left_username=compare_left_username,
        compare_right_username=compare_right_username,
        compare_left_data=compare_left_data,
        compare_right_data=compare_right_data,
        compare_left_orgs=compare_left_orgs,
        compare_right_orgs=compare_right_orgs,
        compare_left_orgs_error=compare_left_orgs_error,
        compare_right_orgs_error=compare_right_orgs_error,
        compare_error=compare_error,
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

    blocks = build_report_lines(username, data, repos, orgs)
    pdf_bytes = build_simple_pdf(username, blocks)
    filename = f"github-report-{username}.pdf"
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(debug=True)
