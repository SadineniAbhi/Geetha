import asyncio
from graph import graph
async def main():
    config = {"configurable": {"thread_id": "1"}}
    try:
        async for chunk, metadata in graph.astream(
            {"messages": [{"role": "user", "content": "Hello tell me about the story of Rome and the weather in London"}]},
            config,
            stream_mode="messages",
        ):
            if chunk.content:
                print(chunk.content, end="", flush=True)
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
