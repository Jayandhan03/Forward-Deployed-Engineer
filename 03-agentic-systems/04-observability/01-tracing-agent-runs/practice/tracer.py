"""A minimal tracer: one trace per run, nested spans per model call / tool call.

This is the shape OpenTelemetry and tools like Langfuse use, in ~40 lines.

Run:
    python tracer.py
"""

import time
import uuid
from contextlib import contextmanager


class Tracer:
    def __init__(self):
        self.trace_id = uuid.uuid4().hex[:8]
        self.spans: list[dict] = []
        self._stack: list[dict] = []

    @contextmanager
    def span(self, name: str, **attrs):
        s = {"id": len(self.spans), "parent": self._stack[-1]["id"] if self._stack else None,
             "name": name, "attrs": attrs, "start": time.perf_counter(), "error": None}
        self.spans.append(s)
        self._stack.append(s)
        try:
            yield s
        except Exception as e:
            s["error"] = repr(e)
            raise
        finally:
            s["ms"] = (time.perf_counter() - s["start"]) * 1000
            self._stack.pop()

    def print_tree(self, parent=None, depth=0):
        for s in self.spans:
            if s["parent"] == parent:
                attrs = " ".join(f"{k}={v}" for k, v in s["attrs"].items())
                flag = f"  !! {s['error']}" if s["error"] else ""
                print(f"{'  ' * depth}{s['name']:<{22 - 2 * depth}} {s['ms']:6.1f}ms  {attrs}{flag}")
                self.print_tree(s["id"], depth + 1)


if __name__ == "__main__":
    t = Tracer()
    with t.span("agent.run", user="alice", task="refund order 881"):
        for step in (1, 2):
            with t.span("llm.call", step=step, model="claude-sonnet-5-5") as s:
                time.sleep(0.03)
                s["attrs"].update(input_tokens=1200 * step, output_tokens=80)
            try:
                with t.span("tool.call", tool="lookup_order" if step == 1 else "refund_order"):
                    time.sleep(0.01)
                    if step == 2:
                        raise TimeoutError("payments API")   # the span records the error
            except TimeoutError:
                pass                                          # the agent handles it; the trace keeps it
        with t.span("tool.call", tool="refund_order", retry=1):
            time.sleep(0.01)

    print(f"trace {t.trace_id}")
    t.print_tree()
