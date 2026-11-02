"""Three multi-agent patterns with fake "agents" (plain functions) so the control flow is the lesson.

  1. Pipeline        research -> draft -> review, each stage feeds the next
  2. Supervisor/workers   fan out independent sub-tasks in parallel, then merge
  3. Critic loop     writer + critic iterate until the critic approves (or a round cap hits)

Each agent call would be a model call, so the printout counts them: coordination has a cost.

Run:
    python multi_agent_patterns.py
"""

from concurrent.futures import ThreadPoolExecutor

calls = 0


def agent(name: str, fn, *args):
    global calls
    calls += 1
    return fn(*args)


def pipeline(topic: str) -> str:
    notes = agent("researcher", lambda t: f"facts about {t}", topic)
    draft = agent("writer", lambda n: f"Draft using {n}", notes)
    return agent("reviewer", lambda d: d + " (reviewed)", draft)


def supervisor_workers(topics: list[str]) -> str:
    with ThreadPoolExecutor() as pool:                         # independent work runs in parallel
        summaries = list(pool.map(lambda t: agent("worker", lambda x: f"summary({x})", t), topics))
    return agent("supervisor", lambda s: " + ".join(s), summaries)


def critic_loop(max_rounds: int = 4) -> str:
    text, round_ = "first draft", 0
    while round_ < max_rounds:                                 # ALWAYS cap the rounds
        round_ += 1
        feedback = agent("critic", lambda t: None if t.count("fixed") >= 2 else "needs work", text)
        if feedback is None:
            print(f"   critic approved after {round_} round(s)")
            return text
        text = agent("writer", lambda t: t + ", fixed", text)
    print(f"   round cap hit ({max_rounds}); shipping best effort / escalating to a human")
    return text


if __name__ == "__main__":
    for name, fn in [("pipeline", lambda: pipeline("EU AI Act")),
                     ("supervisor/workers", lambda: supervisor_workers(["market", "tech", "legal"])),
                     ("critic loop", critic_loop)]:
        calls = 0
        print(f"{name}:\n   -> {fn()}\n   agent calls: {calls}\n")
    print("Start with ONE agent. Add more only when a single agent measurably fails.")
