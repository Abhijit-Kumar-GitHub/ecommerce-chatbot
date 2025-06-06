import sqlite3
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            category TEXT
        )
    ''')
    cursor.execute('DELETE FROM products')
    categories = ['Laptop', 'Smartphone', 'Headphones', 'Camera', 'Tablet']
    for i in range(100):
        name = f"{random.choice(categories)} {i+1}"
        description = f"High-quality {name} with advanced features."
        price = round(random.uniform(100, 2000), 2)
        category = random.choice(categories)
        cursor.execute('INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)',
                       (name, description, price, category))
    conn.commit()
    conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if username and password == 'password123':
            return jsonify({'success': True, 'username': username})
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        if 'under' in query:
            try:
                price_limit = float(query.split('under')[-1].strip().replace('$', ''))
                cursor.execute('SELECT * FROM products WHERE price <= ? AND (name LIKE ? OR category LIKE ?)',
                               (price_limit, f'%{query.split("under")[0].strip()}%', f'%{query.split("under")[0].strip()}%'))
            except ValueError:
                return jsonify({'products': [], 'error': 'Invalid price format'}), 400
        else:
            cursor.execute('SELECT * FROM products WHERE name LIKE ? OR category LIKE ?',
                           (f'%{query}%', f'%{query}%'))
        products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3], 'category': row[4]}
                    for row in cursor.fetchall()]
        conn.close()
        return jsonify({'products': products})
    except Exception as e:
        return jsonify({'products': [], 'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)