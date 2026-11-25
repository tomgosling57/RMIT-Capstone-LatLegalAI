# Working Asynchronously With Fast Api
Working asynchronously with FastAPI allows a single thread to handle multiple requests without blocking the execution of code.
The asynchronous approach will be particularly useful for our use case of waiting for LLM to summarize text. By leveraging asynchronous programming, developers can enhance their application’s responsiveness and scalability, making it suitable for high-concurrency scenarios. 

Multithreading is a programming concept where multiple threads are spawned by a process to execute tasks concurrently, allowing for more efficient use of resources and improving the responsiveness of applications. Each thread runs independently but shares the same memory space of the process, which can lead to complexities such as race conditions and deadlocks.

Thread pools are a programming pattern that manage a set of worker threads, which are created and reused to perform tasks. Instead of creating a new thread for each task, a thread pool maintains a predefined number of threads and assigns tasks to available threads, helping to reduce the overhead of thread creation and destruction, improve performance, and control resource consumption.

In this document, we will explore the fundamentals of asynchronous programming in FastAPI, including how to define asynchronous routes, use asynchronous dependencies, and manage background tasks, providing a comprehensive understanding of the framework's capabilities in an asynchronous context.

## Blocking & Thread Safe Sleeping
Blocking refers to a situation where a thread cannot proceed with its execution until a particular condition is met or a resource becomes available. This can happen, for example, when a thread tries to request a resource from another API via web request, blocking code or execution until the response is received. Blocking can lead to performance issues, particularly if threads are waiting for long periods, as it can cause a slowdown in the overall system. Luckily there are specific practices and libraries that we can use to reduce this.

A thread-safe sleep mechanism is essential in multi-threaded programming to ensure that when one thread pauses for a specific duration, it does not interfere with the execution or state of other threads. This is crucial to prevent blocking and ensure proper synchronization among threads. Without a thread-safe sleep, shared resources may be accessed unpredictably, leading to bugs or inconsistent behavior in applications.

1. **The "Route Definition" Rule of Thumb**

   The most important decision is how you name your function.  
   | If your code uses...              | Use this Header | How FastAPI handles it                                |
   |-----------------------------------|------------------|------------------------------------------------------|
   | await keywords (Async DB, httpx) | async def        | Runs on the high-speed Event Loop.                   |
   | Blocking calls (requests, time.sleep) | def            | Runs in a separate Thread Pool (safe).               |
   | CPU Heavy tasks (ML, Image Processing) | def          | Runs in a Thread Pool so it doesn't freeze the loop. |

   Danger Zone: Using a blocking call (like time.sleep(1)) inside an async def function will freeze your entire server for 1 second for every user.

2. **Library Swaps (Sync vs. Async)**

   If you are moving from Flask or standard scripts, you need to swap your "tools" to their async equivalents.  
   | Category               | ❌ Blocking (Avoid in async def) | ✅ Non-Blocking (Use in async def) |
   |-----------------------|----------------------------------|------------------------------------|
   | HTTP Clients          | requests, urllib                 | httpx, aiohttp                     |
   | Database              | psycopg2, sqlite3               | asyncpg, databases, motor          |
   | Sleeping              | time.sleep()                     | await asyncio.sleep()              |
   | File I/O             | open().read()                    | anyio.Path, aiofiles              |

3. **Common Patterns & Snippets**

   A. **Calling an External API (The Right Way)**

   Use a global client to avoid the overhead of opening a new connection every time.
      from fastapi import FastAPI
   import httpx

   app = FastAPI()
   client = httpx.AsyncClient() # Create once

   @app.get("/external-data")
   async def get_data():
       # 'await' allows the loop to handle other requests while waiting
       response = await client.get("https://api.example.com/data")
       return response.json()
   

   B. **Running Tasks in the Background**

   If you want to return a "202 Accepted" immediately and do work in the background (like sending an email or generating a PDF).
      from fastapi import BackgroundTasks

   def send_email_sync(email: str):
       # Logic to send email
       pass

   @app.post("/signup")
   async def signup(email: str, background_tasks: BackgroundTasks):
       background_tasks.add_task(send_email_sync, email)
       return {"message": "Signup successful, email sending in background"}
   

4. **The "Blocking" Checklist**

   If your FastAPI app feels sluggish, check for these "Loop Killers":

   - Are you using requests? Switch to httpx.
   - Are you using a sync DB driver? Switch to an async one or use def instead of async def.
   - Are you doing heavy math? Move it to a def function or a task queue like Celery.
   - Are you using time.sleep()? Use await asyncio.sleep().

5. **Integration Testing Cheatsheet**

   Since the standard TestClient is synchronous, use httpx.AsyncClient for testing async logic.

   - Package needed: pip install pytest-asyncio httpx

   - Test Snippet:
      @pytest.mark.asyncio
   async def test_async_endpoint():
       async with AsyncClient(app=app, base_url="http://test") as ac:
           response = await ac.get("/your-route")
       assert response.status_code == 200
   