    

import json
import os
from datetime import datetime

USERS_FILE = "data/users.json"

# Ensure file exists
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)  # Empty dict

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def user_exists(user_id):
    users = load_users()
    return user_id in users

def create_user(user_id, name):
    users = load_users()
    users[user_id] = {
        "name": name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_users(users)

def login_user(user_id):
    users = load_users()
    return users.get(user_id, None)
