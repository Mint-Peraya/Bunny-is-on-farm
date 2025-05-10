from game import Game
from stattk import *
from login import *

if __name__ == "__main__":
    # Run login system
    auth_system = AuthSystem()
    user_id = auth_system.run()  # This returns the user_id when login is successful
    
    # Get username from login fields
    username = auth_system.fields["username"].text

    # Start game with the logged in username
    game = Game(username)
    game.run()