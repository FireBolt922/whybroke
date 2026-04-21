USERS = {
    "ada": {"email": "ada@example.com", "role": "admin"},
    "grace": {"email": "grace@example.com", "role": "user"},
}


def get_email(username):
    return USERS[username]["email"]


def send_welcome(username):
    email = get_email(username)
    print(f"Sending welcome to {email}")


if __name__ == "__main__":
    send_welcome("alan")
