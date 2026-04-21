"""Demo bug #1: awaiting a synchronous function — the classic FastAPI/Starlette trap.

Run:  python scripts/demo_bugs/01_fastapi_async.py 2>&1 | whybroke
"""

import asyncio


class UserRepo:
    def get_by_id_sync(self, user_id: int) -> dict:
        return {"id": user_id, "name": "Ada Lovelace"}


async def get_user(user_id: int):
    repo = UserRepo()
    # BUG: get_by_id_sync is a normal function, not a coroutine.
    # await on a dict raises TypeError: object dict can't be used in 'await' expression
    user = await repo.get_by_id_sync(user_id)
    return user


if __name__ == "__main__":
    asyncio.run(get_user(1))
