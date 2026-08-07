# Fraud Block Agent Demo

This safe learning project shows an agentic credit-card fraud-block workflow from a free-form customer message through independent evaluation. All customers and banking records are fictional.

The configured language model interprets the opening request and conversational replies. Authentication, ownership checks, eligibility, block removal, and final-state verification remain deterministic Python rules. The repository does not prescribe a default model provider.

## Setup

Clone the repository and enter its root directory:

```bash
git clone https://github.com/yangzh39/llm_projects.git
cd llm_projects
```

Create an isolated environment and install only this demo's dependencies:

```bash
python3 -m venv fraud_block_agent_demo/.venv
source fraud_block_agent_demo/.venv/bin/activate
python -m pip install -r fraud_block_agent_demo/requirements.txt
```

On Windows, activate the environment with `fraud_block_agent_demo\.venv\Scripts\activate`.

### Configure your model

Copy the safe configuration template to this project's private `.env` file:

```bash
cp fraud_block_agent_demo/.env.example fraud_block_agent_demo/.env
```

Every user must select a provider and model. Generic `LLM_*` variables work across all supported providers:

```text
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key
LLM_MODEL=your_model_name
```

Supported provider presets are:

| `LLM_PROVIDER` | API style | Additional configuration |
|---|---|---|
| `deepseek` | OpenAI-compatible | API key and model |
| `openai` | OpenAI-compatible | API key and model |
| `anthropic` | Anthropic Messages API | API key and model |
| `custom` | OpenAI-compatible by default | Base URL and model; API key optional |

For example, a DeepSeek user can configure:

```text
LLM_PROVIDER=deepseek
LLM_API_KEY=your_api_key
LLM_MODEL=deepseek-chat
```

An Anthropic user can configure:

```text
LLM_PROVIDER=anthropic
LLM_API_KEY=your_api_key
LLM_MODEL=your_model_name
```

For another hosted service or a local model server that exposes an OpenAI-compatible chat-completions endpoint:

```text
LLM_PROVIDER=custom
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=your_local_model
LLM_USE_JSON_MODE=false
```

Custom local endpoints may omit `LLM_API_KEY`. Set `LLM_API_STYLE=anthropic` only when a custom endpoint implements the Anthropic Messages API. Set `LLM_USE_JSON_MODE=false` when an OpenAI-compatible endpoint does not support the `response_format` parameter; the system prompt will still request JSON.

Existing repository-root DeepSeek configurations remain a backward-compatible local fallback. New users should keep configuration in `fraud_block_agent_demo/.env`. If `LLM_PROVIDER` is absent but `DEEPSEEK_API_KEY` exists, the application uses `DEEPSEEK_BASE_URL` and `DEEPSEEK_MODEL`. Generic `LLM_*` variables take precedence, and credentials are never written to traces.

## Run 1: interactive exploration

```bash
python3 fraud_block_agent_demo/explore.py
```

### Optional browser chat UI

Streamlit is included in the project requirements. Launch the browser UI with:

```bash
python -m streamlit run fraud_block_agent_demo/chat_ui.py
```

Using `python -m streamlit` avoids accidentally running a Streamlit executable from another Conda or virtual environment.

Enter any opening customer message. On every model turn, the configured model returns two separate messages:

- `human_message`: a natural response or dynamically generated clarification question for the customer.
- `chatbot_message`: hidden JSON instructions for the orchestrator or a future specialist subagent, including the goal, service, department, collected facts, and next action. This is retained internally but not displayed to the customer.

If clarification is needed, the customer's reply and conversation context go back to the configured model. The agent allows at most three model turns before transferring to a fraud specialist. The Python orchestrator validates the JSON action before doing anything.

Every conversational response is also interpreted by the configured model rather than matched against a hard-coded list. This includes routing confirmation, transfer consent, and recognition of the newest transaction. Full card numbers and DOBs are the deliberate exception: they are treated as private form fields and sent only to deterministic local authentication tools, never to the model API.

- `BLOCK_REMOVAL` continues to authentication.
- `REPORT_FRAUD` transfers directly to a mock fraud specialist and stops.
- `NON_FRAUD` explains that the Fraud Department does not handle the request, offers the appropriate department transfer, and asks whether the customer has a fraud-related need. Accepting the transfer ends the session; declining both options closes politely; stating a fraud need starts a fresh three-attempt fraud-routing chain.
- `UNCLEAR` generates a context-specific clarification question rather than routing prematurely.

