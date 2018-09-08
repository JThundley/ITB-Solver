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
    b.push((2, 1), Direction.LEFT)
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
    b.moveUnit((1, 2), (1, 1))
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
    b.push((2, 1), Direction.LEFT)
    b.push((2, 2), Direction.LEFT)
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
    b.moveUnit((2, 1), (1, 1))
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
    b.push((2, 1), Direction.LEFT)
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
    b.board[(1, 2)].applyAcid()
    b.moveUnit((1, 2), (1, 1))
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
    b.moveUnit((1, 2), (1, 1))
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
    b.moveUnit((1, 2), (1, 1))
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
    b.moveUnit((1, 1), (2, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
    assert b.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert b.board[(2, 1)].effects == set()
    assert b.board[(1, 1)].unit.effects == {Effects.ACID} # unit is massive so it survived.
    b.moveUnit((1, 1), (2, 1)) # the unit moves out and still has acid
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.push((1, 1), Direction.RIGHT)
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
    b.push((1, 1), Direction.RIGHT)
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
    b.push((1, 1), Direction.RIGHT)
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
    b.push((1, 1), Direction.RIGHT)
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
        b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
    assert b.board[(1, 1)].effects == set()
    assert b.board[(8, 8)].effects == set()
    assert b.board[(2, 1)].unit == None
    assert b.board[(8, 8)].unit.effects == set() # unit is on far teleporter
    b.moveUnit((8, 8), (7, 8)) # move it off teleporter
    assert b.board[(1, 1)].unit == None
    assert b.board[(8, 8)].unit == None
    assert b.board[(7, 8)].unit.effects == set() # unit is here
    b.moveUnit((7, 8), (8, 8)) # move it back to far teleporter
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
    b.moveUnit((2, 1), (1, 1)) # move scarab to near teleporter
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((2, 1), (1, 1))
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
    b.push((1, 2), Direction.DOWN)
    assert b.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert b.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    b.push((1, 1), Direction.UP)
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
    b.push((1, 2), Direction.DOWN)
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
    b.moveUnit((2, 1), (1, 1))
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
    print(b.board[(1, 1)].unit)
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
    b.moveUnit((2, 1), (1, 1))
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
    b.moveUnit((1, 1), (2, 1))
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

########### write tests for these:
# do a test of each unit to verify they have the proper attributes by default.
# dead vek that that are pushed to tiles with mines remove the mines!

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
# Shield protects you from being frozen by ice storm.
# If a unit is frozen and damaged and bumped against a wall, the damage removes the ice and then the bump damage hurts the unit.
# A unit leaves effects where its body lands. For example, if you punch a unit with acid on a sand tile, the sand tile creates smoke, the unit dies, and the tile that the unit was pushed to (with no health) gets the acid pool.
# Acid Launcher's weapon is called disentegrator. It hits 5 tiles and kills any unit there and leaves acid on the tile. It's stable with 2 HP.
# If mech stands in water and is hit by the acid gun, the water does not gain acid. The mech is pushed out and gains acid.
# if a mech stands next to water and hit by the acid gun, the unit is pushed into the water and the water and unit gain acid. The tile the mech was previously on does not gain acid.
# If the rocket mech shoots a vek and kills it one shot, the vek will trigger the mine on the tile it is pushed to even though it "died" when it got hit on another tile.
# if you use the burst beam (laser mech) and kill an armor psion and hit another unit behind it, the armor is removed from the other unit after it takes damage from the laser.
# if you shoot your mechs withe acid gun and they have a shield, they get acid anyway! wtf!
# if a non-flying shielded unit is in water and is hit by the acid gun, it's pushed first and then acid goes to the tile where it lands, and does give it acid!
# the shock cannon is a projectile that pushes the unit in its path toward the direction it was fired. it pushes and does damage to the tile on the other side of what got hit.
# Terraformer weapon "terraformer" kills any unit in a 2x3 grid around it, converts tiles to sand tile.
# Earth Mover expands toward 0 and 8 on X 2 squares at a time. It does this on the y row that it's on and the row right below it.
# if a scarab that has an artillery shot weapon only is surrounded by units so it has no place to move and it has no targets available, it will choose to not shoot anything.
# Cannon-bot's weapon is "Cannon 84 Mark I". it's a projectile weapon that does one damage and sets target on fire.
# Repair Drop heals your friendly npc freezemine laying bots that you do not control. I guess to remove bad effects? Repair drop heals your units to full health. It does not remove fire from the tile of a repaired unit.
# Flamethrower weapon can't go through more than one mountain tile.
# The Goo's goo attack just does 4 damage and ice negates it like a regular weapon.
# viscera nanobots do not repair tiles or remove bad effects, it only heals HP.

# buildings do block mech movement
# a burrower taking damage from fire cancels its attack and makes it burrow, but again it does lose fire when it re-emerges.
# when rocks fall on the boss level, it replaces lava with ground. when it falls on ground that's on fire, the fire remains.
# replacing tiles with emerging vek typically gets rid of the emerging vek. e.g. the dam replacing emerging ground tiles with water tiles, cataclysm replacing them with chasm tiles, etc.

########## Research these:
# If a Mech Corpse is repaired (either through Viscera Nanobots or Repair Drop) it reverts to an alive mech. You can also heal allies with the Repair Field passive - when you tell a mech to heal, your other mechs are also healed for 1 hp, even if they're currently disabled.
# What happens when objective units die? specifically: terraformer, disposal unit, satellite rocket, earth mover.

########## Do these ones even matter?
# Spiderling eggs with acid hatch into spiders with acid.
# Timepods can only be on ground tiles, they convert sand and forest to ground upon landing.
# If you set a burrower on fire (when it spawns) and it then moves by burrowing, it re-emerges without fire!

######### Envinronmental actions:
# Ice storm, air strike, tsunami, cataclysm, conveyor belts, falling rocks, tentacles, tiles turning to lava, lighting.

if __name__ == '__main__':
    g = sorted(globals())
    testsrun = 0
    for test in [x for x in g if x.startswith('t_')]:
        runTest(test)
        testsrun += 1
    print(testsrun, "tests run successfully.")