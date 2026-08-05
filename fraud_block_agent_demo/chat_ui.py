"""Simple Streamlit chat UI for the interactive fraud-block agent."""

from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import Any

import streamlit as st

from agent import FraudBlockAgent
from deepseek_intent import classify_with_deepseek, interpret_response_with_deepseek
from evaluator import evaluate
from reporting import save_trace


ROOT = Path(__file__).resolve().parent


class AgentSession:
    """Runs the blocking demo agent in a worker while Streamlit collects replies."""

    def __init__(self) -> None:
        self.inputs: queue.Queue[str] = queue.Queue()
        self.outputs: queue.Queue[dict[str, Any]] = queue.Queue()
        self.thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return bool(self.thread and self.thread.is_alive())

    def start(self, request: str) -> None:
        self.thread = threading.Thread(target=self._run, args=(request,), daemon=True)
        self.thread.start()

    def reply(self, message: str) -> None:
        self.inputs.put(message)

    def _ask(self, kind: str, context: dict[str, Any]) -> str:
        prompt = context["prompt"].strip()
        if prompt not in {"Customer:", "Customer: "}:
            prompt = prompt.removeprefix("Assistant:").strip()
            self.outputs.put({"type": "assistant", "message": prompt})
        self.outputs.put({"type": "request_input", "kind": kind})
        return self.inputs.get()

    def _present(self, human_message: str, _chatbot_message: dict[str, Any]) -> None:
        if human_message:
            self.outputs.put({"type": "assistant", "message": human_message})

    def _run(self, request: str) -> None:
        try:
            agent = FraudBlockAgent(ROOT / "data")
            result = agent.run(
                request,
                classify_with_deepseek,
                interpret_response_with_deepseek,
                self._ask,
                self._present,
            )
            self.outputs.put({"type": "assistant", "message": result["message"]})
            report = evaluate(result["trace"])
            save_trace(ROOT / "traces" / "chat_ui.json", "streamlit_chat", result["trace"], report)
            self.outputs.put({"type": "finished"})
        except Exception as error:
            self.outputs.put({"type": "error", "message": str(error)})


def initialize_state() -> None:
    if "agent_session" not in st.session_state:
        st.session_state.agent_session = AgentSession()
        st.session_state.messages = []
        st.session_state.started = False
        st.session_state.waiting_for_input = True
        st.session_state.pending_kind = "opening_message"
        st.session_state.finished = False


def drain_outputs() -> None:
    runner: AgentSession = st.session_state.agent_session
    while True:
        try:
            event = runner.outputs.get_nowait()
        except queue.Empty:
            break
        if event["type"] == "assistant":
            message = event["message"]
            if not st.session_state.messages or st.session_state.messages[-1] != {"role": "assistant", "content": message}:
                st.session_state.messages.append({"role": "assistant", "content": message})
        elif event["type"] == "request_input":
            st.session_state.pending_kind = event["kind"]
            st.session_state.waiting_for_input = True
        elif event["type"] == "finished":
            st.session_state.finished = True
            st.session_state.waiting_for_input = False
        elif event["type"] == "error":
            st.session_state.messages.append(
                {"role": "assistant", "content": f"The intent service is unavailable: {event['message']}"}
            )
            st.session_state.finished = True
            st.session_state.waiting_for_input = False


def safe_display_value(message: str, kind: str) -> str:
    if kind == "card_number":
        return f"•••• {message[-4:]}" if len(message) >= 4 else "<card number provided>"
    if kind == "date_of_birth":
        return "<date of birth provided>"
    return message


def reset_session() -> None:
    st.session_state.agent_session = AgentSession()
    st.session_state.messages = []
    st.session_state.started = False
    st.session_state.waiting_for_input = True
    st.session_state.pending_kind = "opening_message"
    st.session_state.finished = False


st.set_page_config(page_title="Fraud Block Agent", page_icon="💳", layout="centered")
initialize_state()
drain_outputs()

st.title("💳 Fraud Block Agent")
st.caption("Educational demo using fictional customer and card data only")

with st.sidebar:
    st.subheader("Demo controls")
    st.write("Use a fake profile from the project README. Card numbers and DOBs are masked in the conversation history and saved trace.")
    if st.button("Start new conversation", use_container_width=True):
        reset_session()
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if st.session_state.finished:
    st.info("This conversation has ended. Start a new conversation from the sidebar.")
elif st.session_state.waiting_for_input:
    prompt = "Describe how I can help" if not st.session_state.started else "Your response"
    if customer_message := st.chat_input(prompt):
        pending_kind = st.session_state.pending_kind
        st.session_state.messages.append(
            {"role": "user", "content": safe_display_value(customer_message, pending_kind)}
        )
        st.session_state.waiting_for_input = False
        if not st.session_state.started:
            st.session_state.started = True
            st.session_state.agent_session.start(customer_message)
        else:
            st.session_state.agent_session.reply(customer_message)
        st.rerun()

if st.session_state.started and not st.session_state.waiting_for_input and not st.session_state.finished:
    with st.spinner("Agent is thinking..."):
        time.sleep(0.25)
    st.rerun()
