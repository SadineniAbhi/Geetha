import asyncio
from graph import graph

async def test_agent():
    """Simple test of the LangGraph agent"""
    print("Testing LangGraph agent...")
    
    # Test message
    test_message = "Hello! What's the weather like in New York?"
    print(f"Input: {test_message}")
    print("Response: ", end="")
    
    # Stream response from agent
    async for chunk, _ in graph.astream(
        {"messages": [{"role": "user", "content": test_message}]},
        {"configurable": {"thread_id": "test_session"}},
        stream_mode="messages",
    ):
        if chunk.content:
            print(chunk.content, end="", flush=True)
    
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_agent())
