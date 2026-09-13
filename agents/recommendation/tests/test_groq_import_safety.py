import importlib
from unittest.mock import patch


def test_importing_groq_provider_does_not_load_dotenv_or_create_client() -> None:
    with patch("dotenv.load_dotenv") as load_dotenv, patch("groq.Groq") as groq_client:
        module = importlib.import_module("agents.recommendation.llm.groq_provider")
        importlib.reload(module)

    load_dotenv.assert_not_called()
    groq_client.assert_not_called()


def test_importing_manual_integration_module_does_not_load_dotenv_or_create_client() -> None:
    with patch("dotenv.load_dotenv") as load_dotenv, patch("groq.Groq") as groq_client:
        module = importlib.import_module("agents.recommendation.tests.test_agent3_to_agent4")
        importlib.reload(module)

    load_dotenv.assert_not_called()
    groq_client.assert_not_called()
