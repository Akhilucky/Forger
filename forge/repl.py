from __future__ import annotations

import code
import sys

banner = """
╔══════════════════════════════════════════╗
║           Forge Interactive Shell       ║
║                                          ║
║  Available:                              ║
║    pipe = Pipeline()                     ║
║    pipe.read('file.csv').run()           ║
║    pipe.apply('anonymize').run()         ║
║    pipe.write('out.json').run()          ║
║    engine = Engine()                     ║
║    engine.generate_from_spec(cols, 10)   ║
║                                          ║
║  Shortcuts:                              ║
║    read('f.csv')    → Pipeline().read()  ║
║    gen(cols, N)     → generate_from_spec ║
║    profile(recs)    → HTML profile       ║
║    diff(a, b)       → DiffReport         ║
║                                          ║
╚══════════════════════════════════════════╝
"""


def start_repl():
    from forge.core.pipeline import Pipeline
    from forge.generator.engine import Engine
    from forge.core.plugin import Registry
    from forge.profile import generate_profile
    from forge.diff import diff_datasets

    local_vars = {
        "Pipeline": Pipeline,
        "Engine": Engine,
        "Registry": Registry,
        "profile": generate_profile,
        "diff": diff_datasets,
        "read": lambda s, f=None: Pipeline().read(s, f).run(),
        "gen": lambda cols, n=10: Engine().generate_from_spec(
            [{"name": c} for c in cols] if isinstance(cols, list) and isinstance(cols[0], str) else cols, n
        ),
    }

    shell = code.InteractiveConsole(local_vars)
    shell.interact(banner=banner, exitmsg="")
