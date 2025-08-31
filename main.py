from fastapi import FastAPI
from graph import graph
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


class Query(BaseModel):
    message: str

app = FastAPI()

@app.post("/")
async def invoke_agent(query: Query):
    async def agent_stream(query: Query = query):
        async for chunk, _ in graph.astream(
            {"messages": [{"role": "user", "content": query.message}]},
            {"configurable": {"thread_id": "1"}},
            stream_mode="messages",
        ):
            if chunk.content:
                yield chunk.content

    return StreamingResponse(agent_stream(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

