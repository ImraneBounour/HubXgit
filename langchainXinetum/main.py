from dotenv import load_dotenv
from src.model import ChatInetum
from prompt import prompt_1
from src.Github import Github

load_dotenv()


def main():
    chat = ChatInetum(
        model_name="inetum-gpt4o",
        temperature=0.16,
        api_url="https://playground.inetum.group/api",
    )
    messages = prompt_1

    github = Github()
    auteur, message, file = github.test_github_api()
    message = f"message\n+ {auteur}\n+ {message}\n+ {file}"
    res = chat.invoke(messages)

    print("You:\n", messages, "\n")
    print("model answer :\n", res.content)




if __name__ == "__main__":
    main()
