import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Classe.Github import Github
from dotenv import load_dotenv

def test_github_api():
    # Replace these with your actual GitHub token, repository owner, and repository name
    load_dotenv()

    token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("REPO_OWNER")
    repo_name = os.getenv("REPO_NAME")

    github = Github(token, repo_owner, repo_name)

    try:
        commit_content = github.get_new_commit_content()
        print("Access to GitHub API successful!")
        print("Latest Commit SHA:", commit_content['sha'])
        print("Author:", commit_content['author'])
        print("------------------------------------")
        print("Message:", commit_content['message'])
        print("------------------------------------")
        print("Files Changed:", commit_content['files'])
    except Exception as e:
        print("Failed to access GitHub API:", str(e))

if __name__ == "__main__":
    test_github_api()
    