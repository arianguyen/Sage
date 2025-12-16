from flask import Flask, request, jsonify, render_template_string
import os
import uuid
from dotenv import load_dotenv
from database import init_db, get_db
from agent import run_agent_conversation
from datetime import datetime, timedelta

load_dotenv()
app = Flask(__name__)
init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sage - Plant Care AI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { padding: 20px; text-align: center; border-bottom: 1px solid #eee; }
        .agent-icon { width: 60px; height: 60px; border-radius: 50%; background: #4CAF50; display: inline-flex; align-items: center; justify-content: center; font-size: 24px; margin: 0 auto 10px; }
        .chat-container { height: 400px; overflow-y: auto; padding: 20px; }
        .message { margin: 10px 0; padding: 10px 15px; border-radius: 15px; max-width: 70%; }
        .message.user { background: #C76439; color: white; margin-left: auto; text-align: right; }
        .message.assistant { background: #9CAF88; color: #333; margin-right: auto; }
        .input-area { padding: 20px; border-top: 1px solid #eee; display: flex; gap: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none; }
        button { padding: 10px 20px; background: #C76439; color: white; border: none; border-radius: 20px; cursor: pointer; }
        .sidebar { position: fixed; right: 20px; top: 20px; width: 300px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 15px; max-height: 80vh; overflow-y: auto; }
        .sidebar h3 { margin-top: 0; color: #2d5a27; }
        .schedule-item { background: #f9f9f9; border-radius: 8px; padding: 10px; margin: 8px 0; border-left: 4px solid #4CAF50; }
        .schedule-item.overdue { border-left-color: #F44336; }
        .schedule-item.due-today { border-left-color: #FF5722; }
        .task-info { font-weight: bold; color: #2d5a27; font-size: 14px; }
        .plant-info { color: #666; font-size: 12px; }
        .wishlist-item { background: #fff3e0; border-radius: 8px; padding: 8px; margin: 5px 0; border-left: 4px solid #FF9800; }
        .wishlist-name { font-weight: bold; color: #e65100; font-size: 14px; }
        .wishlist-notes { color: #666; font-size: 12px; }
        .section { margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="agent-icon">🌱</div>
            <h1>Sage</h1>
        </div>
        
        <div class="chat-container" id="chat"></div>
        
        <div class="input-area">
            <input type="text" id="message" placeholder="Ask about plants, add new ones, or get care advice...">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <div class="sidebar">
        <div class="section">
            <h3>🗓️ Care Schedule</h3>
            <div id="schedule-container">Loading...</div>
        </div>
        
        <div class="section">
            <h3>🌟 Plant Wishlist</h3>
            <div id="wishlist-container">Loading...</div>
        </div>
    </div>

    <script>
        function sendMessage() {
            var input = document.getElementById('message');
            var message = input.value.trim();
            if (!message) return;
            
            var chat = document.getElementById('chat');
            chat.innerHTML += '<div class="message user">' + message + '</div>';
            input.value = '';
            chat.scrollTop = chat.scrollHeight;
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                var formattedResponse = data.response
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                    .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                    .replace(/\\n/g, '<br>');
                chat.innerHTML += '<div class="message assistant">' + formattedResponse + '</div>';
                chat.scrollTop = chat.scrollHeight;
                loadSchedule();
                loadWishlist();
            })
            .catch(function(error) {
                chat.innerHTML += '<div class="message assistant">Error: Could not send message.</div>';
            });
        }
        
        function loadSchedule() {
            fetch('/api/schedule')
            .then(function(response) { 
                if (!response.ok) throw new Error('Schedule API failed');
                return response.json(); 
            })
            .then(function(data) {
                var container = document.getElementById('schedule-container');
                if (data.length === 0) {
                    container.innerHTML = '<p>No care schedules set.</p>';
                    return;
                }
                
                var html = '';
                for (var i = 0; i < data.length; i++) {
                    var item = data[i];
                    var statusClass = 'upcoming';
                    var statusText = 'Due in ' + item.days_until + ' days';
                    
                    if (item.days_until < 0) {
                        statusClass = 'overdue';
                        statusText = 'Overdue!';
                    } else if (item.days_until === 0) {
                        statusClass = 'due-today';
                        statusText = 'Due today!';
                    }
                    
                    var icon = item.task_type === 'watering' ? '💧' : '🌱';
                    
                    html += '<div class="schedule-item ' + statusClass + '">';
                    html += '<div class="task-info">' + icon + ' ' + item.plant_name + '</div>';
                    html += '<div class="plant-info">' + item.task_type + ' - ' + statusText + '</div>';
                    html += '</div>';
                }
                container.innerHTML = html;
            })
            .catch(function(error) {
                document.getElementById('schedule-container').innerHTML = '<p>Error loading schedule</p>';
                console.error('Schedule error:', error);
            });
        }
        
        function loadWishlist() {
            fetch('/api/wishlist')
            .then(function(response) { 
                if (!response.ok) throw new Error('Wishlist API failed');
                return response.json(); 
            })
            .then(function(data) {
                var container = document.getElementById('wishlist-container');
                if (data.length === 0) {
                    container.innerHTML = '<p>No plants in wishlist.</p>';
                    return;
                }
                
                var html = '';
                for (var i = 0; i < data.length; i++) {
                    var item = data[i];
                    html += '<div class="wishlist-item">';
                    html += '<div class="wishlist-name">' + item.name + '</div>';
                    if (item.notes) {
                        html += '<div class="wishlist-notes">' + item.notes + '</div>';
                    }
                    html += '</div>';
                }
                container.innerHTML = html;
            })
            .catch(function(error) {
                document.getElementById('wishlist-container').innerHTML = '<p>Error loading wishlist</p>';
                console.error('Wishlist error:', error);
            });
        }
        
        // Add initial greeting first
        document.getElementById('chat').innerHTML = '<div class="message assistant">Hi there! 🌱 I\\'m Sage, your plant care buddy. I\\'m here to help you care for your plants, set up watering schedules, and suggest new green friends for your collection. What can I help you with today?</div>';
        
        // Load data on page load
        loadSchedule();
        loadWishlist();
        
        // Enter key to send message
        document.getElementById('message').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data['message']
    trace_id = str(uuid.uuid4())
    
    try:
        response = run_agent_conversation(user_message, trace_id=trace_id)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'})

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    try:
        print("Schedule API called")
        conn = get_db()
        print("Database connected")
        
        count = conn.execute('SELECT COUNT(*) FROM care_schedules').fetchone()[0]
        print(f"Care schedules count: {count}")
        
        if count == 0:
            conn.close()
            return jsonify([])
        
        query = """
        SELECT p.name as plant_name, cs.task_type, cs.frequency_days, cs.last_completed
        FROM plants p
        JOIN care_schedules cs ON p.id = cs.plant_id
        WHERE (p.status = 'alive' OR p.status IS NULL) AND cs.task_type = 'watering'
        ORDER BY cs.last_completed ASC
        """
        
        results = conn.execute(query).fetchall()
        print(f"Query results: {len(results)} rows")
        conn.close()
        
        schedule_data = []
        current_date = datetime.now()
        
        for row in results:
            try:
                last_completed = datetime.fromisoformat(row[3])
                next_due = last_completed + timedelta(days=row[2])
                days_until = (next_due - current_date).days
                
                schedule_data.append({
                    'plant_name': row[0],
                    'task_type': row[1],
                    'frequency_days': row[2],
                    'last_completed': row[3],
                    'days_until': days_until
                })
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        print(f"Returning {len(schedule_data)} schedule items")
        return jsonify(schedule_data)
        
    except Exception as e:
        print(f"Schedule API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/wishlist', methods=['GET'])
def get_wishlist():
    try:
        print("Wishlist API called")
        conn = get_db()
        print("Database connected for wishlist")
        
        count = conn.execute('SELECT COUNT(*) FROM wishlist').fetchone()[0]
        print(f"Wishlist count: {count}")
        
        if count == 0:
            conn.close()
            return jsonify([])
            
        wishlist = conn.execute('SELECT * FROM wishlist ORDER BY created_at DESC').fetchall()
        conn.close()
        
        result = [dict(w) for w in wishlist]
        print(f"Returning {len(result)} wishlist items")
        return jsonify(result)
        
    except Exception as e:
        print(f"Wishlist API error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Sage Plant Care AI at http://localhost:5001")
    app.run(debug=True, port=5001)