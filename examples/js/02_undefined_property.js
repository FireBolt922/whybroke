const USERS = {
  ada: { email: "ada@example.com", role: "admin" },
  grace: { email: "grace@example.com", role: "user" },
};

function getEmail(username) {
  return USERS[username].email;
}

function sendWelcome(username) {
  const email = getEmail(username);
  console.log(`Sending welcome to ${email}`);
}

sendWelcome("alan");
