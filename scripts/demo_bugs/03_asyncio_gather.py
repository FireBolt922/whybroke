"""Demo bug #3: asyncio.gather called with a list of coroutines-inside-a-list.

Run:  python scripts/demo_bugs/03_asyncio_gather.py 2>&1 | whybroke
"""

import asyncio


async def fetch(n: int) -> int:
    await asyncio.sleep(0.01)
    return n * 2


async def run_all():
    tasks = [fetch(i) for i in range(5)]
    # BUG: passing a list to gather instead of unpacking it with *tasks.
    # Raises TypeError: An asyncio.Future, a coroutine or an awaitable is required.
    results = await asyncio.gather(tasks)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
