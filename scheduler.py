#!/usr/bin/env python3
“””
Simple Group Hangout Scheduler
Run with: python scheduler.py
Then visit: http://localhost:5000
“””

from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(**name**)

# Data directory

DATA_DIR = Path(“scheduler_data”)
DATA_DIR.mkdir(exist_ok=True)

# Word lists for generating IDs

ADJECTIVES = [“happy”, “sunny”, “quick”, “bright”, “cool”, “calm”, “wild”, “bold”, “smart”, “neat”]
NOUNS = [“tiger”, “river”, “cloud”, “star”, “moon”, “tree”, “bird”, “wave”, “fire”, “wind”]

def generate_event_id():
“”“Generate a unique event ID from random words”””
while True:
event_id = f”{random.choice(ADJECTIVES)}-{random.choice(NOUNS)}-{random.randint(10, 99)}”
if not (DATA_DIR / f”{event_id}.json”).exists():
return event_id

def load_event(event_id):
“”“Load event data from JSON file”””
file_path = DATA_DIR / f”{event_id}.json”
if not file_path.exists():
return None
with open(file_path, ‘r’) as f:
return json.load(f)

def save_event(event_id, data):
“”“Save event data to JSON file”””
file_path = DATA_DIR / f”{event_id}.json”
with open(file_path, ‘w’) as f:
json.dump(data, f, indent=2)

# HTML Templates

HOME_TEMPLATE = “””

<!DOCTYPE html>

