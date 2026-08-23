from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from backend.agent.prompts import get_prompt
from backend.agent.tools.actions import build_prepare_action_tool
from backend.agent.tools.data_lookup import build_lookup_data_tool
from backend.agent.tools.doc_search import build_search_documents_tool
from backend.auth.mock_auth import get_user
from backend.data.structured import StructuredData
from backend.data.vectorstore import VectorStore
from backend.models.schemas import PendingAction, ToolCall

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

class ParcelPilotAgent:
    def __init__(self) -> None:
        self.llm: Any | None = None
        self.llm_config_key: str | None = None
        self.structured_data = StructuredData()
        self.vector_store = VectorStore()
        self.memories: Dict[str, ConversationBufferWindowMemory] = {}

    def _get_llm(self) -> Any:
        load_dotenv(PROJECT_ROOT / ".env", override=True)

        requested_provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if requested_provider in {"", "google", "gemini"} and google_api_key:
            model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
            config_key = f"google:{model_name}"
            if self.llm is None or self.llm_config_key != config_key:
                self.llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=google_api_key,
                    temperature=0,
                    max_output_tokens=4096,
                )
                self.llm_config_key = config_key
            return self.llm

        if requested_provider in {"", "anthropic", "claude"} and anthropic_api_key:
            model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
            config_key = f"anthropic:{model_name}"
            if self.llm is None or self.llm_config_key != config_key:
                self.llm = ChatAnthropic(
                    model=model_name,
                    temperature=0,
                    max_tokens=4096,
                )
                self.llm_config_key = config_key
            return self.llm

        if requested_provider in {"google", "gemini"}:
            raise RuntimeError(
                "GOOGLE_API_KEY is not configured. Add it to parcelpilot/.env "
                "or export it before starting the backend."
            )

        if requested_provider in {"anthropic", "claude"}:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not configured. Add it to parcelpilot/.env "
                "or export it before starting the backend."
            )

        raise RuntimeError(
            "No LLM API key is configured. Add GOOGLE_API_KEY or ANTHROPIC_API_KEY "
            "to parcelpilot/.env, then restart the backend."
        )

    def _memory_for(self, session_id: str) -> ConversationBufferWindowMemory:
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferWindowMemory(
                k=10,
                memory_key="chat_history",
                input_key="input",
                output_key="output",
                return_messages=True,
            )
        return self.memories[session_id]

    def _get_agent(self, user_id: str) -> AgentExecutor:
        user = get_user(user_id)
        if not user:
            raise ValueError("Unknown user")

        user_name = user.get("name", "Unknown")
        user_role = user.get("role", "unknown")
        snapshot_time = self.structured_data.get_dataset_snapshot_time()
        tools = [
            build_search_documents_tool(self.vector_store),
            build_lookup_data_tool(self.structured_data, user_id),
            build_prepare_action_tool(user_id),
        ]
        prompt = get_prompt(user_name, user_role, snapshot_time)
        agent = create_tool_calling_agent(self._get_llm(), tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=8,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )

    def chat(
        self,
        message: str,
        user_id: str,
        session_id: str | None = None
    ) -> Dict[str, Any]:
        if not session_id:
            session_id = str(uuid.uuid4())

        memory = self._memory_for(session_id)
        agent = self._get_agent(user_id)

        result = agent.invoke({
            "input": message,
            "chat_history": memory.load_memory_variables({}).get("chat_history", []),
        })
        response_text = result.get("output", "")
        memory.save_context({"input": message}, {"output": response_text})

        tool_calls = []
        pending_action = None

        for action, output in result.get("intermediate_steps", []):
            tool_name = getattr(action, "tool", "unknown")
            tool_input = getattr(action, "tool_input", {})
            tool_input_str = tool_input if isinstance(tool_input, str) else json.dumps(tool_input, default=str)

            tool_calls.append(ToolCall(
                tool=tool_name,
                input=tool_input_str,
                output=str(output)
            ))

            if tool_name == "prepare_action":
                try:
                    pending = json.loads(str(output))
                except json.JSONDecodeError:
                    continue
                if pending.get("status") == "pending_confirmation":
                    pending_action = PendingAction(
                        action_type=pending.get("action_type", ""),
                        payload=pending.get("payload", {}),
                        confirmation_message=pending.get("confirmation_message", ""),
                        action_id=pending.get("action_id", str(uuid.uuid4()))
                    )

        return {
            "response": response_text,
            "tool_calls": tool_calls,
            "pending_action": pending_action,
            "session_id": session_id
        }


agent = ParcelPilotAgent()


def get_agent() -> ParcelPilotAgent:
    return agent
