import os
import json
import requests
import sys
from typing import List

class GitHubClient:
    def __init__(self):
        # GitHub Actions automatically injects these into the runner environment
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPOSITORY") # e.g., "username/doctor-code"
        
        # GitHub stores the webhook event payload in a JSON file
        event_path = os.getenv("GITHUB_EVENT_PATH")
        
        if not all([self.token, self.repo, event_path]):
            raise ValueError("Missing required GitHub environment variables. Are you running in CI?")
            
        with open(event_path, 'r') as f:
            event_data = json.load(f)
            # Extract the Pull Request number from the event payload
            self.pr_number = event_data.get("pull_request", {}).get("number")
            
        if not self.pr_number:
            raise ValueError("Could not find PR number in event payload.")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.api_base = f"https://api.github.com/repos/{self.repo}"

    def get_pr_diff(self) -> str:
        """Fetches the raw diff string of the Pull Request."""
        url = f"{self.api_base}/pulls/{self.pr_number}"
        # Requesting the diff format specifically
        diff_headers = self.headers.copy()
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        
        response = requests.get(url, headers=diff_headers)
        response.raise_for_status()
        return response.text

    def post_review_comment(self, findings: List) -> None:
        """Posts a general review summary to the PR."""
        url = f"{self.api_base}/issues/{self.pr_number}/comments"
        
        if not findings:
            body = "✅ **Doctor Code:** No critical security vulnerabilities, logic bugs, or performance flaws found!"
        else:
            body = "🚨 **Doctor Code found potential issues:**\n\n"
            for i, finding in enumerate(findings, 1):
                body += f"### {i}. [{finding.category}] in `{finding.filename}` (Line {finding.line_number})\n"
                body += f"**Issue:** {finding.bug_description}\n"
                body += f"**Suggested Fix:**\n```python\n{finding.suggested_fix}\n```\n---\n"

        response = requests.post(url, headers=self.headers, json={"body": body})
        response.raise_for_status()
        print(f"Successfully posted review to PR #{self.pr_number}")