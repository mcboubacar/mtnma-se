#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 13 10:31:29 2025

@author: mboubacar
"""

import json
from hashlib import sha256

USERS_FILE = "config/users.json"

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def authenticate(username, password):
    users = load_users()
    hashed = hash_password(password)
    return users.get(username) == hashed

def add_user(username, password):
    users = load_users()
    users[username] = hash_password(password)
    save_users(users)

def delete_user(username):
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
