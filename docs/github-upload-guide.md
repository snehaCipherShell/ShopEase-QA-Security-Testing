# Publishing ShopEase to GitHub (Kali Linux)

## 0. Read this first: use a separate repository for this project
If `git rev-parse --show-toplevel` run inside the project prints your **home folder** (for example `/home/<you>`), then your home directory is a Git repository. **Never push that repository and never run `git add .` there**: it would expose shell history, cloud credentials, browser profiles and other private files. ShopEase needs its own repository, created *inside* the project folder:
```bash
cd ~/Downloads/ShopEase-final/ShopEase-QA-Security-Testing
git rev-parse --show-toplevel        # must NOT print your home folder; if it does, run: git init
git init                             # creates .git inside the project (safe: it does not touch your home repo)
git rev-parse --show-toplevel        # now must print .../ShopEase-QA-Security-Testing
```

## 1. Fill in your own details (replace the values in quotes)
```bash
sed -i 's/<YOUR NAME>/Your Full Name/' LICENSE
sed -i 's#<your-username>#your-github-username#' README.md docs/github-upload-guide.md
grep -rn "<YOUR NAME>\|<your-username>" README.md LICENSE docs | head      # should print nothing
```

## 2. Safety checks before the first commit
```bash
git status --short --ignored | grep '^!!'     # expect: .venv/, instance/shopease.db, screenshots/private/ (and caches)
find . -name "*.db" -not -path "./.venv/*"    # the only .db must be the git-ignored instance/shopease.db
ls screenshots screenshots/private screenshots/sanitized
grep -rniE "shopease_session=[A-Za-z0-9_-]{20,}|authorization:|bearer [a-z0-9._-]{10,}" README.md docs scripts app tests | head   # expect nothing
```
The only passwords in the project are the fictional seed/test accounts documented in the README. `screenshots/private/` holds originals that contain personal data or unrelated sites: it must stay ignored. `screenshots/pytest-output*.txt` contain your local home path; edit them if you do not want your username public.

## 3. First commit
```bash
git config user.name  "Your Name"
git config user.email "you@example.com"      # or your GitHub noreply address
git add .
git status                                   # review every listed file; private/, .venv and .db must NOT appear
git commit -m "ShopEase: QA, API testing and security validation portfolio project"
git branch -M main
git rev-parse --short HEAD                   # record this commit hash in docs/test-execution-report.md if you like
```

## 4. Create the GitHub repository
github.com > **New repository** > name `ShopEase-QA-Security-Testing` > Public > **do not** add a README, `.gitignore` or licence (you already have them) > Create.

## 5. Push (SSH or token)
```bash
git remote add origin https://github.com/<your-username>/ShopEase-QA-Security-Testing.git
git push -u origin main
```
GitHub does not accept account passwords: use a **fine-grained personal access token** as the password, or SSH (`ssh-keygen -t ed25519`, add the public key in GitHub settings, then use `git@github.com:<you>/ShopEase-QA-Security-Testing.git`). **Never commit a token.**

## 6. After pushing
- Open the repository page and check: README renders (including the Mermaid diagram), screenshots show, no `private/` folder, no `.db` file.
- Settings: add the description "Local QA + API + basic security testing portfolio project (educational)" and topics `qa`, `api-testing`, `pytest`, `postman`, `sql`, `flask`, `security-testing`.
- Optional: pin the repository on your GitHub profile.

## 7. Updating results later
Re-run `python -m pytest -v | tee screenshots/pytest-output-latest.txt`, update `docs/test-execution-report.md` and the README results table with the real summary line and the commit hash, then `git add` the changed files and commit.
