# Static checks

Run both before any packaging or release. They are fast and catch the
failure classes that cost eight Odoo runs during the 18.0 consolidation.

```
python3 tools/layercheck.py  modules
python3 tools/importcheck.py modules
```

- **layercheck.py** — for every module, resolves its dependency closure and
  flags any model used via `env['...']` or any `type="object"` button method
  that is defined outside it. Catches a file placed in a module that loads
  before the module providing what it needs.
- **importcheck.py** — verifies every `from odoo.addons.X.Y import Z` and
  `from .Y import Z` resolves: the file exists *and* actually defines the
  imported name. Catches imports left behind when a file is renamed.

Neither replaces running the suite. Both passed clean on builds that the
Odoo run then rejected — they are a fast pre-filter, not the gate.
The gate is `docs/TEST_REPORT_*.md`.
