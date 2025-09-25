from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
from pydantic import BaseModel, Field
from typing import Optional

load_dotenv ()  # take environment variables from .env. (reading)

client = OpenAI()


def get_weather(city: str):
    url = f"https://wttr.in/{city.lower()}?format=%C+%t"
    response  = requests.get(url)

    if response.status_code == 200:
        return f"Weather in {city} is {response.text}"
    
    return "Something went wrong"

available_tools = {
    "get_weather": get_weather
}


SYSTEM_PROMPT = """
    You're an expert AI Assistant in resolving user queries using chain of thoughts prompting
    You work on START, PLAN and OUTPUT steps.
    You need to first PLAN what needs to be done. The PLAN can be multiple steps.
    Once you think enough PLAN has been done, finally you can give an OUTPUT.
    You can also call a tool if required from the list of available tools.
    for every tool call wait for the observe step which is the output from the called tool.


    Rules:
    - Strictly Follow the given JSON output format.
    -Only run one step at a time.
    -The sequence of steps is START (where user gives an input), PLAN (That can be multiple times) and finally OUTPUT (which is going to be displayed by the user)

    Output JSON Format:
    { "step": "START" | "PLAN" | "OUTPUT" | "TOOL", "content": "string", "tool": "string", "input": "string" }
   
    Available Tools:
    - get_weather(city: str): Gets the current weather of the specified city.

     
    Example 1:
    START: Hey, Can you solve 2+3*5 / 10
    PLAN: { "step": "PLAN": "content": "Seems like an interested in math problem" }
    PLAN: { "step": "PLAN": "content": "According to BODMAS, I need to first solve 3*5" }
    PLAN: { "step": "PLAN": "content": "3*5 = 15" }
    PLAN: { "step": "PLAN": "content": "Now the equation becomes 2 + 15 / 10" }

    Example 2:
    START: What is weather of Delhi?
    PLAN: { "step": "PLAN": "content": "Seems like user is interested in getting weather of Delhi" }
    PLAN: { "step": "PLAN": "content": "Lets see if we have any available tool from the list of available tools " }
    PLAN: { "step": "PLAN": "content": Great, we have get_weather tool for delhi as input for city" }
    PLAN: { "step": "TOOL": "tool": "get_weather", "output": "The temp of delhi is cloudy with 20" }
    PLAN: {"step": "OBSERVE": "tool": "get_weather", "output": "Weather in Delhi is Partly cloudy +30°C" }
    PLAN: {"step": "PLAN": "content": "Got the output from the tool get_weather"}
    OUTPUT: { "step": "OUTPUT", "content": "The current weather in delhi is 20 c with some cloudy" }

    
    
    """
print("\n\n\n")

class MyOutputFormat(BaseModel):
    step: str = Field(..., description="The ID of the step. Example: PLAN, OUTPUT, TOOL, etc")
    content: Optional[str] = Field(None, description="Optional string content for the step")
    tool: Optional[str] = Field(None, description="ID of the tool to call")
    input: Optional[str] = Field(None, description="Input params for the tool")


message_history = [
    {"role": "system", "content": SYSTEM_PROMPT },
]
 #while True:
user_query = input("👉🏻")
message_history.append({ "role": "user", "content": user_query })
   

while True:
    response = client.chat.completions.parse(
        model="gpt-4o",
        response_format=MyOutputFormat,
        messages=message_history
    )

    raw_result = response.choices[0].message.content

    message_history.append({ "role": "assistant", "content": raw_result })
    
    parsed_result = response.choices[0].message.parsed


    if parsed_result.step == "START":
        print("🤖", parsed_result.content)
        continue
   
    if parsed_result.step == "TOOL":
       tool_to_call = parsed_result.tool
       tool_input = parsed_result.input
       print(f"☠️: {tool_to_call} ({tool_input})")

       tool_response = available_tools[tool_to_call](tool_input)
       message_history.append({"role": "developer", "content": json.dumps(
           {"step": "OBSERVE", "tool": tool_to_call, "input": tool_input, "output": tool_response}
       )})
       continue

    if parsed_result.step == "PLAN":
        print("🤖", parsed_result.content)
        continue

    if parsed_result.step == "OUTPUT":
        print("🤖", parsed_result.content)
        break 

print("\n\n\n")


