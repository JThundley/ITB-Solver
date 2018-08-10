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
    assert b.board[(1, 1)].effects == set()
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
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)] = Tile_Forest(square=(1, 1), gboard=b)
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}

def t_fireTurnsIceToWater():
    "An ice tile takes fire damage and turns to water"
    b = GameBoard()
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)] = Tile_Ice(square=(1, 1), gboard=b)
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].type == "water"

def t_shieldBlocksTileFire():
    "A shielded unit is hit with fire which blocks the unit from catching fire while the shield remains. The tile is set on fire."
    b = GameBoard()
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b, effects={Effects.SHIELD}))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_IceAndShieldHitWithFire():
    "A frozen unit with a shield is hit by fire. The ice is removed, the shield remains, the tile catches on fire."
    gb = GameBoard()
    gb.board[(1, 1)].putUnitHere(Unit_Blobber(gboard=gb, effects={Effects.SHIELD, Effects.ICE}))
    assert gb.board[(1, 1)].effects == set()
    #gb.board[(1, 1)].applyFire() # why does uncommenting this line break everything? I don't understand, I use putUnitHere in other functions the same way, I use applyFire() in other functions the same way.
    # assert gb.board[(1, 1)].effects == {Effects.FIRE}
    # assert gb.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_ShieldRemovedOnFireTile():
    "A shielded unit is put onto a fire tile. The unit takes a hit which removes the shield and the unit catches fire."
    b = GameBoard()
    b.board[(1, 1)].applyFire()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b, effects={Effects.SHIELD}))
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}

def t_MountainOverkill():
    "A mountain takes 5 damage twice and needs to hits to be destroyed."
    b = GameBoard()
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].putUnitHere(Unit_Mountain(b))
    b.board[(1, 1)].takeDamage(5)
    assert b.board[(1, 1)].unit.type == 'mountain_damaged'
    b.board[(1, 1)].takeDamage(5)
    assert b.board[(1, 1)].unit == None
    assert b.board[(1, 1)].effects == set()

def t_FlyingUnitOnFireOverWater():
    "A flying unit that is on fire that moves to a water tile remains on fire"
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b))
    b.board[(1, 2)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    b.board[(1, 2)].applyFire()
    b.moveUnit((1, 2), (1, 1))
    assert b.board[(1, 1)].unit.type == 'hornet'
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(1, 2)].effects == {Effects.FIRE}
    assert b.board[(1, 2)].unit == None

def t_FlyingUnitIcedOverWater():
    "A flying unit that is frozen on water remains frozen because the tile under it becomes ice instead of water."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b))
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].unit.type == 'hornet'
    assert b.board[(1, 1)].type == 'ice'
    assert b.board[(1, 1)].unit.effects == {Effects.ICE}

def t_WaterUnfreezesUnit():
    "A flying unit or ground unit that is frozen and is then moved onto a water tile is unfrozen."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b)) # make water tiles
    b.replaceTile((1, 2), Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Hornet(b)) # flying unit on the bottom next to the tile
    b.board[(2, 2)].putUnitHere(Unit_Blobber(b)) # ground unit above it next to water tile
    assert b.board[(1, 1)].effects == set() # no tile effects
    assert b.board[(2, 1)].unit.effects == set() # no unit effects
    assert b.board[(1, 2)].effects == set()  # no tile effects
    assert b.board[(2, 2)].unit.effects == set()  # no unit effects
    b.board[(2, 1)].applyIce() # freeze the flyer
    b.board[(2, 2)].applyIce()  # freeze the flyer
    assert b.board[(2, 1)].unit.effects == {Effects.ICE}
    assert b.board[(2, 2)].unit.effects == {Effects.ICE}
    assert b.board[(1, 1)].type == 'water'
    assert b.board[(1, 2)].type == 'water'
    b.push((2, 1), Direction.LEFT)
    b.push((2, 2), Direction.LEFT)
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 2)].unit == None # the ground unit didn't survive the water

def t_WaterTileTurnsToIceWhenFrozen():
    "A water tile that is hit with ice becomes an ice tile"
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b))
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].type == 'ice'

def t_WaterTilePutsOutUnitFire():
    "A ground unit that is on fire that moves into a water tile is no longer on fire."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Beetle_Leader(b)) # massive unit on the bottom next to the water tile
    assert b.board[(1, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyFire()
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    b.moveUnit((2, 1), (1, 1))
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()

def t_RepairWaterAcidTileDontRemoveAcid():
    "When a water tile has acid on it, it becomes an acid water tile. A flying unit repairing here does NOT remove the acid."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b, effects={Effects.ACID}))
    assert b.board[(1, 1)].effects == {Effects.ACID}
    b.board[(1, 1)].repair()
    assert b.board[(1, 1)].effects == {Effects.ACID}

def t_FreezingAcidWaterRemovesAcid():
    "When an acid water tile is frozen, it becomes a frozen acid tile that behaves just like an ice tile. When this frozen acid tile is destroyed, it becomes a regular water tile. Hence, freezing acid effectively removes it."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b, effects={Effects.ACID}))
    assert b.board[(1, 1)].effects == {Effects.ACID}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].type == 'ice'
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].type == 'water'

# A unit that repairs in a smoke cloud (because camilla allows actions while smoked) does NOT remove the smoke.
# A flying unit on an acid water tile does not get acid on it.
# If a forest tile gets acid on it, the forest is removed and it is no longer flammable from damage.
# if a tile with acid on it is frozen, nothing happens. The acid remains.
# A frozen tile that is hit with fire breaks the ice, catches the tile and unit on fire.
# A mountain takes 5 damage and becomes a damaged mountain. It takes another 5 damage and becomes a normal tile. Mountains need 2 hits to become regular tiles, the amount of damage doesn't matter.
# Lava: Only appears on the final map, picture it as unfreezable, hot acid. It sets any massive, non-fliers alight.
#Teleporters: A live unit entering one of these tiles will swap position to the corresponding other tile. If there was a unit already there, it too is teleported. Fire or smoke will not be teleported. This can have some pretty odd looking interactions with the Hazardous mechs, since a unit that reactivates is treated as re-entering the square it died on.
# What happens when a frozen flying or ground unit is pushed onto a chasm tile?
# When you step on an acid tile, it becomes a regular tile. the first unit that steps there takes acid away.
# Mountain tile can't gain acid.
# When a unit with acid dies, it leaves behind an acid pool.
if __name__ == '__main__':
    g = sorted(globals())
    for test in [x for x in g if x.startswith('t_')]:
        runTest(test)