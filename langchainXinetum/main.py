from dotenv import load_dotenv
from langchain_inetum import ChatInetum
from prompt import prompt_1, prompt_2
from src.Github import Github

load_dotenv()


def main():
    try:
        chat = ChatInetum(
            model_name="inetum-gpt4o",
            temperature=0.16,
            api_url="https://playground.inetum.group/api",
        )
    except Exception as e:
        print(f"Erreur lors de l'initialisation du modèle : {e}")
        return

    messages = prompt_2

    github = Github()
    auteur= github.get_latest_pr_commit_content()
    print(auteur)
    #resultat = f"{messages}\n+ {auteur}\n+ {message}\n+ {files}"
    #res = chat.invoke(resultat)

    #print("You:\n", messages, "\n")
    #print("model answer :\n", res.content)


if __name__ == "__main__":
    main()
