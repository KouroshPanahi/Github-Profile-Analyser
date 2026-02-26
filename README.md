This project is a website that takes the user you want on the GitHub site and then outputs the information you want for this user.

This project uses an APIs to find the desired user, the link to which is below:

https://api.github.com/users/{username}

https://api.github.com/users/{username}/orgs

https://api.github.com/users/{username}/repos

Programming languages ​​and libraries used for this project:
- HTML
- CSS
- Python
- Flask
- Requests

Now, what information can we get by giving someone their GitHub username?

- Name
- Username
- Public Repos
- Followings
- Followers
- Bio
- Location
- Company
- Blog/Website
- Twitter Username
- Account Type
- Created At
- Site Admin
- Hireable
- All repositories (public - sorted by stars than forks)
- Organizations
- Pdf Report
- And much more information...

Another feature of this website is comparing two people, which is very useful.
<<<<<<< HEAD

## GitHub API Rate Limit (Token Support)

To avoid hitting GitHub API limits too quickly, this project now supports authenticated
requests using a Personal Access Token.

Without token (unauthenticated): around `60` requests/hour per IP  
With token (authenticated): up to around `5000` requests/hour per user/token

Set one of these environment variables before running the app:
- `GITHUB_TOKEN` (preferred)
- `GH_TOKEN` (fallback)

### macOS / Linux (zsh/bash)
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
python3 main.py
```

### Windows (PowerShell)
```powershell
$env:GITHUB_TOKEN="your_github_personal_access_token"
python main.py
```
=======
>>>>>>> 06a5a9bdf5867d42a8aea9f645031350fc7a78f5

>[!WARNING] Be Careful
>Unlike competing projects, this project does not ask you for your GitHub account password and respects your security. You do not need to create an account and log in to it or pay any financial costs to use our program. It is completely free and its security is guaranteed.


The new feature of the program is the smart comparison between two GitHub users, so that it compares important information and gives them a score. It has 18 points, and below we see what each section has a score:

Followers: 4 points
Public Repository: 3 points
Organizations: 2 points
Account Age (days): 2 points
Followers/Following Ratio: 2 points
Badge Points : 3 points
Badge Count : 1 point