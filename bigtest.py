#!/usr/bin/env python3
from itbsolver import *

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

for i in OrderGenerator(g):
    os = OrderSimulator(g, i)
    os.run()
    #print(i)