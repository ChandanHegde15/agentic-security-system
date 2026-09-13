import json

from agents.dependency_extraction.agent import extract_dependencies
from agents.registry_verification.agent import verify_extraction
from agents.risk_analysis.analyzer import analyze_verification

from agents.recommendation.agent import RecommendationAgent


PROJECT_PATH = "test-projects/P001"
PROJECT_ID = "P001"


def main():
    # Manual/live execution only: normal pytest collection does not load .env.
    from dotenv import load_dotenv
    from agents.recommendation.llm.groq_provider import GroqProvider

    load_dotenv()
    print("\n========== AGENT 3 → AGENT 4 INTEGRATION ==========\n")

    # ---------------------------------------------------------
    # Agent 1 — Dependency Extraction
    # ---------------------------------------------------------
    print("Running Agent 1...")

    extraction_result = extract_dependencies(
        PROJECT_PATH
    )

    print("Agent 1 completed.")

    # ---------------------------------------------------------
    # Agent 2 — Registry Verification
    # ---------------------------------------------------------
    print("Running Agent 2...")

    verification_result = verify_extraction(
        extraction_result
    )

    print("Agent 2 completed.")

    # ---------------------------------------------------------
    # Agent 3 — Deterministic Risk Analysis
    # ---------------------------------------------------------
    print("Running Agent 3...")

    risk_result = analyze_verification(
        verification_result
    )

    print("Agent 3 completed.")

    # ---------------------------------------------------------
    # Display actual Agent 3 output
    # ---------------------------------------------------------
    print("\n========== ACTUAL AGENT 3 OUTPUT ==========\n")

    print(
        json.dumps(
            risk_result,
            indent=2,
        )
    )

    # Safety check
    if risk_result.get("project_id") != PROJECT_ID:
        raise ValueError(
            "Unexpected project_id in Agent 3 output."
        )

    # ---------------------------------------------------------
    # Agent 4 — LLM Recommendation
    # ---------------------------------------------------------
    print("\nRunning Agent 4...")

    provider = GroqProvider()

    agent4 = RecommendationAgent(
        llm_provider=provider
    )

    recommendation_result = agent4.recommend(
        risk_result
    )

    # ---------------------------------------------------------
    # Display Agent 4 result
    # ---------------------------------------------------------
    print("\n========== AGENT 4 RESULT ==========\n")

    print(
        recommendation_result.model_dump_json(
            indent=2
        )
    )

    print(
        "\n========== INTEGRATION SUCCESS ==========\n"
    )


if __name__ == "__main__":
    main()
