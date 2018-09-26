#!/usr/bin/env python3

"These are u nit tests for itbsolver. All test functions must start with t_ to differentiate them from the functions of the main script."

from itbsolver import *

def runTest(funcname):
    "This runs the function funcname and prints information about the tests. This prints out the name of the function, and then PASSED if assertion errors didn't short-circuit this whole script."
    print("%s: " % funcname[2:], end='')
    globals()[funcname]()
    print('PASSED')

def t_BumpDamage():
    "2 units bump into each other and take 1 damage each."
    b = GameBoard()
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    b.board[(2, 1)].putUnitHere(Unit_Alpha_Beetle(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].unit.currenthp == 5
    b.board[(2, 1)].push(Direction.LEFT)
    assert b.board[(1, 1)].unit.currenthp == 2
    assert b.board[(2, 1)].unit.currenthp == 4

def t_ForestCatchesFire():
    "A forest tile takes damage and catches fire."
    b = GameBoard()
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}

def t_FireTurnsIceToWater():
    "An ice tile takes fire damage and turns to water. A flying unit on the tile catches fire."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Ice(b))
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].type == "water"
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}

def t_ShieldBlocksTileFire():
    "a shielded unit that is hit with fire doesn't catch fire but the tile does. The shield remains."
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
    assert b.board[(1, 1)].unit.type == 'mountaindamaged'
    b.board[(1, 1)].takeDamage(5)
    assert b.board[(1, 1)].unit == None
    assert b.board[(1, 1)].effects == set()

def t_FlyingUnitOnFireOverWater():
    "A flying unit that is on fire that moves to a water tile remains on fire"
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(1, 2)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 2)].effects == set()
    b.board[(1, 2)].applyFire()
    b.board[(1, 2)].moveUnit((1, 1))
    assert b.board[(1, 1)].unit.type == 'hornet'
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(1, 2)].effects == {Effects.FIRE}
    assert b.board[(1, 2)].unit == None

def t_FlyingUnitCatchesFireOverWater():
    "A flying unit is set on fire on an Ice tile. The unit catches fire, the tile does not."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Ice(b))
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
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].unit.type == 'hornet'
    assert b.board[(1, 1)].type == 'ice'
    assert b.board[(1, 1)].unit.effects == {Effects.ICE}

def t_WaterRemovesIceFromUnit():
    "A flying unit or ground unit that is frozen and is then moved onto a water tile is unfrozen."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b)) # make water tiles
    b.board[(1, 2)].replaceTile(Tile_Water(b))
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
    b.board[(2, 1)].push(Direction.LEFT)
    b.board[(2, 2)].push(Direction.LEFT)
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 2)].unit == None # the ground unit didn't survive the water

def t_WaterTileTurnsToIceWhenIce():
    "A water tile that is hit with ice becomes an ice tile"
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].type == 'ice'

def t_WaterTilePutsOutUnitFire():
    "A ground unit that is on fire that moves into a water tile is no longer on fire."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Beetle_Leader(b)) # massive unit on the bottom next to the water tile
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyFire()
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()

def t_RepairWaterAcidTileDoesntRemoveAcid():
    "When a water tile has acid on it, it becomes an acid water tile. A flying unit repairing here does NOT remove the acid."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b, effects={Effects.ACID}))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    b.board[(1, 1)].repair(1)
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}

def t_IceAcidWaterThenThawingWithFireRemovesAcid():
    "When an acid water tile is frozen, it becomes a frozen acid tile that behaves just like an ice tile. When this frozen acid tile is destroyed by fire, it becomes a regular water tile."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b, effects={Effects.ACID}))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].type == 'ice'
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'water'

def t_IceAcidWaterThenThawingWithDamageLeavesAcid():
    "When an acid water tile is frozen, it becomes a frozen acid tile that behaves just like an ice tile. When this frozen acid tile is destroyed by damage, it reverts to an acid water tile."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b, effects={Effects.ACID}))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].type == 'ice'
    b.board[(1, 1)].takeDamage(10) # we only damage it once, it needs 2 hits like a mountain.
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].type == 'ice_damaged'
    b.board[(1, 1)].takeDamage(10) # now the ice should be gone
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.ACID}
    assert b.board[(1, 1)].type == 'water'

def t_UnitDoesntGetAcidFromIcedAcidWater():
    "If acid is put onto an ice tile, it becomes a frozen acid tile. This means there is no pool of acid on it and a unit can't pick up acid by moving here."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].type == 'ice'
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].type == 'ice'
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit.effects == set()

def t_RepairingInSmokeLeavesSmoke():
    "A unit that repairs in a smoke cloud (because camilla allows actions while smoked) does NOT remove the smoke."
    b = GameBoard()
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    b.board[(1, 1)].repair(1)
    assert b.board[(1, 1)].effects == {Effects.SMOKE}

def t_FlyingDoesntGetAcidFromAcidWater():
    "A flying unit on an acid water tile does not get acid on it."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b, effects={Effects.ACID}))
    b.board[(2, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].push(Direction.LEFT)
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()

def t_IceDoesntEffectAcidPool():
  "If a tile with acid on it is frozen, nothing happens. The acid remains."
  b = GameBoard()
  b.board[(1, 1)].applyAcid()
  assert b.board[(1, 1)].effects == {Effects.ACID}
  b.board[(1, 1)].applyIce()
  assert b.board[(1, 1)].effects == {Effects.ACID}

def t_IceDoesNothingToLava():
    "Lava is unfreezable."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Lava(b))
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'lava'

def t_LavaSetsMassiveOnFire():
    "Massive units that go into lava catch on fire."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Lava(b))
    b.board[(1, 2)].putUnitHere(Unit_Beetle_Leader(b))
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    b.board[(1, 2)].moveUnit((1, 1))
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
    b.board[(1, 2)].moveUnit((1, 1))
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
    b.board[(1, 2)].applyAcid()
    b.board[(1, 2)].moveUnit((1, 1))
    b.board[(1, 1)].die()
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

def t_IceGroundUnitDiesInChasm():
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Chasm(b))
    b.board[(1, 2)].putUnitHere(Unit_Beetle_Leader(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    b.board[(1, 2)].applyIce()
    assert b.board[(1, 2)].unit.effects == {Effects.ICE}
    b.board[(1, 2)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 1)].unit == None

def t_IceFlyingUnitDiesInChasm():
    "when a flying unit is frozen with ice and then moved to a chasm, it does because it's not really flying anymore."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Chasm(b))
    b.board[(1, 2)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    b.board[(1, 2)].applyIce()
    assert b.board[(1, 2)].unit.effects == {Effects.ICE}
    b.board[(1, 2)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(1, 2)].unit == None

def t_AcidPutsOutTileFire():
    b = GameBoard()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID}

def t_AcidFromDeadUnitPutsOutTileFire():
    "If a tile is on fire and a unit with acid dies on it, Acid pool is left on the tile removing the fire."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    b.board[(1, 1)].takeDamage(10)
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None

def t_RockWithAcidLeavesAcidWhenKilled():
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
    b.board[(1, 1)].moveUnit((2, 1))
    b.board[(2, 1)].die()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit == None

def t_SmallGroundUnitBringsAcidIntoWater():
    "a non-massive ground unit with acid is pushed into water: tile becomes an acid water tile and the unit dies"
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.ACID}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(1, 1)].unit == None # unit wasn't massive so it died.

def t_MassiveGroundUnitBringsAcidIntoWater():
    "a massive ground unit with acid is pushed into water: tile becomes an acid water tile and the unit survives. It then walks out and still has acid."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Large_Goo(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(2, 1)].unit.attributes == {Attributes.MASSIVE}
    b.board[(2, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.ACID}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID} # unit is massive so it survived.
    b.board[(1, 1)].moveUnit((2, 1)) # the unit moves out and still has acid
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.ACID}  # unit still has acid

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
    b.board[(2, 1)].moveUnit((1, 1))
    b.board[(1, 1)].die()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit == None

def t_MountainCantBeSetOnFire():
    "mountains can't be set on fire, but the tile they're on can!"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Mountain(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == set()

def t_SmokePutsOutFire():
    "Attacking a forest tile with something that leaves behind smoke doesn't light it on fire! Does smoke put out fire? Yes, smoke reverts it back to a forest tile. When the jet mech attacks and smokes a forest, it is only smoked. the forest remains, there's no fire, but there is smoke."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].type == 'forest'

def t_AttackingSmokedForestRemovesSmokeAndCatchesFire():
    "Attacking a forest that is smoked will remove the smoke and set the tile on fire."
    b = GameBoard() # This is all the exact same as smoke puts out fire
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].type == 'forest' # until here, now let's attack it again!
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}

def t_SettingFireToSmokedTileRemovesSmokeAndCatchesFire():
    "Setting fire to a normal tile that is smoked will remove the smoke and set the tile on fire."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Ground(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].type == 'ground'
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}

def t_SettingFireToSmokedWaterTileDoesNothing():
    "Setting fire to a water tile that is smoked will leave the smoke."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE, Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'water'
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.SMOKE, Effects.SUBMERGED}

def t_SettingFireToSmokedChasmTileDoesNothing():
    "Setting fire to a chasm tile that is smoked will leave the smoke."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Chasm(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].type == 'chasm'
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}

def t_SettingFireToSmokedIceTileRemovesSmokeAndTurnsToWater():
    "Setting fire to an ice tile that is smoked will remove the smoke and turn it into a water tile."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Ice(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE, Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'water'
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.SMOKE}

def t_BuildingAcidGoesToTile():
    "When a building on a normal tile is hit with acid, the tile has acid."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Building(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit.effects == set()

def t_FlyingUnitWithAcidDiesInWater():
    "When a flying unit with acid dies over water, it becomes a water acid tile."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.ACID}
    b.board[(2, 1)].moveUnit((1, 1))
    b.board[(1, 1)].die()
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit == None

def t_IceGroundUnitWithAcidDiesInWater():
    "frozen with acid units pushed into water make the water into acid water."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyAcid()
    b.board[(2, 1)].applyIce()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.ACID, Effects.ICE}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit == None

def t_IceFlyingUnitOverChasmKillsIt():
    "if you freeze a flying unit over a chasm it dies"
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Chasm(b))
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None

def t_UnitsOnFireCatchForestsOnFireByMovingToThem():
    "Fire spreads from units (including flying) on fire to forest tiles."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    b.board[(2, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyFire()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit == None

def t_UnitsOnFireCatchSmokedForestsOnFireByMovingToThem():
    "If a unit is on fire and it moves to a smoked forest tile, the tile will catch fire and the smoke will disappear."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Forest(b, effects={Effects.SMOKE}))
    b.board[(2, 1)].putUnitHere(Unit_Hornet(b))
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyFire()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit == None

def t_ShieldedUnitOnForestWontIgnightForest():
    "If a Shielded unit stands on a forest and takes damage, the forest will not ignite."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b))
    b.board[(1, 1)].applyShield()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == set()  # no fire on tile
    assert b.board[(1, 1)].unit.effects == set()  # shield gone, but not on fire

def t_UnitSetOnFireThenShieldedNothingWeird():
    "a unit can be set on fire and then shielded, the fire stays."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    b.board[(1, 1)].applyShield()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}

def t_UnitFireAndShieldMovedToForestSetOnFire():
    "if a unit that is on fire and shielded moves to a forest tile, it is set on fire."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    b.board[(2, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyFire()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(1, 1)].effects == set()
    b.board[(2, 1)].applyShield()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}

def t_IceRemovesFireFromUnitAndTile():
    "Ice puts out fire on unit and tile."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ICE}

def t_ShieldBlocksIceFromFire():
    "What happens when a unit is set on fire, shielded, then frozen? Ice has no effect, unit remains shielded and on fire. Tile remains on fire."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    b.board[(1, 1)].applyShield()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}

def t_ShieldBlocksIce():
    "You can't be frozen when you have a shield"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyShield()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_FireBreaksIceWithShield():
    "If a unit is iced, shielded, then fired, the ice breaks, the tile catches fire, but the unit remains shielded and not on fire."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ICE}
    b.board[(1, 1)].applyShield()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ICE, Effects.SHIELD}
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_AcidVatOnFireDoesntCreateFireAcidWater():
    "Test keepeffects by setting an acid vat on fire and then destroying it. The resulting acid water tile should not have fire."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Acid_Vat(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    b.board[(1, 1)].takeDamage(10)
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(1, 1)].unit == None

