from __future__ import annotations

import argparse

from pprint import pprint

from rsare.agents.agent.agent import Agent
from rsare.agents.agent.messages import Messages
from rsare.agents.llm.deepseek_client import DeepSeekClient
from rsare.engine.engine import Engine
from rsare.scenarios.sar.cfar_window_search_scenario import (
    CFARWindowSearchScenario,
)


def build_deepseek_llm() -> DeepSeekClient:
    return DeepSeekClient(
        model="deepseek-chat",
        temperature=0.0,
    )


def print_prompt_sent_to_llm(prompt: str) -> None:
    print("\n" + "=" * 100)
    print("PROMPT SENT TO LLM")
    print("=" * 100)
    print(prompt)


def print_llm_replies(agent: Agent) -> None:
    print("\n" + "=" * 100)
    print("LLM REPLIES")
    print("=" * 100)

    reply_index = 1

    for message in agent.messages.messages:
        if isinstance(message, dict):
            continue

        role = getattr(message, "role", None)
        if role != "assistant":
            continue

        content = getattr(message, "content", None)
        tool_calls = getattr(message, "tool_calls", None)

        print(f"\n--- LLM REPLY {reply_index} ---")

        if tool_calls:
            print("Tool call requested:")
            for i, tool_call in enumerate(tool_calls, start=1):
                function = getattr(tool_call, "function", None)
                print(f"  Tool call {i}:")
                print(f"    name: {getattr(function, 'name', None)}")
                print(f"    arguments: {getattr(function, 'arguments', None)}")

        if content:
            print("Text response:")
            print(content)

        if not tool_calls and not content:
            print("(empty assistant response)")

        reply_index += 1


def run_one_mode(prompt_mode: str) -> dict:
    scenario = CFARWindowSearchScenario(prompt_mode=prompt_mode)

    llm = build_deepseek_llm()

    messages = Messages(
        provider="deepseek",
        system_message=(
            "You are a careful workflow agent. "
            "Use tool feedback to make decisions. "
            "Do not repeat completed upstream steps. "
            "Do not continue beyond the requested task."
        ),
    )

    agent = Agent(
        name=f"cfar_window_search_{prompt_mode}",
        llm=llm,
        messages=messages,
        toolsets=scenario.apps,
    )

    engine = Engine(
        agent=agent,
        scenario=scenario,
    )

    # Use existing framework setup, but avoid Engine.run_scenario_agent()
    # because that method prints the whole workflow.
    scenario.initiate_scenario()
    engine._register_scenario_apps()

    print_prompt_sent_to_llm(scenario.scenario_input)

    agent.run(input=scenario.scenario_input)

    print_llm_replies(agent)

    result = scenario.evaluate_agent_workflow(agent.workflow)

    print("\n" + "=" * 100)
    print("CFAR WINDOW SEARCH EVALUATION")
    print("=" * 100)
    pprint(result)

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=[
            "direct_optimum",
            "choose_from_two",
            "self_propose",
            "all",
        ],
        default="self_propose",
    )
    args = parser.parse_args()

    if args.mode == "all":
        results = {}
        for mode in [
            "direct_optimum",
            "choose_from_two",
            "self_propose",
        ]:
            print("\n" + "#" * 100)
            print(f"RUNNING MODE: {mode}")
            print("#" * 100)
            results[mode] = run_one_mode(mode)

        print("\n" + "=" * 100)
        print("SUMMARY")
        print("=" * 100)
        for mode, result in results.items():
            print(f"{mode}: passed={result['passed']}, calls={result['cfar_call_count']}")
    else:
        result = run_one_mode(args.mode)
        if not result["passed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()