After the customer confirms a block-removal interpretation, the program prompts for the full fake card number and DOB and asks the customer to recognize the most recent flagged transaction. When identity, transaction recognition, and deterministic eligibility checks pass, the block is removed immediately without another confirmation prompt. Because this is a fake-data teaching demo, credential input is visible for usability; saved traces still mask the card number and redact the DOB. The interactive script shows only customer-facing messages; structured traces are saved silently for later evaluation work.

Example opening messages:

```text
Those alert transactions were mine. Can you unblock my card?
I do not recognize this purchase. I think someone stole my card details.
Can you explain my rewards points?
```

For example, a GIC question can produce a natural offer to transfer to Investments plus this machine-readable handoff:

```json
{
  "goal": "NON_FRAUD",
  "service": "GIC rates",
  "department": "Investments",
  "understood": true,
  "next_action": "OFFER_TRANSFER_OR_FRAUD_HELP",
  "collected_facts": ["Customer asked for the current GIC rate"],
  "reason": "GIC information belongs to Investments"
}
```

## Run 2: reproducible evaluation benchmark

```bash
python3 fraud_block_agent_demo/run_evaluation.py
```

The default benchmark uses recorded model outputs, so it needs no API key and produces stable results across ten independent scenarios. A fresh in-memory mock database is loaded before every scenario. Each run saves a structured JSON report under `evaluation/outputs/` and prints these sections:

- `SCENARIO` and `AGENT RESULT`;
- `CODE CHECKS` for objective route, state, transfer, authentication, ownership, transaction, eligibility, removal, and final-state results;
- `TRACE CHECKS` for required steps, prohibited actions, and ordering constraints;
- `METRICS` for model calls, tokens, estimated cost, tool calls, clarification turns, retries, transfers, and latency;
- `OVERALL DECISION`, which fails when any required code or trace check fails.

Run one deterministic case with:

```bash
python3 fraud_block_agent_demo/run_evaluation.py --scenario successful_block_removal
```

Run exactly one bounded live model session with:

```bash
python3 fraud_block_agent_demo/run_evaluation.py --scenario successful_block_removal --live
```

Live mode requires an explicit scenario and enforces a hard maximum of 10 API calls. The full benchmark cannot be run with `--live`, preventing accidental multi-scenario API spending.

### Four evaluation methods

1. **Deterministic code checks** compare objective state and actions with scenario expectations. They answer questions such as: Was the correct card selected? Did the block-removal tool succeed? Is the final card state active?
2. **Trace-based checks** independently inspect the process. A correct final state can still fail if authentication, recognition, eligibility, or final verification occurred in the wrong order or was skipped.
3. **Operational metrics** measure API and tool usage. Recorded-model benchmark runs report token usage and cost as `None`; live runs use usage metadata returned by the configured provider when available.
4. **Validation-set execution** runs ten reusable scenarios covering success, clarification, routing, authentication failures, transaction rejection, ineligibility, and a hidden workflow failure.

### Token and API-cost calculation

Pricing is configured in `evaluation/pricing.py`, with its official source and verification date. The current configuration was verified on 2026-08-06 against DeepSeek's official pricing page. Because prices can change, verify the configuration before later use.

The live cost estimate is:

```text
cache-hit input tokens × cache-hit input rate
+ cache-miss input tokens × cache-miss input rate
+ output tokens × output rate
```

When the API does not provide the required usage metadata or the configured model has no matching price, the estimate is `None` rather than inferred. The bundled pricing table currently contains DeepSeek models only; other providers still report tokens, calls, and latency but require a pricing entry before cost can be calculated.

### Validation scenarios

The reusable set is stored in `evaluation/scenarios.json` and contains:

1. successful block removal;
2. ambiguous request requiring clarification;
3. suspected fraud;
4. non-fraud transfer;
5. incorrect-DOB authentication failure;
6. unknown-card authentication failure;
7. card/DOB mismatch treated as authentication failure;
8. transaction not recognized;
9. removal-ineligible case;
10. hidden workflow failure.

