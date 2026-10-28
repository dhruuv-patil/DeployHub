import os
import sys
import time
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure MySQL from environment variables
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'root')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'devops')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))

# Check whether to use SQLite fallback (e.g. for testing or local development without MySQL C-lib)
USE_SQLITE = os.environ.get('USE_SQLITE', '').lower() in ('true', '1', 'yes')

mysql = None
sqlite_conn = None

try:
    if not USE_SQLITE:
        from flask_mysqldb import MySQL
        mysql = MySQL(app)
        logger.info("Using MySQL database backend.")
    else:
        logger.info("USE_SQLITE is set to True. Using SQLite database backend.")
except ImportError:
    logger.warning("flask_mysqldb not available. Falling back to SQLite backend.")
    USE_SQLITE = True

if USE_SQLITE or mysql is None:
    import sqlite3
    import re

    class SQLiteCursorWrapper:
        def __init__(self, conn):
            self._cursor = conn.cursor()

        def execute(self, query, params=None):
            # Translate MySQL-specific syntax to SQLite
            q = re.sub(r'INT\s+AUTO_INCREMENT\s+PRIMARY\s+KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', query, flags=re.IGNORECASE)
            q = q.replace('AUTO_INCREMENT', 'AUTOINCREMENT')
            q = q.replace('%s', '?')
            if params is not None:
                return self._cursor.execute(q, tuple(params))
            return self._cursor.execute(q)

        def fetchall(self):
            return self._cursor.fetchall()

        def fetchone(self):
            return self._cursor.fetchone()

        @property
        def lastrowid(self):
            return self._cursor.lastrowid

        def close(self):
            self._cursor.close()

    class SQLiteConnWrapper:
        def __init__(self, conn):
            self._conn = conn

        def cursor(self):
            return SQLiteCursorWrapper(self._conn)

        def commit(self):
            self._conn.commit()

        def ping(self):
            return True

    class SQLiteMySQLAdapter:
        def __init__(self):
            db_path = os.environ.get('SQLITE_DB_PATH', ':memory:')
            self._conn = sqlite3.connect(db_path, check_same_thread=False)

        @property
        def connection(self):
            return SQLiteConnWrapper(self._conn)

    mysql = SQLiteMySQLAdapter()


def init_db(max_retries=5, retry_delay=3):
    """
    Initializes the database schema with automatic retry mechanism
    to wait for the database service to be ready during cold boots.
    """
    logger.info("Initializing database schema...")
    for attempt in range(1, max_retries + 1):
        try:
            with app.app_context():
                conn = mysql.connection
                if conn is None:
                    raise Exception("Database connection object is None")
                cur = conn.cursor()
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                conn.commit()

                # Check if there is at least one message, if not insert welcome message
                cur.execute('SELECT COUNT(*) FROM messages')
                count = cur.fetchone()[0]
                if count == 0:
                    cur.execute(
                        'INSERT INTO messages (message) VALUES (%s)',
                        ['Welcome to DeployHub! Continuous delivery with Flask and MySQL 🚀']
                    )
                    conn.commit()

                cur.close()
                logger.info("Database schema initialized successfully.")
                return True
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error("Could not initialize database after maximum retries.")
                return False


@app.route('/')
def index():
    """
    Renders the DeployHub dashboard with the message board feed.
    """
    messages = []
    db_connected = False
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT message, created_at FROM messages ORDER BY id DESC')
        messages = cur.fetchall()
        cur.close()
        db_connected = True
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")

    return render_template('index.html', messages=messages, db_connected=db_connected)


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint for Docker Compose, AWS ELB/ALB, and Jenkins.
    Returns HTTP 200 if the app and database are operational.
    """
    db_status = "connected"
    http_code = 200
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT 1')
        cur.fetchone()
        cur.close()
    except Exception as e:
        logger.warning(f"Health check database ping failed: {e}")
        db_status = f"unhealthy: {str(e)}"
        http_code = 503

    response = {
        'status': 'healthy' if http_code == 200 else 'unhealthy',
        'service': 'DeployHub',
        'version': '1.0.0',
        'database': db_status,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    return jsonify(response), http_code


@app.route('/submit', methods=['POST'])
def submit():
    """
    Submit a new message via AJAX or form-data.
    """
    if request.is_json:
        data = request.get_json()
        new_message = data.get('new_message', '').strip()
    else:
        new_message = request.form.get('new_message', '').strip()

    if not new_message:
        return jsonify({'error': 'Message content cannot be empty'}), 400

    if len(new_message) > 500:
        return jsonify({'error': 'Message exceeds maximum length of 500 characters'}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO messages (message) VALUES (%s)', [new_message])
        mysql.connection.commit()
        cur.close()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({
            'status': 'success',
            'message': new_message,
            'created_at': timestamp
        }), 201
    except Exception as e:
        logger.error(f"Error inserting message: {e}")
        return jsonify({'error': 'Failed to save message to database'}), 500


@app.route('/api/messages', methods=['GET'])
def get_messages():
    """
    API endpoint returning messages as a JSON array.
    """
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT id, message, created_at FROM messages ORDER BY id DESC')
        rows = cur.fetchall()
        cur.close()

        result = []
        for row in rows:
            created_str = str(row[2]) if len(row) > 2 and row[2] else ''
            result.append({
                'id': row[0],
                'message': row[1],
                'created_at': created_str
            })
        return jsonify({'count': len(result), 'messages': result}), 200
    except Exception as e:
        logger.error(f"Error reading messages: {e}")
        return jsonify({'error': 'Failed to retrieve messages'}), 500


@app.route('/api/clear', methods=['POST'])
def clear_messages():
    """
    API endpoint to reset/clear messages.
    """
    try:
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM messages')
        mysql.connection.commit()
        cur.close()
        return jsonify({'status': 'success', 'message': 'All messages cleared'}), 200
    except Exception as e:
        logger.error(f"Error clearing messages: {e}")
        return jsonify({'error': 'Failed to clear messages'}), 500


@app.route('/api/info', methods=['GET'])
def info():
    """
    Returns DeployHub metadata and configuration info.
    """
    return jsonify({
        'app_name': 'DeployHub',
        'description': 'Continuous Delivery for Cloud Applications',
        'author': 'Dhruv Patil',
        'github_repo': 'https://github.com/dhruuv-patil/DeployHub',
        'architecture': 'Two-Tier (Flask Application + MySQL Container)',
        'platform': 'Docker & AWS EC2',
        'ci_cd': 'Jenkins & GitHub Actions'
    }), 200


# Initialize database when module loads in WSGI or direct mode
init_db(max_retries=3, retry_delay=2)

if __name__ == '__main__':
    requested_port = int(os.environ.get('PORT', 5000))
    port = requested_port
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')

    # Detect if port 5000 is occupied (e.g., by macOS AirPlay Receiver)
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', port))
        s.close()
    except OSError:
        if port == 5000 and 'PORT' not in os.environ:
            logger.warning("Port 5000 is currently occupied (macOS AirPlay Receiver). Automatically switching to port 5001.")
            port = 5001

    logger.info(f"Starting DeployHub web server on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
