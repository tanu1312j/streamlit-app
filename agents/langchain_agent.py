"""Build a LangChain-style agent if available, otherwise provide a
lightweight local dispatcher for testing.

This module exposes:
- build_agent(): returns an object with `.run(prompt)` or a local dispatcher
- tool_dispatch: a dict mapping tool names to callables for direct calls
"""

from pydantic import BaseModel, Field
from pydantic import ValidationError
from typing import Any, Dict

# Tools
from tools.savings_model import run_savings_model
from tools.insurance_model import run_insurance_model
from tools.realtime_advice import run_realtime_advice
from tools.rebalancer import compute_rebalance_plan


class GuardedResponse(BaseModel):
    disclaimer: str = Field(default="⚠️ Educational only. Not financial advice.")
    summary: str
    details: Dict[str, Any]


tool_dispatch = {
    "savings_model": run_savings_model,
    "insurance_model": run_insurance_model,
    "realtime_advice": run_realtime_advice,
    "rebalance_plan": compute_rebalance_plan,
}


def build_agent():
    """Try to build a LangChain agent. If LangChain/OpenAI are not
    available or not configured, return a lightweight dispatcher object
    exposing .run(text) that calls tools directly based on simple keywords.
    """
    try:
        # Import lazily to avoid hard dependency at import time
        from langchain_openai import ChatOpenAI
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain.tools import StructuredTool
        from langchain.prompts import PromptTemplate
        from langchain.output_parsers import PydanticOutputParser

        parser = PydanticOutputParser(pydantic_object=GuardedResponse)

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

        tools = [
            StructuredTool.from_function(run_savings_model, name="savings_model"),
            StructuredTool.from_function(run_insurance_model, name="insurance_model"),
            StructuredTool.from_function(run_realtime_advice, name="realtime_advice"),
            StructuredTool.from_function(compute_rebalance_plan, name="rebalance_plan"),
        ]

        sys_prompt = (
            "You are a cautious finance assistant. NEVER provide direct investment advice."
        )

        prompt_text = (
            sys_prompt
            + "\nTools:\n{tools}\n"
            + "Conversation:\n{chat_history}\n"
            + "User: {input}\n\n"
            + "{format_instructions}"
        )

        prompt = PromptTemplate.from_template(prompt_text).partial(
            format_instructions=parser.get_format_instructions()
        )

        agent = create_react_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    except Exception:
        # Fallback: simple dispatcher
        class LocalDispatcher:
            def run(self, text: str):
                # Very naive dispatch: check for keywords and run relevant tool
                txt = text.lower()
                if "save" in txt or "saving" in txt:
                    return {"output": run_savings_model}
                if "insur" in txt:
                    return {"output": run_insurance_model}
                if "rebalan" in txt or "rebalance" in txt:
                    return {"output": compute_rebalance_plan}
                if "real" in txt or "trade" in txt or "ticker" in txt:
                    return {"output": run_realtime_advice}
                return {"output": "No matching tool found"}

        return LocalDispatcher()


def safe_invoke(agent, user_input: str):
    """Invoke the agent or dispatcher and return a GuardedResponse or raw output.

    For the local dispatcher the returned value may be a direct function
    reference; callers should handle that case.
    """
    try:
        if hasattr(agent, "invoke"):
            raw = agent.invoke({"input": user_input})
            return raw
        if hasattr(agent, "run"):
            return agent.run(user_input)
        return {"error": "agent has no runnable interface"}
    except ValidationError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
