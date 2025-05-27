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
        """
        Test the GitHub API by fetching the latest commit content.
        :return: A tuple containing the author, message, and files of the latest commit.
        """
        try:
            commit_content = self.get_new_commit_content()
            print(type(commit_content))
            print("Successful access to GitHub API")
            return commit_content.get('author'), commit_content.get('message'), commit_content.get('files')
        except ValueError as ve:
            print("Configuration error:", str(ve))
        except RuntimeError as re:
            print("GitHub API error:", str(re))
        except Exception as e:
            print("Unexpected error:", str(e))
        return None, None, None
    
    
    def get_latest_pr_commit_content(self):
        """
        Récupère les informations principales de la dernière pull request ouverte,
        ainsi que les infos du dernier commit de cette PR.
        :return: Un dictionnaire structuré avec les infos principales
        ou None si aucune PR trouvée.
        """
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Récupérer la dernière pull request ouverte (triée par date de création)
        prs_url = (
            f"{self.api_url}/pulls?state=open&sort=created&direction=desc"
        )
        response = requests.get(prs_url, headers=headers, verify=False)
        if response.status_code != 200:
            raise RuntimeError(
                f"Erreur lors de la récupération des PRs: "
                f"{response.status_code} {response.text}"
            )

        prs = response.json()
        if not prs:
            print("Aucune pull request ouverte trouvée.")
            return None

        latest_pr = prs[0]
        pr_number = latest_pr['number']

        # Récupérer les commits de cette PR
        commits_url = f"{self.api_url}/pulls/{pr_number}/commits"
        response = requests.get(commits_url, headers=headers, verify=False)
        if response.status_code != 200:
            raise RuntimeError(
                f"Erreur lors de la récupération des commits de la PR: "
                f"{response.status_code} {response.text}"
            )

        commits = response.json()
        if not commits:
            print("Aucun commit trouvé dans la PR.")
            return None

        last_commit = commits[-1]
        commit_sha = last_commit['sha']

        # Récupérer les détails du commit
        commit_url = f"{self.api_url}/commits/{commit_sha}"
        response = requests.get(commit_url, headers=headers, verify=False)
        if response.status_code != 0:
            raise RuntimeError(
                f"Erreur lors de la récupération du commit: "
                f"{response.status_code} {response.text}"
            )

        commit_details = response.json()
        files_changed = commit_details.get('files', [])

        # Construction du dictionnaire de retour avec les infos principales
        return {
            'pr_number': latest_pr['number'],
            'pr_title': latest_pr['title'],
            'pr_author': latest_pr['user']['login'],
            'pr_state': latest_pr['state'],
            'pr_created_at': latest_pr['created_at'],
            'pr_commits_count': latest_pr['commits'],
            'pr_changed_files': latest_pr['changed_files'],
            'pr_additions': latest_pr['additions'],
            'pr_deletions': latest_pr['deletions'],
            'last_commit': {
                'sha': commit_sha,
                'author': last_commit['commit']['author']['name'],
                'message': last_commit['commit']['message'],
                'files': [
                    {
                        'filename': file['filename'],
                        'status': file['status'],
                        'patch': file.get('patch')
                    } for file in files_changed
                ]
            }
        }