def t_AcidVatWithSmokeKeepsSmokeAfterKilled():
    "Test keepeffects by smoking an acid vat and then destroying it. The resulting tile should be acid water with smoke."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Acid_Vat(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applySmoke()
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].takeDamage(10)
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED, Effects.SMOKE}
    assert b.board[(1, 1)].unit == None

def t_AcidUnitAttackedonDesertLeavesAcidNoSmoke():
    "If a unit with acid stands on a desert tile and is attacked and killed, an acid pool is left on the tile along with smoke. The sand is removed."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Sand(b))
    b.board[(1, 1)].putUnitHere(Unit_Blobber(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID}
    b.board[(1, 1)].takeDamage(10)
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SMOKE}
    assert b.board[(1, 1)].unit == None
    assert b.board[(1, 1)].type == 'ground'

def t_AcidRemovesSand():
    "Acid that lands on sand converts it to a ground tile with acid."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Sand(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None
    assert b.board[(1, 1)].type == 'ground'

def t_AcidRemovesForest():
    "Acid that lands on forest converts it to a ground tile with acid."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None
    assert b.board[(1, 1)].type == 'ground'

def t_AcidDoesNothingToLava():
  "Nothing happens when acid hits lava."
  b = GameBoard()
  b.board[(1, 1)].replaceTile(Tile_Lava(b))
  assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
  b.board[(1, 1)].applyAcid()
  assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
  assert b.board[(1, 1)].unit == None
  assert b.board[(1, 1)].type == 'lava'

def t_FireErasesSandTile():
  "A sand tile being set on fire converts the sand tile to a ground tile on fire."
  b = GameBoard()
  b.board[(1, 1)].replaceTile(Tile_Sand(b))
  assert b.board[(1, 1)].effects == set()
  b.board[(1, 1)].applyFire()
  assert b.board[(1, 1)].effects == {Effects.FIRE}
  assert b.board[(1, 1)].unit == None
  assert b.board[(1, 1)].type == 'ground'

def t_FireRemovesAcidPool():
  "If there's an acid pool on a tile, setting it on fire removes the acid pool."
  b = GameBoard()
  assert b.board[(1, 1)].effects == set()
  b.board[(1, 1)].applyAcid()
  assert b.board[(1, 1)].effects == {Effects.ACID}
  b.board[(1, 1)].applyFire()
  assert b.board[(1, 1)].effects == {Effects.FIRE}
  assert b.board[(1, 1)].unit == None
  assert b.board[(1, 1)].type == 'ground'

def t_FireImmuneUnitDoesntCatchFire():
    "A unit with fire immunity doesn't catch fire, duh."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Hornet(b, attributes={Attributes.IMMUNEFIRE}))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.IMMUNEFIRE, Attributes.FLYING}
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE} # tile on fire
    assert b.board[(1, 1)].unit.effects == set() # unit is not

def t_MechCorpsePush():
    "Dead mechs are not stable and can be pushed around."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Mech_Corpse(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    b.board[(1, 1)].push(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit.attributes == {Attributes.MASSIVE}

def t_MechCorpsePushIntoChasm():
    "Dead mechs disappear into chasms. They have the flying attribute ingame for some reason but are clearly not flying."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Mech_Corpse(b))
    b.board[(2, 1)].replaceTile( Tile_Chasm(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit ==  None
    b.board[(1, 1)].push(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit == None

def t_MechCorpseCantBeIced():
    "Mech corpses cannot be frozen."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Mech_Corpse(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()

def t_MechCorpseSpreadsFire():
    "Even though in the game it doesn't show mech corpses as having fire or acid, they do as evidenced by spreading of fire to forests and acid to water."
    b = GameBoard()
    b.board[(2, 1)].replaceTile( Tile_Forest(b))
    b.board[(1, 1)].putUnitHere(Unit_Mech_Corpse(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit == None
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit == None
    b.board[(1, 1)].push(Direction.RIGHT)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}

def t_MechCorpseSpreadsAcid():
    "Even though in the game it doesn't show mech corpses as having fire or acid, they do as evidenced by spreading of fire to forests and acid to water."
    b = GameBoard()
    b.board[(2, 1)].replaceTile( Tile_Water(b))
    b.board[(1, 1)].putUnitHere(Unit_Mech_Corpse(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert b.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit == None
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID}
    assert b.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit == None
    b.board[(1, 1)].push(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == {Effects.SUBMERGED, Effects.ACID}
    assert b.board[(2, 1)].unit.effects == {Effects.ACID}

def t_MechCorpseInvulnerable():
    "Dead mechs can't be killed by damage."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Mech_Corpse(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    b.board[(1, 1)].takeDamage(100)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyAcid()
    b.board[(1, 1)].takeDamage(100)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID}

def t_MechCorpseCantBeShielded():
    "Mech corpses cannot be shielded even though the game implies that it can be."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Mech_Corpse(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyShield()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert b.board[(1, 1)].unit.effects == set()

def t_UnitWithAcidKilledOnSandThenSetOnFire():
    "A unit with acid is killed on a sand tile, tile now has smoke and acid and is no longer a sand tile. Setting it on fire gets rid of smoke and acid."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Sand(b))
    b.board[(1, 1)].putUnitHere(Unit_Scarab(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID}
    b.board[(1, 1)].takeDamage(10)
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SMOKE}
    assert b.board[(1, 1)].unit == None
    assert b.board[(1, 1)].type == 'ground'
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit == None
    assert b.board[(1, 1)].type == 'ground'

def t_DamagedIceBecomesIceWhenFrozen():
    "If a damaged ice tile is hit with ice, it becomes an ice tile."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].type == 'ice'
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].type == 'ice_damaged'
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].type == 'ice'

def t_BrokenTeleporter():
    "Make sure an exception is raised if a unit moves onto a teleporter tile that doesn't have a companion."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Teleporter(b))
    b.board[(2, 1)].putUnitHere(Unit_Scarab(b))
    try:
        b.board[(2, 1)].moveUnit((1, 1))
    except MissingCompanionTile:
        pass
    else:
        assert False # The expected exception wasn't raised!

def t_WorkingTeleporter():
    "Make sure a unit can teleport back and fourth between 2 teleporters."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Teleporter(b, companion=(8, 8)))
    b.board[(8, 8)].replaceTile(Tile_Teleporter(b, companion=(1, 1)))
    b.board[(2, 1)].putUnitHere(Unit_Scarab(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(8, 8)].effects == set()
    assert b.board[(8, 8)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(2, 1)].unit == None
    assert b.board[(8, 8)].unit.effects == set() # unit is on far teleporter
    b.board[(8, 8)].moveUnit((7, 8)) # move it off teleporter
    assert b.board[(1, 1)].unit == None
    assert b.board[(8, 8)].unit == None
    assert b.board[(7, 8)].unit.effects == set() # unit is here
    b.board[(7, 8)].moveUnit((8, 8)) # move it back to far teleporter
    assert b.board[(1, 1)].unit.effects == set() # unit is here
    assert b.board[(8, 8)].unit == None
    assert b.board[(7, 8)].unit == None

def t_TeleporterSwaps2Units():
    "If a unit is on a teleporter when another unit moves to its companion, the units will swap places."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Teleporter(b, companion=(8, 8)))
    b.board[(8, 8)].replaceTile(Tile_Teleporter(b, companion=(1, 1)))
    b.board[(2, 1)].putUnitHere(Unit_Scarab(b)) # put scarab next to near teleporter
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(8, 8)].effects == set()
    assert b.board[(8, 8)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].moveUnit((1, 1)) # move scarab to near teleporter
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(2, 1)].unit == None
    assert b.board[(8, 8)].unit.type == 'scarab' # unit is on far teleporter
    b.board[(1, 1)].putUnitHere(Unit_Hornet_Leader(b)) # they instantly swap
    assert b.board[(1, 1)].unit.type == 'scarab' # is hornetleader
    assert b.board[(8, 8)].unit.type == 'hornetleader'

def t_TeleporterWithFire():
    "A unit that is pushed onto an on fire teleporter also catches fire and is then teleported."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Teleporter(b, effects={Effects.FIRE}, companion=(8, 8)))
    b.board[(8, 8)].replaceTile(Tile_Teleporter(b, companion=(1, 1)))
    b.board[(2, 1)].putUnitHere(Unit_Scarab(b))
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit == None
    assert b.board[(8, 8)].effects == set()
    assert b.board[(8, 8)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(8, 8)].effects == set()
    assert b.board[(2, 1)].unit == None
    assert b.board[(8, 8)].unit.effects == {Effects.FIRE} # unit is on far teleporter

def t_TeleporterWithAcid():
    "If there's an acid pool on a teleporter, it's picked up by the unit that moves there and then the unit is teleported."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Teleporter(b, effects={Effects.ACID}, companion=(8, 8)))
    b.board[(8, 8)].replaceTile(Tile_Teleporter(b, companion=(1, 1)))
    b.board[(2, 1)].putUnitHere(Unit_Scarab(b))
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None
    assert b.board[(8, 8)].effects == set()
    assert b.board[(8, 8)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(2, 1)].unit == None
    assert b.board[(8, 8)].unit.effects == {Effects.ACID} # unit is on far teleporter

def t_DamDies():
    "The Dam is a special 2-tile unit. In this program, it's treated as 2 separate units that replicate actions to each other. In this test, we kill one and make sure they both die and flood the map."
    b = GameBoard()
    b.board[(8, 3)].replaceTile(Tile_Water(b))
    b.board[(8, 4)].replaceTile(Tile_Water(b))
    b.board[(8, 3)].putUnitHere(Unit_Dam(b))
    b.board[(8, 4)].putUnitHere(Unit_Dam(b))
    assert b.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert b.board[(8, 4)].effects == {Effects.SUBMERGED}
    assert b.board[(7, 3)].effects == set() # the tiles next to the dam are normal
    assert b.board[(7, 4)].effects == set()
    b.board[(8, 3)].takeDamage(1)
    assert b.board[(8, 3)].unit.currenthp == 1
    assert b.board[(8, 4)].unit.currenthp == 1
    b.board[(8, 4)].takeDamage(1)
    assert b.board[(8, 3)].unit.type == 'volcano'
    assert b.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 7):
            assert b.board[(x, y)].type == 'water'

def t_DamDiesWithAcidUnits():
    "In this test, we kill one and make sure that a unit with acid dies and leaves acid in the new water. Also a flying unit will survive the flood."
    b = GameBoard()
    b.board[(8, 3)].replaceTile(Tile_Water(b))
    b.board[(8, 4)].replaceTile(Tile_Water(b))
    b.board[(8, 3)].putUnitHere(Unit_Dam(b))
    b.board[(8, 4)].putUnitHere(Unit_Dam(b))
    b.board[(7, 3)].putUnitHere(Unit_Blobber(b, effects={Effects.ACID}))
    b.board[(7, 4)].putUnitHere(Unit_Hornet(b, effects={Effects.ACID}))
    assert b.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert b.board[(8, 4)].effects == {Effects.SUBMERGED}
    assert b.board[(7, 3)].effects == set() # the tiles next to the dam are normal
    assert b.board[(7, 4)].effects == set()
    assert b.board[(7, 3)].unit.effects == {Effects.ACID}  # the units next to the dam have acid
    assert b.board[(7, 4)].unit.effects == {Effects.ACID}
    b.board[(8, 3)].takeDamage(1)
    assert b.board[(8, 3)].unit.currenthp == 1
    assert b.board[(8, 4)].unit.currenthp == 1
    b.board[(8, 4)].takeDamage(1)
    assert b.board[(8, 3)].unit.type == 'volcano'
    assert b.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 8):
            assert b.board[(x, y)].type == 'water'
    assert b.board[(7, 3)].unit == None # the blobber died
    assert b.board[(7, 3)].effects == {Effects.ACID, Effects.SUBMERGED} # the blobber left acid in the water
    assert b.board[(7, 4)].unit.type == 'hornet' # the hornet survived
    assert b.board[(7, 4)].effects == {Effects.SUBMERGED}  # the acid is still on the hornet and not the water

