import os
import requests
import urllib3
import sys
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Github:
    
    def __init__(self):
        """
        Initialize the Github class with the GitHub token and repository details.
        :param token: Personal access token for GitHub API
        :param repo_owner: Owner of the repository
        :param repo_name: Name of the repository
        """
        load_dotenv()

        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("REPO_OWNER")
        self.repo_name = os.getenv("REPO_NAME")

        if not self.token or not self.repo_owner or not self.repo_name:
            raise ValueError("Missing required parameters: token, repo_owner, or repo_name")

        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"

    def get_new_commit_content(self):
        """
        Retrieve the content of the latest commit in the repository.
        :return: A dictionary containing commit information and file changes.
        """
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Get the latest commit
        commits_url = f"{self.api_url}/commits"
        response = requests.get(commits_url, headers=headers, verify=False)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch commits: {response.status_code} {response.text}")

        commits = response.json()
        if not commits:
            raise RuntimeError("No commits found in the repository.")

        latest_commit = commits[0]
        commit_sha = latest_commit['sha']

        # Get the details of the latest commit
        commit_url = f"{self.api_url}/commits/{commit_sha}"
        response = requests.get(commit_url, headers=headers, verify=False)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch commit details: {response.status_code} {response.text}")

        commit_details = response.json()
        files_changed = commit_details.get('files', [])

        return {
            'sha': commit_sha,
            'author': latest_commit['commit']['author']['name'],
            'message': latest_commit['commit']['message'],
            'files': [
                {
                    'filename': file['filename'],
                    'status': file['status'],
                    'patch': file.get('patch')
                } for file in files_changed
            ]
        }
    def test_github_api(self): 
        try:
            commit_content = self.get_new_commit_content()
            print("Successful access to GitHub API")
            return commit_content['author'], commit_content['message'], commit_content['files']
        except Exception as e:
            print("Failed to access GitHub API:", str(e))
