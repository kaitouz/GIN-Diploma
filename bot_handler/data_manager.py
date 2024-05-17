import sqlite3
import os
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Database_manager:

    def __init__(self):
        self.conn = sqlite3.connect('Database/database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
                                user_id TEXT PRIMARY KEY, 
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Photos (
                                photo_id TEXT PRIMARY KEY,
                                user_id TEXT,
                                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES Users(user_id)
                            )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Prompts (
                                prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id TEXT,
                                prompt_text TEXT,
                                message_id TEXT,
                                rating INTEGER,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES Users(user_id)
                            )''')
        
    # ==== Users ====
    def check_user_exists(self, user_id):
        self.cursor.execute("SELECT COUNT(*) FROM Users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] > 0

    def create_user_id(self, user_id):
        self.cursor.execute("INSERT INTO Users (user_id) VALUES (?)", (user_id,))
        self.conn.commit()

    # ==== Images ====
    def get_uploads_by_user_id(self, user_id):
        self.cursor.execute('SELECT photo_id FROM Photos WHERE user_id=?', (user_id,))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []


    def create_upload_by_user_id(self, photo_id, user_id):
        self.cursor.execute('INSERT INTO Photos (photo_id, user_id) VALUES (?, ?)', (photo_id, user_id))
        self.conn.commit()

    def delete_photo_by_user_id(self, photo_id):
        self.cursor.execute("DELETE FROM Photos WHERE photo_id=?", (photo_id, ))
        self.conn.commit()

    # ==== Prompts ====
    def create_prompt_by_user_id(self, user_id, mesaage_id, prompt_text):
        self.cursor.execute('''INSERT INTO Prompts 
                                (user_id, prompt_text, message_id) VALUES (?, ?, ?)''', 
                                (user_id, prompt_text, mesaage_id, ))
        self.conn.commit()

    def update_rating_by_message_id(self, message_id, rating):
        self.cursor.execute('''UPDATE Prompts
                                SET rating = ?
                                WHERE message_id = ?''', 
                                (rating, message_id))
        self.conn.commit()

    def get_rating_by_message_id(self, message_id):
        self.cursor.execute('''SELECT rating
                                FROM Prompts
                                WHERE message_id = ?;''', (message_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_popular_prompts(self, limit):
        self.cursor.execute('''SELECT prompt_text, COUNT(prompt_text) AS usage_count
                                FROM Prompts
                                GROUP BY prompt_text
                                ORDER BY usage_count DESC
                                LIMIT ?;''', (limit, ))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []

    def get_top_rated_prompts(self, limit):
        self.cursor.execute('''SELECT prompt_text, AVG(rating) AS average_rating
                                FROM Prompts
                                WHERE rating IS NOT NULL
                                GROUP BY prompt_text
                                ORDER BY average_rating DESC
                                LIMIT ?;''', (limit, ))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []