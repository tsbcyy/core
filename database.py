# -*- coding: utf-8 -*-

import sqlite3

class Database:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                class TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                student_name TEXT,
                student_class TEXT,
                manual_points INTEGER,
                ocr_points INTEGER,
                final_points INTEGER,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                image_path TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by TEXT,
                reviewed_at TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER,
                error_type TEXT,
                error_detail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0,
                resolved_by TEXT,
                resolution_note TEXT,
                resolved_at TIMESTAMP,
                FOREIGN KEY (submission_id) REFERENCES submissions(id)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_name TEXT,
                action TEXT,
                target_id TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            conn.commit()
    
    def add_student(self, student_id, name, class_name=''):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO students (id, name, class, created_at) 
                VALUES (?, ?, ?, COALESCE((SELECT created_at FROM students WHERE id=?), CURRENT_TIMESTAMP))
            """, (student_id, name, class_name, student_id))
            conn.commit()
    
    def add_submission(self, student_id, student_name, student_class, 
                      manual_points, ocr_points, image_path, error_msg=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if error_msg:
                status = 'error'
                final_points = None
            elif manual_points is not None and ocr_points is not None and manual_points != ocr_points:
                status = 'mismatch'
                final_points = None
            else:
                status = 'matched'
                final_points = manual_points if manual_points is not None else ocr_points
            
            cursor.execute('''INSERT INTO submissions 
                (student_id, student_name, student_class, manual_points, ocr_points, final_points, status, error_message, image_path)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (student_id, student_name, student_class, manual_points, ocr_points, final_points, status, error_msg, image_path))
            
            submission_id = cursor.lastrowid
            
            if error_msg:
                cursor.execute('''INSERT INTO error_logs (submission_id, error_type, error_detail)
                    VALUES (?,?,?)''', (submission_id, 'ocr_mismatch', error_msg))
            
            conn.commit()
            return submission_id
    
    def get_pending_errors(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT s.*, e.id as error_id, e.error_detail 
                FROM submissions s
                JOIN error_logs e ON s.id = e.submission_id
                WHERE e.resolved = 0
                ORDER BY s.submitted_at DESC''')
            return cursor.fetchall()
    
    def resolve_error(self, error_id, admin_name, resolution):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE error_logs 
                SET resolved = 1, resolved_by = ?, resolution_note = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (admin_name, resolution, error_id))
            
            cursor.execute('''INSERT INTO admin_logs (admin_name, action, target_id, details)
                VALUES (?,?,?,?)''', (admin_name, 'resolve_error', str(error_id), resolution))
            conn.commit()
    
    def get_statistics(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {
                'total_submissions': cursor.execute("SELECT COUNT(*) FROM submissions").fetchone()[0],
                'matched': cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='matched'").fetchone()[0],
                'mismatch': cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='mismatch'").fetchone()[0],
                'errors': cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='error'").fetchone()[0],
                'pending_errors': cursor.execute("SELECT COUNT(*) FROM error_logs WHERE resolved=0").fetchone()[0],
                'total_students': cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            }
            return stats
