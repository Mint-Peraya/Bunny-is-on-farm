from game import Game
from stattk import *
from login import *

if __name__ == "__main__":
    auth = AuthSystem()
    user_id = auth.run()
    print(f"Logged in with user ID: {user_id}")  # You can use this ID to save game data
    Game().run()