#!/usr/bin/env python3
from itbsolver import *
from itertools import permutations
from copy import deepcopy

g = Game()
# set forest tiles:
for sq in (3, 8), (3, 4), (3, 6), (5, 8), (8, 8), (8, 6):
    g.board[sq].replaceTile(Tile_Forest(g))
# set water tiles:
for sq in (1, 6), (1, 2), (1, 1), (2, 1), (3, 1), (4, 1):
    g.board[sq].replaceTile(Tile_Water(g))
# create 1hp buildings:
for sq in (4, 7), (6, 7), (7, 7):
    g.board[sq].createUnitHere(Unit_Building(g, hp=1, maxhp=1))
# create 2hp buildings:
for sq in (2, 4), (2, 5), (7, 4), (7, 5):
    g.board[sq].createUnitHere(Unit_Building(g, hp=2, maxhp=2))
# the only mountain:
g.board[(1, 5)].createUnitHere(Unit_Mountain(g))
# the only damaged mountain:
g.board[(1, 4)].createUnitHere(Unit_Mountain_Damaged(g))
# set tiles on fire:
for sq in (3, 4), (4, 6):
    g.board[sq].applyFire()
# set vekemerge tiles:
g.vekemerge.squares = [(4, 2), (5, 1)]
# Create friendly units:
g.board[(5, 6)].createUnitHere(Unit_OldArtillery(g))
g.board[(4, 4)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery(g)))
g.board[(4, 3)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(g))) # TODO: weapon 2 is viscera nanobots
g.board[(7, 8)].createUnitHere(Unit_Leap_Mech(g, hp=7, maxhp=8, weapon1=Weapon_HydraulicLegs(g), attributes={Attributes.IMMUNEFIRE, Attributes.MASSIVE}))
# Create enemies:
g.board[(2, 2)].createUnitHere(Unit_Firefly(g, hp=2, qshot=(Direction.UP,)))
g.board[(3, 2)].createUnitHere(Unit_BlastPsion(g))
g.board[(5, 3)].createUnitHere(Unit_Hornet(g, qshot=(Direction.LEFT,)))
g.board[(4, 6)].createUnitHere(Unit_AlphaScarab(g, hp=1, qshot=(Direction.DOWN, 3), effects={Effects.FIRE}))

# print("Simulation starting")
# g.start()
# assert g.board[(4, 6)].unit.effects == {Effects.FIRE, Effects.EXPLOSIVE} # make sure vek got explosive
# assert g.board[(4, 6)].unit.gotfire == False # make sure that alpha scarab didn't "get" fire, it was on fire before this turn started.
#
# # get the scorekeeper out so we can use it in different simulations:
# sk = g.score
#
# for pcu in permutations(g.playerunits): # For each possible order of the player controlled units:
#     thisgame = deepcopy(g) # set up a new board for this simulation and
#     thisgame.score = sk # replace the copy of the scorekeeper with one we intend to use throughout.
#     for unit in pcu: # TODO: we also need to allow units to move, then other units move, then the first shoot. more permutations
#         for position in unit.getMoves():
#             if thisgame.board[position].unit: # if the square is occupied...
#                 if unit.square != position: # and it's not occupied by this unit itself
#                     continue # we can't move to it
#             thisgame.board[unit.square].moveUnit(position)
#             for weapon in 'repweapon', 'weapon1', 'weapon2':
#                 if getattr(unit, weapon, False): # if the mech has this type of weapon...
#                     for shot in getattr(unit, weapon).genShots():
#                         getattr(unit, weapon).shoot(*shot)

ag = AttemptGenerator(g)
for i in ag.gen():
    pass
    #print(i)