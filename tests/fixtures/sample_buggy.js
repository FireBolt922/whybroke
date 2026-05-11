class UserService {
  getUserSync(userId) {
    return { id: userId, name: "Ada" };
  }
}

async function getUser(userId) {
  const service = new UserService();
  const userData = await service.getUserSync(userId);
  return userData;
}

function topLevelHelper() {
  const x = 1;
  const y = 2;
  return x + y;
}

getUser(1);