def t_DamDiesWithAcidOnGround():
    "In this test, we kill one and make sure that a ground tile with acid leaves acid in the new water tile."
    b = GameBoard()
    b.board[(8, 3)].replaceTile(Tile_Water(b))
    b.board[(8, 4)].replaceTile(Tile_Water(b))
    b.board[(8, 3)].putUnitHere(Unit_Dam(b))
    b.board[(8, 4)].putUnitHere(Unit_Dam(b))
    b.board[(7, 3)].applyAcid()
    assert b.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert b.board[(8, 4)].effects == {Effects.SUBMERGED}
    assert b.board[(7, 3)].effects == {Effects.ACID} # the tile next to the dam has acid
    assert b.board[(7, 4)].effects == set()
    b.board[(8, 3)].takeDamage(1)
    assert b.board[(8, 3)].unit.currenthp == 1
    assert b.board[(8, 4)].unit.currenthp == 1
    b.board[(8, 4)].takeDamage(1)
    assert b.board[(8, 3)].unit.type == 'volcano'
    assert b.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 8):
            assert b.board[(x, y)].type == 'water'
    assert b.board[(7, 3)].effects == {Effects.ACID, Effects.SUBMERGED} # the acid on the ground left acid in the water
    assert b.board[(7, 4)].effects == {Effects.SUBMERGED} # this tile never got acid

def t_ShieldedDamHitWithAcidGetsAcid():
    "If the dam is shielded and then hit with acid, it's immediately inflicted with acid."
    b = GameBoard()
    b.board[(8, 3)].replaceTile(Tile_Water(b))
    b.board[(8, 4)].replaceTile(Tile_Water(b))
    b.board[(8, 3)].putUnitHere(Unit_Dam(b))
    b.board[(8, 4)].putUnitHere(Unit_Dam(b))
    b.board[(8, 4)].applyShield()
    assert b.board[(8, 3)].unit.effects == {Effects.SHIELD}
    assert b.board[(8, 4)].unit.effects == {Effects.SHIELD}
    b.board[(8, 3)].applyAcid()
    assert b.board[(8, 3)].unit.effects == {Effects.SHIELD, Effects.ACID}
    assert b.board[(8, 4)].unit.effects == {Effects.SHIELD, Effects.ACID}

def t_ShieldedUnitDoesntGetAcidFromGround():
    "a shielded unit does not pick up acid from the ground."
    b = GameBoard()
    b.board[(2, 1)].putUnitHere(Unit_Scorpion(b))
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyShield()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.SHIELD}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.ACID} # still acid on the ground
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD} # still shielded only
    assert b.board[(2, 1)].effects == set() # nothing on that tile
    assert b.board[(2, 1)].unit == None  # nothing on that tile

def t_ShieldedUnitRepairsDoesntRemoveAcidFromGround():
    "if a shielded unit repairs on an acid pool, the acid pool remains."
    b = GameBoard()
    b.board[(2, 1)].putUnitHere(Unit_Aegis_Mech(b))
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyShield()
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.SHIELD}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.ACID} # still acid on the ground
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD} # still shielded only
    assert b.board[(2, 1)].effects == set() # nothing on that tile
    assert b.board[(2, 1)].unit == None  # nothing on that tile
    b.board[(1, 1)].repair(1)
    assert b.board[(1, 1)].effects == {Effects.ACID}  # still acid on the ground
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}  # still shielded only
    assert b.board[(2, 1)].effects == set()  # nothing on that tile
    assert b.board[(2, 1)].unit == None  # nothing on that tile

def t_ShieldedUnitGetsAcidFromWater():
    "if a non-flying shielded unit goes into acid water, it gets acid!"
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(2, 1)].putUnitHere(Unit_Scorpion_Leader(b))
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].applyShield()
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.SHIELD}
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED} # still acid in the water
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD, Effects.ACID} # Shielded and acid!
    assert b.board[(2, 1)].effects == set() # nothing on that tile
    assert b.board[(2, 1)].unit == None  # nothing on that tile

def t_MechRepairsRemovesBadEffectsTileAndUnit():
    "A mech and its forest tile are set on fire and then hit with acid and repaired."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.currenthp == 2
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    assert b.board[(1, 1)].unit.currenthp == 2
    b.board[(1, 1)].repair(1)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3

def t_MechRepairsRemovesIceFromUnit():
    "A mech and its water tile are frozen and then hit with acid and repaired."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Water(b))
    b.board[(1, 1)].putUnitHere(Unit_Cannon_Mech(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 2
    b.board[(1, 1)].applyIce()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].type == 'ice'
    assert b.board[(1, 1)].unit.effects == {Effects.ICE}
    assert b.board[(1, 1)].unit.currenthp == 2
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ICE, Effects.ACID}
    assert b.board[(1, 1)].unit.currenthp == 2
    b.board[(1, 1)].repair(1)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3

def t_BurrowerWithAcidLeavesItWhenKilled():
    "Do burrowers leave acid when they die? Yes!"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Burrower(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyAcid()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID}
    b.board[(1, 1)].takeDamage(2)
    assert b.board[(1, 1)].effects == {Effects.ACID}
    assert b.board[(1, 1)].unit == None

def t_LavaDoesntRemoveAcidFromUnit():
    "Does lava remove acid from a unit like water does? NO, you still have acid."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Lava(b))
    b.board[(1, 2)].putUnitHere(Unit_Laser_Mech(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert b.board[(1, 2)].unit.effects == set()
    b.board[(1, 2)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert b.board[(1, 2)].unit.effects == {Effects.ACID}
    b.board[(1, 2)].push(Direction.DOWN)
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    b.board[(1, 1)].push(Direction.UP)
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert b.board[(1, 2)].unit.effects == {Effects.FIRE, Effects.ACID}

def t_UnitWithAcidDiesInLava():
    "Lava doesn't get acid from an acid unit dying on it."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Lava(b))
    b.board[(1, 2)].putUnitHere(Unit_Acid_Scorpion(b))
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert b.board[(1, 2)].unit.effects == set()
    b.board[(1, 2)].applyAcid()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert b.board[(1, 2)].unit.effects == {Effects.ACID}
    b.board[(1, 2)].push(Direction.DOWN)
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert b.board[(1, 1)].unit == None

def t_MechCorpseIsRepairedBackToLife():
    "a mech is killed, becomes a mech corpse, and then is repaired to become the alive mech again."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Judo_Mech(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].takeDamage(4) # 3 hp, but it has armor :)
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.type == 'mechcorpse'
    b.board[(1, 1)].repair(1)
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.type == 'judo'
    assert b.board[(1, 1)].unit.currenthp == 1

def t_MechDiesAndRevivedOnTeleporter():
    "a mech dies on a teleporter and is then revived. The act of reviving the unit should teleport it through again."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Teleporter(b, companion=(8, 8)))
    b.board[(8, 8)].replaceTile(Tile_Teleporter(b, companion=(1, 1)))
    b.board[(2, 1)].putUnitHere(Unit_Flame_Mech(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(8, 8)].effects == set()
    assert b.board[(8, 8)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(2, 1)].unit == None
    assert b.board[(8, 8)].unit.effects == set() # unit is on far teleporter
    b.board[(8, 8)].takeDamage(3)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(8, 8)].unit.effects == set()  # unit is on far teleporter
    assert b.board[(8, 8)].unit.type == 'mechcorpse'
    b.board[(8, 8)].repair(1)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(8, 8)].unit == None  # no unit on far teleporter
    assert b.board[(1, 1)].unit.type == 'flame'  # unit is back on the near teleporter
    assert b.board[(1, 1)].unit.currenthp == 1 # the repair worked properly

def t_MechCorpsesDontGoThroughTelePorter():
    "if a mech dies and is pushed to a teleporter tile, it does not teleport. Corpses don't teleport at all, even if they die and then are pushed onto a teleporter."
    b = GameBoard()
    b.board[(1, 1)].replaceTile(Tile_Teleporter(b, companion=(8, 8)))
    b.board[(8, 8)].replaceTile(Tile_Teleporter(b, companion=(1, 1)))
    b.board[(2, 1)].putUnitHere(Unit_Leap_Mech(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(8, 8)].effects == set()
    assert b.board[(8, 8)].unit == None
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    b.board[(2, 1)].takeDamage(3)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(2, 1)].unit.type == 'mechcorpse'
    b.board[(2, 1)].moveUnit((1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(2, 1)].unit == None
    assert b.board[(8, 8)].unit == None  # unit is on near teleporter
    assert b.board[(1, 1)].unit.type == 'mechcorpse'

def t_RevivedMechCorpsesKeepAcidButNotFire():
    "When a mech corpse is repaired back to life, it keeps acid if it had it before. If the mech died with fire, it is revived without fire (assuming it's not on a fire tile. The revived unit will be on fire if revived on a fire tile)."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Cannon_Mech(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyAcid()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    b.board[(1, 1)].takeDamage(2)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.type == 'mechcorpse'
    b.board[(1, 1)].moveUnit((2, 1))
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.type == 'mechcorpse'
    b.board[(2, 1)].unit.repair(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.ACID}
    assert b.board[(2, 1)].unit.type == 'cannon'

def t_ReviveMechCorpseKeepsAcidGetsFireFromTile():
    "When a mech corpse is repaired back to life, it keeps acid if it had it before. If the mech died with fire, it is revived without fire (assuming it's not on a fire tile. The revived unit will be on fire if revived on a fire tile)."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Jet_Mech(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    b.board[(1, 1)].applyAcid()
    b.board[(1, 1)].applyFire()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    b.board[(1, 1)].takeDamage(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.type == 'mechcorpse'
    b.board[(1, 1)].unit.repair(1)
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.ACID, Effects.FIRE}
    assert b.board[(1, 1)].unit.type == 'jet'

def t_IceStormEnvironmental():
    b = GameBoard(environmentaleffect=Environ_IceStorm({(x,y) for x in range(1, 5) for y in range(1, 5)}))
    b.board[(1, 1)].putUnitHere(Unit_Jet_Mech(b))
    b.board[(2, 1)].replaceTile(Tile_Water(b))
    b.board[(3, 1)].applyFire()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(3, 1)].effects == {Effects.FIRE}
    b.environmentaleffect.run()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ICE}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].type == 'ice'
    assert b.board[(3, 1)].effects == set()

def t_AirStrikeEnvironmental():
    b = GameBoard(environmentaleffect=Environ_AirStrike({(1, 2), (2, 3), (2, 2), (2, 1), (3, 2)}))
    b.board[(1, 2)].putUnitHere(Unit_Charge_Mech(b))
    b.board[(2, 3)].replaceTile(Tile_Water(b))
    b.board[(2, 2)].replaceTile(Tile_Forest(b))
    b.board[(2, 1)].applyFire()
    b.board[(3, 2)].replaceTile(Tile_Sand(b))
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    assert b.board[(2, 3)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 2)].effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(3, 2)].effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    assert b.board[(1, 2)].unit.type == 'mechcorpse'
    assert b.board[(2, 3)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 2)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(3, 2)].effects == {Effects.SMOKE}

def t_LightningEnvironmental():
    "lol literally the same thing as AirStrike"
    b = GameBoard(environmentaleffect=Environ_Lightning({(1, 2), (2, 3), (2, 2), (2, 1), (3, 2)}))
    b.board[(1, 2)].putUnitHere(Unit_Charge_Mech(b))
    b.board[(2, 3)].replaceTile(Tile_Water(b))
    b.board[(2, 2)].replaceTile(Tile_Forest(b))
    b.board[(2, 1)].applyFire()
    b.board[(3, 2)].replaceTile(Tile_Sand(b))
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    assert b.board[(2, 3)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 2)].effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(3, 2)].effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 2)].effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    assert b.board[(1, 2)].unit.type == 'mechcorpse'
    assert b.board[(2, 3)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 2)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(3, 2)].effects == {Effects.SMOKE}

