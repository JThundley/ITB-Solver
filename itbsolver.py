#!/usr/bin/env python3

# This script brute forces the best possible single turn in Into The Breach
############# NOTES ######################

############ IMPORTS ######################

############### GLOBALS ###################

############### FUNCTIONS #################

############### CLASSES #################
class GameBoard():
    "This represents the game board and some of the most basic rules of the game."
    def __init__(self, powergrid_hp=7):
        self.board = {} # a dictionary of all 64 squares on the board. Each key is a coordinate to a tile type: {'a1': TileType}
        for letter in 'abcdefgh':
            for num in range(1, 9):
                self.board['%s%i' % (letter, num)] = None
        self.powergrid_hp = powergrid_hp # max is 7
############## PROGRAM FLOW FUNCTIONS ###############

############## MAIN ########################
if __name__ == '__main__':
    pass
