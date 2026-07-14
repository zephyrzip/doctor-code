# 🩺 Doctor Code: The AI Code Review Co-Pilot

Doctor Code is an autonomous code reviewer that transforms from a simple bug-hunter into a true **repository co-pilot**. Designed to run natively in your terminal or autonomously in the cloud, it analyzes your code to provide human-readable architectural summaries and aggressively stress-tests your diffs for critical flaws.

---

## ✨ Key Features

- **Dual-Mandate AI:** Automatically generates a concise, high-level summary of the overall changes and intent of your Pull Request, followed by a granular scan for **Security Vulnerabilities**, **Critical Logic Bugs**, and **Performance Flaws**.
- **Multi-Provider Architecture:** Built on a robust Provider Pattern (Abstract Base Class), allowing you to seamlessly swap between **Gemini**, **OpenAI (GPT-4o)**, and **Anthropic (Claude)** without rewriting any core logic.
- **Bring Your Own Key (BYOK):** Doctor Code operates on a developer-friendly BYOK model. You aren't locked into a paid subscription service — just plug your existing API keys into your local environment or GitHub Secrets.
- **Zero-Friction CI/CD:** Runs autonomously as a GitHub Action. It fetches PR diffs and posts beautifully formatted review summaries via GitHub's REST API. The repository owner foots the fractional token cost, meaning open-source contributors get **free automated reviews**.
- **Local Testing CLI:** A fully functional command-line interface lets you test your code diffs locally before you ever push a commit.

---

## 🛠️ Tech Stack

| Component | Details |
|-----------|---------|
| **Language** | Python 3.10+ |
| **AI Libraries** | `google-genai`, `openai`, `anthropic` |
| **Data Validation** | `pydantic` (enforces strict JSON output from AI) |
| **Utilities** | `subprocess` (local Git ops), `requests` (GitHub API) |

---

## 🚀 Installation (Local CLI Mode)

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

> ⚠️ **Important:** Ensure `.env` is listed in your `.gitignore` file to prevent accidental key leaks!

---

## 💻 Usage

### Local Execution

Run Doctor Code against your latest uncommitted changes or a specific target branch:

```bash
# Default (Uses Gemini)
python -m src.main --local

# Specify a different AI provider
python -m src.main --local --provider openai
python -m src.main --local --provider anthropic

# Target a specific commit or branch
python -m src.main --local --target main
```

### GitHub Actions (CI/CD Mode)

Automate Doctor Code to run every time a Pull Request is opened in your repository.

**Step 1 — Add Repository Secrets:**

Navigate to your repository on GitHub → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`.

Add your chosen API key (e.g., `GEMINI_API_KEY` or `OPENAI_API_KEY`).

**Step 2 — Create the Workflow File:**

Create `.github/workflows/review.yml` in your repository:

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

> 💡 To use OpenAI or Anthropic, change the `--provider` flag and pass the respective API key in the `env` block.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

If you want to expand the "Brains" or integrate external security scanners, feel free to open a Pull Request.

---

<p align="center">Thank you for using doctor code. I hope my little project helped. 🫶</p>
