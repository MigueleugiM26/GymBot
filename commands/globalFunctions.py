import json


def load_xp_data():
    with open("storage/levelTable.json", "r") as file:
        return json.load(file)
    

def save_user_data(user_data):
    with open("storage/users.json", "w") as file:
        json.dump(user_data, file, indent=4)


def load_user_data():
    try:
        with open("storage/users.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No user data file found.")
        return {}
    

def get_user_entry(user_id):
    user_data = load_user_data()
    user_id = str(user_id) 
    
    if user_id not in user_data:
        user_data[user_id] = {
            "level": 1, 
            "hp": 2,
            "strength": 1,
            "agility": 1,
            "endurance": 1,
            "flexibility": 1,
            "skill": 0,
            "hasRoutine": False,
            "workoutMessageId": "",
            "exercisesDone": 0,
            "groupsDone": [],
            "battles": 0,
            "inventory": {}
        }
        save_user_data(user_data)  
    return user_data[user_id]