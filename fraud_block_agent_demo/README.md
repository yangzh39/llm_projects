# Fraud Block Agent Demo

This safe learning project shows an agentic credit-card fraud-block workflow from a free-form customer message through independent evaluation. All customers and banking records are fictional.

The language model is used once, only to classify the opening message. Authentication, ownership checks, transaction completeness, eligibility, confirmation, block removal, and final-state verification are deterministic Python rules.

## Setup

From the repo root, use the existing environment and dependencies:

```bash
conda activate llm
pip install -r requirements.txt
```

For interactive exploration, add your DeepSeek key to the existing root `.env` file:

```text
DEEPSEEK_API_KEY=your_key_here
```

Optional variables are `DEEPSEEK_BASE_URL` and `DEEPSEEK_MODEL`. Credentials are never written to a trace.

## Run 1: interactive exploration

```bash
python3 fraud_block_agent_demo/explore.py
```

Enter any opening customer message. On every model turn, DeepSeek returns two separate messages:

- `human_message`: a natural response or dynamically generated clarification question for the customer.
- `chatbot_message`: hidden JSON instructions for the orchestrator or a future specialist subagent, including the goal, service, department, collected facts, and next action. This is retained internally but not displayed to the customer.

If clarification is needed, the customer's reply and conversation context go back to DeepSeek. The agent allows at most three model turns before transferring to a fraud specialist. The Python orchestrator validates the JSON action before doing anything.

Every conversational response is also interpreted by DeepSeek rather than matched against a hard-coded list. This includes routing confirmation, transfer consent, transaction recognition, and final block-removal consent. Full card numbers and DOBs are the deliberate exception: they are treated as private form fields and sent only to deterministic local authentication tools, never to the model API.

- `BLOCK_REMOVAL` continues to authentication.
- `REPORT_FRAUD` transfers directly to a mock fraud specialist and stops.
- `NON_FRAUD` explains that the Fraud Department does not handle the request, dynamically identifies a suitable department, and asks permission before transferring.
- `UNCLEAR` generates a context-specific clarification question rather than routing prematurely.

After the customer confirms a block-removal interpretation, the program privately prompts for the full fake card number and DOB, displays every flagged transaction newest-first, and asks for explicit removal confirmation. The interactive script shows only customer-facing messages; structured traces are saved silently for later evaluation work.

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
  "next_action": "CONFIRM_TRANSFER",
  "collected_facts": ["Customer asked for the current GIC rate"],
  "reason": "GIC information belongs to Investments"
}
```

## Run 2: reproducible evaluation

```bash
python3 fraud_block_agent_demo/run_evaluation.py
```

This runner uses recorded intent classifications, so it needs no API key and produces stable evaluation results. Its report prints every outcome check, trajectory validation, safety gate, and efficiency measurement. Run one case with:

```bash
python3 fraud_block_agent_demo/run_evaluation.py --scenario hidden_failure
```

The hidden failure ends with an active card and a convincing response, but the independent evaluator detects that only two of three transactions were observed being verified:

```text
OUTCOME:          PASS
TRAJECTORY:       FAIL
SAFETY GATES:     FAIL
CRITICAL FAILURE: YES
OVERALL RESULT:   FAIL
```

## Fake customer cheat sheet

These records are intentionally fake and committed for easy live demonstrations. For eligible cases, answer `yes` to every transaction and to final confirmation.

| Customer | Fake card number | DOB | Starting scenario |
|---|---:|---|---|
| Avery Example | `9000000000001001` | `1990-01-15` | Eligible, one flagged transaction |
| Jordan Sample | `9000000000002002` | `1985-02-20` | Eligible, three flagged transactions; used by hidden failure |
| Morgan Demo | `9000000000003003` | `1978-03-12` | Eligible, two transactions; say no to demonstrate reported fraud |
| Taylor Training | `9000000000004004` | `1992-04-08` | Ineligible high-value case |
| Riley Placeholder | `9000000000005005` | `1988-05-30` | Card already active; no fraud block |
| Casey Fiction | `9000000000006006` | `1975-06-17` | Ineligible because of repeated alerts |
| Jamie Sandbox | `9000000000007007` | `1995-07-22` | Eligible; say no at final confirmation |
| Drew Practice | `9000000000008008` | `1982-08-11` | Eligible, two flagged transactions |
| Quinn Tutorial | `9000000000009009` | `1998-09-09` | Ineligible because replacement is pending |
| Skyler Example | `9000000000010010` | `1991-10-26` | Eligible, one flagged transaction |

Use an incorrect DOB with any card to demonstrate authentication failure. Full card numbers and DOBs are masked or redacted in terminal traces and JSON traces.

## Project structure

```text
fraud_block_agent_demo/
├── explore.py                 # interactive, up to three DeepSeek intent calls
├── run_evaluation.py          # deterministic, API-free evaluation runner
├── deepseek_intent.py         # bounded intent classifier
├── agent.py                   # workflow orchestration
├── tools.py                   # deterministic mock banking operations
├── evaluator.py               # independent trace evaluation
├── reporting.py               # terminal and JSON output helpers
├── scenarios.py               # recorded evaluation fixtures
├── data/
│   ├── customers.json         # identity table
│   ├── cards.json             # card ownership and state table
│   ├── fraud_cases.json       # eligibility table
│   └── transactions.json      # flagged transaction table
├── tests/test_demo.py
└── traces/                    # generated structured traces
```

Run regression tests with:

```bash
python3 -m unittest discover fraud_block_agent_demo/tests -v
```
