import asyncio


class UserService:
    def get_user_sync(self, user_id: int) -> dict:
        return {"id": user_id, "name": "Ada"}


async def get_user(user_id: int):
    service = UserService()
    user_data = await service.get_user_sync(user_id)
    return user_data


def top_level_helper():
    x = 1
    y = 2
    return x + y


if __name__ == "__main__":
    asyncio.run(get_user(1))
