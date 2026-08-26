# Using Open-Weight Models as Codex-Style Coding Agents

**Last source verification:** 2026-08-11  
**Project boundary:** these agents may staff Research, Engineering, and
Validation. They must never be imported by or credentialed inside allocation,
risk, execution, reconciliation, or `src/fund/runtime/`.

## The practical recommendation

Use hosted APIs first. For this fund, the clean initial split is:

| Desk | Model and harness | Why |
|---|---|---|
| Engineering | DeepSeek V4 Flash through Codex CLI | DeepSeek's Responses API is directly compatible with the protocol current Codex uses. |
| Validation | Kimi K3 through Kimi Code or OpenCode | Different model vendor and a separate agent harness; no protocol translator is needed. |
| Research | Kimi K3 through Kimi Code/OpenCode, in a result-blind workspace | Strong long-context research path, kept physically separate from evaluation outputs. |

DeepSeek V4 Pro currently supports Chat Completions and Anthropic-compatible
traffic, but the current DeepSeek model table does not list Responses API
support for Pro. Use V4 Flash for direct Codex integration; use V4 Pro through
OpenCode or Claude Code. Kimi's general Open Platform exposes OpenAI-compatible
**Chat Completions**, while current Codex custom providers require
**Responses**. That is why Kimi-in-Codex needs a translator and is not the
recommended Kimi path.

An “open-weight model” and a “coding agent” are different layers:

1. The weights are the neural model.
2. A server such as the vendor API, vLLM, or SGLang exposes an HTTP protocol.
3. The agent harness supplies repository context, tool schemas, the
   model/tool/result loop, approvals, patch application, and session memory.
4. Your governance decides what the agent may see and do.

Using DeepSeek's or Kimi's hosted API does not self-host the weights: source
code and prompts leave your machine for that provider. “Open weight” also does
not guarantee an OSI-approved license; inspect each model's license before
commercial self-hosting.

## Prerequisites and secret handling

Install the agent harnesses you intend to use, create separate provider
accounts, and set small account-level spend limits. Keep provider keys out of
this repository, screenshots, shell history, and logs.

For a temporary zsh session, read a secret without echoing it:

```zsh
read -s "DEEPSEEK_API_KEY?DeepSeek API key: "
echo
export DEEPSEEK_API_KEY
```

Use the same pattern with `MOONSHOT_API_KEY`. Do not place either key in a
project `.env` file. Never expose an IBKR username, password, access token,
account number, live order endpoint, or live P&L to a coding agent. The broker
adapter will be deterministic code and tested with paper credentials outside
the agent environment.

Start every agent in a dedicated branch or worktree. Keep approvals enabled,
inspect the diff, and run tests independently before accepting a change.

## Route A — DeepSeek V4 Flash directly through Codex CLI

DeepSeek documents a native Responses endpoint for V4 Flash. Current Codex
supports custom providers through a user-level profile and reads the key from
the environment. Create `~/.codex/deepseek-v4.config.toml`:

```toml
model = "deepseek-v4-flash"
model_provider = "deepseek"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[model_providers.deepseek]
name = "DeepSeek"
base_url = "https://api.deepseek.com"
env_key = "DEEPSEEK_API_KEY"
wire_api = "responses"
```

Do not copy DeepSeek's example `experimental_bearer_token` into the file.
Codex's current configuration reference explicitly discourages a literal
bearer token and supports `env_key` for this purpose.

Launch an interactive session or a bounded one-shot task:

```zsh
cd /Users/kroixjones/Documents/prop_trading_bot
codex --profile deepseek-v4

codex exec --profile deepseek-v4 \
  "Read AGENTS.md and implement only the named frozen task; run its focused tests."
```

Profile files require Codex 0.134.0 or later. If `codex --profile deepseek-v4`
does not load the file, update Codex and confirm the filename is exactly
`~/.codex/deepseek-v4.config.toml`. Do not put provider configuration in the
repository's `.codex/config.toml`; Codex deliberately ignores machine-local
provider and authentication settings there.

First perform a harmless tool round-trip: ask the agent to read one file, make
a one-line change on a disposable branch, show the diff, run one focused test,
and revert only its own change. Confirm the provider dashboard records the
request and that no key appears in the transcript.

### DeepSeek V4 Pro with Claude Code

If Claude Code is already installed, DeepSeek publishes an
Anthropic-compatible endpoint. Run it in a subshell so the provider overrides
do not leak into unrelated sessions:

```zsh
(
  export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
  export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"
  export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
  export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
  export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
  export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
  export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
  export CLAUDE_CODE_EFFORT_LEVEL="max"
  cd /Users/kroixjones/Documents/prop_trading_bot
  claude
)
```

