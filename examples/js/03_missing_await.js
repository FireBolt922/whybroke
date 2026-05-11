async function fetchUser(id) {
  return { id, name: "Ada" };
}

function greetUser(id) {
  const user = fetchUser(id);
  return `Hello, ${user.name.toUpperCase()}`;
}

console.log(greetUser(1));
