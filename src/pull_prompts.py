"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, load_yaml, check_env_vars, print_section_header

load_dotenv()

SEED_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"


def _message_template(message) -> str:
    """Extrai o texto de uma mensagem do ChatPromptTemplate."""
    prompt_template = getattr(message, "prompt", None)
    if prompt_template is not None and hasattr(prompt_template, "template"):
        return prompt_template.template

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    return str(content)


def _message_role(message) -> str:
    """Identifica se a mensagem é system ou user."""
    class_name = type(message).__name__.lower()
    if "system" in class_name:
        return "system"
    if "human" in class_name or "user" in class_name:
        return "user"

    role = getattr(message, "role", None)
    if isinstance(role, str):
        return role.lower()
    return ""


def pull_prompts_from_langsmith():
    """
    Puxa o prompt semente e grava prompts/bug_to_user_story_v1.yml.

    Returns:
        True se o arquivo foi salvo, False caso contrário.
    """
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    print(f"Puxando prompt: {SEED_PROMPT}")
    client = Client()
    prompt = client.pull_prompt(
        SEED_PROMPT,
        dangerously_pull_public_prompt=True,
    )

    system_prompt = ""
    user_prompt = ""
    for message in prompt.messages:
        role = _message_role(message)
        template = _message_template(message)
        if role == "system" and not system_prompt:
            system_prompt = template
        elif role in ("user", "human") and not user_prompt:
            user_prompt = template

    if not system_prompt:
        print("❌ O prompt puxado não contém system prompt.")
        return False

    if not user_prompt:
        user_prompt = "{bug_report}"

    existing = (load_yaml(str(OUTPUT_PATH)) or {}) if OUTPUT_PATH.exists() else {}
    root = existing.get("bug_to_user_story_v1", {})
    if not isinstance(root, dict):
        root = {}

    root["description"] = root.get(
        "description",
        "Prompt para converter relatos de bugs em User Stories",
    )
    root["system_prompt"] = system_prompt
    root["user_prompt"] = user_prompt
    root["version"] = root.get("version", "v1")
    root["created_at"] = root.get("created_at", "2025-01-15")
    root["tags"] = root.get(
        "tags",
        ["bug-analysis", "user-story", "product-management"],
    )

    saved = save_yaml({"bug_to_user_story_v1": root}, str(OUTPUT_PATH))
    if not saved:
        return False

    print(f"✓ Prompt salvo em {OUTPUT_PATH}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH")
    try:
        return 0 if pull_prompts_from_langsmith() else 1
    except Exception as error:
        print(f"❌ Erro ao fazer pull do prompt: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