Authentication remains a single attempt by design. Invalid card, DOB, or customer combinations fail authentication, disclose no account details, and transfer to a fraud specialist.

### Core presentation example

Run the hidden failure with:

```bash
python3 fraud_block_agent_demo/run_evaluation.py --scenario hidden_workflow_failure
```

The demo-only flawed path ends with an active card and a convincing response, but the independent trace evaluator detects that an older transaction was recognized instead of the required newest transaction:

```text
CODE CHECKS:       PASS
TRACE CHECKS:      FAIL
OVERALL RESULT:    FAIL
```

Recommended live teaching sequence:

1. Run `successful_block_removal` and show both check types passing.
2. Run `hidden_workflow_failure` and compare its successful final state with the failed trace check.
3. Run the full deterministic benchmark.
4. Run one live `successful_block_removal` session and compare API cost, latency, and call counts.

## Fake customer cheat sheet

These records are intentionally fake and committed for easy live demonstrations. For eligible cases, recognize the most recent transaction and the workflow removes the block automatically after eligibility passes.

| Customer | Fake card number | DOB | Starting scenario |
|---|---:|---|---|
| Avery Example | `9000000000001001` | `1990-01-15` | Eligible, one flagged transaction |
| Jordan Sample | `9000000000002002` | `1985-02-20` | Eligible, three flagged transactions; used by hidden failure |
| Morgan Demo | `9000000000003003` | `1978-03-12` | Eligible, two transactions; say no to demonstrate reported fraud |
| Taylor Training | `9000000000004004` | `1992-04-08` | Ineligible high-value case |
| Riley Placeholder | `9000000000005005` | `1988-05-30` | Card already active; no fraud block |
| Casey Fiction | `9000000000006006` | `1975-06-17` | Ineligible because of repeated alerts |
| Jamie Sandbox | `9000000000007007` | `1995-07-22` | Eligible, one flagged transaction |
| Drew Practice | `9000000000008008` | `1982-08-11` | Eligible, two flagged transactions |
| Quinn Tutorial | `9000000000009009` | `1998-09-09` | Ineligible because replacement is pending |
| Skyler Example | `9000000000010010` | `1991-10-26` | Eligible, one flagged transaction |

Use an incorrect DOB with any card to demonstrate authentication failure. Full card numbers and DOBs are masked or redacted in terminal traces and JSON traces.

## Project structure

```text
fraud_block_agent_demo/
├── .env.example              # safe model-configuration template
├── requirements.txt          # minimal standalone dependencies
├── explore.py                 # interactive, up to three model intent calls
├── chat_ui.py                 # optional Streamlit browser chat
├── run_evaluation.py          # deterministic, API-free evaluation runner
├── deepseek_intent.py         # provider-configurable bounded model client
├── agent.py                   # workflow orchestration
├── tools.py                   # deterministic mock banking operations
├── evaluator.py               # independent trace evaluation
├── reporting.py               # terminal and JSON output helpers
├── scenarios.py               # recorded evaluation fixtures
├── evaluation/
│   ├── harness.py             # execute, reset, grade, measure, and save
│   ├── scenarios.json         # ten-scenario validation set
│   ├── trace.py               # structured privacy-aware tracing
│   ├── metrics.py             # operational metrics and cost calculation
│   ├── pricing.py             # sourced, configurable DeepSeek prices
│   ├── report.py              # concise terminal output
│   ├── graders/               # deterministic and trace-based checks
│   └── outputs/               # structured per-scenario reports
├── data/
│   ├── customers.json         # identity table
│   ├── cards.json             # card ownership and state table
│   ├── fraud_cases.json       # eligibility table
│   └── transactions.json      # flagged transaction table
├── tests/test_demo.py
├── tests/test_evaluation.py
└── traces/                    # generated structured traces
```

## Add the demo to another repository

The demo contains no nested Git repository. To copy only files currently tracked by Git—excluding your `.env`, generated artifacts, traces, caches, and local environment—run this from the source repository:

```bash
git archive HEAD fraud_block_agent_demo | tar -x -C /path/to/other-repository
```

Then review and commit the copied folder from the destination repository:

```bash
git status
git add fraud_block_agent_demo
git commit -m "Add fraud block agent demo"
```

Run regression tests with:

```bash
python3 -m unittest discover fraud_block_agent_demo/tests -v
```
