from Github import Github

if __name__ == "__main__":
    # Specify the path to your local git repository
    repo_path = "path/to/your/repo"

    try:
        # Initialize the Github class
        github = Github(repo_path)

        # Retrieve new commits
        commits = github.get_new_commits()

        # Print the retrieved commits
        for commit in commits:
            print(f"Hash: {commit['hash']}, Author: {commit['author']}, Message: {commit['message']}")
    except Exception as e:
        print(f"An error occurred: {e}")