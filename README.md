# Doctor Code: The AI Code Review Co-Pilot

Doctor Code is an autonomous code reviewer that transforms from a simple bug-hunter into a true **repository co-pilot**. Designed to run natively in your terminal or autonomously in the cloud, it analyzes your code to provide human-readable architectural summaries and aggressively stress-tests your diffs for critical flaws.

---

## Key Features

- **Dual-Mandate AI:** Automatically generates a concise, high-level summary of the overall changes and intent of your Pull Request, followed by a granular scan for **Security Vulnerabilities**, **Critical Logic Bugs**, and **Performance Flaws**.
- **Multi-Provider Architecture:** Built on a robust Provider Pattern (Abstract Base Class), allowing you to seamlessly swap between **Gemini**, **OpenAI (GPT-4o)**, and **Anthropic (Claude)** without rewriting any core logic.
- **Bring Your Own Key (BYOK):** Doctor Code operates on a developer-friendly BYOK model. You aren't locked into a paid subscription service — just plug your existing API keys into your local environment or GitHub Secrets.
- **Zero-Friction CI/CD:** Runs autonomously as a GitHub Action. It fetches PR diffs and posts beautifully formatted review summaries via GitHub's REST API. The repository owner foots the fractional token cost, meaning open-source contributors get **free automated reviews**.
- **Local Testing CLI:** A fully functional command-line interface lets you test your code diffs locally before you ever push a commit.

---

## Tech Stack

| Component | Details |
|-----------|---------|
| **Language** | Python 3.10+ |
| **AI Libraries** | `google-genai`, `openai`, `anthropic` |
| **Data Validation** | `pydantic` (enforces strict JSON output from AI) |
| **Utilities** | `subprocess` (local Git ops), `requests` (GitHub API) |

---
## Working Demos
[![View Live Demo](https://img.shields.io/badge/Live_Demo-Open_Pull_Request-green?style=for-the-badge&logo=github)](https://github.com/zephyrzip/doctor-code/pull/4)
---
GitHub Actions CI Demo
|**Buggy-Code**|**Doctor-Code's Verdict**|
|--------------|-------------------------|
|<img width="1001" height="523" alt="image" src="https://github.com/user-attachments/assets/fd970f3f-2ad5-4545-93ba-b5a226eb278d" />|<img width="566" height="678" alt="image" src="https://github.com/user-attachments/assets/8103d130-6ef4-4781-82bc-415e876dc35f" />|

---
Local Terminal Demo
|**Without Buggy Code (Open PR)**| <img width="1092" height="327" alt="image" src="https://github.com/user-attachments/assets/171ebefe-69ed-456f-90cf-241cb0aaa843" /> |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
|**With Bug in Code (Open PR + changed potential bug in code)**|<img width="1070" height="322" alt="image" src="https://github.com/user-attachments/assets/89dae8f0-48a0-4d6a-897f-42eb843ead8e" /> |


---


## Installation (Local CLI Mode)

Test your code locally before pushing it to GitHub.

### 1. Clone the Repository

```bash
git clone https://github.com/zephyrzip/doctor-code.git
cd doctor-code
```

### 2. Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Your API Keys

Create a `.env` file in the root directory and add your preferred provider keys (you only need the one you plan to use):

```env
GEMINI_API_KEY="your_gemini_key_here"
OPENAI_API_KEY="your_openai_key_here"
ANTHROPIC_API_KEY="your_anthropic_key_here"
```

> **Important:** Ensure `.env` is listed in your `.gitignore` file to prevent accidental key leaks!

---

## Usage

Doctor Code can be used in **two distinct ways** depending on your workflow. Choose the one that fits your needs.

---

### Way 1 — Local CLI (Run on Your Machine)

This mode is ideal for developers who want to review their own code **before making a commit**, without any cloud setup.

You run Doctor Code directly on your machine, pointing it at any local repository.

```bash
# Default (Uses Gemini)
python -m src.main --local

# Specify a different AI provider
python -m src.main --local --provider openai
python -m src.main --local --provider anthropic

# Target a specific commit or branch
python -m src.main --local --target main
```

>  The script analyzes your local Git diff, so make sure you're inside the target repository directory with staged or uncommitted changes to review.

---

###  Way 2 — GitHub Actions (CI/CD Automation)

This mode is for teams and open-source maintainers who want **automatic AI reviews on every Pull Request** — no manual intervention needed.

The key insight: **you don't copy Doctor Code into your repo.** You just reference it. The workflow dynamically clones the Doctor Code engine at runtime, so your project stays clean and always gets the latest version of the tool.

**Step 1 — Add Your API Key as a Repository Secret:**

Navigate to your repository on GitHub → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`.

Add your chosen API key (e.g., `GEMINI_API_KEY`).

**Step 2 — Create the Workflow File:**

Create `.github/workflows/doctor-code-review.yml` in **your own repository**:

```yaml
name: Doctor Code AI Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Doctor Code
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_EVENT_PATH: ${{ github.event_path }}
        run: python -m src.main --ci --provider gemini
```

>  To use OpenAI or Anthropic instead, swap the `--provider` flag and pass the respective secret in the `env` block.

Once set up, every new PR in your repository will automatically receive an AI-generated review comment from Doctor Code. **Your contributors get free reviews; you only pay the fractional API token cost.**

---

##  Contributing

Contributions, issues, and feature requests are welcome!

If you want to expand the "Brains" or integrate external security scanners, feel free to open a Pull Request.

---

<p align="center">Thank you for using doctor code. I hope my little project helped. <3 </p>