def t_TsunamiEnvironmental():
    b = GameBoard(environmentaleffect=Environ_Tsunami(((1, 1), (2, 1), (3, 1))))
    b.board[(1, 1)].putUnitHere(Unit_Hook_Mech(b))
    b.board[(2, 1)].putUnitHere(Unit_Scorpion(b))
    b.board[(3, 1)].putUnitHere(Unit_Blood_Psion(b))
    b.board[(3, 1)].applySmoke()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(3, 1)].effects == {Effects.SMOKE}
    assert b.board[(3, 1)].unit.effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit == None # he drowned
    assert b.board[(3, 1)].effects == {Effects.SUBMERGED, Effects.SMOKE} # smoke remains
    assert b.board[(3, 1)].unit.effects == set() # so does this flying unit
    b.board[(1, 1)].applyIce() # make sure these new tiles are tied to this GameBoard instance:
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].type == 'ice'

def t_CataclysmEnvironmental():
    b = GameBoard(environmentaleffect=Environ_Cataclysm(((1, 1), (2, 1), (3, 1))))
    b.board[(1, 1)].putUnitHere(Unit_Mirror_Mech(b))
    b.board[(2, 1)].putUnitHere(Unit_Acid_Scorpion(b))
    b.board[(2, 1)].applyFire()
    b.board[(3, 1)].putUnitHere(Unit_Blast_Psion(b))
    b.board[(3, 1)].applySmoke()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(3, 1)].effects == {Effects.SMOKE}
    assert b.board[(3, 1)].unit.effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None # mech died, so did the corpse
    assert b.board[(2, 1)].effects == set() # no more fire since the ground is gone lol
    assert b.board[(2, 1)].unit == None # he also died
    assert b.board[(3, 1)].effects == {Effects.SMOKE} # smoke remains
    assert b.board[(3, 1)].unit.effects == set() # so does this flying unit
    b.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this GameBoard instance:
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].type == 'chasm'

def t_FallingRockEnvironmental():
    b = GameBoard(environmentaleffect=Environ_FallingRock(((1, 1), (2, 1), (3, 1))))
    b.board[(1, 1)].putUnitHere(Unit_Unstable_Mech(b))
    b.board[(2, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(2, 1)].applyFire()
    b.board[(3, 1)].putUnitHere(Unit_Psion_Tyrant(b))
    b.board[(3, 1)].applySmoke()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(3, 1)].effects == {Effects.SMOKE}
    assert b.board[(3, 1)].unit.effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.type == 'mechcorpse' # mech died, the corpse remains
    assert b.board[(2, 1)].effects == {Effects.FIRE} # fire remains after rocks fall
    assert b.board[(2, 1)].unit == None # he also died
    assert b.board[(3, 1)].effects == {Effects.SMOKE} # smoke remains
    assert b.board[(3, 1)].unit == None # flying unit died
    b.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this GameBoard instance:
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].type == 'ground'

def t_TentaclesEnvironmental():
    b = GameBoard(environmentaleffect=Environ_Tentacles(((1, 1), (2, 1), (3, 1))))
    b.board[(1, 1)].putUnitHere(Unit_Artillery_Mech(b))
    b.board[(2, 1)].putUnitHere(Unit_Firefly(b))
    b.board[(2, 1)].applyFire()
    b.board[(3, 1)].putUnitHere(Unit_Hornet(b))
    b.board[(3, 1)].applySmoke()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(3, 1)].effects == {Effects.SMOKE}
    assert b.board[(3, 1)].unit.effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.type == 'mechcorpse' # mech died, the corpse remains
    assert b.board[(2, 1)].effects == {Effects.FIRE, Effects.SUBMERGED} # fire doubly so
    assert b.board[(2, 1)].unit == None # he also died
    assert b.board[(3, 1)].effects == {Effects.SMOKE, Effects.FIRE, Effects.SUBMERGED} # smoke remains
    assert b.board[(3, 1)].unit == None # flying unit died
    b.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this GameBoard instance:
    assert b.board[(1, 1)].effects == {Effects.SMOKE, Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'lava'

def t_LavaFlowEnvironmental():
    b = GameBoard(environmentaleffect=Environ_LavaFlow(((1, 1), (2, 1), (3, 1))))
    b.board[(1, 1)].putUnitHere(Unit_Rocket_Mech(b))
    b.board[(2, 1)].putUnitHere(Unit_Firefly(b))
    b.board[(2, 1)].applyFire()
    b.board[(3, 1)].putUnitHere(Unit_Acid_Hornet(b))
    b.board[(3, 1)].applySmoke()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(3, 1)].effects == {Effects.SMOKE}
    assert b.board[(3, 1)].unit.effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE} # mech survived but is now in lava
    assert b.board[(2, 1)].effects == {Effects.FIRE, Effects.SUBMERGED} # fire doubly so
    assert b.board[(2, 1)].unit == None # he died
    assert b.board[(3, 1)].effects == {Effects.SMOKE, Effects.FIRE, Effects.SUBMERGED} # smoke remains
    assert b.board[(3, 1)].unit.effects == set() # flying unit survived and did not catch on fire
    b.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this GameBoard instance:
    assert b.board[(1, 1)].effects == {Effects.SMOKE, Effects.FIRE, Effects.SUBMERGED}
    assert b.board[(1, 1)].type == 'lava'

def t_VolcanicProjectileEnvironmental():
    b = GameBoard(environmentaleffect=Environ_VolcanicProjectile(((1, 1), (2, 1), (3, 1))))
    b.board[(1, 1)].putUnitHere(Unit_Boulder_Mech(b))
    b.board[(2, 1)].putUnitHere(Unit_Alpha_Firefly(b))
    b.board[(2, 1)].applyFire()
    b.board[(3, 1)].putUnitHere(Unit_Hornet_Leader(b))
    b.board[(3, 1)].applySmoke()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(3, 1)].effects == {Effects.SMOKE}
    assert b.board[(3, 1)].unit.effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 1)].effects == {Effects.FIRE}
    assert b.board[(1, 1)].unit.type == 'mechcorpse' # mech died
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit == None # he died
    assert b.board[(3, 1)].effects == {Effects.FIRE} # smoke removed by fire
    assert b.board[(3, 1)].unit == None # flying unit died
    b.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this GameBoard instance:
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].type == 'ground'

def t_VekEmergeEnvironmental():
    b = GameBoard(vekemerge=Environ_VekEmerge([(1, 1), (2, 1), (3, 1), (4, 1)]))
    b.board[(1, 1)].putUnitHere(Unit_Siege_Mech(b))
    b.board[(2, 1)].putUnitHere(Unit_Leaper(b))
    b.board[(2, 1)].applyFire()
    b.board[(3, 1)].putUnitHere(Unit_Scorpion_Leader(b))
    b.board[(3, 1)].applySmoke()
    b.board[(4, 1)].putUnitHere(Unit_Mech_Corpse(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(3, 1)].effects == {Effects.SMOKE}
    assert b.board[(3, 1)].unit.effects == set()
    assert b.board[(4, 1)].effects == set()
    assert b.board[(4, 1)].unit.effects == set()
    b.vekemerge.run()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.currenthp == 1 # mech took bump damage
    assert b.board[(2, 1)].effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit == None # he died from the bump
    assert b.board[(3, 1)].effects == {Effects.SMOKE} # smoke remains
    assert b.board[(3, 1)].unit.currenthp == 6
    assert b.board[(4, 1)].effects == set()
    assert b.board[(4, 1)].unit.currenthp == 1 # corpse didn't take damage
    assert b.board[(4, 1)].unit.type == 'mechcorpse' # and is a corpse
    b.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this GameBoard instance:
    assert b.board[(1, 1)].effects == {Effects.SMOKE}
    assert b.board[(1, 1)].type == 'ground'

def t_TsunamiEnvironmentalReplaceTile():
    "make sure that when Tsunami replaces tiles with water, they are in fact different tile objects and not the same one."
    b = GameBoard(environmentaleffect=Environ_Tsunami({(1, 1), (2, 1), (3, 1)}))
    b.board[(1, 1)].putUnitHere(Unit_Hook_Mech(b))
    b.board[(2, 1)].putUnitHere(Unit_Scorpion(b))
    b.board[(3, 1)].putUnitHere(Unit_Blood_Psion(b))
    b.board[(3, 1)].applySmoke()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(3, 1)].effects == {Effects.SMOKE}
    assert b.board[(3, 1)].unit.effects == set()
    b.environmentaleffect.run()
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert b.board[(2, 1)].unit == None  # he drowned
    assert b.board[(3, 1)].effects == {Effects.SUBMERGED, Effects.SMOKE}  # smoke remains
    assert b.board[(3, 1)].unit.effects == set()  # so does this flying unit
    b.board[(1, 1)].applyIce()
    b.board[(2, 1)].applyAcid()
    assert b.board[(1, 1)].effects == set() # one tile is frozen, one has acid, the last has smoke
    assert b.board[(1, 1)].type == 'ice'
    assert b.board[(2, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].type == 'water'
    assert b.board[(3, 1)].effects == {Effects.SUBMERGED, Effects.SMOKE}
    assert b.board[(3, 1)].type == 'water'

def t_ConveyorBeltsEnviron():
    "make sure that when Tsunami replaces tiles with water, they are in fact different tile objects and not the same one."
    b = GameBoard(environmentaleffect=Environ_ConveyorBelts({(1, x): Direction.UP for x in range(1, 9)})) # all tiles against the left border pushing up
    b.board[(1, 1)].putUnitHere(Unit_Meteor_Mech(b))
    b.board[(1, 2)].putUnitHere(Unit_Beetle(b))
    b.board[(1, 7)].putUnitHere(Unit_Spider_Leader(b))
    b.board[(1, 8)].putUnitHere(Unit_Blood_Psion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(1, 2)].unit.currenthp == 4
    assert b.board[(1, 7)].unit.currenthp == 6
    assert b.board[(1, 8)].unit.currenthp == 2
    b.environmentaleffect.run()
    assert b.board[(1, 1)].unit == None # meteor got pushed off this tile
    assert b.board[(1, 2)].unit.currenthp == 3 # meteor still has 3 hp
    assert b.board[(1, 3)].unit.currenthp == 4 # beetle took no damage as well
    assert b.board[(1, 7)].unit.currenthp == 5 # spider leader took a bump when he was pushed into the blood psion, so he didn't move
    assert b.board[(1, 8)].unit.currenthp == 1 # blood psion tried to get pushed off the board so he stayed put and got bumped

def t_WeaponTitanFistFirst():
    "My very first weapon test. Have a mech punch another!"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist()))
    b.board[(2, 1)].putUnitHere(Unit_Judo_Mech(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(2, 1)].unit.currenthp == 3
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].unit == None # judo was pushed off this square
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit.effects == set()
    assert b.board[(3, 1)].unit.currenthp == 2 # he only lost 1 health because of armor

