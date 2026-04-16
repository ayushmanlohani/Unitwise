import asyncio
import httpx

async def test():
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", "http://127.0.0.1:8000/api/v1/ask", json={
            "query": "What is TCP?",
            "subject": "CN",
            "chat_history": []
        }) as response:
            print(f"STATUS: {response.status_code}")
            last_chunks = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    last_chunks.append(line)
                    if len(last_chunks) > 5:
                        last_chunks.pop(0)
            print(f"\n--- LAST 5 CHUNKS ---")
            for c in last_chunks:
                print(c)

asyncio.run(test())
