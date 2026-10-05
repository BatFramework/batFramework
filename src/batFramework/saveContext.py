import batFramework as bf
from typing import Callable


class SaveContext:
    """
        This class will allow the user to register key value pairs where keys are 
        what they want to save, it's getter method, and a default value or fallback method 
        examples : 
        SaveContext().add("player_inventory",self.player.inventory.serialize, Inventory().serialize)
        SaveContext().add("player_health",lambda : self.player.maxhp, 16) # or grab the value from a list of constants for initialization/game start 

        methods like load(self, data) and save(self)->data are used to serialize/deserialize the save
        
    """