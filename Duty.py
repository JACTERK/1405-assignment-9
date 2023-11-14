'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
REMINDER:
You are **NOT** expected OR required to read and understand this code. 

It uses MANY advanced techniques that are not covered in this course.
Reading this code many further confuse things and is not necessary to complete the assignment.
All information about how the functions should be used is available in the assignment specification.

You may read through it if you are curious, but do not rely on it to complete the assignment.

Do **NOT** make ANY modifications to this file.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from datetime import datetime
import time
import random
import os
from warnings import warn
from typing import Union

class Room:
    def __init__(self, name: str, items: list[str]):
        self.name = name
        self.items = items
        self.anomaly = ""
        self.anomaly_items = []

    def get_anomaly(self) -> str:
        return self.anomaly

    def add_anomaly(self, name: str, items: list[str]) -> bool:
        # Compare the items in the room to the items in the anomaly
        # If the incoming item sequence is the same, don't add the anomaly
        if self.items == items:
            return False

        self.anomaly = name.upper()
        self.anomaly_items = items
        return True
    
class GameManager:
    def __init__(self):
        self.rooms = []
        self.anomalies = []

        self.data = {
            "camera": 0,
            "time": 0,
            "seconds_since_last_anomaly_check": 0,
            "found_anomalies": 0,
            "active_anomalies": 0,
            "seconds_since_last_anomaly": 0
        }

        self.settings = {
            "debug": False,
            "timescale": 10.0,
            "probability": 0.1,
            "max_anomalies": 4.0,
            "anomaly_report_time": 5.0,
            "max_seconds": 60*60*5.0,
            "min_seconds_between_anomalies": 20*60.0 # **in-game** seconds
        }

        self.gameover = {
            "timeup": False,
            "anomalies": False,
            "quit": False
        }

    def add_room(self, name: str, items: list[str]) -> bool:
        if self.room_exists(name.upper()):
            warn("Tried to add a room that already exists.")
            return False
        else:
            self.rooms.append(Room(name.upper(), items))
            return True

    def get_room(self, room: Union[int, str]) -> Room:
        if isinstance(room, int):
            return self.rooms[room]
        elif isinstance(room, str):
            for room_obj in self.rooms:
                if room_obj.name == room:
                    return room_obj
            warn(f"Room {room} not found.")
            return None
        else:
            raise TypeError(f"Invalid room type {type(room)}")
    
    def get_rooms(self) -> list[Room]:
        return self.rooms
    
    def room_exists(self, name: str) -> bool:
        for room in self.rooms:
            if room.name == name:
                return True
        return False

    def get_data(self, key: str):
        if key in self.data:
            return self.data[key]
        else:
            return None
    
    def set_data(self, key: str, value):
        self.data[key] = value
    

    def get_setting(self, setting: str):
        if setting not in self.settings:
            warn(f"Setting {setting} not found.")
            return None
        return self.settings[setting]
    
    def set_setting(self, setting: str, value):
        # We'll do some type conversion here to make it easier to work with
        # Look for boolean values, then try to convert to int, then float
        if value in ["False", "True"]:
            value = value == "True"
        elif isinstance(value, str):
            # Try to convert to int
            try:
                value = int(value)
            except ValueError:
                # If that failed, try to convert to float
                try:
                    value = float(value)
                except ValueError:
                    # Don't crash or anything, just assign the value normally
                    pass
                
        self.settings[setting] = value

    def end_game(self, reason: str):
        """
        Stores that the game should quit for the provided reason.
        reason should be a key in the gameover dictionary.
        """
        self.gameover[reason] = True

    def should_end_game(self) -> bool:
        """
        Return whether the game should end.
        """
        if any(self.gameover.values()):
            return True

    def get_time_string(self) -> str:
        return f"{self.get_data('time')//3600:02}:{(self.get_data('time')%3600)//60:02}"

    def tick_time(self) -> int:
        """
        Update the in-game clock according to the time scale.
        Returns the number of in-game seconds since the previous tick.
        """
        # Create a "static" variable to store the previous timestamp within this function
        # This is because no other function needs to know about this variable
        if not self.get_data("prev_tick"):
            self.set_data("prev_tick", datetime.now())

        current_time = datetime.now()
        time_delta = current_time - self.get_data("prev_tick")
        self.set_data("prev_tick", current_time)
        seconds_passed = time_delta.total_seconds()
        scaled_seconds = int(seconds_passed * self.get_setting("timescale"))

        new_time = self.get_data("time") + scaled_seconds
        self.set_data("time", new_time)

        # And update anomaly timers
        self.set_data("seconds_since_last_anomaly_check", self.get_data("seconds_since_last_anomaly_check") + scaled_seconds)
        self.set_data("seconds_since_last_anomaly", self.get_data("seconds_since_last_anomaly") + scaled_seconds)

        return scaled_seconds

    def over_time(self) -> bool:
        """
        Return whether the game is over the time limit.
        """
        return self.get_data("time") >= self.get_setting("max_seconds")
    
    def too_many_anomalies(self) -> bool:
        """
        Return whether there are too many anomalies active.
        """
        return self.get_data("active_anomalies") >= self.get_setting("max_anomalies")

    def number_of_anomalies_to_create(self) -> int:
        """
        Return the number of anomalies to spawn based on the anomaly probability
        and time since the last anomaly check. Only creates one per time
        specified in the settings, but can create more than one if the time
        since the last anomaly check is greater than the time specified in the settings.
        """
        SECONDS_BETWEEN_CHECKS = 60

        # Raise an error if the number of rooms is fewer than the max number of anomlies
        if len(self.get_rooms()) < self.get_setting("max_anomalies"):
            raise ValueError(f"Number of rooms {len(self.get_rooms())} is fewer than the max number of anomalies {self.get_setting('max_anomalies')}.")

        # Work out how many anomalies to try to spawn based on the time since the last anomaly check

        last_check = self.get_data("seconds_since_last_anomaly_check")
        last_anomaly = self.get_data("seconds_since_last_anomaly")
        min_between = self.get_setting("min_seconds_between_anomalies")
        p = self.get_setting("probability")
        n_active = self.get_data("active_anomalies")
        n_max = self.get_setting("max_anomalies")
        n_rooms = len( [r for r in self.get_rooms() if not r.get_anomaly()] )

        n_checks = last_check // SECONDS_BETWEEN_CHECKS # e.g., if 120 seconds have passed, and checking every 60 seconds, we should check twice
        
        # If there hasn't been enough time between anomalies, just don't bother and reset the checks
        if last_anomaly < min_between:
            n_checks = 0
        else:
            last_anomaly -= (n_checks-1) * SECONDS_BETWEEN_CHECKS # Go "back in time" to the last check
            last_anomaly = max(0, last_anomaly) # Make sure we don't go negative, but we shouldn't need to

        num_to_spawn = 0

        for _ in range(n_checks):
            spawning_is_valid = n_active < n_max and n_rooms > 0
            last_anomaly += SECONDS_BETWEEN_CHECKS
            if not spawning_is_valid:
                continue # Skip to continue simulating time passing

            try_to_spawn = random.random() < p

            if last_anomaly >= min_between and try_to_spawn:
                n_active += 1
                num_to_spawn += 1
                n_rooms -= 1
                last_anomaly = 0
        
        self.set_data("seconds_since_last_anomaly_check", last_check % SECONDS_BETWEEN_CHECKS)
        self.set_data("seconds_since_last_anomaly", last_anomaly)
        
        return num_to_spawn

    def register(self, name: str):
        """
        Register an anomaly.
        """
        self.anomalies.append(name.upper())

    def is_registered_anomaly(self, name: str) -> bool:
        """
        Return whether the name is a registered anomaly.
        """
        return name.upper() in self.anomalies

    def add_anomaly(self, name: str, room: Room, modified_item_list: list[str]) -> bool:
        """
        Add an anomaly to the list of anomalies, unless there is already an active anomaly in the room.
        Adds the name to the list of active anomalies and modifies the list of items in the room.

        Return True if the anomaly was added, False otherwise.
        """
        if room.get_anomaly():
            if self.get_setting("debug"):
                print(f"Anomaly {name} not added to room {room.name} because there is already an anomaly in it.")
            return False
        
        name = name.upper()
        if not self.is_registered_anomaly(name):
            raise ValueError(f"Anomaly {name} not registered.")
        
        added = room.add_anomaly(name, modified_item_list)
        
        if added:
            self.set_data("active_anomalies", self.get_data("active_anomalies") + 1)                
            self.set_data("seconds_since_last_anomaly", 0)
            if self.get_setting("debug"):
                print(f"Anomaly {name} added to room {room.name} with updated items {room.anomaly_items}.")
            return True
        else:
            if self.get_setting("debug"):
                print(f"Anomaly {name} not added to room {room.name} because the modified items {modified_item_list} are the same as the current items {room.items}.")
            return False
 

    def print_warning(self):
        if self.get_data("active_anomalies") >= self.get_setting("max_anomalies")-1:
            print(f"{'='*40}\n!! WARNING !!: Too many anomalies active at one time. Report anomalies soon or you will fail your shift.\n{'='*40}\n")

    def print_help(self):
        print("COMMANDS:")
        print("  next   (n) or <enter>: Go to the next camera")
        print("  prev   (p): Go to the previous camera")
        print("  report (r) : Report an anomaly, will prompt for additional details.")
        print("  quit   (q): Quit the game")
        print("  help   (h, ?): Print this help message")
    
    def print_ingame_time(self):
        """
        Print the current in-game time in the format HH:MM.
        """
        time = self.get_data("time")
        hours = time // 3600
        minutes = (time % 3600) // 60
        time = f"{hours:02}:{minutes:02}"
        print(f"TIME: {time}")

    def print_camera(self, index: int = None):
        if index is None:
            index = self.get_data("camera")
        if len(self.rooms) == 0:
            raise ValueError("No rooms added to the game.")

        room = self.get_rooms()[index]

        if room.get_anomaly():
            if "CAMERA MALFUNCTION" in room.get_anomaly():
                # Skip to the next camera without a malfunction
                next_index = self.next_camera()
                if next_index == -1:
                    print("ALL CAMERAS OFFLINE")
                    return
                
                room = self.get_rooms()[next_index]
                if room.get_anomaly():
                    items = room.anomaly_items[:]
                else:
                    items = room.items[:]
            else:
                items = room.anomaly_items[:]
        else:
            items = room.items[:]
        
        print(f"CAMERA {index+1:02}: {room.name.upper()}")
        for item_index, item in enumerate(items):
            print(f"  [{item_index}] {item}")

    def print_gameover(self):
        """
        Prints the game over screen data.
        """
        self.clear()
        found_count = self.get_data("found_anomalies")
        total_count = found_count + self.get_data("active_anomalies")
        time = self.get_time_string()

        if self.gameover["anomalies"]:
            print("GAME OVER\nYou have failed your shift. Too many anomalies active at one time.")
            print("Active Anomalies:")
            for room in self.get_rooms():
                if room.get_anomaly():
                    print(f"  {room.name.upper()}: {room.get_anomaly()}")

        elif self.gameover["timeup"]:
            print("GAME OVER\nCongratulations! You have completed your shift.")
        elif self.gameover["quit"]:
            print("GAME OVER\nYou have quit your shift.")
        
        print(f"Time: {time}")
        print(f"FOUND: {found_count} out of {total_count} total anomalies.")
        print(f"\n")

    def get_report(self) -> tuple[int, int]:
        """
        Handles the user input for reporting an anomaly.

        Return a tuple of the room index and the anomaly index, or -1 -1 if the user cancelled.
        """

        print(f"REPORTING ANOMALY\n{'-'*20}")
        print("  Which room is the anomaly in?")
        for i, room in enumerate(self.get_rooms()):
            print(f"    [{i+1:02}] {room.name.upper()}")
        while True:
            room_index = int(input("Enter a Room Number (-1 to cancel)\n>> "))
            if room_index < -1 or room_index > len(self.get_rooms()):
                print(f"Invalid room number {room_index}. Please enter a number between 1 and {len(self.get_rooms())} or -1 to cancel.")
            elif room_index == -1:
                print("Cancelling report.")
                return -1, -1
            else:
                break

        print(f"  What is the anomaly?")
        for i, anomaly_name in enumerate(self.anomalies):
            print(f"    [{i+1:02}] {anomaly_name.upper()}")
        while True:
            anomaly_index = int(input("Enter an Anomaly Number (-1 to cancel)\n>> "))
            if anomaly_index == -1:
                print("Cancelling report.")
                return -1, -1
            elif anomaly_index < 1 or anomaly_index > len(self.anomalies):
                print(f"Invalid anomaly number {anomaly_index}. Please enter a number between 1 and {len(self.anomalies)} or -1 to cancel.")
            else:
                break

        # -1 because we'll start at 0 for the user interface, but we really want the index
        return room_index-1, anomaly_index-1
    
    def report(self, room_index, anomaly_index) -> bool:
        """
        Sleeps for a few seconds and if the anomaly is active in the room, it fixes it and returns True.
        """
        self.clear()
        if anomaly_index < 0 or anomaly_index >= len(self.anomalies):
            print(f"Invalid anomaly index.")
            return False
        if room_index < 0 or room_index >= len(self.get_rooms()):
            print(f"Invalid room index.")
            return False
        
        anomaly = self.anomalies[anomaly_index]
        room = self.get_rooms()[room_index]

        print(f"Checking for anomaly {anomaly} in room {room.name}", end="", flush=True)
        for _ in range(int(self.get_setting("anomaly_report_time"))):
            print(".", end="", flush=True)
            time.sleep(1)
        
        if room.get_anomaly() == anomaly.upper():
            print(f"\nAnomaly [{anomaly}] found in room [{room.name}]!")
            print(f"Fixing anomaly...")
            time.sleep(1)
            room.anomaly = ""
            room.anomaly_items = []
            self.set_data("active_anomalies", self.get_data("active_anomalies") - 1)
            self.set_data("found_anomalies", self.get_data("found_anomalies") + 1)
            print(f"Anomaly fixed.")
            return True
        else:
            time.sleep(1)
            print(f"\nAnomaly [{anomaly}] not found in room [{room.name}].")
            return False
        
    def next_camera(self, reverse=False) -> int:
        """
        Change to the correct camera.
        Return the index of the next camera to observe, skipping broken cameras and looping around. 
        Returns -1 if there are no cameras to observe.
        """
        if len(self.get_rooms()) == 0:
            raise ValueError("No rooms added to the game.")
        
        next_index = self.get_data("camera")
        inc = 1 if not reverse else -1

        for _ in range(0, len(self.get_rooms())):
            next_index = (next_index + inc) % len(self.get_rooms())
            room = self.get_room(next_index)
            if "CAMERA MALFUNCTION" in room.get_anomaly():
                continue
            else:
                self.set_data("camera", next_index)
                return next_index

        return -1
    
    def clear(self):
        """
        Clear the screen.
        """
        os.system('cls' if os.name == 'nt' else 'clear')

