from database import get_db
from datetime import datetime, timedelta
from deepeval.tracing import observe

@observe(type="tool")
def add_plant_tool(name, location=None, species=None, notes=None):
    """Add a new plant to the user's collection"""
    conn = get_db()
    conn.execute(
        'INSERT INTO plants (name, species, location, notes, created_at) VALUES (?, ?, ?, ?, ?)',
        (name, species, location, notes, datetime.now().isoformat())
    )
    conn.commit()
    plant_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return {"success": True, "plant_id": plant_id, "message": f"Added {name} to your collection"}

@observe(type="tool")
def update_care_schedule_tool(plant_id, watering_days=None, fertilizing_days=None):
    """Update or create care schedule for a plant"""
    conn = get_db()
    
    if watering_days:
        existing = conn.execute('SELECT id FROM care_schedules WHERE plant_id = ? AND task_type = ?', 
                               (plant_id, 'watering')).fetchone()
        if existing:
            conn.execute('UPDATE care_schedules SET frequency_days = ? WHERE id = ?',
                        (watering_days, existing[0]))
        else:
            conn.execute('INSERT INTO care_schedules (plant_id, task_type, frequency_days, last_completed) VALUES (?, ?, ?, ?)',
                        (plant_id, 'watering', watering_days, datetime.now().isoformat()))
    
    if fertilizing_days:
        existing = conn.execute('SELECT id FROM care_schedules WHERE plant_id = ? AND task_type = ?',
                               (plant_id, 'fertilizing')).fetchone()
        if existing:
            conn.execute('UPDATE care_schedules SET frequency_days = ? WHERE id = ?',
                        (fertilizing_days, existing[0]))
        else:
            conn.execute('INSERT INTO care_schedules (plant_id, task_type, frequency_days, last_completed) VALUES (?, ?, ?, ?)',
                        (plant_id, 'fertilizing', fertilizing_days, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return {"success": True, "message": "Care schedule updated"}

@observe(type="tool")
def get_care_schedule_tool():
    """Get detailed care schedule with next care dates including fertilizing"""
    conn = get_db()
    
    query = """
    SELECT p.id, p.name, p.location, cs.task_type, cs.frequency_days, cs.last_completed
    FROM plants p
    JOIN care_schedules cs ON p.id = cs.plant_id
    WHERE p.status = 'alive' OR p.status IS NULL
    """
    
    results = conn.execute(query).fetchall()
    conn.close()
    
    schedule_info = []
    current_date = datetime.now()
    
    for row in results:
        last_completed = datetime.fromisoformat(row[5])
        next_due = last_completed + timedelta(days=row[4])
        days_until = (next_due.date() - current_date.date()).days
        
        schedule_info.append({
            "plant_id": row[0],
            "plant_name": row[1],
            "location": row[2] or "Unknown location",
            "task_type": row[3],
            "frequency_days": row[4],
            "last_completed": row[5],
            "next_due_date": next_due.strftime("%Y-%m-%d"),
            "days_until": days_until,
            "status": "overdue" if days_until < 0 else "due_today" if days_until == 0 else "upcoming",
            "current_date": current_date.strftime("%Y-%m-%d")
        })
    
    return {"care_schedule": schedule_info}

@observe(type="tool")
def add_to_wishlist_tool(name, notes=None):
    """Add a plant to the wishlist"""
    conn = get_db()
    
    # Check if plant already exists in wishlist
    existing = conn.execute('SELECT id FROM wishlist WHERE LOWER(name) = LOWER(?)', (name,)).fetchone()
    if existing:
        conn.close()
        return {"success": False, "message": f"{name} is already on your wishlist"}
    
    conn.execute(
        'INSERT INTO wishlist (name, notes, created_at) VALUES (?, ?, ?)',
        (name, notes, datetime.now().isoformat())
    )
    conn.commit()
    wishlist_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return {"success": True, "wishlist_id": wishlist_id, "message": f"Added {name} to your wishlist"}

@observe(type="tool")
def remove_from_wishlist_tool(wishlist_id=None, name=None):
    """Remove a plant from the wishlist by ID or name"""
    conn = get_db()
    
    if wishlist_id:
        # Remove by ID
        plant = conn.execute('SELECT name FROM wishlist WHERE id = ?', (wishlist_id,)).fetchone()
        if not plant:
            conn.close()
            return {"success": False, "message": "Plant not found in wishlist"}
        
        conn.execute('DELETE FROM wishlist WHERE id = ?', (wishlist_id,))
        plant_name = plant[0]
    elif name:
        # Remove by name (case-insensitive)
        plant = conn.execute('SELECT id, name FROM wishlist WHERE LOWER(name) = LOWER(?)', (name,)).fetchone()
        if not plant:
            conn.close()
            return {"success": False, "message": f"{name} not found in wishlist"}
        
        conn.execute('DELETE FROM wishlist WHERE id = ?', (plant[0],))
        plant_name = plant[1]
    else:
        conn.close()
        return {"success": False, "message": "Must provide either wishlist_id or name"}
    
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Removed {plant_name} from your wishlist"}

@observe(type="tool")
def mark_plant_dead_tool(plant_id):
    """Mark a plant as dead and remove its care schedules"""
    conn = get_db()
    
    # Update plant status to dead
    conn.execute('UPDATE plants SET status = ? WHERE id = ?', ('dead', plant_id))
    
    # Remove all care schedules for this plant
    conn.execute('DELETE FROM care_schedules WHERE plant_id = ?', (plant_id,))
    
    conn.commit()
    conn.close()
    return {"success": True, "message": "Plant marked as dead and care schedules removed"}

@observe(type="tool")
def get_plants_context():
    """Get all plants, schedules, and wishlist for context"""
    conn = get_db()
    plants = conn.execute('SELECT * FROM plants').fetchall()
    schedules = conn.execute('SELECT * FROM care_schedules').fetchall()
    wishlist = conn.execute('SELECT * FROM wishlist').fetchall()
    conn.close()
    
    return {
        "plants": [dict(p) for p in plants], 
        "schedules": [dict(s) for s in schedules],
        "wishlist": [dict(w) for w in wishlist]
    }

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_plant",
            "description": "Add a new plant to the user's personal plant collection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Common name of the plant"},
                    "location": {"type": "string", "description": "Where the plant is located"},
                    "species": {"type": "string", "description": "Plant species or variety"},
                    "notes": {"type": "string", "description": "Additional notes about the plant"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_care_schedule",
            "description": "Update watering and fertilizing schedule for a plant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plant_id": {"type": "integer", "description": "ID of the plant to update"},
                    "watering_days": {"type": "integer", "description": "How often to water in days"},
                    "fertilizing_days": {"type": "integer", "description": "How often to fertilize in days"}
                },
                "required": ["plant_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_care_schedule",
            "description": "Get detailed care schedule for all plants including watering and fertilizing with current date context.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_wishlist",
            "description": "Add a plant to the user's wishlist for future purchase or acquisition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the plant to add to wishlist"},
                    "notes": {"type": "string", "description": "Notes about why they want this plant or where to get it"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_wishlist",
            "description": "Remove a plant from the user's wishlist by ID or name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "wishlist_id": {"type": "integer", "description": "ID of the wishlist item to remove"},
                    "name": {"type": "string", "description": "Name of the plant to remove from wishlist"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_plant_dead",
            "description": "Mark a plant as dead and automatically remove all its care schedules.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plant_id": {"type": "integer", "description": "ID of the plant that has died"}
                },
                "required": ["plant_id"]
            }
        }
    }
]

def execute_tool(tool_name, arguments):
    """Execute a tool by name with given arguments"""
    if tool_name == "add_plant":
        return add_plant_tool(**arguments)
    elif tool_name == "update_care_schedule":
        return update_care_schedule_tool(**arguments)
    elif tool_name == "get_care_schedule":
        return get_care_schedule_tool()
    elif tool_name == "add_to_wishlist":
        return add_to_wishlist_tool(**arguments)
    elif tool_name == "remove_from_wishlist":
        return remove_from_wishlist_tool(**arguments)
    elif tool_name == "mark_plant_dead":
        return mark_plant_dead_tool(**arguments)
    else:
        return {"error": "Unknown tool"}