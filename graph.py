from typing import Annotated
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
llm = ChatOpenAI(
    api_key= "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",
    base_url="https://openrouter.ai/api/v1",
    model="gpt-4o-mini",

)
class State(TypedDict):
    content_from_rag: str
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

def getWeather(city: str)->str:
    '''return the weather of the city'''
    return f"It is sunny in {city}."

llm_with_tools = llm.bind_tools([getWeather])

async def ragnode(state: State):
    # mock RAG node
    # hitrag(state['messages'])
    return {"content_from_rag": "Abhijeeth is an btech student who studying gokaraju rangaraju institute of technoloy and getting his major in ai/ml he also expert in data engineering."}

async def chatbot(state: State):
    system_message = {
        "role": "system",
        "content": "you are a helpful assistant that helps the user.",
    }
    return {"messages": [await llm_with_tools.ainvoke([system_message, state["content_from_rag"]] + state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("rag_node", ragnode)
tool_node = ToolNode(tools=[getWeather])
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge("rag_node", "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("rag_node")
memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)


