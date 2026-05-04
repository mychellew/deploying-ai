import os
import json
import gradio
from typing import List, Tuple
from langchain_openai import ChatOpenAI

# Import the services
from services.weather_api import get_weather
from services.planner_agent import plan_trip
from services.travel_rag import query_travel_info

# Initialize the model
router_llm = ChatOpenAI(
    model="gpt-4o-mini",
    base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1',
    api_key='any value',
    default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')}
)

restricted_topics = ["cats", "dogs", "horoscope", "zodiac", "taylor swift"]

# -------------------------
# GUARDRAILS
# -------------------------
def check_guardrails(user_input: str) -> str:
    lower_input = user_input.lower()
    for topic in restricted_topics:
        if topic in lower_input:
            return "Sorry, I cannot discuss that topic. Let's plan your trip to Canada instead!"
    
    # basic prompt injection protection
    if any(x in lower_input for x in ["system prompt", "ignore previous instructions", "reveal instructions"]):
        return "Sorry, I can’t share or modify my internal instructions."

    return None

# -------------------------
# FUNCTION CALLING ROUTER
# -------------------------
def function_call_router(user_input: str, history: List[Tuple[str, str]]) -> str:
    context = f"Previous Bot Message: {history[-1][1]}\n" if history else ""

    prompt = f"""
    Context: {context}
    User Input: {user_input}

    Decide which function to call.

    Available functions:
    - get_weather: ONLY for current, real-time weather information about a city
    - plan_trip: For itinerary or travel planning
    - travel_info: For general travel information about cities, if the user is asking about a specific destination or travel tips
        If the user is asking for general climate, historical weather patterns

    Return ONLY a JSON object like:
    {{"function": "get_weather"}}

    Valid values:
    get_weather, plan_trip, travel_info
    """

    try:
        response = router_llm.invoke(prompt).content.strip()
        data = json.loads(response)

        return data.get("function", "travel_info")

    except:
        # fallback logic
        lower = user_input.lower()
        if "weather" in lower:
            return "get_weather"
        if "plan" in lower or "itinerary" in lower:
            return "plan_trip"
        return "travel_info"

# -------------------------
# MAIN CHAT FUNCTION
# -------------------------
def travel_buddy_chat(user_input: str, history: List[Tuple[str, str]]):
    # Guardrails
    guardrail_response = check_guardrails(user_input)
    if guardrail_response:
        history.append((user_input, guardrail_response))
        return history, history

    # Function calling router
    function_name = function_call_router(user_input, history)

    try:
        if function_name == "get_weather":
            raw_weather = get_weather(user_input)

            # Rewrite using LLM (tone + compliance)
            response = router_llm.invoke(
                f"Rewrite this weather info in a friendly Canadian travel assistant tone:\n{raw_weather}"
            ).content

        elif function_name == "plan_trip":
            response = plan_trip(user_input)

        else:
            response = query_travel_info(user_input)

    except Exception as e:
        response = f"Sorry, there was an error processing your request: {str(e)}"

    history.append((user_input, response))
    return history, history

# -------------------------
# CLEAR CHAT
# -------------------------
def clear_chat():
    return [], []

# -------------------------
# UI SETUP
# -------------------------
with gradio.Blocks() as demo:
    gradio.Markdown(
        '''
        # 🇨🇦 Travel Buddy Chat: Your AI Travel Assistant!
        Ask me about:
            - Weather forecasts
            - Trip itineraries
            - General city information
        '''
    )

    chatbot = gradio.Chatbot(type="tuples")
    user_input = gradio.Textbox(placeholder="Ask me about your travel plans!")

    with gradio.Row():
        submit_btn = gradio.Button("Submit", variant="primary")
        clear_btn = gradio.Button("Clear Chat")

    submit_btn.click(
        travel_buddy_chat,
        inputs=[user_input, chatbot],
        outputs=[chatbot, chatbot]
    ).then(lambda: "", None, user_input)

    clear_btn.click(clear_chat, outputs=[chatbot, chatbot])

if __name__ == "__main__":
    demo.launch()