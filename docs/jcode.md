# jcode as a brain — evaluation & integration

**Verdict: integrated as an optional brain, kept off the default route until we
benchmark it.** jcode is a strong fit for where this system is going (massive
parallelism + semantic memory), but it is largely a one-person open-source
project, so we adopt it deliberately, not blindly.

## What jcode is

[jcode](https://github.com/1jehuang/jcode) (MIT) is a coding agent written in
Rust. Relevant properties for us:

- **Low footprint, fast start** — reported ~6× less RAM and far faster startup
  than Node-based agents. For a fleet of parallel workers (roadmap **A**) that
  directly raises how many we can run per machine.
- **Multi-provider** — OpenRouter, Anthropic, OpenAI/Codex, Gemini, Ollama, etc.
  It can run our **free OpenRouter** models as the workhorse and premium models
  when needed, same as OpenCode.
- **Built-in semantic memory** — aligns with the Obsidian/RAG goal (roadmap
  **G**); a candidate backend to evaluate there.
- **Headless** — `jcode run --json --quiet -p <provider> -C <dir> <message>`,
  machine-readable output. Native Windows binary (verified working on the VPS).

## Honest risks

- **Bus factor**: predominantly one maintainer. Acceptable for an *internal*
  tool (we control when we upgrade, and we can pin a binary), but we do not want
  it on the critical path until it has earned trust on real tasks.
- **Cost surprises**: if invoked without pinning a model, the provider's default
  could be a paid model. Our invoker defaults the provider to OpenRouter and the
  recommendation is to **pin a free model** in the preset before using it as a
  workhorse.
- **Telemetry**: disabled by the invoker (`JCODE_NO_TELEMETRY=1`).

## How it's wired in

- `devteam/brains/jcode.py` — invoker following the same `BrainResult` contract
  as the other brains. Headless `jcode run --json --no-update -p openrouter`,
  telemetry off, multiline-safe (native exe). A reported cost of `0.0` (free
  model) is preserved, never overwritten by an estimate.
- `config.BRAIN_JCODE` + `DEFAULT_MODELS[BRAIN_JCODE]` (default `None` → jcode's
  own default; pin a free OpenRouter slug per preset for cost safety).
- Registered in `brains.get_invoker`, so the executor/router can call it.
- `presets.backend-jcode` — an experimental worker preset.
- `devteam.cli doctor` shows an optional, non-failing jcode availability line.
- Binary resolution: `DEVTEAM_JCODE` env → `~/dev/tools/jcode.exe` → PATH.

It is **not** routed to by default and **not** used as an auditor yet.

## Next step — benchmark before promoting (roadmap H)

Run the model-evaluation harness with jcode vs OpenCode on the same set of real
backend/frontend tasks and compare **success rate, cost, latency, and RAM under
N parallel workers**. Promote jcode to a default workhorse only if it wins on
throughput-per-dollar without losing quality. Until then it is available for
opt-in use and experimentation.

```powershell
# smoke test (needs jcode's OpenRouter auth configured once):
$env:JCODE_NO_TELEMETRY = "1"
C:\Users\<user>\dev\tools\jcode.exe run --json --quiet -p openrouter -C . "print hello to stdout"
```