def t_WeaponTitanFistChargeSecond():
    "My very second weapon test. Have a mech dash punch another!"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist(power1=True)))
    b.board[(6, 1)].putUnitHere(Unit_Judo_Mech(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(6, 1)].effects == set()
    assert b.board[(6, 1)].unit.effects == set()
    assert b.board[(6, 1)].unit.currenthp == 3
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None # Combat dashed off of this tile
    assert b.board[(5, 1)].unit.effects == set() # and he's now here
    assert b.board[(5, 1)].unit.currenthp == 3
    assert b.board[(6, 1)].unit == None # judo was pushed off this square
    assert b.board[(7, 1)].effects == set() # and he's here now
    assert b.board[(7, 1)].unit.effects == set()
    assert b.board[(7, 1)].unit.currenthp == 2 # he only lost 1 health because of armor

def t_WeaponTitanFistChargeToEdge():
    "When you charge to the edge of the map without hitting a unit, you do NOT attack the tile at the edge like a projectile does."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist(power1=True)))
    b.board[(8, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(8, 1)].effects == set()
    assert b.board[(8, 1)].unit == None
    assert b.board[(8, 1)].type == 'forest'
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # he's not here anymore
    assert b.board[(8, 1)].effects == set() # still no fire
    assert b.board[(8, 1)].unit.effects == set() # no change
    assert b.board[(8, 1)].unit.currenthp == 3 # no change
    assert b.board[(8, 1)].type == 'forest'

def t_HurtAndPushedVekOnFireSetsForestOnFire():
    "This is testing the concept of the vek corpse. A vek is lit on fire, and then punched for 4 damage so it's killed, but it's fake corpse is pushed to a forest tile and sets it on fire."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist(power2=True)))
    b.board[(2, 1)].putUnitHere(Unit_Firefly(b, effects={Effects.FIRE}))
    b.board[(3, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit == None
    assert b.board[(3, 1)].type == 'forest'
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set() # no change for punchbot
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set() # still no effects here
    assert b.board[(2, 1)].unit == None # firefly was pushed off this tile
    assert b.board[(3, 1)].effects == {Effects.FIRE}
    assert b.board[(3, 1)].unit == None # The firefly died after spreading fire here. We did a strong 4 damage punch
    assert b.board[(3, 1)].type == 'forest' # still a forest? lol

def t_HurtAndPushedMechOnFireDoesNotSetForestOnFire():
    "A mech is lit on fire, and then punched for 4 damage so it's killed, but it's mech corpse is not on fire like the mech was! the corpse is pushed to a forest tile and sets it on fire."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist(power2=True)))
    b.board[(2, 1)].putUnitHere(Unit_Swap_Mech(b, effects={Effects.FIRE}))
    b.board[(3, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert b.board[(2, 1)].unit.currenthp == 2
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit == None
    assert b.board[(3, 1)].type == 'forest'
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set() # no change for punchbot
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set() # still no effects here
    assert b.board[(2, 1)].unit == None # swapper was pushed off this tile
    assert b.board[(3, 1)].effects == set() # corpse is not on fire
    assert b.board[(3, 1)].unit.type == 'mechcorpse' # The swapper died after spreading fire here. We did a strong 4 damage punch
    assert b.board[(3, 1)].type == 'forest' # still a forest? lol

def t_HurtAndPushedVekRemovesMine():
    "This is also testing the concept of the vek corpse. A vek is punched for 4 damage so it's killed, but it's fake corpse is pushed to a tile with a mine. The mine trips and then the unit and mine are gone."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist(power2=True)))
    b.board[(2, 1)].putUnitHere(Unit_Firefly(b))
    b.board[(3, 1)].effects.add(Effects.MINE)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].effects == {Effects.MINE}
    assert b.board[(3, 1)].unit == None
    assert b.board[(3, 1)].type == 'ground'
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set() # no change for punchbot
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set() # still no effects here
    assert b.board[(2, 1)].unit == None # firefly was pushed off this tile
    assert b.board[(3, 1)].effects == set() # mine is gone
    assert b.board[(3, 1)].unit == None # The firefly died after we did a strong 4 damage punch
    assert b.board[(3, 1)].type == 'ground' # still a forest? lol

def t_HurtAndPushedVekRemovesFreezeMine():
    "This is also testing the concept of the vek corpse. A vek is punched for 4 damage so it's killed, but it's fake corpse is pushed to a tile with a mine. The mine trips and then the unit and mine are gone."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist(power2=True)))
    b.board[(2, 1)].putUnitHere(Unit_Firefly(b))
    b.board[(3, 1)].effects.add(Effects.FREEZEMINE)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].effects == {Effects.FREEZEMINE}
    assert b.board[(3, 1)].unit == None
    assert b.board[(3, 1)].type == 'ground'
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set() # no change for punchbot
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == set() # still no effects here
    assert b.board[(2, 1)].unit == None # firefly was pushed off this tile
    assert b.board[(3, 1)].effects == set() # mine is gone
    assert b.board[(3, 1)].unit == None # The firefly died after we did a strong 4 damage punch
    assert b.board[(3, 1)].type == 'ground' # still a forest? lol

def t_MechMovesToMine():
    "Make sure mines work"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist(power2=True)))
    b.board[(2, 1)].effects.add(Effects.MINE)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == {Effects.MINE}
    assert b.board[(2, 1)].unit == None
    b.board[(1, 1)].moveUnit((2, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == set() # mine tripped
    assert b.board[(2, 1)].unit.type == 'mechcorpse' # ol' punchbot died

def t_MechMovesToFreezeMine():
    "Make sure mines work"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Combat_Mech(b, weapon1=Weapon_TitanFist(power2=True)))
    b.board[(2, 1)].effects.add(Effects.FREEZEMINE)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].effects == {Effects.FREEZEMINE}
    assert b.board[(2, 1)].unit == None
    b.board[(1, 1)].moveUnit((2, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].effects == set() # mine tripped
    assert b.board[(2, 1)].unit.type == 'combat' # ol' punchbot survived
    assert b.board[(2, 1)].unit.effects == {Effects.ICE}  # ol' punchbot survived

def t_WeaponElectricWhipLowPower():
    "Shoot the electric whip without building chain or extra damage powered and make sure it goes through units it should and not through units it shouldn't."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Lightning_Mech(b, weapon1=Weapon_ElectricWhip()))
    for x in range(2, 7): # spider bosses on x tiles 2-6
        b.board[(x, 1)].putUnitHere(Unit_Spider_Leader(b))
    b.board[(7, 1)].putUnitHere(Unit_Mountain(b)) # a mountain to block it
    b.board[(8, 1)].putUnitHere(Unit_Spider_Leader(b)) # and a spider boss on the other side which should stay safe
    for y in range(2, 7):
        b.board[(3, y)].putUnitHere(Unit_Spider_Leader(b)) # start branching vertically
    b.board[(3, 7)].putUnitHere(Unit_Building(b))  # a building to block it
    b.board[(3, 8)].putUnitHere(Unit_Spider_Leader(b)) # and another spider boss on the other side which should also stay safe
    assert b.board[(1, 1)].unit.currenthp == 3 # lightning mech
    assert b.board[(2, 1)].unit.currenthp == 6 # spider bosses
    assert b.board[(3, 1)].unit.currenthp == 6
    assert b.board[(4, 1)].unit.currenthp == 6
    assert b.board[(5, 1)].unit.currenthp == 6
    assert b.board[(6, 1)].unit.currenthp == 6
    assert b.board[(3, 2)].unit.currenthp == 6
    assert b.board[(3, 3)].unit.currenthp == 6
    assert b.board[(3, 4)].unit.currenthp == 6
    assert b.board[(3, 5)].unit.currenthp == 6
    assert b.board[(3, 6)].unit.currenthp == 6
    assert b.board[(7, 1)].unit.type == 'mountain'
    assert b.board[(3, 7)].unit.type == 'building'
    assert b.board[(8, 1)].unit.currenthp == 6 # safe spider 1
    assert b.board[(3, 8)].unit.currenthp == 6  # safe spider 2
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 3  # lightning mech untouched
    assert b.board[(2, 1)].unit.currenthp == 4  # spider bosses lose 2 hp
    assert b.board[(3, 1)].unit.currenthp == 4
    assert b.board[(4, 1)].unit.currenthp == 4
    assert b.board[(5, 1)].unit.currenthp == 4
    assert b.board[(6, 1)].unit.currenthp == 4
    assert b.board[(3, 2)].unit.currenthp == 4
    assert b.board[(3, 3)].unit.currenthp == 4
    assert b.board[(3, 4)].unit.currenthp == 4
    assert b.board[(3, 5)].unit.currenthp == 4
    assert b.board[(3, 6)].unit.currenthp == 4
    assert b.board[(7, 1)].unit.type == 'mountain'
    assert b.board[(3, 7)].unit.type == 'building'
    assert b.board[(8, 1)].unit.currenthp == 6  # safe spider 1
    assert b.board[(3, 8)].unit.currenthp == 6  # safe spider 2

def t_WeaponElectricWhipBuildingChainPower():
    "Shoot the electric whip without building chain or extra damage powered and make sure it goes through units it should and not through units it shouldn't."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Lightning_Mech(b, weapon1=Weapon_ElectricWhip(power1=True)))
    for x in range(2, 7): # spider bosses on x tiles 2-6
        b.board[(x, 1)].putUnitHere(Unit_Spider_Leader(b))
    b.board[(7, 1)].putUnitHere(Unit_Mountain(b)) # a mountain to block it
    b.board[(8, 1)].putUnitHere(Unit_Spider_Leader(b)) # and a spider boss on the other side which should stay safe
    for y in range(2, 7):
        b.board[(3, y)].putUnitHere(Unit_Spider_Leader(b)) # start branching vertically
    b.board[(3, 7)].putUnitHere(Unit_Building(b))  # a building to block it
    b.board[(3, 8)].putUnitHere(Unit_Spider_Leader(b)) # and another spider boss on the other side which should also stay safe
    assert b.board[(1, 1)].unit.currenthp == 3 # lightning mech
    assert b.board[(2, 1)].unit.currenthp == 6 # spider bosses
    assert b.board[(3, 1)].unit.currenthp == 6
    assert b.board[(4, 1)].unit.currenthp == 6
    assert b.board[(5, 1)].unit.currenthp == 6
    assert b.board[(6, 1)].unit.currenthp == 6
    assert b.board[(3, 2)].unit.currenthp == 6
    assert b.board[(3, 3)].unit.currenthp == 6
    assert b.board[(3, 4)].unit.currenthp == 6
    assert b.board[(3, 5)].unit.currenthp == 6
    assert b.board[(3, 6)].unit.currenthp == 6
    assert b.board[(7, 1)].unit.type == 'mountain'
    assert b.board[(3, 7)].unit.type == 'building'
    assert b.board[(8, 1)].unit.currenthp == 6 # safe spider 1
    assert b.board[(3, 8)].unit.currenthp == 6  # building chain  spider 2
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 3  # lightning mech untouched
    assert b.board[(2, 1)].unit.currenthp == 4  # spider bosses lose 2 hp
    assert b.board[(3, 1)].unit.currenthp == 4
    assert b.board[(4, 1)].unit.currenthp == 4
    assert b.board[(5, 1)].unit.currenthp == 4
    assert b.board[(6, 1)].unit.currenthp == 4
    assert b.board[(3, 2)].unit.currenthp == 4
    assert b.board[(3, 3)].unit.currenthp == 4
    assert b.board[(3, 4)].unit.currenthp == 4
    assert b.board[(3, 5)].unit.currenthp == 4
    assert b.board[(3, 6)].unit.currenthp == 4
    assert b.board[(7, 1)].unit.type == 'mountain'
    assert b.board[(3, 7)].unit.type == 'building'
    assert b.board[(8, 1)].unit.currenthp == 6  # safe spider 1
    assert b.board[(3, 8)].unit.currenthp == 4  # building chain spider 2 took damage

def t_WeaponElectricWhipDoesntChainInCicle():
    "Shoot the electric whip with the power2 extra damage and make sure we don't loop through the weaponwielder"
    b = GameBoard()
    b.board[(2, 2)].putUnitHere(Unit_Lightning_Mech(b, weapon1=Weapon_ElectricWhip(power2=True)))
    b.board[(1, 1)].putUnitHere(Unit_Spider_Leader(b)) # shocked spider
    b.board[(2, 1)].putUnitHere(Unit_Spider_Leader(b))  # shocked spider
    b.board[(1, 2)].putUnitHere(Unit_Spider_Leader(b))  # shocked spider
    b.board[(2, 3)].putUnitHere(Unit_Spider_Leader(b))  # undamaged spider
    assert b.board[(2, 2)].unit.currenthp == 3 # lightning mech
    assert b.board[(1, 1)].unit.currenthp == 6 # spider bosses
    assert b.board[(2, 1)].unit.currenthp == 6
    assert b.board[(1, 2)].unit.currenthp == 6
    assert b.board[(2, 3)].unit.currenthp == 6
    b.board[(2, 2)].unit.weapon1.shoot(Direction.DOWN)
    assert b.board[(2, 2)].unit.currenthp == 3  # lightning mech
    assert b.board[(1, 1)].unit.currenthp == 3  # spider bosses took 3 damage
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(1, 2)].unit.currenthp == 3
    assert b.board[(2, 3)].unit.currenthp == 6 # this one didn't get hit because we can't chain back through the wielder

