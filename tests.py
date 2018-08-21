#!/usr/bin/env python3

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
    b.replaceTile((1, 1), Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}

def t_fireTurnsIceToWater():
    "An ice tile takes fire damage and turns to water. A flying unit on the tile catches fire."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Ice(b))
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].type == "water"
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}

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
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    b.board[(1, 1)].applyIce()
    b.board[(1, 1)].applyShield()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ICE, Effects.SHIELD}
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}

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
    "A mountain takes 5 damage twice and needs two hits to be destroyed."
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
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 2)].effects == set()
    b.board[(1, 2)].applyFire()
    b.moveUnit((1, 2), (1, 1))
    assert b.board[(1, 1)].unit.type == 'hornet'
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(1, 2)].effects == {Effects.FIRE}
    assert b.board[(1, 2)].unit == None

def t_FlyingUnitCatchesFireOverWater():
    "A flying unit is set on fire on an Ice tile. The unit catches fire, the tile does not."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Ice(b))
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].unit.type == 'hornet'
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}

def t_FlyingUnitIcedOverWater():
    "A flying unit that is frozen on water remains frozen because the tile under it becomes ice instead of water."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b))
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
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
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED} # no new tile effects
    assert b.board[(2, 1)].unit.effects == set() # no unit effects
    assert b.board[(1, 2)].effects == {Effects.SUBMERGED}  # no new tile effects
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
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyFire()
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    b.moveUnit((2, 1), (1, 1))
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()

def t_RepairWaterAcidTileDoesntRemoveAcid():
    "When a water tile has acid on it, it becomes an acid water tile. A flying unit repairing here does NOT remove the acid."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b, effects={Effects.ACID}))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    b.board[(1, 1)].repair()
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}

def t_FreezingAcidWaterRemovesAcid():
    "When an acid water tile is frozen, it becomes a frozen acid tile that behaves just like an ice tile. When this frozen acid tile is destroyed, it becomes a regular water tile. Hence, freezing acid effectively removes it."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b, effects={Effects.ACID}))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'ice'
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'water'

def t_RepairingInSmokeLeavesSmoke():
    "A unit that repairs in a smoke cloud (because camilla allows actions while smoked) does NOT remove the smoke."
    b = GameBoard()
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    b.board[(1, 1)].repair()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}

def t_FlyingDoesntGetAcidFromAcidWater():
    "A flying unit on an acid water tile does not get acid on it."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b, effects={Effects.ACID}))
    b.board[(2, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    b.push((2, 1), Direction.LEFT)
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()

def t_AcidRemovesForest():
    "If a forest tile gets acid on it, the forest is removed and it is no longer flammable from damage."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Forest(b))
    assert b.board[(1, 1)].type == "forest"
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].type == "ground"
    assert b.board[(1, 1)].effects == {Effects.ACID}

def t_IceDoesntEffectAcidPool():
  "If a tile with acid on it is frozen, nothing happens. The acid remains."
  b = GameBoard()
  b.board[(1, 1)].applyAcid()
  assert b.board[(1, 1)].effects == {Effects.ACID}
  b.board[(1, 1)].applyIce()
  assert b.board[(1, 1)].effects == {Effects.ACID}

def t_LavaCantBeFrozen():
    "Lava is unfreezable."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Lava(b))
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'lava'

def t_LavaSetsMassiveOnFire():
    "Massive units that go into lava catch on fire."
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Lava(b))
    b.board[(1, 2)].putUnitHere(Unit_Beetle_Leader(b))
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    b.moveUnit((1, 2), (1, 1))
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}