GAME_DATA = GameManager()

def init(anomalies: list[str] = None, rooms: list[str] = None, room_items: list[str] = None, **settings) -> None:
    """
    Sets up a new game with the given timescale, rooms, and room items.

    Defaults to a timescale of 10 minutes per minute, and a list of rooms and room items, 
    10% probability per in-game minute to create anomaly
    """
    global GAME_DATA

    GAME_DATA.clear()

    # **kwargs is a special parameter that allows us to pass in any number of keyword arguments
    # and they will be stored in a dictionary called kwargs; 
    for key, value in settings.items():
        GAME_DATA.set_setting(key, value)

    if rooms is not None and room_items is not None:
        # Zip is a cool function which takes two lists and combines them into a list of tuples
        # Then we can loop over this with a single loop!
        for room, items in zip(rooms, room_items):
            GAME_DATA.add_room(room, items)

    if anomalies is not None:
        for anomaly in anomalies:
            GAME_DATA.register(anomaly)

    if GAME_DATA.get_setting("debug"):
        print("=== DEBUG INFORMATION ===")
        print(f"Registered Anomalies: {GAME_DATA.anomalies}")
        print(f"Rooms: ")
        for room in GAME_DATA.get_rooms():
            print(f"  {room.name}: {len(room.items)} items")
        print(f"Settings (when init() was called): ")
        for key, value in GAME_DATA.settings.items():
            print(f"  {key}: {value}")
        print("========================\n")

    

    print("Welcome to 'I Am On Duty Watching Changes to Rooms'!")
    print("Your Mission:")
    print(" - Watch cameras for changes to the rooms.")
    print(" - Type 'n' or 'p' to go to the next or previous camera.")
    print(" - Report anomalies to the control room by typing r and selecting the room and anomaly.")
    print("    - You will be asked to input a room number, then an anomaly number.")
    print("    - The only penalty for reporting incorrect anomalies is the time it took to report, so try it out!")
    print(f" - You have {GAME_DATA.get_setting('max_seconds')/3600:.2f} hours in-game to complete your shift.")
    print(f" - For every second that passes in real life, {GAME_DATA.get_setting('timescale')} seconds will pass in-game.")
    print(f" - You can only have {GAME_DATA.get_setting('max_anomalies')} anomalies active at one time before losing the game.")
    print(f" - Changes will begin after {GAME_DATA.get_setting('min_seconds_between_anomalies')/60:.2f} in-game minutes.")
    print("Type 'help' for a list of commands.")
    print("Good luck!")
    response = input("Press enter to begin or `help` to see a list of commands.\n>> ")

    if response.lower() == "help":
        GAME_DATA.print_help()
        input("Press enter to begin.")

    
    GAME_DATA.tick_time()
    GAME_DATA.clear()

