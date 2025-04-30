import os
import requests

class Github:
    def __init__(self, token, repo_owner, repo_name):
        """
        Initialize the GithubCopilot class with the GitHub token and repository details.
        :param token: Personal access token for GitHub API
        :param repo_owner: Owner of the repository
        :param repo_name: Name of the repository
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

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
        response = requests.get(commits_url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch commits: {response.status_code} {response.text}")

        commits = response.json()
        if not commits:
            raise RuntimeError("No commits found in the repository.")

        latest_commit = commits[0]
        commit_sha = latest_commit['sha']

        # Get the details of the latest commit
        commit_url = f"{self.api_url}/commits/{commit_sha}"
        response = requests.get(commit_url, headers=headers)
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