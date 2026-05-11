type User = { id: number; name: string };

class UserService {
  getUserSync(userId: number): User {
    return { id: userId, name: "Ada" };
  }
}

async function getUser(userId: number): Promise<User> {
  const service = new UserService();
  const userData: User = await service.getUserSync(userId);
  return userData;
}

getUser(1);
