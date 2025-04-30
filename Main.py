from Github import Github

if __name__ == "__main__":
    # Informations nécessaires pour accéder au GitHub
    token = "your_github_token"  # Remplacez par votre token GitHub
    repo_owner = "repo_owner"    # Remplacez par le propriétaire du dépôt
    repo_name = "repo_name"      # Remplacez par le nom du dépôt

    try:
        # Initialiser la classe Github
        github = Github(token, repo_owner, repo_name)

        # Récupérer le contenu du dernier commit
        latest_commit = github.get_new_commit_content()

        # Afficher les informations du dernier commit
        print(f"Commit SHA: {latest_commit['sha']}")
        print(f"Auteur: {latest_commit['author']}")
        print(f"Message: {latest_commit['message']}")
        print("Fichiers modifiés:")
        for file in latest_commit['files']:
            print(f"  - {file['filename']} ({file['status']})")
            if file.get('patch'):
                print(f"    Patch:\n{file['patch']}")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")