# 🦜🔗 Inetum LangChain Integration 

Bienvenue dans la librairie Python pour l'intégration LangChain des modèles de GenAI Inetum. 
Cette librairie permet de connecter et d'utiliser les services d'Inetum avec LangChain, un framework pour le développement d'applications GenAI.

## Ressources
- [Documentation LangChain](https://python.langchain.com/docs)
- [Playground Inetum](https://playground.inetum.group/)

## Installation

Pour installer la librairie, vous pouvez utiliser pip :

```bash
pip install langchain-inetum
```

## Configuration

Pour récupérer la clé API, allez dans [l'onglet "developer" du Inetum Playground](https://playground.inetum.group/developer) et générez une clé API.

Vous pouvez soit la spécifier directement dans le code:
```python
llm = ChatInetum(api_key='VOTRE_API_KEY')
```

Soit la définir dans la variable `INETUM_GENAI_API_KEY` d'un fichier `.env` à la racine de votre projet :
```env
INETUM_GENAI_API_KEY=VOTRE_API_KEY
```
Et la librairie la récupérera automatiquement.

## Utilisation

Voici un exemple de code pour utiliser l'intégration LangChain des modèles Inetum :

```python
from langchain_inetum import ChatInetum

# Initialiser l'intégration
llm = ChatInetum(
    api_key='VOTRE_API_KEY', # Optionnel si défini dans le .env
    model_name='inetum-gpt4o',
    temperature=0.4,
)

# Utiliser l'intégration pour traiter du texte
response = llm.invoke("Votre texte ici")
print(response)
```


## Modèles disponibles
| Modèle | `model_name` argument |
|--------|------------|
| gpt-3.5-turbo | inetum-gpt35turbo |
| gpt-4 | inetum-gpt4 |
| gpt-4-turbo | inetum-gpt4-turbo |
| gpt-4o | inetum-gpt4o |
