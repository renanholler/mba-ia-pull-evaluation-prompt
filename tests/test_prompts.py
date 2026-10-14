"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_optimized_prompt():
    """Retorna o dict do prompt v2, com ou sem chave raiz."""
    data = load_prompts(str(PROMPT_PATH))
    if isinstance(data, dict) and "system_prompt" not in data and len(data) == 1:
        data = next(iter(data.values()))
    return data


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = load_optimized_prompt()
        system_prompt = prompt.get("system_prompt", "")
        assert isinstance(system_prompt, str)
        assert system_prompt.strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = load_optimized_prompt()["system_prompt"]
        normalized = system_prompt.lower()
        assert "você é" in normalized
        assert "product manager" in normalized

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = load_optimized_prompt()["system_prompt"].lower()
        mentions_markdown = "markdown" in system_prompt
        mentions_user_story = "como um" in system_prompt or "user story" in system_prompt
        assert mentions_markdown or mentions_user_story

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = load_optimized_prompt()["system_prompt"].lower()
        assert "exemplo" in system_prompt
        assert "entrada" in system_prompt
        assert "saída" in system_prompt

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt = load_optimized_prompt()
        serialized = yaml.dump(prompt, allow_unicode=True)
        assert "[TODO]" not in serialized
        assert "TODO" not in prompt.get("system_prompt", "")
        assert "TODO" not in str(prompt.get("user_prompt", ""))

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompt = load_optimized_prompt()
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2

        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
