from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from dataclasses import dataclass
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


@dataclass
class MyState:
    topic: str
    joke: str = ""


model = init_chat_model(model="gpt-4o-mini")

def call_model(state: MyState):
    """Call the LLM to generate a joke about a topic"""
    # Note that message events are emitted even when the LLM is run using .invoke rather than .stream
    model_response = model.invoke(  
        [
            {"role": "user", "content": f"Generate a joke about {state.topic} for about 10 sentences."}
        ]
    )
    return {"joke": model_response.content}

graph = (
    StateGraph(MyState)
    .add_node(call_model)
    .add_edge(START, "call_model")
    .compile()
)

# The "messages" stream mode returns an iterator of tuples (message_chunk, metadata)
# where message_chunk is the token streamed by the LLM and metadata is a dictionary
# with information about the graph node where the LLM was called and other information
for message_chunk, metadata in graph.stream(
    {"topic": "ice cream"},
    stream_mode="messages",  
):
    if message_chunk.content:
        print(message_chunk.content, end="", flush=True)

# class State(TypedDict):
#     topic: str
#     joke: str

# def refine_topic(state: State):
#     return {"topic": state["topic"] + " and cats"}

# def generate_joke(state: State):
#     return {"joke": f"This is joke about {state['topic']}"}

# graph = (
#     StateGraph(state_schema=State)
#     .add_node(refine_topic)
#     .add_node(generate_joke)
#     .add_edge(START, "refine_topic")
#     .add_edge("refine_topic", "generate_joke")
#     .add_edge("generate_joke", END)
#     .compile()
# )

# # The stream() method returns an iterator that yields streamed outputs
# for chunk in graph.stream(
#     {"topic": "ice cream"},
#     stream_mode="updates",
# ):
#     print(chunk)