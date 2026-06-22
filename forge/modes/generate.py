from __future__ import annotations

from typing import Any

from forge.core.plugin import Mode, Registry
from forge.generator.engine import Engine


@Registry.register_mode
class GenerateMode(Mode):
    name = "generate"

    def run(self, records: list[dict], **kwargs) -> list[dict]:
        count = kwargs.get("count", len(records) if records else 10)
        use_llm = kwargs.get("llm", False)
        model = kwargs.get("model")
        iterations = kwargs.get("iterations", 1)

        engine = Engine()

        if records:
            engine.learn(records)

        if iterations > 1:
            return engine.self_iterate(
                count=count, iterations=iterations,
                use_llm=use_llm, model_path=model,
            )

        return engine.generate(
            count=count, use_llm=use_llm, model_path=model,
        )
