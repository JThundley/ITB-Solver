#!/usr/bin/env python3

# This script brute forces the best possible single turn in Into The Breach
############# NOTES ######################
# Order of turn operations:
#   0 Fire
#   1 Environment
#   2 Enemy Actions
#   3 NPC actions
#   4 Enemies emerge

############ IMPORTS ######################

############### GLOBALS ###################

############### FUNCTIONS #################

############### CLASSES #################
class GameBoard():
    "This represents the game board and some of the most basic rules of the game."
    def __init__(self, powergrid_hp=7):
        self.board = {} # a dictionary of all 64 squares on the board. Each key is a coordinate and each value is a list of the tile object and unit object: {'a1': [Tile, Unit]}
        for letter in 'abcdefgh':
            for num in range(1, 9):
                self.board['%s%i' % (letter, num)] = [None, None]
        self.powergrid_hp = powergrid_hp # max is 7

class Tile():
    "This object is a normal tile. All other tiles are based on this."
    def __init__(self, name='normal', effect=None, environment=None, flammable=False, desert=False, air=False, water=False):
        self.name = name # Name or type of tile
        self.effect = effect # Current effect on the tile such as fire, smoke, acid, mine, freezemine. Effects are on top of the tile and can be removed by having your mech repair while on the tile.
                            # these effects are immediately applied to any unit that stops on the tile.
        self.environment = environment # environmental effects targeting the tile that take place at the end of the player turn. https://intothebreach.gamepedia.com/Environments
                                        # possible environment effects are vekemerge, airstrike, fallingrock, hightide, icestorm, lavaflow, lightning, seismic, tentacles, volcanicfireball
        self.flammable = flammable # This tile turns to fire if damaged if true.
        self.desert = desert # this tile turns to smoke if damaged if true.
        self.air = air # indicates that units can walk on this tile.
        self.water = water # indicates if this is a water tile
    def takeDamage(self, damage):
        "Process the tile taking damage. Damage is an int of how much damage to take, but tiles ignore this. return nothing."
        if self.flammable:
            self.effect = 'fire'
        elif self.desert:
            self.effect = 'smoke'

class Tile_Air(Tile):
    "This tile is an empty chasm. If walking units are pushed here, they die."
    def __init__(self, name='air', effect=None, environment=None, flammable=False, desert=False, air=True):
        super(Tile_Air, self).__init__(*args)

class Tile_Water(Tile):
    "This tile is an empty chasm. If walking units are pushed here, they die."
    def __init__(self, name='water', water=True):
        super(Tile_Water, self).__init__(*args)

class Tile_Grassland(Tile):
    "This is a regular tile that needs to be terraformed back into sand by the terraformer"
    def __init__(self, name='grassland'):
        super().__init__(*args)

a = Tile_Grassland

class Tile_Terraformed(Tile):
    "This is a tile that has been terraformed by the terraformer"
    def __init__(self, name='terraformed'):
        super(Tile_Terraformed, self).__init__()


############## PROGRAM FLOW FUNCTIONS ###############

############## MAIN ########################
if __name__ == '__main__':
    pass