def display() -> None:
    """
    Prints all in-game information to the screen.
    If show_active_count is True, also prints the number of active anomalies.
    """
    global GAME_DATA

    if GAME_DATA.should_end_game():
        GAME_DATA.print_gameover()
    else:
        if GAME_DATA.get_setting("debug"):
            print(f"(DEBUG) Active Anomalies: {GAME_DATA.get_data('active_anomalies')}")

        GAME_DATA.print_warning()
        GAME_DATA.print_ingame_time()
        GAME_DATA.print_camera()

def handle_input(clear=True) -> None:
    """
    Handle input from the user and run the appropriate command.

    Ticks time forward after the command is entered.

    Params:
        clear: Whether to clear the screen after accepting input.
    """
    global GAME_DATA

     

    if GAME_DATA.should_end_game():
        input("Press enter to exit.")
        quit()
    
    cmd = input(">> ").lower().strip().split()

    if len(cmd) == 0:
        cmd = ["next"]

    if clear:
        GAME_DATA.clear()

    match cmd:
        case ['next'| 'n']:
            GAME_DATA.next_camera(reverse=False)
        case ["prev" | "p"]:
            GAME_DATA.next_camera(reverse=True)
        case ["report" | "r"]:
            room, anomaly = GAME_DATA.get_report()
            if room != -1 and anomaly != -1:
                GAME_DATA.report(room, anomaly)
        case ["quit" | "q"]:
            GAME_DATA.end_game("quit")
        case ["help" | "h" | "?"]:
            GAME_DATA.print_help()
        case _:
            print(f"Invalid command \"{cmd}\". Type \"help\" for a list of commands.")

    GAME_DATA.tick_time()  

