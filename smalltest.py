#!/usr/bin/env python3
from itbsolver import *

g = Game()
# put mountains on every tile:
for x in range(1, 9):
    for y in range(1, 9):
        g.board[(x, y)].createUnitHere(Unit_Mountain(g))

# Create friendly units:
g.board[(1, 1)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(g))) # TODO: weapon 2 is viscera nanobots
# Create enemies:
g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, qshot=(Direction.LEFT,)))

# Make a little more space for suboptimal sims
g.board[(1, 2)].unit = None
g.board[(2, 2)].unit = None

# init a blank score
highestscore = ScoreKeeper()

for i in OrderGenerator(g):
    try:
        os = OrderSimulator(g, i)
    except SimulationFinished: # this can happen when there were no valid actions to be taken.
        continue # In this instance, we try to simulate the mech moving everywhere, but it can't move at all because it's blocked in.
    highscore = os.run()
    if highscore:
        if highscore > highestscore:
            highestscore = highscore
    #print(i)

print("Solution found:", highestscore)