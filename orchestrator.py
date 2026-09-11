"""
Orchestrator: a Groq-powered LLM agent that decides which specialized tool
(diagnosis, weather, mandi price, scheme lookup, crop-input recommendation)
to call based on the farmer's natural-language message, then responds in
plain language. Supports multi-turn conversation history.
"""

import os
import re
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from weather_agent import get_forecast, compute_disease_risk
from mandi_agent import get_mandi_price
from scheme_agent import query_schemes
from medicine_db import get_crop_input_suggestion

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.4, max_tokens=500, model_kwargs={"frequency_penalty": 0.6, "presence_penalty": 0.3}, groq_api_key=os.getenv("GROQ_API_KEY"))


@tool
def check_weather_risk(latitude: float, longitude: float) -> str:
    """Check upcoming weather-based crop disease risk for a location.
    Use this when the farmer asks specifically about weather, rain, humidity, or disease risk forecasts."""
    try:
        data = get_forecast(latitude, longitude)
        risk = compute_disease_risk(data)
        city = data.get("city", {}).get("name", "your area")
        return (f"Weather risk for your location ({latitude:.4f}, {longitude:.4f}), "
                f"using data from the nearest weather station ({city}): "
                f"{risk['risk']} -- {risk['reason']}")
    except Exception as e:
        return f"Could not fetch weather data: {e}"


@tool
def check_mandi_price(commodity: str, state: str = "Uttar Pradesh") -> str:
    """Check current mandi (market) price for a crop/commodity in a given state.
    Use this when the farmer asks about prices, mandi rates, or where to sell."""
    try:
        result = get_mandi_price(commodity, state=state)
        if not result["found"]:
            return f"No recent price data found for {commodity} in {state}."
        records = result["records"][:3]
        lines = [f"{r['market']} ({r['district']}): Rs {r['modal_price']}/quintal" for r in records]
        return f"Current {commodity} prices in {state}:\n" + "\n".join(lines)
    except Exception as e:
        return f"Could not fetch mandi price: {e}"


@tool
def check_government_scheme(query: str) -> str:
    """Look up relevant government schemes for farmers based on a topic
    (e.g. insurance, credit, solar, soil testing, income support).
    Use this when the farmer asks about schemes, subsidies, loans, or government help."""
    try:
        docs = query_schemes(query, top_k=2)
        return "\n\n".join(docs)
    except Exception as e:
        return f"Could not look up schemes: {e}"


@tool
def recommend_crop_input(crop: str, need: str) -> str:
    """Recommend a specific agricultural product (herbicide, pesticide, or
    other crop input) with purchase links. Use this whenever the farmer asks
    for a specific medicine/dawa/spray/chemical/herbicide/pesticide recommendation
    for their crop -- e.g. weed control, pest control, fungal issues.
    'need' should be a short category like 'weeds', 'insects', 'fungus'.
    Always give the actual product name and link -- never defer to a doctor,
    that is for human health, not crops."""
    try:
        result = get_crop_input_suggestion(crop, need)
        if not result["found"]:
            return result["message"]
        lines = [f"- {p['product']}: {p['link']}" for p in result["products"]]
        return f"Recommended products for {need} in {crop}:\n" + "\n".join(lines) + f"\n\nUsage note: {result['note']}"
    except Exception as e:
        return f"Could not fetch product recommendation: {e}"


TOOLS = [check_weather_risk, check_mandi_price, check_government_scheme, recommend_crop_input]
llm_with_tools = llm.bind_tools(TOOLS)

SYSTEM_PROMPT = """You are KhetGPT, a knowledgeable AI agriculture advisor for Indian farmers.
You have access to tools: check_weather_risk, check_mandi_price, check_government_scheme,
and recommend_crop_input. Use the tool that matches the farmer's question. Never call any
other tool, and call each tool AT MOST ONCE per question -- once a tool returns a result,
use it to write your final answer instead of calling again.

If no tool is relevant (e.g. general farming knowledge, crop timing based on season),
answer directly from your own knowledge.

CRITICAL: You are an AGRICULTURE advisor, not a medical doctor. When a farmer asks for a
"dawa" (medicine), spray, herbicide, pesticide, or fungicide for their CROP, this is a crop
protection question -- always use recommend_crop_input and give the actual product name and
purchase link directly. NEVER tell a farmer to "consult a doctor" -- that phrase is for human
health and is never appropriate here. If asked about a diagnosed plant disease, name the
specific fungicide/pesticide directly, same as recommend_crop_input would.

Give thorough, practical answers, not one-line replies: include specific product names or
numbers, brief reasoning, and one clear next step. Aim for 4-6 sentences unless the question
is truly simple. NEVER repeat the same point, sentence, or advice more than once in your
answer -- state each fact a single time and move on. Respond in a friendly tone, in Hinglish (Hindi-English mix) unless the farmer
writes in pure English. If location or state isn't given, assume Uttar Pradesh / Lucknow and
mention that assumption.

NEVER write raw function-call syntax like <function=...></function> in your answer -- if you
need to call a tool, use the proper tool-calling mechanism, not text."""

INLINE_FUNCTION_PATTERN = re.compile(r'<function=(\w+)>\s*(\{.*?\})\s*</function>', re.DOTALL)


def chat(user_message, history=None):
    """
    history: optional list of {"role": "user"|"assistant", "content": str}
    representing prior turns in this conversation, oldest first.
    """
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if history:
        for turn in history[-10:]:  # keep last 10 turns to bound context size
            if turn.get("role") == "user":
                messages.append(HumanMessage(content=turn["content"]))
            elif turn.get("role") == "assistant":
                messages.append(AIMessage(content=turn["content"]))

    messages.append(HumanMessage(content=user_message))
    tools_by_name = {t.name: t for t in TOOLS}

    for _ in range(6):
        response = llm_with_tools.invoke(messages)
        content = response.content or ""
        inline_match = INLINE_FUNCTION_PATTERN.search(content)

        if not response.tool_calls and inline_match:
            func_name = inline_match.group(1)
            try:
                func_args = json.loads(inline_match.group(2))
            except json.JSONDecodeError:
                func_args = {}

            if func_name in tools_by_name:
                tool_output = tools_by_name[func_name].invoke(func_args)
                messages.append(HumanMessage(
                    content=f"[Tool '{func_name}' result: {tool_output}]\n\n"
                            f"Now write your final answer to the farmer's original question "
                            f"using this information. Do not include any function-call syntax."
                ))
                continue
            else:
                cleaned = INLINE_FUNCTION_PATTERN.sub('', content).strip()
                return cleaned if cleaned else "(No response generated -- please try rephrasing.)"

        if not response.tool_calls:
            if content:
                return content
            return "(No response generated -- please try rephrasing.)"

        messages.append(response)
        for tool_call in response.tool_calls:
            if tool_call["name"] not in tools_by_name:
                messages.append({"role": "tool", "content": "Unknown tool, ignore.", "tool_call_id": tool_call["id"]})
                continue
            selected_tool = tools_by_name[tool_call["name"]]
            tool_output = selected_tool.invoke(tool_call["args"])
            messages.append({"role": "tool", "content": tool_output, "tool_call_id": tool_call["id"]})

    return "(Could not complete after multiple tool calls.)"


if __name__ == "__main__":
    print(chat("mujhe apne 5 acres dhan ke khet ke liye koi aisi dawa chahiye jo ghass na ugne de"))
