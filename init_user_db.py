# init_user_db.py
import pandas as pd
import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

data = {
    'username': ['admin', 'user1', 'guest'],
    'password': ['admin', 'pass1', 'guest'],
    'role' : ['admin','user','guest']
}

df = pd.DataFrame(data)
df['password'] = df['password'].apply(hash_password)

conn = sqlite3.connect('user_data.db')
df.to_sql('users', conn, if_exists='replace', index=False)
conn.close()

print("✅ user_data.db 생성 완료!")