def update() -> bool:
    """
    Update the game data according to the command that was run.

    Return True if the game should continue, False otherwise. 
    """
    global GAME_DATA
    
    if  GAME_DATA.over_time():
        GAME_DATA.end_game("timeup")
    
    elif GAME_DATA.too_many_anomalies():
        GAME_DATA.end_game("anomalies")
    
    return not GAME_DATA.should_end_game()

def rooms_without_anomalies() -> list[str]:
    """
    Return a list of all room names without anomalies.
    """
    global GAME_DATA

    rooms = []
    for i, room in enumerate(GAME_DATA.get_rooms()):
        if not room.get_anomaly():
            rooms.append(room.name)
    return rooms

def number_of_anomalies_to_create() -> int:
    """
    Return the number of anomalies to spawn based on the anomaly probability
    and time since the last anomaly check.
    """
    global GAME_DATA
    return GAME_DATA.number_of_anomalies_to_create()

def register_anomaly(name: str):
    """
    Adds the name to the list of registered anomalies.
    """
    global GAME_DATA
    GAME_DATA.register(name)

def add_anomaly(name: str, room: Union[str, int], modified_item_list: list[str]) -> bool:
    """
    Add an anomaly to the list of anomalies, unless there is already an active anomaly in the room.
    Adds the name to the list of active anomalies and modifies the list of items in the room.

    Return True if the anomaly was added, False otherwise.
    """
    global GAME_DATA

    room = GAME_DATA.get_room(room)

    if room is None:
        return False
    else:
        return GAME_DATA.add_anomaly(name, room, modified_item_list)

def get_rooms() -> list[str]:
    """
    Return a copy of the list of rooms.
    """
    return GAME_DATA.get_rooms()[:]

def get_random_unchanged_room() -> str:
    """
    Return a random room that has no anomaly in it.
    """
    global GAME_DATA

    rooms = rooms_without_anomalies()
    if len(rooms) == 0:
        return None
    else:
        return random.choice(rooms)

def add_room(room_name: str, room_items: list[str]) -> bool:
    """
    Add a room to the list of rooms to observe; does not add duplicates.

    Return True if the room was added, False otherwise.
    """
    global GAME_DATA

    return GAME_DATA.add_room(room_name, room_items)

def get_room_items(room: Union[str, int]) -> list[str]:
    """
    Return a copy of the list of items in the room.
    """
    global GAME_DATA

    room = GAME_DATA.get_room(room)
    if room is None:
        return []
    else:
        return room.items[:]
    
def get_random_anomaly() -> str:
    """
    Return a random registered anomaly.
    """
    return random.choice(GAME_DATA.anomalies)

def set_setting(setting: str, value):

    """
    Set a game setting.
    """
    global GAME_DATA

    GAME_DATA.set_setting(setting, value)
