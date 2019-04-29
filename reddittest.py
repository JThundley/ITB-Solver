#!/usr/bin/env python3
from itbsolver import *

# This is a test of https://old.reddit.com/r/IntoTheBreach/comments/bgmz5f/help_jet_move_5_pulse_4_rocket_3_default_weapons/

g = Game()

# sand tile:
g.board[(2, 6)].replaceTile(Tile_Sand(g))

# Mountains:
for sq in (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (3, 6), (7, 3), (7, 4), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 8):
    g.board[sq].createUnitHere(Unit_Mountain(g))

# Single power buildings:
for sq in (3, 8), (4, 8), (5, 8), (7, 6):
    g.board[sq].createUnitHere(Unit_Building(g, hp=1, maxhp=1))

# 2 power buildings:
for sq in (3, 5), (4, 5), (7, 5):
    g.board[sq].createUnitHere(Unit_Building(g, hp=2, maxhp=2))

# objective building
g.board[(4, 6)].createUnitHere(Unit_Building_Objective(g, hp=1, maxhp=1))

# prototype bombs:
for sq in (2, 4), (4, 3):
    g.board[sq].createUnitHere(Unit_PrototypeRenfieldBomb(g))

# Emerging vek:
g.vekemerge.squares = [(6, 2), (6, 3)]

# Create friendly units:
g.board[(2, 5)].createUnitHere(Unit_Rocket_Mech(g, weapon1=Weapon_RocketArtillery(g), weapon2=Weapon_StormGenerator(power1=True), moves=3))
g.board[(5, 5)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(g), moves=5))
g.board[(6, 5)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(g), moves=4))

# Create enemies:
#g.board[(2, 2)].createUnitHere(Unit_Scorpion(g, qshot=(Direction.LEFT,)))
g.board[(2, 3)].createUnitHere(Unit_AlphaHornet(g, qshot=(Direction.UP,)))
g.board[(3, 4)].createUnitHere(Unit_Hornet(g, qshot=(Direction.LEFT,)))
g.board[(4, 2)].createUnitHere(Unit_BlastPsion(g))

# init a blank score
highestscore = ScoreKeeper()

# Get a count of how many orders we need to simulate:
totalorders = 0
for i in OrderGenerator(g):
    totalorders += 1

currentorder = 0
totalsims = 0
for i in OrderGenerator(g):
    currentorder += 1
    print('Order {0}/{1}, {2} simulations.'.format(currentorder, totalorders, totalsims))
    try:
        os = OrderSimulator(g, i)
    except SimulationFinished: # this can happen when there were no valid actions to be taken.
        continue
    try:
        sims, highscore = os.run()
    except TypeError: # os.run was the empty order that we skipped
        continue
    totalsims += sims
    if highscore:
        if highscore > highestscore:
            highestscore = highscore

print("Solution found:", highestscore)