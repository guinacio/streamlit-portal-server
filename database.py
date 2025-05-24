import sqlite3
import bcrypt
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import json

class StreamlitPortalDB:
    def __init__(self, db_path: str = "portal.db"):
        self.db_path = db_path
        self.init_database()
        self.create_admin_user()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        # Apps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                port INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                image_path TEXT,
                category TEXT DEFAULT 'General',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')

        # User groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                group_name TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, group_name)
            )
        ''')

        # App permissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER,
                group_name TEXT,
                FOREIGN KEY (app_id) REFERENCES apps (id),
                UNIQUE(app_id, group_name)
            )
        ''')

        # Sessions table for security
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_admin_user(self):
        """Create default admin user if it doesn't exist"""
        if not self.get_user_by_username("admin"):
            password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
            self.create_user(
                username="admin",
                password="admin123",
                full_name="System Administrator",
                email="admin@portal.local",
                role="admin"
            )

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def create_user(self, username: str, password: str, full_name: str = "", 
                   email: str = "", role: str = "user") -> bool:
        """Create a new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, email, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, full_name, email, role))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user info"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password_hash, full_name, email, role, is_active
            FROM users WHERE username = ? AND is_active = 1
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and self.verify_password(password, user[2]):
            # Update last login
            self.update_last_login(user[0])
            return {
                'id': user[0],
                'username': user[1],
                'full_name': user[3],
                'email': user[4],
                'role': user[5]
            }
        return None

    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, full_name, email, role, is_active, created_at, last_login
            FROM users WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'full_name': user[2],
                'email': user[3],
                'role': user[4],
                'is_active': user[5],
                'created_at': user[6],
                'last_login': user[7]
            }
        return None

    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, full_name, email, role, is_active, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        
        return [{
            'id': user[0],
            'username': user[1],
            'full_name': user[2],
            'email': user[3],
            'role': user[4],
            'is_active': user[5],
            'created_at': user[6],
            'last_login': user[7]
        } for user in users]

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, full_name, email, role, is_active, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'full_name': user[2],
                'email': user[3],
                'role': user[4],
                'is_active': user[5],
                'created_at': user[6],
                'last_login': user[7]
            }
        return None

    def update_user(self, user_id: int, username: str = None, password: str = None, 
                   full_name: str = None, email: str = None, role: str = None) -> bool:
        """Update user information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Build dynamic update query
            update_fields = []
            update_values = []
            
            if username is not None:
                update_fields.append("username = ?")
                update_values.append(username)
            if password is not None:
                update_fields.append("password_hash = ?")
                update_values.append(self.hash_password(password))
            if full_name is not None:
                update_fields.append("full_name = ?")
                update_values.append(full_name)
            if email is not None:
                update_fields.append("email = ?")
                update_values.append(email)
            if role is not None:
                update_fields.append("role = ?")
                update_values.append(role)
            
            if not update_fields:
                return False
            
            update_values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            
            cursor.execute(query, update_values)
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_user(self, user_id: int) -> bool:
        """Delete a user (also removes from groups)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First remove user from all groups
            cursor.execute('DELETE FROM user_groups WHERE user_id = ?', (user_id,))
            
            # Then delete the user
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def remove_user_from_group(self, user_id: int, group_name: str) -> bool:
        """Remove user from a specific group"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM user_groups WHERE user_id = ? AND group_name = ?
            ''', (user_id, group_name))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def set_user_groups(self, user_id: int, groups: List[str]) -> bool:
        """Set user's groups (removes from all current groups and adds to new ones)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Remove from all current groups
            cursor.execute('DELETE FROM user_groups WHERE user_id = ?', (user_id,))
            
            # Add to new groups
            for group in groups:
                cursor.execute('''
                    INSERT INTO user_groups (user_id, group_name)
                    VALUES (?, ?)
                ''', (user_id, group))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def create_app(self, port: int, name: str, description: str = "", 
                  image_path: str = "", category: str = "General", 
                  created_by: int = None) -> bool:
        """Create or update an app configuration"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if app with this port already exists
            cursor.execute('SELECT id FROM apps WHERE port = ?', (port,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing app
                cursor.execute('''
                    UPDATE apps SET name = ?, description = ?, image_path = ?, 
                           category = ?, is_active = 1 WHERE port = ?
                ''', (name, description, image_path, category, port))
            else:
                # Create new app
                cursor.execute('''
                    INSERT INTO apps (port, name, description, image_path, category, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (port, name, description, image_path, category, created_by))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating app: {e}")
            return False

    def get_app_by_port(self, port: int) -> Optional[Dict]:
        """Get app configuration by port"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, port, name, description, image_path, category, is_active, created_at
            FROM apps WHERE port = ?
        ''', (port,))
        app = cursor.fetchone()
        conn.close()
        
        if app:
            return {
                'id': app[0],
                'port': app[1],
                'name': app[2],
                'description': app[3],
                'image_path': app[4],
                'category': app[5],
                'is_active': app[6],
                'created_at': app[7]
            }
        return None

    def get_all_apps(self) -> List[Dict]:
        """Get all app configurations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, port, name, description, image_path, category, is_active, created_at
            FROM apps ORDER BY name
        ''')
        apps = cursor.fetchall()
        conn.close()
        
        return [{
            'id': app[0],
            'port': app[1],
            'name': app[2],
            'description': app[3],
            'image_path': app[4],
            'category': app[5],
            'is_active': app[6],
            'created_at': app[7]
        } for app in apps]

    def delete_app(self, app_id: int) -> bool:
        """Delete an app configuration"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM apps WHERE id = ?', (app_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def add_user_to_group(self, user_id: int, group_name: str) -> bool:
        """Add user to a group"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO user_groups (user_id, group_name)
                VALUES (?, ?)
            ''', (user_id, group_name))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_user_groups(self, user_id: int) -> List[str]:
        """Get all groups for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT group_name FROM user_groups WHERE user_id = ?
        ''', (user_id,))
        groups = cursor.fetchall()
        conn.close()
        return [group[0] for group in groups]

    def set_app_permissions(self, app_id: int, groups: List[str]) -> bool:
        """Set which groups can access an app"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Remove existing permissions
            cursor.execute('DELETE FROM app_permissions WHERE app_id = ?', (app_id,))
            
            # Add new permissions
            for group in groups:
                cursor.execute('''
                    INSERT INTO app_permissions (app_id, group_name)
                    VALUES (?, ?)
                ''', (app_id, group))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_accessible_apps(self, user_id: int) -> List[Dict]:
        """Get apps accessible to a user based on their groups"""
        user_groups = self.get_user_groups(user_id)
        
        # Get user info to check if admin
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user_role = cursor.fetchone()
        
        if user_role and user_role[0] == 'admin':
            # Admins can see all apps
            cursor.execute('''
                SELECT id, port, name, description, image_path, category, is_active, created_at
                FROM apps WHERE is_active = 1 ORDER BY name
            ''')
            apps = cursor.fetchall()
        else:
            # Regular users see apps based on group permissions OR public apps
            # First get public apps (apps with __public__ permission)
            cursor.execute('''
                SELECT DISTINCT a.id, a.port, a.name, a.description, a.image_path, 
                       a.category, a.is_active, a.created_at
                FROM apps a
                JOIN app_permissions ap ON a.id = ap.app_id
                WHERE a.is_active = 1 AND ap.group_name = '__public__'
            ''')
            public_apps = cursor.fetchall()
            
            # Then get group-restricted apps if user has groups
            group_apps = []
            if user_groups:
                placeholders = ','.join('?' * len(user_groups))
                cursor.execute(f'''
                    SELECT DISTINCT a.id, a.port, a.name, a.description, a.image_path, 
                           a.category, a.is_active, a.created_at
                    FROM apps a
                    JOIN app_permissions ap ON a.id = ap.app_id
                    WHERE a.is_active = 1 AND ap.group_name IN ({placeholders})
                          AND ap.group_name != '__public__'
                    ORDER BY a.name
                ''', user_groups)
                group_apps = cursor.fetchall()
            
            # Combine public and group apps, removing duplicates by app id
            seen_ids = set()
            apps = []
            
            for app in public_apps + group_apps:
                if app[0] not in seen_ids:
                    apps.append(app)
                    seen_ids.add(app[0])
            
            # Sort by name
            apps.sort(key=lambda x: x[2])  # Sort by name (index 2)
        
        conn.close()
        
        return [{
            'id': app[0],
            'port': app[1],
            'name': app[2],
            'description': app[3],
            'image_path': app[4],
            'category': app[5],
            'is_active': app[6],
            'created_at': app[7]
        } for app in apps]

    def get_all_groups(self) -> List[str]:
        """Get all unique group names"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT group_name FROM user_groups ORDER BY group_name')
        groups = cursor.fetchall()
        conn.close()
        return [group[0] for group in groups] 