def t_WeaponArtemisArtilleryDefault():
    "Do the default power Artillery demo from the game when you mouseover the weapon."
    b = GameBoard()
    b.board[(2, 2)].putUnitHere(Unit_Artillery_Mech(b, weapon1=Weapon_ArtemisArtillery()))
    b.board[(3, 2)].putUnitHere(Unit_Mountain(b))
    b.board[(4, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(5, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b)) # this one is actually against the wall and cannot be pushed
    b.board[(4, 3)].putUnitHere(Unit_Alpha_Scorpion(b)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert b.board[(2, 2)].unit.currenthp == 2
    assert b.board[(3, 2)].unit.currenthp == 1
    assert b.board[(4, 2)].unit.currenthp == 5
    assert b.board[(5, 2)].unit.currenthp == 5
    assert b.board[(4, 1)].unit.currenthp == 5
    assert b.board[(4, 3)].unit.currenthp == 5
    b.board[(2, 2)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(2, 2)].unit.currenthp == 2 # firing unit unchanged
    assert b.board[(3, 2)].unit.currenthp == 1 # mountain unchanged
    assert b.board[(3, 2)].unit.type == 'mountain' # mountain unchanged
    assert b.board[(4, 2)].unit.currenthp == 4 # target square took 1 damage
    assert b.board[(5, 2)].unit == None # vek pushed off this square
    assert b.board[(4, 1)].unit.currenthp == 5 # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert b.board[(4, 3)].unit == None # vek also pushed off this square
    assert b.board[(6, 2)].unit.currenthp == 5 # pushed vek has full health
    assert b.board[(4, 4)].unit.currenthp == 5 # vek pushed has full health

def t_WeaponArtemisArtilleryPower1():
    "Do the Artillery demo from the game when you mouseover the weapon and you have buildings immune powered."
    b = GameBoard()
    b.board[(2, 2)].putUnitHere(Unit_Artillery_Mech(b, weapon1=Weapon_ArtemisArtillery(power1=True)))
    b.board[(3, 2)].putUnitHere(Unit_Mountain(b))
    b.board[(4, 2)].putUnitHere(Unit_Building(b))
    b.board[(5, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b)) # this one is actually against the wall and cannot be pushed
    b.board[(4, 3)].putUnitHere(Unit_Alpha_Scorpion(b)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert b.board[(2, 2)].unit.currenthp == 2
    assert b.board[(3, 2)].unit.currenthp == 1
    assert b.board[(4, 2)].unit.currenthp == 1 # the building
    assert b.board[(5, 2)].unit.currenthp == 5
    assert b.board[(4, 1)].unit.currenthp == 5
    assert b.board[(4, 3)].unit.currenthp == 5
    b.board[(2, 2)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(2, 2)].unit.currenthp == 2  # firing unit unchanged
    assert b.board[(3, 2)].unit.currenthp == 1  # mountain unchanged
    assert b.board[(3, 2)].unit.type == 'mountain'  # mountain unchanged
    assert b.board[(4, 2)].unit.currenthp == 1  # target square took no damage since it's a building and power1 prevents damage to it
    assert b.board[(5, 2)].unit == None  # vek pushed off this square
    assert b.board[(4, 1)].unit.currenthp == 5  # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert b.board[(4, 3)].unit == None  # vek also pushed off this square
    assert b.board[(6, 2)].unit.currenthp == 5  # pushed vek has full health
    assert b.board[(4, 4)].unit.currenthp == 5  # vek pushed has full health

def t_WeaponArtemisArtilleryPower2():
    "Do the power Artillery demo from the game when you mouseover the weapon and you have extra damage powered."
    b = GameBoard()
    b.board[(2, 2)].putUnitHere(Unit_Artillery_Mech(b, weapon1=Weapon_ArtemisArtillery(power2=True)))
    b.board[(3, 2)].putUnitHere(Unit_Mountain(b))
    b.board[(4, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(5, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b)) # this one is actually against the wall and cannot be pushed
    b.board[(4, 3)].putUnitHere(Unit_Alpha_Scorpion(b)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert b.board[(2, 2)].unit.currenthp == 2
    assert b.board[(3, 2)].unit.currenthp == 1
    assert b.board[(4, 2)].unit.currenthp == 5
    assert b.board[(5, 2)].unit.currenthp == 5
    assert b.board[(4, 1)].unit.currenthp == 5
    assert b.board[(4, 3)].unit.currenthp == 5
    b.board[(2, 2)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(2, 2)].unit.currenthp == 2 # firing unit unchanged
    assert b.board[(3, 2)].unit.currenthp == 1 # mountain unchanged
    assert b.board[(3, 2)].unit.type == 'mountain' # mountain unchanged
    assert b.board[(4, 2)].unit.currenthp == 2 # target square took 1 damage
    assert b.board[(5, 2)].unit == None # vek pushed off this square
    assert b.board[(4, 1)].unit.currenthp == 5 # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert b.board[(4, 3)].unit == None # vek also pushed off this square
    assert b.board[(6, 2)].unit.currenthp == 5 # pushed vek has full health
    assert b.board[(4, 4)].unit.currenthp == 5 # vek pushed has full health

def t_WeaponArtemisArtilleryFullPower():
    "Do the Artillery demo from the game when you mouseover the weapon and you have buildings immune powered and damage powered."
    b = GameBoard()
    b.board[(2, 2)].putUnitHere(Unit_Artillery_Mech(b, weapon1=Weapon_ArtemisArtillery(power1=True)))
    b.board[(3, 2)].putUnitHere(Unit_Mountain(b))
    b.board[(4, 2)].putUnitHere(Unit_Building(b))
    b.board[(5, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b)) # this one is actually against the wall and cannot be pushed
    b.board[(4, 3)].putUnitHere(Unit_Alpha_Scorpion(b)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert b.board[(2, 2)].unit.currenthp == 2
    assert b.board[(3, 2)].unit.currenthp == 1
    assert b.board[(4, 2)].unit.currenthp == 1 # the building
    assert b.board[(5, 2)].unit.currenthp == 5
    assert b.board[(4, 1)].unit.currenthp == 5
    assert b.board[(4, 3)].unit.currenthp == 5
    b.board[(2, 2)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(2, 2)].unit.currenthp == 2  # firing unit unchanged
    assert b.board[(3, 2)].unit.currenthp == 1  # mountain unchanged
    assert b.board[(3, 2)].unit.type == 'mountain'  # mountain unchanged
    assert b.board[(4, 2)].unit.currenthp == 1  # target square took no damage since it's a building and power1 prevents damage to it
    assert b.board[(5, 2)].unit == None  # vek pushed off this square
    assert b.board[(4, 1)].unit.currenthp == 5  # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert b.board[(4, 3)].unit == None  # vek also pushed off this square
    assert b.board[(6, 2)].unit.currenthp == 5  # pushed vek has full health
    assert b.board[(4, 4)].unit.currenthp == 5  # vek pushed has full health

def t_WeaponBurstBeamNoPower():
    "Do the weapon demo with default power"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Laser_Mech(b, weapon1=Weapon_BurstBeam()))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Defense_Mech(b))
    b.board[(5, 1)].putUnitHere(Unit_Mountain(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].unit == None
    assert b.board[(3, 1)].unit.currenthp == 5
    assert b.board[(4, 1)].unit.currenthp == 2
    assert b.board[(5, 1)].unit.type == 'mountain'
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert b.board[(2, 1)].unit == None # still nothing here
    assert b.board[(2, 1)].effects == set()
    assert b.board[(3, 1)].unit.currenthp == 3 # vek took 2 damage
    assert b.board[(4, 1)].unit.currenthp == 1 # friendly took 1 damage
    assert b.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_WeaponBurstBeamAllyPower():
    "Do the weapon demo with ally immune powered"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Laser_Mech(b, weapon1=Weapon_BurstBeam(power1=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Defense_Mech(b))
    b.board[(5, 1)].putUnitHere(Unit_Mountain(b))
    b.board[(6, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].unit == None
    assert b.board[(3, 1)].unit.currenthp == 5
    assert b.board[(4, 1)].unit.currenthp == 2
    assert b.board[(5, 1)].unit.type == 'mountain'
    assert b.board[(6, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert b.board[(2, 1)].unit == None # still nothing here
    assert b.board[(2, 1)].effects == set()
    assert b.board[(3, 1)].unit.currenthp == 3 # vek took 2 damage
    assert b.board[(4, 1)].unit.currenthp == 2 # friendly took NO damage
    assert b.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged
    assert b.board[(6, 1)].unit.currenthp == 5 # this vek was saved by the mountain

def t_WeaponBurstBeamDamagePower():
    "Do the weapon demo with extra damage powered"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Laser_Mech(b, weapon1=Weapon_BurstBeam(power2=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Defense_Mech(b))
    b.board[(5, 1)].putUnitHere(Unit_Mountain(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].unit == None
    assert b.board[(3, 1)].unit.currenthp == 5
    assert b.board[(4, 1)].unit.currenthp == 2
    assert b.board[(5, 1)].unit.type == 'mountain'
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert b.board[(2, 1)].unit == None # still nothing here
    assert b.board[(2, 1)].effects == set()
    assert b.board[(3, 1)].unit.currenthp == 2 # vek took 3 damage
    assert b.board[(4, 1)].unit.type == 'mechcorpse' # friendly took 2 damage and died
    assert b.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_WeaponBurstBeamFullPower():
    "Do the weapon demo with ally immune powered"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Laser_Mech(b, weapon1=Weapon_BurstBeam(power1=True, power2=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Defense_Mech(b))
    b.board[(5, 1)].putUnitHere(Unit_Mountain(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].unit == None
    assert b.board[(3, 1)].unit.currenthp == 5
    assert b.board[(4, 1)].unit.currenthp == 2
    assert b.board[(5, 1)].unit.type == 'mountain'
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert b.board[(2, 1)].unit == None # still nothing here
    assert b.board[(2, 1)].effects == set()
    assert b.board[(3, 1)].unit.currenthp == 2 # vek took 3 damage
    assert b.board[(4, 1)].unit.currenthp == 2 # friendly took NO damage
    assert b.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_ExplosiveUnitDies():
    "Test a unit with the explosive effect dying"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Laser_Mech(b, weapon1=Weapon_BurstBeam()))
    b.board[(2, 1)].putUnitHere(Unit_Scorpion(b, effects={Effects.EXPLOSIVE}))
    b.board[(3, 1)].putUnitHere(Unit_Defense_Mech(b))
    b.board[(2, 2)].putUnitHere(Unit_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3 # laser mech
    assert b.board[(2, 1)].unit.currenthp == 3 # explosive vek
    assert b.board[(3, 1)].unit.currenthp == 2 # defense mech
    assert b.board[(2, 2)].unit.currenthp == 3 # vek to take damage from explosion
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    print(b.board[(1, 1)])
    assert b.board[(1, 1)].unit.currenthp == 2  # laser mech took damage from explosion
    assert b.board[(2, 1)].unit == None  # explosive vek died and exploded
    assert b.board[(3, 1)].unit.type == 'mechcorpse'  # defense mech died from shot, then the corpse got exploded on
    assert b.board[(2, 2)].unit.currenthp == 2  # vek took damage from explosion

def t_WeaponRammingEnginesDefault():
    "Do the weapon demo with no powered upgrades"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(2, 1)].unit.currenthp == 2  # wielder took 1 damage
    assert b.board[(3, 1)].unit == None # vek pushed off this tile
    assert b.board[(4, 1)].unit.currenthp == 3 # vek pushed here took 2 damage

def t_WeaponRammingEnginesPower1():
    "Do the weapon demo with the first upgrade powered"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=True, power2=False)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(2, 1)].unit.currenthp == 1  # wielder took 2 damage
    assert b.board[(3, 1)].unit == None # vek pushed off this tile
    assert b.board[(4, 1)].unit.currenthp == 2 # vek pushed here took 3 damage

def t_WeaponRammingEnginesPower2():
    "Do the weapon demo with the second upgrade powered"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=False, power2=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(2, 1)].unit.currenthp == 2  # wielder took 1 damage
    assert b.board[(3, 1)].unit == None # vek pushed off this tile
    assert b.board[(4, 1)].unit.currenthp == 2 # vek pushed here took 3 damage

def t_WeaponRammingEnginesFullPower():
    "Do the weapon demo with the both upgrades powered"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=True, power2=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(2, 1)].unit.currenthp == 1  # wielder took 2 damage
    assert b.board[(3, 1)].unit == None # vek pushed off this tile
    assert b.board[(4, 1)].unit.currenthp == 1 # vek pushed here took 4 damage

def t_WeaponRammingEnginesTileDamage():
    "Do the weapon demo with no powered upgrades but on sand tiles to make sure they get damaged"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(1, 1)].replaceTile(Tile_Sand(b))
    b.board[(2, 1)].replaceTile(Tile_Sand(b))
    b.board[(3, 1)].replaceTile(Tile_Sand(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    assert b.board[(1, 1)].effects == set() # sand tiles are all normal
    assert b.board[(2, 1)].effects == set()
    assert b.board[(3, 1)].effects == set()
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(2, 1)].unit.currenthp == 2  # wielder took 1 damage
    assert b.board[(3, 1)].unit == None # vek pushed off this tile
    assert b.board[(4, 1)].unit.currenthp == 3 # vek pushed here took 2 damage
    assert b.board[(1, 1)].effects == set() # this one untouched
    assert b.board[(2, 1)].effects == {Effects.SMOKE} # these 2 got smoked from the self damage
    assert b.board[(3, 1)].effects == {Effects.SMOKE} # and vek getting hit

def t_WeaponRammingEnginesShieldedTileDamage():
    "Do the weapon demo with no powered upgrades but on sand tiles with a shield to make sure they don't get damaged"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    b.board[(1, 1)].applyShield()
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(1, 1)].replaceTile(Tile_Sand(b))
    b.board[(2, 1)].replaceTile(Tile_Sand(b))
    b.board[(3, 1)].replaceTile(Tile_Sand(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    assert b.board[(1, 1)].effects == set() # sand tiles are all normal
    assert b.board[(2, 1)].effects == set()
    assert b.board[(3, 1)].effects == set()
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(2, 1)].unit.currenthp == 3  # wielder took 0 damage
    assert b.board[(3, 1)].unit == None # vek pushed off this tile
    assert b.board[(4, 1)].unit.currenthp == 3 # vek pushed here took 2 damage
    assert b.board[(1, 1)].effects == set() # this one untouched
    assert b.board[(2, 1)].effects == set() # this sand tile took no damage since the mech was shielded
    assert b.board[(3, 1)].effects == {Effects.SMOKE} # this one does take damage because this is where the vek got hit

def t_WeaponRammingEnginesIntoChasm():
    "Charge but stop at a chasm and die in it"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(2, 1)].replaceTile(Tile_Chasm(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    assert b.board[(3, 1)].effects == set() # normal chasm tile
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(2, 1)].unit == None # wielder and mech corpse died in the chasm
    assert b.board[(3, 1)].unit == None # vek pushed off this tile
    assert b.board[(4, 1)].unit.currenthp == 3 # vek pushed here took 2 damage
    assert b.board[(3, 1)].effects == set()  # normal chasm tile

def t_WeaponRammingEnginesOverChasm():
    "Charge over a chasm and don't die in it"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    b.board[(2, 1)].replaceTile(Tile_Chasm(b))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(4, 1)].unit.currenthp == 5
    assert b.board[(2, 1)].effects == set() # normal chasm tile
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    #for x in range(1, 6):
    #    print(b.board[x, 1])
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(3, 1)].unit.currenthp == 2 # wielder took 1 damage
    assert b.board[(4, 1)].unit == None # vek pushed off this tile
    assert b.board[(5, 1)].unit.currenthp == 3 # vek pushed here took 2 damage
    assert b.board[(2, 1)].effects == set()  # normal chasm tile

def t_WeaponRammingEnginesShield():
    "A shielded unit that uses ramming engines takes no self-damage."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=True, power2=True), effects={Effects.SHIELD}))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(1, 1)].unit.effects == {Effects.SHIELD}
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # wielder moved
    assert b.board[(2, 1)].unit.currenthp == 3  # wielder took 0 damage
    assert b.board[(3, 1)].unit == None # vek pushed off this tile
    assert b.board[(4, 1)].unit.currenthp == 1 # vek pushed here took 4 damage

def t_WeaponRammingEnginesMiss():
    "if ramming engine doesn't hit a unit, it doesn't take self damage."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=True, power2=True)))
    b.board[(1, 1)].replaceTile(Tile_Forest(b))
    b.board[(8, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 1)].effects == set()
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None  # wielder moved
    assert b.board[(8, 1)].unit.currenthp == 3  # wielder took 0 damage
    assert b.board[(1, 1)].effects == set() # original forest tile didn't take damage
    assert b.board[(8, 1)].effects == set() # destination forest tile undamaged as well


