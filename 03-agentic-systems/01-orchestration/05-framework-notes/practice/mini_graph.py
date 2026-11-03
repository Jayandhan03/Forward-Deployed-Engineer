"""A 40-line graph runner: the core idea behind LangGraph-style frameworks.

State is a dict. Nodes are functions that return state updates. Edges (including conditional ones)
pick the next node. Add checkpointing + interrupts and you have most of what the frameworks sell.

Use this to decide: adopt a framework for persistence/streaming/HITL you don't want to build, or
hand-roll when your flow is simple and you want to see every step.

Run:
    python mini_graph.py
"""

END = "__end__"


class Graph:
    def __init__(self):
        self.nodes, self.edges, self.router = {}, {}, {}

    def node(self, name, fn):
        self.nodes[name] = fn
        return self

    def edge(self, src, dst):
        self.edges[src] = dst
        return self

    def conditional(self, src, chooser):
        self.router[src] = chooser                    # chooser(state) -> next node name
        return self

    def run(self, state: dict, start: str, max_steps=20, on_step=None) -> dict:
        current = start
        for step in range(max_steps):                 # a graph with a cycle needs a step cap
            state = {**state, **self.nodes[current](state)}
            if on_step:
                on_step(step, current, state)         # hook for checkpoint / trace / stream
            current = self.router[current](state) if current in self.router else self.edges.get(current, END)
            if current == END:
                return state
        raise RuntimeError("max steps exceeded")


# --- An agent-shaped graph: draft -> check -> (revise -> check)* -> publish ------------------

def draft(s):   return {"text": "v1 of the answer", "revisions": 0}
def check(s):   return {"ok": s["revisions"] >= 2}
def revise(s):  return {"text": s["text"] + "+", "revisions": s["revisions"] + 1}
def publish(s): return {"published": s["text"]}


if __name__ == "__main__":
    g = (Graph()
         .node("draft", draft).node("check", check).node("revise", revise).node("publish", publish)
         .edge("draft", "check")
         .conditional("check", lambda s: "publish" if s["ok"] else "revise")
         .edge("revise", "check"))

    final = g.run({}, "draft", on_step=lambda i, n, s: print(f"  step {i}: {n:<8} state={s}"))
    print("\nfinal:", final["published"])