<html>
<head>
    <title>Group Hangout Scheduler</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        input, button {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #45a049; }
        .checkbox-group {
            margin: 15px 0;
        }
        .checkbox-group label {
            display: block;
            margin: 5px 0;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
            font-size: 14px;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            border-top: 2px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 Group Hangout Scheduler</h1>

```
    <div class="section">
        <h2>Create New Event</h2>
        <form method="POST" action="/create">
            <input type="text" name="title" placeholder="Event Title" required>
            <input type="date" name="start_date" required>
            <input type="date" name="end_date" required>
            <div class="checkbox-group">
                <label>
                    <input type="checkbox" name="exclude_weekdays" value="true">
                    Automatically exclude weekdays (Mon-Fri)
                </label>
            </div>
            <button type="submit">Create Event</button>
        </form>
    </div>

    <div class="section">
        <h2>Join Existing Event</h2>
        <form method="GET" action="/event">
            <input type="text" name="event_id" placeholder="Event ID (e.g., happy-tiger-42)" required>
            <button type="submit">Join Event</button>
        </form>
    </div>

    <div class="warning">
        <strong>⚠️ Privacy Warning:</strong> Do not enter any sensitive personal information. 
        This is a simple tool for coordinating schedules. Use at your own risk. 
        Event data is stored in plain text files on the server.
    </div>
</div>
```

</body>
</html>
"""

EVENT_TEMPLATE = “””

<!DOCTYPE html>

<html>
<head>
    <title>{{ event['title'] }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .event-id {
            background: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 18px;
        }
        input, button {
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 16px;
            padding: 10px 20px;
        }
        button:hover { background: #45a049; }
        .calendar {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .day {
            border: 2px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            cursor: pointer;
            user-select: none;
        }
        .day.available {
            background: #d4edda;
            border-color: #28a745;
        }
        .day.unavailable {
            background: #f8d7da;
            border-color: #dc3545;
        }
        .day.excluded {
            background: #e2e3e5;
            border-color: #6c757d;
            opacity: 0.5;
        }
        .day-name {
            font-weight: bold;
            font-size: 12px;
            color: #666;
        }
        .day-date {
            font-size: 18px;
            margin: 5px 0;
        }
        .participants {
            margin: 20px 0;
        }
        .participant {
            background: #f8f9fa;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
        }
        .checkbox-group {
            margin: 15px 0;
        }
        .checkbox-group label {
            display: inline-block;
            margin-right: 15px;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
            font-size: 14px;
        }
        .summary {
            background: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ event['title'] }}</h1>
        <div class="event-id">
            <strong>Event ID:</strong> {{ event_id }}
        </div>
        <p>Share this ID with others so they can join!</p>

```
    <form method="POST" action="/event/{{ event_id }}/submit">
        <input type="text" name="name" id="userName" placeholder="Your Name" required>
        
        <div class="checkbox-group">
            <strong>Quick exclude:</strong><br>
            <label><input type="checkbox" class="weekday-exclude" value="1"> Mondays</label>
            <label><input type="checkbox" class="weekday-exclude" value="2"> Tuesdays</label>
            <label><input type="checkbox" class="weekday-exclude" value="3"> Wednesdays</label>
            <label><input type="checkbox" class="weekday-exclude" value="4"> Thursdays</label>
            <label><input type="checkbox" class="weekday-exclude" value="5"> Fridays</label>
            <label><input type="checkbox" class="weekday-exclude" value="6"> Saturdays</label>
            <label><input type="checkbox" class="weekday-exclude" value="0"> Sundays</label>
        </div>

        <p><strong>Click days you're NOT available:</strong></p>
        <div class="calendar" id="calendar"></div>
        
        <input type="hidden" name="unavailable_dates" id="unavailableDates">
        <button type="submit">Submit Availability</button>
    </form>

    <div class="summary">
        <h2>Availability Summary</h2>
        <p>Days when <strong>everyone</strong> is available:</p>
        <div id="bestDays"></div>
    </div>

    <div class="participants">
        <h2>Participants ({{ event['responses']|length }})</h2>
        {% for response in event['responses'] %}
            <div class="participant">
                <strong>{{ response['name'] }}</strong> - 
                Unavailable: {{ response['unavailable_dates']|length }} days
            </div>
        {% endfor %}
    </div>

    <div class="warning">
        <strong>⚠️ Privacy Warning:</strong> Do not enter any sensitive personal information. 
        Use at your own risk.
    </div>
    
    <p><a href="/">← Back to Home</a></p>
</div>

<script>
    const eventData = {{ event|tojson }};
    const excludedDates = new Set(eventData.excluded_dates || []);
    const unavailableDates = new Set();
    
    // Generate calendar
    const calendar = document.getElementById('calendar');
    const startDate = new Date(eventData.start_date);
    const endDate = new Date(eventData.end_date);
    
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        const dayDiv = document.createElement('div');
        dayDiv.className = 'day';
        dayDiv.dataset.date = dateStr;
        
        if (excludedDates.has(dateStr)) {
            dayDiv.className = 'day excluded';
            dayDiv.innerHTML = `
                <div class="day-name">${days[d.getDay()]}</div>
                <div class="day-date">${d.getDate()}</div>
                <div style="font-size: 10px;">Excluded</div>
            `;
        } else {
            dayDiv.innerHTML = `
                <div class="day-name">${days[d.getDay()]}</div>
                <div class="day-date">${d.getDate()}</div>
            `;
            
            dayDiv.addEventListener('click', function() {
                if (this.classList.contains('unavailable')) {
                    this.classList.remove('unavailable');
                    unavailableDates.delete(dateStr);
                } else {
                    this.classList.add('unavailable');
                    unavailableDates.add(dateStr);
                }
                updateHiddenInput();
            });
        }
        
        calendar.appendChild(dayDiv);
    }
    
    // Handle weekday exclusion
    document.querySelectorAll('.weekday-exclude').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const dayOfWeek = parseInt(this.value);
            const checked = this.checked;
            
            for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
                if (d.getDay() === dayOfWeek) {
                    const dateStr = d.toISOString().split('T')[0];
                    const dayDiv = document.querySelector(`[data-date="${dateStr}"]`);
                    
                    if (dayDiv && !dayDiv.classList.contains('excluded')) {
                        if (checked) {
                            dayDiv.classList.add('unavailable');
                            unavailableDates.add(dateStr);
                        } else {
                            dayDiv.classList.remove('unavailable');
                            unavailableDates.delete(dateStr);
                        }
                    }
                }
            }
            updateHiddenInput();
        });
    });
    
    function updateHiddenInput() {
        document.getElementById('unavailableDates').value = Array.from(unavailableDates).join(',');
    }
    
    // Calculate best days
    function calculateBestDays() {
        const allDates = [];
        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
            const dateStr = d.toISOString().split('T')[0];
            if (!excludedDates.has(dateStr)) {
                allDates.push(dateStr);
            }
        }
        
        const unavailableByDate = {};
        eventData.responses.forEach(response => {
            response.unavailable_dates.forEach(date => {
                if (!unavailableByDate[date]) unavailableByDate[date] = 0;
                unavailableByDate[date]++;
            });
        });
        
        const availableDays = allDates.filter(date => !unavailableByDate[date]);
        
        const bestDaysDiv = document.getElementById('bestDays');
        if (availableDays.length > 0) {
            bestDaysDiv.innerHTML = '<ul>' + availableDays.map(date => {
                const d = new Date(date + 'T00:00:00');
                return `<li><strong>${date}</strong> (${days[d.getDay()]})</li>`;
            }).join('') + '</ul>';
        } else {
            bestDaysDiv.innerHTML = '<p>No days when everyone is available yet. More responses needed!</p>';
        }
    }
    
    calculateBestDays();
</script>
```

</body>
</html>
"""

@app.route(’/’)
def home():
return render_template_string(HOME_TEMPLATE)

@app.route(’/create’, methods=[‘POST’])
def create_event():
event_id = generate_event_id()
title = request.form[‘title’]
start_date = request.form[‘start_date’]
end_date = request.form[‘end_date’]
exclude_weekdays = request.form.get(‘exclude_weekdays’) == ‘true’

```
# Generate excluded dates if weekdays should be excluded
excluded_dates = []
if exclude_weekdays:
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    for i in range((end - start).days + 1):
        date = start + timedelta(days=i)
        if date.weekday() < 5:  # Monday = 0, Friday = 4
            excluded_dates.append(date.strftime('%Y-%m-%d'))

event_data = {
    'title': title,
    'start_date': start_date,
    'end_date': end_date,
    'excluded_dates': excluded_dates,
    'responses': [],
    'created_at': datetime.now().isoformat()
}

save_event(event_id, event_data)
return redirect(url_for('view_event', event_id=event_id))
```

@app.route(’/event’)
def view_event():
event_id = request.args.get(‘event_id’, ‘’).strip()
if not event_id:
return redirect(url_for(‘home’))

```
event = load_event(event_id)
if not event:
    return f"Event '{event_id}' not found. <a href='/'>Go back</a>"

return render_template_string(EVENT_TEMPLATE, event=event, event_id=event_id)
```

@app.route(’/event/<event_id>/submit’, methods=[‘POST’])
def submit_response(event_id):
event = load_event(event_id)
if not event:
return “Event not found”, 404

```
name = request.form['name'].strip()
unavailable_dates_str = request.form['unavailable_dates']
unavailable_dates = [d.strip() for d in unavailable_dates_str.split(',') if d.strip()]

# Remove existing response from this person if exists
event['responses'] = [r for r in event['responses'] if r['name'].lower() != name.lower()]

# Add new response
event['responses'].append({
    'name': name,
    'unavailable_dates': unavailable_dates,
    'submitted_at': datetime.now().isoformat()
})

save_event(event_id, event)
return redirect(url_for('view_event') + f'?event_id={event_id}')
```

if **name** == ‘**main**’:
print(”\n” + “=”*50)
print(“🚀 Group Hangout Scheduler Starting!”)
print(”=”*50)
print(f”\n📂 Data will be stored in: {DATA_DIR.absolute()}”)
print(”\n🌐 Visit: http://localhost:5000”)
print(”\n⚠️  Press CTRL+C to stop the server\n”)

```
# For local development
app.run(debug=True, port=5000)
```

# For production (Gunicorn will use this)

# The app object is already defined above