This uses Claude Code as the harness, not an Anthropic model. Compatibility
endpoints can lag native features, so repeat the tool/edit/test smoke test after
every harness or provider upgrade.

## Route B — Kimi K3 through Kimi Code

Kimi Code is Moonshot's MIT-licensed, open-source terminal agent. It can read
and edit repositories, run commands, use MCP, launch subagents, and expose an
ACP endpoint to compatible editors. The official binary installer does not
require Node.js.

For a security-conscious install, download and inspect the official installer
before running it:

```zsh
installer_path="${TMPDIR:-/tmp}/kimi-code-install.sh"
curl -fsSL https://code.kimi.com/kimi-code/install.sh -o "$installer_path"
less "$installer_path"
bash "$installer_path"
kimi --version
```

Then:

```zsh
cd /Users/kroixjones/Documents/prop_trading_bot
kimi
```

Inside Kimi Code, run `/login` and choose **Moonshot AI Open Platform API
key**. Start with a read-only repository explanation, then the same disposable
edit/test smoke test used for DeepSeek. The older `MoonshotAI/kimi-cli` project
is winding down in favor of Kimi Code; do not start a new integration on the
older CLI.

## Route C — Run either provider through OpenCode

[OpenCode](https://github.com/anomalyco/opencode) is an MIT-licensed,
provider-neutral coding agent. This is the simplest common harness when you
want a fair DeepSeek-versus-Kimi comparison.

Install on macOS:

```zsh
brew install anomalyco/tap/opencode
opencode --version
```

For Kimi K3:

```zsh
opencode auth login
# Select: Moonshot AI; paste the Kimi Open Platform key.
cd /Users/kroixjones/Documents/prop_trading_bot
opencode
# In the UI: /models -> Kimi K3
# Then:      /variants -> max (or high for lower latency)
```

For DeepSeek, repeat `opencode auth login`, select DeepSeek, and select
`deepseek-v4-pro` or `deepseek-v4-flash` from `/models`. Provider menus and
model catalogs change, so verify the exact model ID in both the status bar and
provider usage dashboard rather than trusting a friendly display name.

For an A2 validation pass, give the second agent the frozen requirement, diff,
and test output—not the writer agent's hidden reasoning or conclusions. Use a
fresh session and separate provider. Its brief should be adversarial: “Assume
this is wrong; find the bug and explain why apparently good results may be
false.”

## Adapting another open-weight model

Identify the **served protocol**, not just the model name:

| Provider endpoint | Best first harness |
|---|---|
| OpenAI Responses-compatible | Codex custom provider |
| OpenAI Chat Completions-compatible | OpenCode, Kimi Code, or Aider |
| Anthropic Messages-compatible | Claude Code with provider overrides |
| Local Ollama or LM Studio | Codex's built-in local-provider mode, or OpenCode |
| Raw weights only | Deploy vLLM/SGLang first, then treat its endpoint as a new provider |

For another Responses-compatible host, clone the DeepSeek profile and replace
only these values:

```toml
model = "<exact-model-id>"
model_provider = "my-provider"

[model_providers.my-provider]
name = "My provider"
base_url = "https://provider.example/api"
env_key = "MY_PROVIDER_API_KEY"
wire_api = "responses"
```

Do not point Codex directly at a Chat Completions-only URL and assume
“OpenAI-compatible” is sufficient. Codex currently sends Responses objects;
the protocol mismatch appears during streaming and tool calls even when a
simple text request seems to work. Prefer a harness that natively speaks Chat
Completions before introducing a translation proxy.

## Optional — Kimi K3 inside Codex through a translator

Kimi's official Codex guide uses
[CC Switch](https://platform.kimi.ai/docs/guide/codex-kimi), a third-party local
router that translates Codex Responses traffic to Kimi Chat Completions. It
works around a real protocol mismatch, but the router processes the API key,
prompts, tool calls, source, and responses. For fund work, prefer Kimi Code or
OpenCode until Kimi provides a native Responses endpoint. If you still use CC
Switch, pin and review its source/release, bind the listener to localhost,
disable request-body logging, use a low-limit key, and repeat the golden tool
tests after every update.

## What the open-source projects teach us

The useful implementations converge on the same loop:

```text
user task + repository instructions
              |
              v
       model response
        /          \
 final text      structured tool call
                    |
             policy + approval
                    |
        read/search/patch/fixed test
                    |
              tool result
                    |
              next model turn
```

- Codex and OpenCode provide sandbox/approval modes and repository guidance.
- Kimi Code adds hooks, MCP, subagents, and editor integration while retaining
  the same model/tool/result loop.
- [Aider](https://github.com/Aider-AI/aider) is a mature, simpler alternative
  with repository maps, Git-native edits, and automatic lint/test hooks.
- DeepSeek and Kimi both require correct preservation of assistant reasoning
  and tool-call history across turns. A generic “OpenAI-compatible” label does
  not prove that a long agentic tool loop is correct.

If you build a small custom harness, use the official OpenAI SDK against each
vendor's Chat Completions endpoint and preserve the returned assistant object
intact. The irreducible loop is:

```python
from openai import OpenAI

client = OpenAI(api_key=api_key, base_url=base_url)
messages = [{"role": "user", "content": task}]

for _ in range(max_turns):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tool_schemas,
        extra_body={"thinking": {"type": "enabled"}},
    )
    reply = response.choices[0].message
    messages.append(reply.model_dump(exclude_none=True))
    if not reply.tool_calls:
        break
    for call in reply.tool_calls:
        result = validate_approve_and_dispatch(call)
        messages.append(
            {"role": "tool", "tool_call_id": call.id, "content": result}
        )
```

That snippet is architectural, not production-ready. A safe implementation
still needs: schema validation; repository-root path containment; symlink
defense; output and context limits; timeouts; retries with idempotency; an
approval UI; redaction; audit logs; and a fixed command allowlist. Do not expose
an unrestricted shell. Start with four tools—read file, `rg` search,
`apply_patch`, and named test targets—and let deterministic code enforce every
permission.

For Kimi and DeepSeek thinking-mode tool calls, retaining the complete
assistant message is particularly important because it may contain
provider-specific reasoning state alongside `tool_calls`. Reconstructing only
the visible text and calls can cause a later request to fail or behave
differently.

## Why not self-host these weights yet?

Self-hosting is possible but not economical on this development Mac. Current
deployment reports put DeepSeek V4 Flash around four B200/B300 GPUs and V4 Pro
around eight; Kimi K3's easiest path is eight B300/MI355X GPUs, with a reported
minimum of sixteen B200s. Those are data-center deployments, not laptop
deployments. Hosted APIs let M0/M1 validate the workflow before committing to
GPU rental and inference operations.

If self-hosting later becomes justified, use the model publishers' vLLM or
SGLang recipes, pin model revision and serving image digest, record quantization
and tensor-parallel settings, expose only an authenticated private endpoint,
and rerun the same golden agent-tool suite. Treat a self-hosted endpoint as a
new provider: it does not inherit validation from the hosted API.

## Acceptance checklist for every model/harness pair

1. Record provider, exact model ID, harness version/commit, endpoint protocol,
   reasoning mode, and date.
2. Confirm the secret is absent from Git, config files, process output, and
   transcripts.
3. Prove read, search, patch, and focused-test tool round-trips on a disposable
   branch.
4. Prove a denied path and a denied command are actually blocked.
5. Test a deliberately failing command, malformed tool call, timeout, rate
   limit, and interrupted stream.
6. Confirm tool-call and reasoning history survives at least twenty turns and
   one context compaction.
7. Set account budget/rate limits and inspect provider usage after the run.
8. Review the complete diff and rerun tests outside the agent session.
9. Scan the `src/fund/runtime/` dependency closure and environment; no model
   client or credential may cross A1.
10. Have a different-vendor validator challenge the implementation before it
    becomes a trusted workflow.

## Primary sources and reference implementations

- [Codex advanced configuration and custom providers](https://learn.chatgpt.com/docs/config-file/config-advanced#custom-model-providers)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [DeepSeek Responses API](https://api-docs.deepseek.com/guides/responses_api/)
- [DeepSeek models and current protocol support](https://api-docs.deepseek.com/quick_start/pricing/)
- [DeepSeek agent integrations](https://api-docs.deepseek.com/guides/coding_agents)
- [DeepSeek V4 Flash weights and model card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash)
- [Kimi API overview](https://platform.kimi.ai/docs/api/overview)
- [Kimi tool-use protocol](https://platform.kimi.ai/docs/api/tool-use)
- [Kimi K3 with OpenCode](https://platform.kimi.ai/docs/guide/open-code)
- [Kimi K3 with Codex and CC Switch](https://platform.kimi.ai/docs/guide/codex-kimi)
- [Kimi Code source](https://github.com/MoonshotAI/kimi-code)
- [Kimi K3 weights, serving recipes, and license](https://github.com/MoonshotAI/Kimi-K3)
- [OpenCode source](https://github.com/anomalyco/opencode)
- [Aider source](https://github.com/Aider-AI/aider)
- [vLLM DeepSeek V4 deployment report](https://github.com/vllm-project/vllm-project.github.io/blob/main/_posts/2026-04-24-deepseek-v4.md)
- [vLLM Kimi K3 deployment report](https://github.com/vllm-project/vllm-project.github.io/blob/main/_posts/2026-07-27-k3.md)
