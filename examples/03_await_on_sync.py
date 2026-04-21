import asyncio


class UserRepo:
    def fetch(self, user_id: int) -> dict:
        return {"id": user_id, "name": "Ada"}


async def load_user(user_id: int):
    repo = UserRepo()
    user = await repo.fetch(user_id)
    return user


if __name__ == "__main__":
    asyncio.run(load_user(1))
