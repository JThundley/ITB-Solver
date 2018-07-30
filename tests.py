"These are u nit tests for itbsolver. All test functions must start with t_ to differentiate them from the functions of the main script."

from itbsolver import *

def runTest(funcname):
    "This runs the function funcname and prints information about the tests. This prints out the name of the function, and then PASSED if assertion errors didn't short-circuit this whole script."
    print("%s: " % funcname[2:], end='')
    globals()[funcname]()
    print('PASSED')

def t_bumpDamage():
    "2 units bump into each other and take 1 damage each."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    b.board[(2, 1)].putUnitHere(Unit_Alpha_Beetle(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].unit.currenthp == 5
    b.push((2, 1), Direction.LEFT)
    assert b.board[(1, 1)].unit.currenthp == 2
    assert b.board[(2, 1)].unit.currenthp == 4

def t_forestCatchesFire():
    "A forest tile takes damage and catches fire."
    b = GameBoard()
    b.board[(1, 1)] = Tile_Forest(square=(1, 1), gboard=b)
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}

def t_fireTurnsIceToWater():
    "An ice tile takes fire damage and turns to water"
    b = GameBoard()
    b.board[(1, 1)] = Tile_Ice(square=(1, 1), gboard=b)
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].type == "water"

def t_shieldBlocksTileFire():
    "A shielded unit is hit with fire which blocks the unit from catching fire while the shield remains. The tile is set on fire."
    b = GameBoard()
    print(b.board[(1, 1)].effects)
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b, effects={Effects.SHIELD}))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_IceAndShieldHitWithFire():
    "A frozen unit with a shield is hit by fire. The ice is removed, the shield remains, the tile catches on fire."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b, effects={Effects.SHIELD, Effects.ICE}))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_ShieldRemovedOnFireTile():
    "A shielded unit is put onto a fire tile. The unit takes a hit which removes the shield and the unit catches fire."
    b = GameBoard()
    b.board[(1, 1)].applyFire()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b, effects={Effects.SHIELD}))
    #print(b.board[(1, 1)].unit.square)
    #print(b.board[(1, 1)].unit.gboard)
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.currenthp == 3
    #print("Unit effects are:", b.board[(1, 1)].unit.effects)
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}



# A flying unit that is on fire that moves to a water tile remains on fire
# A flying unit that is frozen on water remains frozen because the tile under it becomes ice instead of water.
# A flying unit or ground unit that is frozen and is then moved onto a water tile is unfrozen.
# A water tile that is hit with ice becomes an ice tile
# A ground unit that is on fire that moves into a water tile is no longer on fire.
# A unit that repairs in a smoke cloud (because camilla allows actions while smoked) does NOT remove the smoke.
# When a water tile has acid on it, it becomes an acid water tile. A flying unit repairing here does NOT remove the acid.
#   When this is frozen, it becomes a frozen acid tile that behaves just like an ice tile. When this frozen acid tile is destroyed, it becomes a regular water tile. Hence, freezing acid effectively removes it.
# A flying unit on an acid water tile does not get acid on it.
# If a forest tile gets acid on it, the forest is removed and it is no longer flammable from damage.
# if a tile with acid on it is frozen, nothing happens. The acid remains.
# A frozen tile that is hit with fire breaks the ice, catches the tile and unit on fire.
# A mountain takes 5 damage and becomes a damaged mountain. It takes another 5 damage and becomes a normal tile. Mountains need 2 hits to become regular tiles, the amount of damage doesn't matter.
if __name__ == '__main__':
    g = sorted(globals())
    for test in [x for x in g if x.startswith('t_')]:
        runTest(test)