def t_NoOffBoardShotsGenCorner():
    "test noOffBoardShotsGen by putting a unit in a corner"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g = b.board[(1, 1)].unit.weapon1.genShots()
    assert next(g) == Direction.UP
    assert next(g) == Direction.RIGHT
    try:
        next(g)
    except StopIteration: # no more directions
        pass # which is good
    else:
        assert False # we got another direction?

def t_NoOffBoardShotsGenSide():
    "test noOffBoardShotsGen by putting a unit in a corner"
    b = GameBoard()
    b.board[(1, 2)].putUnitHere(Unit_Charge_Mech(b, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g = b.board[(1, 2)].unit.weapon1.genShots()
    assert next(g) == Direction.UP
    assert next(g) == Direction.RIGHT
    assert next(g) == Direction.DOWN
    try:
        next(g)
    except StopIteration: # no more directions
        pass # which is good
    else:
        assert False # we got another direction?

def t_WeaponTaurusCannonDefaultPower():
    "Shoot the Taurus Cannon with default power"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Cannon_Mech(b, weapon1=Weapon_TaurusCannon()))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit.effects == set()
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None # vek was pushed off this square
    assert b.board[(4, 1)].effects == set()
    assert b.board[(4, 1)].unit.effects == set()
    assert b.board[(4, 1)].unit.currenthp == 4 # vek lost 1 hp

def t_WeaponTaurusCannonDefaultPower1():
    "Shoot the Taurus Cannon with power1"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Cannon_Mech(b, weapon1=Weapon_TaurusCannon(power1=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit.effects == set()
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None # vek was pushed off this square
    assert b.board[(4, 1)].effects == set()
    assert b.board[(4, 1)].unit.effects == set()
    assert b.board[(4, 1)].unit.currenthp == 3 # vek lost 2 hp

def t_WeaponTaurusCannonPower2():
    "Shoot the Taurus Cannon with power2"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Cannon_Mech(b, weapon1=Weapon_TaurusCannon(power2=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit.effects == set()
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None # vek was pushed off this square
    assert b.board[(4, 1)].effects == set()
    assert b.board[(4, 1)].unit.effects == set()
    assert b.board[(4, 1)].unit.currenthp == 3 # vek lost 2 hp

def t_WeaponTaurusCannonFullPower():
    "Shoot the Taurus Cannon with power1"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Cannon_Mech(b, weapon1=Weapon_TaurusCannon(power1=True, power2=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit.effects == set()
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None # vek was pushed off this square
    assert b.board[(4, 1)].effects == set()
    assert b.board[(4, 1)].unit.effects == set()
    assert b.board[(4, 1)].unit.currenthp == 2 # vek lost 3 hp

def t_WeaponAttractionPulseDefault():
    "Shoot the Attraction Pulse at a unit with no power"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Defense_Mech(b, weapon1=Weapon_AttractionPulse(power1=False, power2=False)))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 2
    assert b.board[(4, 1)].effects == set()
    assert b.board[(4, 1)].unit.effects == set()
    assert b.board[(4, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 2
    assert b.board[(4, 1)].unit == None # vek was pushed off this square
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit.effects == set() # pulled 1 square closer
    assert b.board[(3, 1)].unit.currenthp == 5 # vek lost 0 hp

def t_WeaponAttractionPulseFullPower():
    "Shoot the Attraction Pulse at a unit with full power. IRL this gun takes no power, just making sure this doesn't break."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Defense_Mech(b, weapon1=Weapon_AttractionPulse(power1=True, power2=True)))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 2
    assert b.board[(4, 1)].effects == set()
    assert b.board[(4, 1)].unit.effects == set()
    assert b.board[(4, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 2
    assert b.board[(4, 1)].unit == None # vek was pushed off this square
    assert b.board[(3, 1)].effects == set()
    assert b.board[(3, 1)].unit.effects == set() # pulled 1 square closer
    assert b.board[(3, 1)].unit.currenthp == 5 # vek lost 0 hp

def t_WeaponAttractionPulseBump():
    "Attraction pulse does not set fire to forest tile if you pull another unit into you for bump damage."
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Defense_Mech(b, weapon1=Weapon_AttractionPulse(power1=True, power2=True)))
    b.board[(2, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    for x in 1, 2:
        b.board[(x, 1)].replaceTile(Tile_Forest(b))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 2
    assert b.board[(2, 1)].effects == set()
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(2, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].effects == set() # no fire
    assert b.board[(1, 1)].unit.effects == set()
    assert b.board[(1, 1)].unit.currenthp == 1 # took 1 damage
    assert b.board[(2, 1)].effects == set() # no fire
    assert b.board[(2, 1)].unit.effects == set()
    assert b.board[(2, 1)].unit.currenthp == 4 # vek lost 1 hp from bump

def t_WeaponShieldProjectorDefaultPower():
    "Maiden test of the shield projector with no upgrade power"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Defense_Mech(b, weapon1=Weapon_ShieldProjector(power1=False, power2=False)))
    b.board[(2, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(5, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(1, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(2, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(3, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(5, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    for x in range(1, 6):
        for y in range(1, 3):
            assert b.board[(x, y)].unit.effects == set()
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(1, 1)].unit.effects == set()  # no change
    assert b.board[(2, 1)].unit.effects == set() # shot over this one
    assert b.board[(3, 1)].unit.effects == {Effects.SHIELD}
    assert b.board[(4, 1)].unit.effects == {Effects.SHIELD}
    assert b.board[(5, 1)].unit.effects == set()
    assert b.board[(1, 2)].unit.effects == set()  # no change to anything in the 2nd row
    assert b.board[(2, 2)].unit.effects == set()
    assert b.board[(3, 2)].unit.effects == set()
    assert b.board[(4, 2)].unit.effects == set()
    assert b.board[(5, 2)].unit.effects == set()

def t_WeaponShieldProjectorPower2():
    "Shield Projector with power2"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Defense_Mech(b, weapon1=Weapon_ShieldProjector(power1=True, power2=True))) # power1 is ignored
    b.board[(2, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(5, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(1, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(2, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(3, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(4, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(5, 2)].putUnitHere(Unit_Alpha_Scorpion(b))
    for x in range(1, 6):
        for y in range(1, 3):
            assert b.board[(x, y)].unit.effects == set()
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(1, 1)].unit.effects == set()  # no change
    assert b.board[(2, 1)].unit.effects == {Effects.SHIELD} # shot over this one but he got shielded anyway
    assert b.board[(3, 1)].unit.effects == {Effects.SHIELD}
    assert b.board[(4, 1)].unit.effects == {Effects.SHIELD}
    assert b.board[(5, 1)].unit.effects == set()
    assert b.board[(1, 2)].unit.effects == set()
    assert b.board[(2, 2)].unit.effects == set()
    assert b.board[(3, 2)].unit.effects == {Effects.SHIELD}
    assert b.board[(4, 2)].unit.effects == set()
    assert b.board[(5, 2)].unit.effects == set()

def t_WeaponShieldProjectorGen():
    "Test the generator for the shield projector."
    b = GameBoard()
    b.board[(5, 5)].putUnitHere(Unit_Defense_Mech(b, weapon1=Weapon_ShieldProjector(power1=True, power2=True, usesremaining=1)))  # power1 is ignored
    g = b.board[(5, 5)].unit.weapon1.genShots()
    assert next(g) == (Direction.UP, 2) # generator generates what we expect
    b.board[(5, 5)].unit.weapon1.shoot(Direction.UP, 2) # shoot to spend the ammo
    try:
        next(g)
    except StopIteration:
        pass # what we expect
    else:
        assert False # ya fucked up

def t_WeaponViceFistNoPower():
    "Test the Vice Fist with no power"
    b = GameBoard()
    b.board[(2, 1)].putUnitHere(Unit_Judo_Mech(b, weapon1=Weapon_ViceFist(power1=False, power2=False)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 4
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None

def t_WeaponViceFistPower1():
    "Test the Vice Fist with power1"
    b = GameBoard()
    b.board[(2, 1)].putUnitHere(Unit_Judo_Mech(b, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 4 # no additional effect since this was an enemy
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None

def t_WeaponViceFistPower2():
    "Test the Vice Fist with power1"
    b = GameBoard()
    b.board[(2, 1)].putUnitHere(Unit_Judo_Mech(b, weapon1=Weapon_ViceFist(power1=False, power2=True)))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 2 # took additional damage
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None

def t_WeaponViceFistPower1Friendly():
    "Test the Vice Fist with power1 and a friendly unit"
    b = GameBoard()
    b.board[(2, 1)].putUnitHere(Unit_Judo_Mech(b, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    b.board[(3, 1)].putUnitHere(Unit_Siege_Mech(b))
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 2
    b.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit.currenthp == 2 # friendly unit took no damage
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None

def t_WeaponViceFistPower1FriendlyChasm():
    "Test the Vice Fist with power1 and a friendly unit, but kill the unit by throwing it into a chasm"
    b = GameBoard()
    b.board[(2, 1)].putUnitHere(Unit_Judo_Mech(b, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    b.board[(3, 1)].putUnitHere(Unit_Siege_Mech(b))
    b.board[(1, 1)].replaceTile(Tile_Chasm(b))
    assert b.board[(1, 1)].unit == None
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 2
    b.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert b.board[(1, 1)].unit == None # friendly unit died in the chasm
    assert b.board[(2, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit == None

def t_WeaponClusterArtilleryNoPower():
    "Default power test for Cluster Artillery"
    b = GameBoard()
    b.board[(1, 3)].putUnitHere(Unit_Siege_Mech(b, weapon1=Weapon_ClusterArtillery(power1=False, power2=False)))
    b.board[(3, 3)].putUnitHere(Unit_Building(b))
    b.board[(4, 3)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(3, 4)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 3)].unit.currenthp == 2
    assert b.board[(3, 3)].unit.currenthp == 1 # building
    assert b.board[(4, 3)].unit.currenthp == 5
    assert b.board[(3, 4)].unit.currenthp == 5
    b.board[(1, 3)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(1, 3)].unit.currenthp == 2
    assert b.board[(3, 3)].unit.currenthp == 1  # building
    assert b.board[(4, 3)].unit == None # vek pushed
    assert b.board[(5, 3)].unit.currenthp == 4 # took 1 damage
    assert b.board[(3, 4)].unit == None # vek pushed
    assert b.board[(3, 5)].unit.currenthp == 4 # took 1 damage

def t_WeaponClusterArtilleryPower1():
    "power1 test for Cluster Artillery"
    b = GameBoard()
    b.board[(1, 3)].putUnitHere(Unit_Siege_Mech(b, weapon1=Weapon_ClusterArtillery(power1=True, power2=False)))
    b.board[(3, 3)].putUnitHere(Unit_Building(b))
    b.board[(4, 3)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(3, 4)].putUnitHere(Unit_Building(b))
    assert b.board[(1, 3)].unit.currenthp == 2
    assert b.board[(3, 3)].unit.currenthp == 1 # building
    assert b.board[(4, 3)].unit.currenthp == 5
    assert b.board[(3, 4)].unit.currenthp == 1 # attacked building
    b.board[(1, 3)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(1, 3)].unit.currenthp == 2
    assert b.board[(3, 3)].unit.currenthp == 1  # building
    assert b.board[(4, 3)].unit == None # vek pushed
    assert b.board[(5, 3)].unit.currenthp == 4 # took 1 damage
    assert b.board[(3, 4)].unit.currenthp == 1  # attacked building took no damage

def t_WeaponClusterArtilleryFullPower():
    "full power test for Cluster Artillery"
    b = GameBoard()
    b.board[(1, 3)].putUnitHere(Unit_Siege_Mech(b, weapon1=Weapon_ClusterArtillery(power1=True, power2=True)))
    b.board[(3, 3)].putUnitHere(Unit_Building(b))
    b.board[(4, 3)].putUnitHere(Unit_Alpha_Scorpion(b))
    b.board[(3, 4)].putUnitHere(Unit_Building(b))
    assert b.board[(1, 3)].unit.currenthp == 2
    assert b.board[(3, 3)].unit.currenthp == 1 # building
    assert b.board[(4, 3)].unit.currenthp == 5
    assert b.board[(3, 4)].unit.currenthp == 1 # attacked building
    b.board[(1, 3)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(1, 3)].unit.currenthp == 2
    assert b.board[(3, 3)].unit.currenthp == 1  # building
    assert b.board[(4, 3)].unit == None # vek pushed
    assert b.board[(5, 3)].unit.currenthp == 3 # took 2 damage
    assert b.board[(3, 4)].unit.currenthp == 1  # attacked building took no damage

def t_WeaponGravWellNormal():
    "default test for grav well"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Gravity_Mech(b, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(1, 1)].unit.currenthp == 3 # untouched wielder
    assert b.board[(3, 1)].unit == None # vek pushed
    assert b.board[(2, 1)].unit.currenthp == 5 # to here with no damage

def t_WeaponGravWellStable():
    "grav well can't pull stable units"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Gravity_Mech(b, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    b.board[(3, 1)].putUnitHere(Unit_Mountain(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(3, 1)].unit.currenthp == 1
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(1, 1)].unit.currenthp == 3 # untouched wielder
    assert b.board[(3, 1)].unit.currenthp == 1 # mountain not moved and undamaged
    assert b.board[(3, 1)].unit.type == 'mountain'

def t_WeaponGravWellBump():
    "grav well pulls vek into a mountain"
    b = GameBoard()
    b.board[(1, 1)].putUnitHere(Unit_Gravity_Mech(b, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    b.board[(2, 1)].putUnitHere(Unit_Mountain(b))
    b.board[(3, 1)].putUnitHere(Unit_Alpha_Scorpion(b))
    assert b.board[(1, 1)].unit.currenthp == 3
    assert b.board[(2, 1)].unit.currenthp == 1
    assert b.board[(2, 1)].unit.type == 'mountain'
    assert b.board[(3, 1)].unit.currenthp == 5
    b.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    assert b.board[(1, 1)].unit.currenthp == 3 # untouched wielder
    assert b.board[(3, 1)].unit.currenthp == 4 # vek pushed and bumped for 1 damage
    assert b.board[(2, 1)].unit.currenthp == 1 # damage mountain now
    assert b.board[(2, 1)].unit.type == 'mountaindamaged'

########### write tests for these:
# If you shield a beam ally (train) with allies immune and then shoot it, the shield remains.
# if a mech with ramming engine is shielded and then rams something and stops on a forest tile, the shield takes the damage and the forest does not take any damage and catch fire.
# shielded blobber bombs still explode normally

########## special objective units:
# Satellite Rocket: 2 hp, Not powered, Smoke Immune, stable, "Satellite Launch" weapon kills nearby tiles when it launches.
# Train: 1 hp, Fire immune, smoke immune, stable, "choo choo" weapon move forward 2 spaces but will be destroyed if blocked. kills whatever unit it runs into, stops dead on the tile before that unit. It is multi-tile, shielding one tile shields both.
    # when attacked and killed, becomes a "damaged train" that is also stable and fire immune. When that is damaged again, it becomes a damaged train corpse that can't be shielded, is no longer fire immune, and is flying like a normal corpse.
    # units can bump into the corpse
# ACID Launcher: 2 hp, stable. weapon is "disentegrator": hits 5 tiles killing anything present and leaves acid on them.


########## Weapons stuff for later
# rocks thrown at sand tiles do not create smoke. This means that rocks do damage to units but not tiles at all.
# when leap mech leaps onto an acid tile, he takes the acid first and then takes double damage.
# when unstable cannon shoots and lands on acid tile, it takes damage then gains acid. when unstable cannon shoots, it damages the tile that it's on and then pushes.
# if a mech has a shield and fires the cryo launcher, the shooter does not freeze.
# If a unit is frozen and damaged and bumped against a wall, the damage removes the ice and then the bump damage hurts the unit.
# Acid Launcher's weapon is called disentegrator. It hits 5 tiles and kills any unit there and leaves acid on the tile. It's stable with 2 HP.
# If mech stands in water and is hit by the acid gun, the water does not gain acid. The mech is pushed out and gains acid.
# if a mech stands next to water and hit by the acid gun, the unit is pushed into the water and the water and unit gain acid. The tile the mech was previously on does not gain acid.
# if you use the burst beam (laser mech) and kill an armor psion and hit another unit behind it, the armor is removed from the other unit after it takes damage from the laser.
# if you shoot your mechs with the acid gun and they have a shield, they get acid anyway! wtf!
# if a non-flying shielded unit is in water and is hit by the acid gun, it's pushed first and then acid goes to the tile where it lands, and does give it acid!
# the shock cannon is a projectile that pulls the unit in its path toward the direction it was fired. It pushes and does damage to the tile on the other side of what got hit.
# Terraformer weapon "terraformer" kills any unit in a 2x3 grid around it, converts tiles to sand tile.
# Earth Mover expands toward 0 and 8 on X 2 squares at a time. It does this on the y row that it's on and the row right below it.
# if a scarab that has an artillery shot weapon only is surrounded by units so it has no place to move and it has no targets available, it will choose to not shoot anything.
# Cannon-bot's weapon is "Cannon 84 Mark I". it's a projectile weapon that does one damage and sets target on fire.
# Repair Drop heals your friendly npc freezemine laying bots that you do not control. I guess to remove bad effects? Repair drop heals your units to full health. It does not remove fire from the tile of a repaired unit.
# Flamethrower weapon can't go through more than one mountain tile.
# The Goo's goo attack just does 4 damage and ice negates it like a regular weapon.
# viscera nanobots do not repair tiles or remove bad effects, it only heals HP.
# Shield tank: first power gives it 2 hp, second power makes it shoot a projectile that gives shields. has 1 hp by default.
# Satellite launches happen after enemy attacks.
# robots do not benefit from psion vek passives such as explosive.
# If a vek is attacking the tile in front of him and he's moved to the edge of the board so he can't hit a tile in front of him, his attack is cancelled.

# buildings do block mech movement
# a burrower taking damage from fire cancels its attack and makes it burrow, but again it does lose fire when it re-emerges.
# the little bombs that the blobber throws out are not considered enemies when your objective is to kill 7 enemies.
# blobbers will move out of smoke and throw out a bomb after you take your turn.

########## Research these:
# You can heal allies with the Repair Field passive - when you tell a mech to heal, your other mechs are also healed for 1 hp, even if they're currently disabled.
# What happens when objective units die? specifically: terraformer, disposal unit, satellite rocket (leaves a corpse that is invincible and can't be pushed. It's friendly so you can move through it), earth mover.
# what happens if lightning strikes a desert or forest tile with a vek with acid on it? Does it create smoke first, then kill the enemy, then drop the acid and convert the tile to a regular ground tile? Or does the acid drop first converting the tiel before it does anything?

########## Do these ones even matter?
# Spiderling eggs with acid hatch into spiders with acid.
# Timepods can only be on ground tiles, they convert sand and forest to ground upon landing.
# If you set a burrower on fire (when it spawns) and it then moves by burrowing, it re-emerges without fire!

# Movement POC:
# obstructions = ((2, 2), (-1, -1))
#
# moves = ((0, 1), (1, 0), (-1, 0), (0, -1))
#
# positions = {}
#
# def branch(x, y, n):
#     if n == 0:
#         return
#
#     positions[(x, y)] = n
#
#     for mx, my in moves:
#         if (x + mx, y + my) not in obstructions and positions.get((x + mx, y + my)) < n:
#             branch(x + mx, y + my, n - 1)
#
# branch(0, 0, 5)
#
# print
# positions
if __name__ == '__main__':
    g = sorted(globals())
    testsrun = 0
    for test in [x for x in g if x.startswith('t_')]:
        runTest(test)
        testsrun += 1
    print(testsrun, "tests run successfully.")