def t_UnitTakesAcidFromTile():
    "When you step on an acid tile, it becomes a regular tile. the first unit that steps there takes acid away."
    b = GameBoard()
    b.board[(1, 1)].applyAcid()
    b.board[(1, 2)].putUnitHere(Unit_Beetle_Leader(b))
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    b.moveUnit((1, 2), (1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID}

def t_UnitLeavesAcidWhenKilled():
    "When a unit with acid dies, it leaves behind an acid pool."
    b = GameBoard()
    b.board[(1, 2)].putUnitHere(Unit_Beetle_Leader(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    b.board[(1, 2)].unit.applyAcid()
    b.moveUnit((1, 2), (1, 1))
    b.board[(1, 1)].unit.die()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 2)].effects == set()

def t_MountainTileCantGainAcid():
    "Mountain tile can't gain acid., absolutely nothing happens to the mountain or the tile."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Mountain(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()

def t_FrozenGroundUnitDiesInChasm():
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Chasm(b))
    b.board[(1, 2)].putUnitHere(Unit_Beetle_Leader(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    b.board[(1, 2)].applyIce()
    assert b.board[(1, 2)].unit.effects == {Effects.ICE}
    b.moveUnit((1, 2), (1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 1)].unit == None

def t_FrozenFlyingUnitDiesInChasm():
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Chasm(b))
    b.board[(1, 2)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    b.board[(1, 2)].applyIce()
    assert b.board[(1, 2)].unit.effects == {Effects.ICE}
    b.moveUnit((1, 2), (1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 1)].unit == None

def t_AcidPutsOutTileFire():
    b = GameBoard()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID}

def t_FrozenFlyingUnitDiesInChasm():
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Rock(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID}
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None

def t_UnitsOnFireDontLightTileOnDeath():
    "flying units that are on fire doesn't transfer fire to the vek emerge tile below."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    b.moveUnit((1, 1), (2, 1))
    b.board[(2, 1)].unit.die()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit == None

def t_GroundUnitBringsAcidIntoWater():
    "a ground unit with acid is pushed into water: tile becomes an acid water tile"
    b = GameBoard()
    b.replaceTile((1, 1), Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.ACID}
    b.moveUnit((2, 1), (1, 1))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(1, 1)].unit == None

def t_GroundUnitWithAcidAndFireDies():
    "a ground unit with acid and fire dies on a normal tile: acid pool is left on the tile."
    b = GameBoard()
    b.board[(2, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyAcid()
    b.board[(2, 1)].applyFire()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.ACID, Effects.FIRE}
    b.moveUnit((2, 1), (1, 1))
    b.board[(1, 1)].unit.die()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit == None

# # mountains can't be set on fire, but the tile they're on can!. Raise attribute error so the tile that tried to give fire to the present unit gets it instead.
# Attacking a forest tile with something that leaves behind smoke doesn't light it on fire! Does smoke put out fire? Yes, smoke reverts it back to a forest tile
    # when the jet mech attacks and smokes a forest, it is only smoked. the forest remains, there's no fire, but there is smoke.
# Attacking a forest that is smoked will remove the smoke and set the tile on fire.
# What happens when Acid hits lava?
# When a building on a normal tile is hit with acid, the tile has acid.
# When a massive unit dies in water, it becomes a water acid tile.
# Spiderling eggs with acid hatch into spiders with acid.
# frozen with acid units pushed into water make the water into acid water.
# if you freeze a flying unit over a chasm it dies
# rocks thrown at sand tiles do not create smoke. This means that rocks do damage to units but not tiles at all.
# a mountain hit with fire catches the tile on fire, but not the mountain
# a mountain hit with acid does nothing to the mountain or the tile.
# when leap mech leaps onto an acid tile, he takes the acid first and then takes double damage.
# when unstable mech shoots and lands on acid tile, it takes damage then gains acid.
# 
# Fire spreads from units on fire to forest tiles. This makes a burning unit standing on forest "immune" to smoke. As the fire spreading will clear the smoke. what? test this first
#  I'm pretty sure the damage to a shielded unit will not start a forest fire if they are standing on a forest tile.
# Ice puts out fire, this is a dupe
# If a unit is frozen and damaged and bumped against a wall, the damage removes the ice and then the bump damage hurts the unit.
# Test keepeffects by setting an acid vat on fire and then destroying it. The resulting acid water tile should not have fire.
# Teleporters: A live unit entering one of these tiles will swap position to the corresponding other tile. If there was a unit already there, it too is teleported. Fire or smoke will not be teleported. This can have some pretty odd looking interactions with the Hazardous mechs, since a unit that reactivates is treated as re-entering the square it died on.

if __name__ == '__main__':
    g = sorted(globals())
    for test in [x for x in g if x.startswith('t_')]:
        runTest(test)
