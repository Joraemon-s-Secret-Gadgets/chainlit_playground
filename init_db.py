import sqlite3

def init_db():
    print("⏳ 데이터베이스 초기화를 시작합니다...")
    conn = sqlite3.connect('local_chat_history.db')
    cursor = conn.cursor()
    
    # 꼬여있을 수 있는 기존 테이블 삭제
    tables = ['feedbacks', 'elements', 'steps', 'threads', 'users']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
    # Chainlit 로그에 맞춘 완벽한 테이블 생성
    cursor.execute('''
        CREATE TABLE users (
            "id" TEXT PRIMARY KEY,
            "identifier" TEXT NOT NULL UNIQUE,
            "metadata" TEXT NOT NULL,
            "createdAt" TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE threads (
            "id" TEXT PRIMARY KEY,
            "createdAt" TEXT,
            "name" TEXT,
            "userId" TEXT,
            "userIdentifier" TEXT,
            "tags" TEXT,
            "metadata" TEXT,
            FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE steps (
            "id" TEXT PRIMARY KEY,
            "name" TEXT NOT NULL,
            "type" TEXT NOT NULL,
            "threadId" TEXT NOT NULL,
            "parentId" TEXT,
            "disableFeedback" BOOLEAN,
            "streaming" BOOLEAN,
            "waitForAnswer" BOOLEAN,
            "isError" BOOLEAN,
            "metadata" TEXT,
            "tags" TEXT,
            "input" TEXT,
            "output" TEXT,
            "createdAt" TEXT,
            "start" TEXT,
            "end" TEXT,
            "generation" TEXT,
            "showInput" TEXT,
            "language" TEXT,
            "indent" INTEGER,
            "defaultOpen" BOOLEAN,
            "autoCollapse" BOOLEAN,
            FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE elements (
            "id" TEXT PRIMARY KEY,
            "threadId" TEXT,
            "type" TEXT,
            "url" TEXT,
            "chainlitKey" TEXT,
            "name" TEXT NOT NULL,
            "display" TEXT,
            "objectKey" TEXT,
            "size" TEXT,
            "page" INTEGER,
            "language" TEXT,
            "forId" TEXT,
            "mime" TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE feedbacks (
            "id" TEXT PRIMARY KEY,
            "forId" TEXT NOT NULL,
            "threadId" TEXT NOT NULL,
            "value" INTEGER NOT NULL,
            "comment" TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("초기화 및 최신 테이블 생성 완료!")

if __name__ == '__main__':
    init_db()