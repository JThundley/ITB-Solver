#!/usr/bin/env python3

"These are u nit tests for itbsolver. All test functions must start with t_ to differentiate them from the functions of the main script."

from itbsolver import *

def runTest(funcname):
    "This runs the function funcname and prints information about the tests. This prints out the name of the function, and then PASSED if assertion errors didn't short-circuit this whole script."
    print("%s: " % funcname[2:], end='')
    globals()[funcname]()
    print('PASSED')

def testTheTests():
    "Test this tests file to look for common errors."
    funcs = set()
    docstrings = set()
    commentisnext = False
    lineno = 0
    for line in open('tests.py'):
        lineno += 1
        if line.startswith('def '):
            commentisnext = True
            funcname = line.split()[1].split('()')[0]
            if funcname in funcs:
                print("#%s Duplicate function detected:" % lineno, funcname)
            funcs.add(funcname)
        elif commentisnext:
            docstring = line.strip()
            if not docstring or not docstring.startswith('"'):
                print("#%s Blank docstring for" % lineno, funcname)
            elif docstring in docstrings:
                print("#%s Duplicate docstring detected:" % lineno, docstring)
            docstrings.add(line.strip())
            commentisnext = False
        elif line.startswith("if __name__ == '__main__':"):
            return
        elif line.startswith('    print') and funcname.startswith('t_'):
            print("#%s print statment left in" % lineno, funcname)

def t_BumpDamage():
    "2 units bump into each other and take 1 damage each."
    g = Game()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Beetle(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit.currenthp == 5
    g.board[(2, 1)].push(Direction.LEFT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 4

def t_BumpDamageOnForestNoFire():
    "2 units bump into each other on a forest the forest does NOT catch fire."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Beetle(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit.currenthp == 5
    g.board[(2, 1)].push(Direction.LEFT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 4
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()

def t_ForestCatchesFire():
    "A forest tile takes damage and catches fire."
    g = Game()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}

def t_FireTurnsIceToWater():
    "An ice tile takes fire damage and turns to water. A flying unit on the tile catches fire."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Ice(g))
    g.board[(1, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].type == "water"
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}

def t_ShieldBlocksTileFire():
    "a shielded unit that is hit with fire doesn't catch fire but the tile does. The shield remains."
    g = Game()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g, effects={Effects.SHIELD}))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_IceAndShieldHitWithFire():
    "A frozen unit with a shield is hit by fire. The ice is removed, the shield remains, the tile catches on fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    g.board[(1, 1)].applyIce()
    g.board[(1, 1)].applyShield()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ICE, Effects.SHIELD}
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_ShieldRemovedOnFireTile():
    "A shielded unit is put onto a fire tile. The unit takes a hit which removes the shield and the unit catches fire."
    g = Game()
    g.board[(1, 1)].applyFire()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g, effects={Effects.SHIELD}))
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}

def t_MountainOverkill():
    "A mountain takes 5 damage twice and needs two hits to be destroyed."
    g = Game()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 1)].takeDamage(5)
    assert g.board[(1, 1)].unit.type == 'mountaindamaged'
    g.board[(1, 1)].takeDamage(5)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None
    assert g.board[(1, 1)].effects == set()

def t_FlyingUnitOnFireOverWater():
    "A flying unit that is on fire that moves to a water tile remains on fire"
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 2)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 2)].effects == set()
    g.board[(1, 2)].applyFire()
    g.board[(1, 2)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].unit.type == 'hornet'
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(1, 2)].effects == {Effects.FIRE}
    assert g.board[(1, 2)].unit == None

def t_FlyingUnitCatchesFireOverWater():
    "A flying unit is set on fire on an Ice tile. The unit catches fire, the tile does not."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Ice(g))
    g.board[(1, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 2)].effects == set()
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].unit.type == 'hornet'
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}

def t_FlyingUnitIcedOverWater():
    "A flying unit that is frozen on water remains frozen because the tile under it becomes ice instead of water."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].unit.type == 'hornet'
    assert g.board[(1, 1)].type == 'ice'
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}

def t_WaterRemovesIceFromUnit():
    "A flying unit or ground unit that is frozen and is then moved onto a water tile is unfrozen."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g)) # make water tiles
    g.board[(1, 2)].replaceTile(Tile_Water(g))
    g.board[(2, 1)].createUnitHere(Unit_Hornet(g)) # flying unit on the bottom next to the tile
    g.board[(2, 2)].createUnitHere(Unit_Blobber(g)) # ground unit above it next to water tile
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED} # no new tile effects
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].effects == {Effects.SUBMERGED}  # no new tile effects
    assert g.board[(2, 2)].unit.effects == set()  # no unit effects
    g.board[(2, 1)].applyIce() # freeze the flyer
    g.board[(2, 2)].applyIce()  # freeze the flyer
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}
    assert g.board[(2, 2)].unit.effects == {Effects.ICE}
    assert g.board[(1, 1)].type == 'water'
    assert g.board[(1, 2)].type == 'water'
    g.board[(2, 1)].push(Direction.LEFT)
    g.board[(2, 2)].push(Direction.LEFT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 2)].unit == None # the ground unit didn't survive the water

def t_WaterTileTurnsToIceWhenIce():
    "A water tile that is hit with ice becomes an ice tile"
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].type == 'ice'

def t_WaterTilePutsOutUnitFire():
    "A ground unit that is on fire that moves into a water tile is no longer on fire."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(2, 1)].createUnitHere(Unit_Beetle_Leader(g)) # massive unit on the bottom next to the water tile
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyFire()
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == set()

def t_RepairWaterAcidTileDoesntRemoveAcid():
    "When a water tile has acid on it, it becomes an acid water tile. A flying unit repairing here does NOT remove the acid."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g, effects={Effects.ACID}))
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    g.board[(1, 1)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}

def t_IceAcidWaterThenThawingWithFireRemovesAcid():
    "When an acid water tile is frozen, it becomes a frozen acid tile that behaves just like an ice tile. When this frozen acid tile is destroyed by fire, it becomes a regular water tile."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g, effects={Effects.ACID}))
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].type == 'ice'
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].type == 'water'

def t_IceAcidWaterThenThawingWithDamageLeavesAcid():
    "When an acid water tile is frozen, it becomes a frozen acid tile that behaves just like an ice tile. When this frozen acid tile is destroyed by damage, it reverts to an acid water tile."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g, effects={Effects.ACID}))
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].type == 'ice'
    g.board[(1, 1)].takeDamage(10) # we only damage it once, it needs 2 hits like a mountain.
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].type == 'ice_damaged'
    g.board[(1, 1)].takeDamage(10) # now the ice should be gone
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.ACID}
    assert g.board[(1, 1)].type == 'water'

def t_UnitDoesntGetAcidFromIcedAcidWater():
    "If acid is put onto an ice tile, it becomes a frozen acid tile. This means there is no pool of acid on it and a unit can't pick up acid by moving here."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].type == 'ice'
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].type == 'ice'
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit.effects == set()

def t_RepairingInSmokeLeavesSmoke():
    "A unit that repairs in a smoke cloud (because camilla allows actions while smoked) does NOT remove the smoke."
    g = Game()
    g.board[(1, 1)].applySmoke()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    g.board[(1, 1)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}

def t_FlyingDoesntGetAcidFromAcidWater():
    "A flying unit on an acid water tile does not get acid on it."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g, effects={Effects.ACID}))
    g.board[(2, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].push(Direction.LEFT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == set()

def t_IceDoesntEffectAcidPool():
    "If a tile with acid on it is frozen, nothing happens. The acid remains."
    g = Game()
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}

def t_IceDoesNothingToLava():
    "Lava is unfreezable."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Lava(g))
    assert g.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert g.board[(1, 1)].type == 'lava'

def t_LavaSetsMassiveOnFire():
    "Massive units that go into lava catch on fire."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Lava(g))
    g.board[(1, 2)].createUnitHere(Unit_Beetle_Leader(g))
    assert g.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    g.board[(1, 2)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}

def t_UnitTakesAcidFromTile():
    "When you step on an acid tile, it becomes a regular tile. the first unit that steps there takes acid away."
    g = Game()
    g.board[(1, 1)].applyAcid()
    g.board[(1, 2)].createUnitHere(Unit_Beetle_Leader(g))
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    g.board[(1, 2)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}

def t_UnitLeavesAcidWhenKilled():
    "When a unit with acid dies, it leaves behind an acid pool."
    g = Game()
    g.board[(1, 2)].createUnitHere(Unit_Beetle_Leader(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    g.board[(1, 2)].applyAcid()
    g.board[(1, 2)].moveUnit((1, 1))
    g.board[(1, 1)].die()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 2)].effects == set()

def t_MountainTileCantGainAcid():
    "Mountain tile can't gain acid., absolutely nothing happens to the mountain or the tile."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyAcid()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()

def t_IceGroundUnitDiesInChasm():
    "A frozen unit dies in a chasm."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Chasm(g))
    g.board[(1, 2)].createUnitHere(Unit_Beetle_Leader(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    g.board[(1, 2)].applyIce()
    assert g.board[(1, 2)].unit.effects == {Effects.ICE}
    g.board[(1, 2)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 1)].unit == None

def t_IceFlyingUnitDiesInChasm():
    "when a flying unit is frozen with ice and then moved to a chasm, it dies because it's not really flying anymore."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Chasm(g))
    g.board[(1, 2)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    g.board[(1, 2)].applyIce()
    assert g.board[(1, 2)].unit.effects == {Effects.ICE}
    g.board[(1, 2)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(1, 2)].unit == None

def t_AcidPutsOutTileFire():
    "When a tile gets acid, it removes the fire from the tile."
    g = Game()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    g.board[(1, 1)].applyAcid()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}

def t_AcidFromDeadUnitPutsOutTileFire():
    "If a tile is on fire and a unit with acid dies on it, Acid pool is left on the tile removing the fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    g.board[(1, 1)].takeDamage(10)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None

def t_RockWithAcidLeavesAcidWhenKilled():
    "A rock leaves acid when killed just like a vek"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Rock(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None

def t_UnitsOnFireDontLightTileOnDeath():
    "flying units that are on fire doesn't transfer fire to the vek emerge tile below."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    g.board[(1, 1)].moveUnit((2, 1))
    g.board[(2, 1)].die()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit == None

def t_SmallGroundUnitBringsAcidIntoWater():
    "a non-massive ground unit with acid is pushed into water: tile becomes an acid water tile and the unit dies"
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(2, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.ACID}
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit == None # unit wasn't massive so it died.

def t_MassiveGroundUnitBringsAcidIntoWater():
    "a massive ground unit with acid is pushed into water: tile becomes an acid water tile and the unit survives. It then walks out and still has acid."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(2, 1)].createUnitHere(Unit_Large_Goo(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.attributes == {Attributes.MASSIVE}
    g.board[(2, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.ACID}
    g.board[(2, 1)].moveUnit((1, 1))
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID} # unit is massive so it survived.
    g.board[(1, 1)].moveUnit((2, 1)) # the unit moves out and still has acid
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.ACID}  # unit still has acid

def t_GroundUnitWithAcidAndFireDies():
    "a ground unit with acid and fire dies on a normal tile: acid pool is left on the tile."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyAcid()
    g.board[(2, 1)].applyFire()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.ACID, Effects.FIRE}
    g.board[(2, 1)].moveUnit((1, 1))
    g.board[(1, 1)].die()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit == None

def t_MountainCantBeSetOnFire():
    "mountains can't be set on fire, but the tile they're on can!"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == set()

def t_SmokePutsOutFire():
    "Attacking a forest tile with something that leaves behind smoke doesn't light it on fire! Does smoke put out fire? Yes, smoke reverts it back to a forest tile. When the jet mech attacks and smokes a forest, it is only smoked. the forest remains, there's no fire, but there is smoke."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    g.board[(1, 1)].applySmoke()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].type == 'forest'

def t_AttackingSmokedForestRemovesSmokeAndCatchesFire():
    "Attacking a forest that is smoked will remove the smoke and set the tile on fire."
    g = Game() # This is all the exact same as smoke puts out fire
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    g.board[(1, 1)].applySmoke()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].type == 'forest' # until here, now let's attack it again!
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}

def t_SettingFireToSmokedTileRemovesSmokeAndCatchesFire():
    "Setting fire to a normal tile that is smoked will remove the smoke and set the tile on fire."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Ground(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    g.board[(1, 1)].applySmoke()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].type == 'ground'
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}

def t_SettingFireToSmokedWaterTileDoesNothing():
    "Setting fire to a water tile that is smoked will leave the smoke."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    g.board[(1, 1)].applySmoke()
    assert g.board[(1, 1)].effects == {Effects.SMOKE, Effects.SUBMERGED}
    assert g.board[(1, 1)].type == 'water'
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE, Effects.SUBMERGED}

def t_SettingFireToSmokedChasmTileDoesNothing():
    "Setting fire to a chasm tile that is smoked will leave the smoke."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Chasm(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].applySmoke()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].type == 'chasm'
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}

def t_SettingFireToSmokedIceTileRemovesSmokeAndTurnsToWater():
    "Setting fire to an ice tile that is smoked will remove the smoke and turn it into a water tile."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Ice(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    g.board[(1, 1)].applySmoke()
    assert g.board[(1, 1)].effects == {Effects.SMOKE, Effects.SUBMERGED}
    assert g.board[(1, 1)].type == 'water'
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.SMOKE}

def t_BuildingAcidGoesToTile():
    "When a building on a normal tile is hit with acid, the tile has acid."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Building(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyAcid()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit.effects == set()

def t_FlyingUnitWithAcidDiesInWater():
    "When a flying unit with acid dies over water, it becomes a water acid tile."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(2, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.ACID}
    g.board[(2, 1)].moveUnit((1, 1))
    g.board[(1, 1)].die()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit == None

def t_IceGroundUnitWithAcidDiesInWater():
    "frozen with acid units pushed into water make the water into acid water."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(2, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyAcid()
    g.board[(2, 1)].applyIce()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.ACID, Effects.ICE}
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit == None

def t_IceFlyingUnitOverChasmKillsIt():
    "if you freeze a flying unit over a chasm it dies"
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Chasm(g))
    g.board[(1, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None

def t_UnitsOnFireCatchForestsOnFireByMovingToThem():
    "Fire spreads from units (including flying) on fire to forest tiles."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyFire()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit == None

def t_UnitsOnFireCatchSmokedForestsOnFireByMovingToThem():
    "If a unit is on fire and it moves to a smoked forest tile, the tile will catch fire and the smoke will disappear."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g, effects={Effects.SMOKE}))
    g.board[(2, 1)].createUnitHere(Unit_Hornet(g))
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyFire()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit == None

def t_ShieldedUnitOnForestWontIgnightForest():
    "If a Shielded unit stands on a forest and takes damage, the forest will not ignite."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Hornet(g))
    g.board[(1, 1)].applyShield()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()  # no fire on tile
    assert g.board[(1, 1)].unit.effects == set()  # shield gone, but not on fire

def t_UnitSetOnFireThenShieldedNothingWeird():
    "a unit can be set on fire and then shielded, the fire stays."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    g.board[(1, 1)].applyShield()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}

def t_UnitFireAndShieldMovedToForestSetOnFire():
    "if a unit that is on fire and shielded moves to a forest tile, it is set on fire."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyFire()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(1, 1)].effects == set()
    g.board[(2, 1)].applyShield()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}

def t_IceRemovesFireFromUnitAndTile():
    "Ice puts out fire on unit and tile."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}

def t_ShieldBlocksIceFromFire():
    "What happens when a unit is set on fire, shielded, then frozen? Ice has no effect, unit remains shielded and on fire. Tile remains on fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    g.board[(1, 1)].applyShield()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}

def t_ShieldBlocksIce():
    "You can't be frozen when you have a shield"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyShield()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_FireBreaksIceWithShield():
    "If a unit is iced, shielded, then fired, the ice breaks, the tile catches fire, but the unit remains shielded and not on fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}
    g.board[(1, 1)].applyShield()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ICE, Effects.SHIELD}
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}

def t_AcidVatOnFireDoesntCreateFireAcidWater():
    "Test keepeffects by setting an acid vat on fire and then destroying it. The resulting acid water tile should not have fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Acid_Vat(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    g.board[(1, 1)].takeDamage(10)
    #print(g.board[(1, 1)])
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(1, 1)].unit == None

def t_AcidVatWithSmokeKeepsSmokeAfterKilled():
    "Test keepeffects by smoking an acid vat and then destroying it. The resulting tile should be acid water with smoke."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Acid_Vat(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applySmoke()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].takeDamage(10)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED, Effects.SMOKE}
    assert g.board[(1, 1)].unit == None

def t_AcidUnitAttackedOnSandLeavesAcidNoSmoke():
    "If a unit with acid stands on a sand tile and is attacked and killed, an acid pool is left on the tile along with smoke. The sand is removed."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}
    g.board[(1, 1)].takeDamage(10)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SMOKE}
    assert g.board[(1, 1)].unit == None
    assert g.board[(1, 1)].type == 'ground'

def t_AcidRemovesSand():
    "Acid that lands on sand converts it to a ground tile with acid."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].applyAcid()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None
    assert g.board[(1, 1)].type == 'ground'

def t_AcidRemovesForest():
    "Acid that lands on forest converts it to a ground tile with acid."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].applyAcid()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None
    assert g.board[(1, 1)].type == 'ground'

def t_AcidDoesNothingToLava():
  "Nothing happens when acid hits lava."
  g = Game()
  g.board[(1, 1)].replaceTile(Tile_Lava(g))
  assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
  g.board[(1, 1)].applyAcid()
  assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
  assert g.board[(1, 1)].unit == None
  assert g.board[(1, 1)].type == 'lava'

def t_FireErasesSandTile():
  "A sand tile being set on fire converts the sand tile to a ground tile on fire."
  g = Game()
  g.board[(1, 1)].replaceTile(Tile_Sand(g))
  assert g.board[(1, 1)].effects == set()
  g.board[(1, 1)].applyFire()
  assert g.board[(1, 1)].effects == {Effects.FIRE}
  assert g.board[(1, 1)].unit == None
  assert g.board[(1, 1)].type == 'ground'

def t_FireRemovesAcidPool():
  "If there's an acid pool on a tile, setting it on fire removes the acid pool."
  g = Game()
  assert g.board[(1, 1)].effects == set()
  g.board[(1, 1)].applyAcid()
  assert g.board[(1, 1)].effects == {Effects.ACID}
  g.board[(1, 1)].applyFire()
  assert g.board[(1, 1)].effects == {Effects.FIRE}
  assert g.board[(1, 1)].unit == None
  assert g.board[(1, 1)].type == 'ground'

def t_FireImmuneUnitDoesntCatchFire():
    "A unit with fire immunity doesn't catch fire, duh."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hornet(g, attributes={Attributes.IMMUNEFIRE}))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.IMMUNEFIRE, Attributes.FLYING}
    g.board[(1, 1)].applyFire()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE} # tile on fire
    assert g.board[(1, 1)].unit.effects == set() # unit is not

def t_MechCorpsePush():
    "Dead mechs are not stable and can be pushed around."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Mech_Corpse(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    g.board[(1, 1)].push(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.attributes == {Attributes.MASSIVE}

def t_MechCorpsePushIntoChasm():
    "Dead mechs disappear into chasms. They have the flying attribute ingame for some reason but are clearly not flying."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Mech_Corpse(g))
    g.board[(2, 1)].replaceTile( Tile_Chasm(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit ==  None
    g.board[(1, 1)].push(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit == None

def t_MechCorpseCantBeIced():
    "Mech corpses cannot be frozen."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Mech_Corpse(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()

def t_MechCorpseSpreadsFire():
    "Even though in the game it doesn't show mech corpses as having fire or acid, they do as evidenced by spreading of fire to forests and acid to water. Here we test fire."
    g = Game()
    g.board[(2, 1)].replaceTile( Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Mech_Corpse(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit == None
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit == None
    g.board[(1, 1)].push(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}

def t_MechCorpseSpreadsAcid():
    "Even though in the game it doesn't show mech corpses as having fire or acid, they do as evidenced by spreading of fire to forests and acid to water. Here we test acid"
    g = Game()
    g.board[(2, 1)].replaceTile( Tile_Water(g))
    g.board[(1, 1)].createUnitHere(Unit_Mech_Corpse(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert g.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit == None
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}
    assert g.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit == None
    g.board[(1, 1)].push(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == {Effects.SUBMERGED, Effects.ACID}
    assert g.board[(2, 1)].unit.effects == {Effects.ACID}

def t_MechCorpseInvulnerable():
    "Dead mechs can't be killed by damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Mech_Corpse(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    g.board[(1, 1)].takeDamage(100)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyAcid()
    g.board[(1, 1)].takeDamage(100)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}

def t_MechCorpseCantBeShielded():
    "Mech corpses cannot be shielded even though the game implies that it can be."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Mech_Corpse(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyShield()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.attributes == {Attributes.MASSIVE}
    assert g.board[(1, 1)].unit.effects == set()

def t_UnitWithAcidKilledOnSandThenSetOnFire():
    "A unit with acid is killed on a sand tile, tile now has smoke and acid and is no longer a sand tile. Setting it on fire gets rid of smoke and acid."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_Scarab(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}
    g.board[(1, 1)].takeDamage(10)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SMOKE}
    assert g.board[(1, 1)].unit == None
    assert g.board[(1, 1)].type == 'ground'
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit == None
    assert g.board[(1, 1)].type == 'ground'

def t_DamagedIceBecomesIceWhenFrozen():
    "If a damaged ice tile is hit with ice, it becomes an ice tile."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].type == 'ice'
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].type == 'ice_damaged'
    g.board[(1, 1)].applyIce()
    g.flushHurt()
    assert g.board[(1, 1)].type == 'ice'

def t_BrokenTeleporter():
    "Make sure an exception is raised if a unit moves onto a teleporter tile that doesn't have a companion."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Teleporter(g))
    g.board[(2, 1)].createUnitHere(Unit_Scarab(g))
    try:
        g.board[(2, 1)].moveUnit((1, 1))
    except MissingCompanionTile:
        pass
    else:
        assert False # The expected exception wasn't raised!

def t_WorkingTeleporter():
    "Make sure a unit can teleport back and fourth between 2 teleporters."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Teleporter(g, companion=(8, 8)))
    g.board[(8, 8)].replaceTile(Tile_Teleporter(g, companion=(1, 1)))
    g.board[(2, 1)].createUnitHere(Unit_Scarab(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(8, 8)].effects == set()
    assert g.board[(8, 8)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].moveUnit((1, 1))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 8)].effects == set()
    assert g.board[(2, 1)].unit == None
    assert g.board[(8, 8)].unit.effects == set() # unit is on far teleporter
    g.board[(8, 8)].moveUnit((7, 8)) # move it off teleporter
    assert g.board[(1, 1)].unit == None
    assert g.board[(8, 8)].unit == None
    assert g.board[(7, 8)].unit.effects == set() # unit is here
    g.board[(7, 8)].moveUnit((8, 8)) # move it back to far teleporter
    g.flushHurt()
    assert g.board[(1, 1)].unit.effects == set() # unit is here
    assert g.board[(8, 8)].unit == None
    assert g.board[(7, 8)].unit == None

def t_TeleporterSwaps2Units():
    "If a unit is on a teleporter when another unit moves to its companion, the units will swap places."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Teleporter(g, companion=(8, 8)))
    g.board[(8, 8)].replaceTile(Tile_Teleporter(g, companion=(1, 1)))
    g.board[(2, 1)].createUnitHere(Unit_Scarab(g)) # put scarab next to near teleporter
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(8, 8)].effects == set()
    assert g.board[(8, 8)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].moveUnit((1, 1)) # move scarab to near teleporter
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 8)].effects == set()
    assert g.board[(2, 1)].unit == None
    assert g.board[(8, 8)].unit.type == 'scarab' # unit is on far teleporter
    g.board[(1, 1)].createUnitHere(Unit_Hornet_Leader(g)) # they instantly swap
    g.flushHurt()
    assert g.board[(1, 1)].unit.type == 'scarab' # is hornetleader
    assert g.board[(8, 8)].unit.type == 'hornetleader'

def t_TeleporterWithFire():
    "A unit that is pushed onto an on fire teleporter also catches fire and is then teleported."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Teleporter(g, effects={Effects.FIRE}, companion=(8, 8)))
    g.board[(8, 8)].replaceTile(Tile_Teleporter(g, companion=(1, 1)))
    g.board[(2, 1)].createUnitHere(Unit_Scarab(g))
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit == None
    assert g.board[(8, 8)].effects == set()
    assert g.board[(8, 8)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(8, 8)].effects == set()
    assert g.board[(2, 1)].unit == None
    assert g.board[(8, 8)].unit.effects == {Effects.FIRE} # unit is on far teleporter

def t_TeleporterWithAcid():
    "If there's an acid pool on a teleporter, it's picked up by the unit that moves there and then the unit is teleported."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Teleporter(g, effects={Effects.ACID}, companion=(8, 8)))
    g.board[(8, 8)].replaceTile(Tile_Teleporter(g, companion=(1, 1)))
    g.board[(2, 1)].createUnitHere(Unit_Scarab(g))
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None
    assert g.board[(8, 8)].effects == set()
    assert g.board[(8, 8)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 8)].effects == set()
    assert g.board[(2, 1)].unit == None
    assert g.board[(8, 8)].unit.effects == {Effects.ACID} # unit is on far teleporter

def t_DamDies():
    "The Dam is a special 2-tile unit. In this program, it's treated as 2 separate units that replicate actions to each other. In this test, we kill one and make sure they both die and flood the map."
    g = Game()
    g.board[(8, 3)].replaceTile(Tile_Water(g))
    g.board[(8, 4)].replaceTile(Tile_Water(g))
    g.board[(8, 3)].createUnitHere(Unit_Dam(g))
    g.board[(8, 4)].createUnitHere(Unit_Dam(g))
    assert g.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(8, 4)].effects == {Effects.SUBMERGED}
    assert g.board[(7, 3)].effects == set() # the tiles next to the dam are normal
    assert g.board[(7, 4)].effects == set()
    g.board[(8, 3)].takeDamage(1)
    assert g.board[(8, 3)].unit.currenthp == 1
    assert g.board[(8, 4)].unit.currenthp == 1
    g.board[(8, 4)].takeDamage(1)
    g.flushHurt()
    assert g.board[(8, 3)].unit.type == 'volcano'
    assert g.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 7):
            assert g.board[(x, y)].type == 'water'

def t_DamDiesWithAcidUnits():
    "In this test, we kill one and make sure that a unit with acid dies and leaves acid in the new water. Also a flying unit will survive the flood."
    g = Game()
    g.board[(8, 3)].replaceTile(Tile_Water(g))
    g.board[(8, 4)].replaceTile(Tile_Water(g))
    g.board[(8, 3)].createUnitHere(Unit_Dam(g))
    g.board[(8, 4)].createUnitHere(Unit_Dam(g))
    g.board[(7, 3)].createUnitHere(Unit_Blobber(g, effects={Effects.ACID}))
    g.board[(7, 4)].createUnitHere(Unit_Hornet(g, effects={Effects.ACID}))
    assert g.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(8, 4)].effects == {Effects.SUBMERGED}
    assert g.board[(7, 3)].effects == set() # the tiles next to the dam are normal
    assert g.board[(7, 4)].effects == set()
    assert g.board[(7, 3)].unit.effects == {Effects.ACID}  # the units next to the dam have acid
    assert g.board[(7, 4)].unit.effects == {Effects.ACID}
    g.board[(8, 3)].takeDamage(1)
    assert g.board[(8, 3)].unit.currenthp == 1
    assert g.board[(8, 4)].unit.currenthp == 1
    g.board[(8, 4)].takeDamage(1)
    assert g.board[(8, 3)].unit.type == 'volcano'
    assert g.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 8):
            assert g.board[(x, y)].type == 'water'
    g.flushHurt()
    assert g.board[(7, 3)].unit == None # the blobber died
    assert g.board[(7, 3)].effects == {Effects.ACID, Effects.SUBMERGED} # the blobber left acid in the water
    assert g.board[(7, 4)].unit.type == 'hornet' # the hornet survived
    assert g.board[(7, 4)].effects == {Effects.SUBMERGED}  # the acid is still on the hornet and not the water

def t_DamDiesWithAcidOnGround():
    "In this test, we kill one and make sure that a ground tile with acid leaves acid in the new water tile."
    g = Game()
    g.board[(8, 3)].replaceTile(Tile_Water(g))
    g.board[(8, 4)].replaceTile(Tile_Water(g))
    g.board[(8, 3)].createUnitHere(Unit_Dam(g))
    g.board[(8, 4)].createUnitHere(Unit_Dam(g))
    g.board[(7, 3)].applyAcid()
    assert g.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(8, 4)].effects == {Effects.SUBMERGED}
    assert g.board[(7, 3)].effects == {Effects.ACID} # the tile next to the dam has acid
    assert g.board[(7, 4)].effects == set()
    g.board[(8, 3)].takeDamage(1)
    assert g.board[(8, 3)].unit.currenthp == 1
    assert g.board[(8, 4)].unit.currenthp == 1
    g.board[(8, 4)].takeDamage(1)
    assert g.board[(8, 3)].unit.type == 'volcano'
    assert g.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 8):
            assert g.board[(x, y)].type == 'water'
    g.flushHurt()
    assert g.board[(7, 3)].effects == {Effects.ACID, Effects.SUBMERGED} # the acid on the ground left acid in the water
    assert g.board[(7, 4)].effects == {Effects.SUBMERGED} # this tile never got acid

def t_ShieldedDamHitWithAcidGetsAcid():
    "If the dam is shielded and then hit with acid, it's immediately inflicted with acid."
    g = Game()
    g.board[(8, 3)].replaceTile(Tile_Water(g))
    g.board[(8, 4)].replaceTile(Tile_Water(g))
    g.board[(8, 3)].createUnitHere(Unit_Dam(g))
    g.board[(8, 4)].createUnitHere(Unit_Dam(g))
    g.board[(8, 4)].applyShield()
    assert g.board[(8, 3)].unit.effects == {Effects.SHIELD}
    assert g.board[(8, 4)].unit.effects == {Effects.SHIELD}
    g.board[(8, 3)].applyAcid()
    g.flushHurt()
    assert g.board[(8, 3)].unit.effects == {Effects.SHIELD, Effects.ACID}
    assert g.board[(8, 4)].unit.effects == {Effects.SHIELD, Effects.ACID}

def t_ShieldedUnitDoesntGetAcidFromGround():
    "a shielded unit does not pick up acid from the ground."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g))
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyShield()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD}
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID} # still acid on the ground
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD} # still shielded only
    assert g.board[(2, 1)].effects == set() # nothing on that tile
    assert g.board[(2, 1)].unit == None  # nothing on that tile

def t_ShieldedUnitRepairsDoesntRemoveAcidFromGround():
    "if a shielded unit repairs on an acid pool, the acid pool remains."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Aegis_Mech(g))
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyShield()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD}
    g.board[(2, 1)].moveUnit((1, 1))
    assert g.board[(1, 1)].effects == {Effects.ACID} # still acid on the ground
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD} # still shielded only
    assert g.board[(2, 1)].effects == set() # nothing on that tile
    assert g.board[(2, 1)].unit == None  # nothing on that tile
    g.board[(1, 1)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}  # still acid on the ground
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}  # still shielded only
    assert g.board[(2, 1)].effects == set()  # nothing on that tile
    assert g.board[(2, 1)].unit == None  # nothing on that tile

def t_ShieldedUnitGetsAcidFromWater():
    "if a non-flying shielded unit goes into acid water, it gets acid!"
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion_Leader(g))
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].applyShield()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD}
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID, Effects.SUBMERGED} # still acid in the water
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD, Effects.ACID} # Shielded and acid!
    assert g.board[(2, 1)].effects == set() # nothing on that tile
    assert g.board[(2, 1)].unit == None  # nothing on that tile

def t_MechRepairsRemovesBadEffectsTileAndUnit():
    "A mech and its forest tile are set on fire and then hit with acid and repaired."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.currenthp == 2
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    assert g.board[(1, 1)].unit.currenthp == 2
    g.board[(1, 1)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3

def t_MechRepairsRemovesIceFromUnit():
    "A mech and its water tile are frozen and then hit with acid and repaired."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].takeDamage(1)
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].type == 'ice'
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}
    assert g.board[(1, 1)].unit.currenthp == 2
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ICE, Effects.ACID}
    assert g.board[(1, 1)].unit.currenthp == 2
    g.board[(1, 1)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3

def t_BurrowerWithAcidLeavesItWhenKilled():
    "Do burrowers leave acid when they die? Yes!"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Burrower(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}
    g.board[(1, 1)].takeDamage(2)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None

def t_LavaDoesntRemoveAcidFromUnit():
    "Does lava remove acid from a unit like water does? NO, you still have acid."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Lava(g))
    g.board[(1, 2)].createUnitHere(Unit_Laser_Mech(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert g.board[(1, 2)].unit.effects == set()
    g.board[(1, 2)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert g.board[(1, 2)].unit.effects == {Effects.ACID}
    g.board[(1, 2)].push(Direction.DOWN)
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    g.board[(1, 1)].push(Direction.UP)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert g.board[(1, 2)].unit.effects == {Effects.FIRE, Effects.ACID}

def t_UnitWithAcidDiesInLava():
    "Lava doesn't get acid from an acid unit dying on it."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Lava(g))
    g.board[(1, 2)].createUnitHere(Unit_Acid_Scorpion(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert g.board[(1, 2)].unit.effects == set()
    g.board[(1, 2)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert g.board[(1, 2)].unit.effects == {Effects.ACID}
    g.board[(1, 2)].push(Direction.DOWN)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED, Effects.FIRE}
    assert g.board[(1, 1)].unit == None

def t_MechCorpseIsRepairedBackToLife():
    "a mech is killed, becomes a mech corpse, and then is repaired to become the alive mech again."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Judo_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].takeDamage(4) # 3 hp, but it has armor :)
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.type == 'mechcorpse'
    g.board[(1, 1)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.type == 'judo'
    assert g.board[(1, 1)].unit.currenthp == 1

def t_MechDiesAndRevivedOnTeleporter():
    "a mech dies on a teleporter and is then revived. The act of reviving the unit should teleport it through again."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Teleporter(g, companion=(8, 8)))
    g.board[(8, 8)].replaceTile(Tile_Teleporter(g, companion=(1, 1)))
    g.board[(2, 1)].createUnitHere(Unit_Flame_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(8, 8)].effects == set()
    assert g.board[(8, 8)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].moveUnit((1, 1))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 8)].effects == set()
    assert g.board[(2, 1)].unit == None
    assert g.board[(8, 8)].unit.effects == set() # unit is on far teleporter
    g.board[(8, 8)].takeDamage(3)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 8)].effects == set()
    assert g.board[(8, 8)].unit.effects == set()  # unit is on far teleporter
    assert g.board[(8, 8)].unit.type == 'mechcorpse'
    g.board[(8, 8)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 8)].effects == set()
    assert g.board[(8, 8)].unit == None  # no unit on far teleporter
    assert g.board[(1, 1)].unit.type == 'flame'  # unit is back on the near teleporter
    assert g.board[(1, 1)].unit.currenthp == 1 # the repair worked properly

def t_MechCorpsesDontGoThroughTelePorter():
    "if a mech dies and is pushed to a teleporter tile, it does not teleport. Corpses don't teleport at all, even if they die and then are pushed onto a teleporter."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Teleporter(g, companion=(8, 8)))
    g.board[(8, 8)].replaceTile(Tile_Teleporter(g, companion=(1, 1)))
    g.board[(2, 1)].createUnitHere(Unit_Leap_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(8, 8)].effects == set()
    assert g.board[(8, 8)].unit == None
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].takeDamage(3)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 8)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.type == 'mechcorpse'
    g.board[(2, 1)].moveUnit((1, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 8)].effects == set()
    assert g.board[(2, 1)].unit == None
    assert g.board[(8, 8)].unit == None  # unit is on near teleporter
    assert g.board[(1, 1)].unit.type == 'mechcorpse'

def t_RevivedMechCorpsesKeepAcidButNotFire():
    "When a mech corpse is repaired back to life, it keeps acid if it had it before. If the mech died with fire, it is revived without fire (assuming it's not on a fire tile. The revived unit will be on fire if revived on a fire tile)."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyAcid()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    g.board[(1, 1)].takeDamage(2)
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.type == 'mechcorpse'
    g.board[(1, 1)].moveUnit((2, 1))
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.type == 'mechcorpse'
    g.board[(2, 1)].unit.repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.ACID}
    assert g.board[(2, 1)].unit.type == 'cannon'

def t_ReviveMechCorpseKeepsAcidGetsFireFromTile():
    "When a mech corpse is repaired back to life, it keeps acid if it had it before. In this test we get fire from the tile we were revived on."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyAcid()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    g.board[(1, 1)].takeDamage(1)
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.type == 'mechcorpse'
    g.board[(1, 1)].unit.repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.ACID, Effects.FIRE}
    assert g.board[(1, 1)].unit.type == 'jet'

def t_IceStormEnvironmental():
    "Test an ice storm."
    g = Game(environeffect=Environ_IceStorm({(x,y) for x in range(1, 5) for y in range(1, 5)}))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g))
    g.board[(2, 1)].replaceTile(Tile_Water(g))
    g.board[(3, 1)].applyFire()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    g.environeffect.run()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].type == 'ice'
    assert g.board[(3, 1)].effects == set()

def t_AirStrikeEnvironmental():
    "test an airstrike"
    g = Game(environeffect=Environ_AirStrike({(1, 2), (2, 3), (2, 2), (2, 1), (3, 2)}))
    g.board[(1, 2)].createUnitHere(Unit_Charge_Mech(g))
    g.board[(2, 3)].replaceTile(Tile_Water(g))
    g.board[(2, 2)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 2)].replaceTile(Tile_Sand(g))
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(2, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 2)].effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 2)].effects == set()
    g.environeffect.run()
    g.flushHurt()
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(1, 2)].unit.type == 'mechcorpse'
    assert g.board[(2, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 2)].effects == {Effects.SMOKE}

def t_AirStrikeEnvironmentalAcidForest():
    "if a vek with acid is on a forest and is then hit with an airstrike, the tile is damaged and catches fire, then the unit dies leaving its acid and removing the fire and forest."
    g = Game(environeffect=Environ_AirStrike({(1, 1)}))
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Scorpion(g, effects={Effects.ACID}))
    assert g.board[(1, 1)].effects == set()
    g.environeffect.run()
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.ACID}
    assert g.board[(1, 1)].unit == None
    assert g.board[(1, 1)].type == 'ground'

def t_LightningEnvironmental():
    "lol literally the same thing as AirStrike"
    g = Game(environeffect=Environ_Lightning({(1, 2), (2, 3), (2, 2), (2, 1), (3, 2)}))
    g.board[(1, 2)].createUnitHere(Unit_Charge_Mech(g))
    g.board[(2, 3)].replaceTile(Tile_Water(g))
    g.board[(2, 2)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 2)].replaceTile(Tile_Sand(g))
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(2, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 2)].effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 2)].effects == set()
    g.environeffect.run()
    g.flushHurt()
    assert g.board[(1, 2)].effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(1, 2)].unit.type == 'mechcorpse'
    assert g.board[(2, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 2)].effects == {Effects.SMOKE}

def t_TsunamiEnvironmental():
    "test a tsunami"
    g = Game(environeffect=Environ_Tsunami(((1, 1), (2, 1), (3, 1))))
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Blood_Psion(g))
    g.board[(3, 1)].applySmoke()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    g.environeffect.run()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit == None # he drowned
    assert g.board[(3, 1)].effects == {Effects.SUBMERGED, Effects.SMOKE} # smoke remains
    assert g.board[(3, 1)].unit.effects == set() # so does this flying unit
    g.board[(1, 1)].applyIce() # make sure these new tiles are tied to this Game instance:
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].type == 'ice'

def t_CataclysmEnvironmental():
    "test a cataclysm"
    g = Game(environeffect=Environ_Cataclysm(((1, 1), (2, 1), (3, 1))))
    g.board[(1, 1)].createUnitHere(Unit_Mirror_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Acid_Scorpion(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_Blast_Psion(g))
    g.board[(3, 1)].applySmoke()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    g.environeffect.run()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None # mech died, so did the corpse
    assert g.board[(2, 1)].effects == set() # no more fire since the ground is gone lol
    assert g.board[(2, 1)].unit == None # he also died
    assert g.board[(3, 1)].effects == {Effects.SMOKE} # smoke remains
    assert g.board[(3, 1)].unit.effects == set() # so does this flying unit
    g.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this Game instance:
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].type == 'chasm'

def t_FallingRockEnvironmental():
    "test falling rocks from the volcano level."
    g = Game(environeffect=Environ_FallingRock(((1, 1), (2, 1), (3, 1))))
    g.board[(1, 1)].createUnitHere(Unit_Unstable_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_Psion_Tyrant(g))
    g.board[(3, 1)].applySmoke()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    g.environeffect.run()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.type == 'mechcorpse' # mech died, the corpse remains
    assert g.board[(2, 1)].effects == {Effects.FIRE} # fire remains after rocks fall
    assert g.board[(2, 1)].unit == None # he also died
    assert g.board[(3, 1)].effects == {Effects.SMOKE} # smoke remains
    assert g.board[(3, 1)].unit == None # flying unit died
    g.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this Game instance:
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].type == 'ground'

def t_TentaclesEnvironmental():
    "test the tentacles."
    g = Game(environeffect=Environ_Tentacles(((1, 1), (2, 1), (3, 1))))
    g.board[(1, 1)].createUnitHere(Unit_Artillery_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_Hornet(g))
    g.board[(3, 1)].applySmoke()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    g.environeffect.run()
    assert g.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.type == 'mechcorpse' # mech died, the corpse remains
    assert g.board[(2, 1)].effects == {Effects.FIRE, Effects.SUBMERGED} # fire doubly so
    assert g.board[(2, 1)].unit == None # he also died
    assert g.board[(3, 1)].effects == {Effects.SMOKE, Effects.FIRE, Effects.SUBMERGED} # smoke remains
    assert g.board[(3, 1)].unit == None # flying unit died
    g.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this Game instance:
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE, Effects.FIRE, Effects.SUBMERGED}
    assert g.board[(1, 1)].type == 'lava'

def t_LavaFlowEnvironmental():
    "test the lava flow environmental"
    g = Game(environeffect=Environ_LavaFlow(((1, 1), (2, 1), (3, 1))))
    g.board[(1, 1)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_Acid_Hornet(g))
    g.board[(3, 1)].applySmoke()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    g.environeffect.run()
    assert g.board[(1, 1)].effects == {Effects.FIRE, Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE} # mech survived but is now in lava
    assert g.board[(2, 1)].effects == {Effects.FIRE, Effects.SUBMERGED} # fire doubly so
    assert g.board[(2, 1)].unit == None # he died
    assert g.board[(3, 1)].effects == {Effects.SMOKE, Effects.FIRE, Effects.SUBMERGED} # smoke remains
    assert g.board[(3, 1)].unit.effects == set() # flying unit survived and did not catch on fire
    g.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this Game instance:
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE, Effects.FIRE, Effects.SUBMERGED}
    assert g.board[(1, 1)].type == 'lava'

def t_VolcanicProjectileEnvironmental():
    "test volcanic projectile"
    g = Game(environeffect=Environ_VolcanicProjectile(((1, 1), (2, 1), (3, 1))))
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Firefly(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_Hornet_Leader(g))
    g.board[(3, 1)].applySmoke()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    g.environeffect.run()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.type == 'mechcorpse' # mech died
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit == None # he died
    assert g.board[(3, 1)].effects == {Effects.FIRE} # smoke removed by fire
    assert g.board[(3, 1)].unit == None # flying unit died
    g.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this Game instance:
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].type == 'ground'

def t_VekEmergeEnvironmental():
    "test vek emerging environmental"
    g = Game(vekemerge=Environ_VekEmerge([(1, 1), (2, 1), (3, 1), (4, 1)]))
    g.board[(1, 1)].createUnitHere(Unit_Siege_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Leaper(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_Scorpion_Leader(g))
    g.board[(3, 1)].applySmoke()
    g.board[(4, 1)].createUnitHere(Unit_Mech_Corpse(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    g.vekemerge.run()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.currenthp == 1 # mech took bump damage
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit == None # he died from the bump
    assert g.board[(3, 1)].effects == {Effects.SMOKE} # smoke remains
    assert g.board[(3, 1)].unit.currenthp == 6
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.currenthp == 1 # corpse didn't take damage
    assert g.board[(4, 1)].unit.type == 'mechcorpse' # and is a corpse
    g.board[(1, 1)].applySmoke() # make sure these new tiles are tied to this Game instance:
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 1)].type == 'ground'

def t_TsunamiEnvironmentalReplaceTile():
    "make sure that when Tsunami replaces tiles with water, they are in fact different tile objects and not the same one."
    g = Game(environeffect=Environ_Tsunami({(1, 1), (2, 1), (3, 1)}))
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Blood_Psion(g))
    g.board[(3, 1)].applySmoke()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    g.environeffect.run()
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == {Effects.SUBMERGED}
    assert g.board[(2, 1)].unit == None  # he drowned
    assert g.board[(3, 1)].effects == {Effects.SUBMERGED, Effects.SMOKE}  # smoke remains
    assert g.board[(3, 1)].unit.effects == set()  # so does this flying unit
    g.board[(1, 1)].applyIce()
    g.board[(2, 1)].applyAcid()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # one tile is frozen, one has acid, the last has smoke
    assert g.board[(1, 1)].type == 'ice'
    assert g.board[(2, 1)].effects == {Effects.ACID, Effects.SUBMERGED}
    assert g.board[(2, 1)].type == 'water'
    assert g.board[(3, 1)].effects == {Effects.SUBMERGED, Effects.SMOKE}
    assert g.board[(3, 1)].type == 'water'

def t_ConveyorBeltsEnviron():
    "make sure that converyor belts works."
    g = Game(environeffect=Environ_ConveyorBelts({(1, x): Direction.UP for x in range(1, 9)})) # all tiles against the left border pushing up
    g.board[(1, 1)].createUnitHere(Unit_Meteor_Mech(g))
    g.board[(1, 2)].createUnitHere(Unit_Beetle(g))
    g.board[(1, 7)].createUnitHere(Unit_Spider_Leader(g))
    g.board[(1, 8)].createUnitHere(Unit_Blood_Psion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(1, 2)].unit.currenthp == 4
    assert g.board[(1, 7)].unit.currenthp == 6
    assert g.board[(1, 8)].unit.currenthp == 2
    g.environeffect.run()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # meteor got pushed off this tile
    assert g.board[(1, 2)].unit.currenthp == 3 # meteor still has 3 hp
    assert g.board[(1, 3)].unit.currenthp == 4 # beetle took no damage as well
    assert g.board[(1, 7)].unit.currenthp == 5 # spider leader took a bump when he was pushed into the blood psion, so he didn't move
    assert g.board[(1, 8)].unit.currenthp == 1 # blood psion tried to get pushed off the board so he stayed put and got bumped

def t_WeaponTitanFistFirst():
    "My very first weapon test. Have a mech punch another!"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist()))
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.currenthp == 3
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit == None # judo was pushed off this square
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.currenthp == 2 # he only lost 1 health because of armor

def t_WeaponTitanFistChargeSecond():
    "My very second weapon test. Have a mech dash punch another!"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power1=True)))
    g.board[(6, 1)].createUnitHere(Unit_Judo_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(6, 1)].effects == set()
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(6, 1)].unit.currenthp == 3
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None # Combat dashed off of this tile
    assert g.board[(5, 1)].unit.effects == set() # and he's now here
    assert g.board[(5, 1)].unit.currenthp == 3
    assert g.board[(6, 1)].unit == None # judo was pushed off this square
    assert g.board[(7, 1)].effects == set() # and he's here now
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(7, 1)].unit.currenthp == 2 # he only lost 1 health because of armor

def t_WeaponTitanFistChargeToEdge():
    "When you charge to the edge of the map without hitting a unit, you do NOT attack the tile at the edge like a projectile does."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power1=True)))
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(8, 1)].effects == set()
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].type == 'forest'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # he's not here anymore
    assert g.board[(8, 1)].effects == set() # still no fire
    assert g.board[(8, 1)].unit.effects == set() # no change
    assert g.board[(8, 1)].unit.currenthp == 3 # no change
    assert g.board[(8, 1)].type == 'forest'

def t_WeaponTitanFistIceOnIce():
    "if you punch a frozen unit on an ice tile, the ice tile isn't damaged."
    g = Game()
    g.board[(2, 1)].replaceTile(Tile_Ice(g))
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist()))
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, effects={Effects.ICE}))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}
    assert g.board[(2, 1)].unit.currenthp == 3
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit == None # judo was pushed off this square
    assert g.board[(2, 1)].type == 'ice' # tile wasn't damaged
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.currenthp == 3 # he only lost 0 health because of ice

def t_HurtAndPushedVekOnFireSetsForestOnFire():
    "This is testing the concept of the vek corpse. A vek is lit on fire, and then punched for 4 damage so it's killed, but it's fake corpse is pushed to a forest tile and sets it on fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g, effects={Effects.FIRE}))
    g.board[(3, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'forest'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set() # still no effects here
    assert g.board[(2, 1)].unit == None # firefly was pushed off this tile
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # The firefly died after spreading fire here. We did a strong 4 damage punch
    assert g.board[(3, 1)].type == 'forest' # still a forest? lol

def t_HurtAndPushedMechOnFireDoesNotSetForestOnFire():
    "A mech is lit on fire, and then punched for 4 damage so it's killed, but its mech corpse is not on fire like the mech was! the corpse is pushed to a forest tile and does NOT set it on fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Swap_Mech(g, effects={Effects.FIRE}))
    g.board[(3, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.currenthp == 2
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'forest'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set() # still no effects here
    assert g.board[(2, 1)].unit == None # swapper was pushed off this tile
    assert g.board[(3, 1)].effects == set() # forest is not on fire
    assert g.board[(3, 1)].unit.effects == set()  # corpse is not on fire
    assert g.board[(3, 1)].unit.type == 'mechcorpse' # The swapper died after spreading fire here. We did a strong 4 damage punch
    assert g.board[(3, 1)].type == 'forest' # still a forest? lol

def t_HurtAndPushedVekRemovesMine():
    "This is also testing the concept of the vek corpse. A vek is punched for 4 damage so it's killed, but its fake corpse is pushed to a tile with a mine. The mine trips and then the unit and mine are gone."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g))
    g.board[(3, 1)].effects.add(Effects.MINE)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].effects == {Effects.MINE}
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'ground'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set() # still no effects here
    assert g.board[(2, 1)].unit == None # firefly was pushed off this tile
    assert g.board[(3, 1)].effects == set() # mine is gone
    assert g.board[(3, 1)].unit == None # The firefly died after we did a strong 4 damage punch
    assert g.board[(3, 1)].type == 'ground' # still a forest? lol

def t_HurtAndPushedVekRemovesFreezeMine():
    "This is also testing the concept of the vek corpse. A vek is punched for 4 damage so it's killed, but it's fake corpse is pushed to a tile with a freeze mine. The mine trips and then the unit and mine are gone."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g))
    g.board[(3, 1)].effects.add(Effects.FREEZEMINE)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].effects == {Effects.FREEZEMINE}
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'ground'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == set() # still no effects here
    assert g.board[(2, 1)].unit == None # firefly was pushed off this tile
    assert g.board[(3, 1)].effects == set() # mine is gone
    assert g.board[(3, 1)].unit == None # The firefly died after we did a strong 4 damage punch
    assert g.board[(3, 1)].type == 'ground' # still a forest? lol

def t_MechMovesToMine():
    "Make sure mines work"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power2=True)))
    g.board[(2, 1)].effects.add(Effects.MINE)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == {Effects.MINE}
    assert g.board[(2, 1)].unit == None
    g.board[(1, 1)].moveUnit((2, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == set() # mine tripped
    assert g.board[(2, 1)].unit.type == 'mechcorpse' # ol' punchbot died

def t_MechMovesToFreezeMine():
    "Make sure freezemines work"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power2=True)))
    g.board[(2, 1)].effects.add(Effects.FREEZEMINE)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].effects == {Effects.FREEZEMINE}
    assert g.board[(2, 1)].unit == None
    g.board[(1, 1)].moveUnit((2, 1))
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].effects == set() # mine tripped
    assert g.board[(2, 1)].unit.type == 'combat' # ol' punchbot survived
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}  # ol' punchbot survived

def t_WeaponElectricWhipLowPower():
    "Shoot the electric whip without building chain or extra damage powered and make sure it goes through units it should and not through units it shouldn't."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Lightning_Mech(g, weapon1=Weapon_ElectricWhip()))
    for x in range(2, 7): # spider bosses on x tiles 2-6
        g.board[(x, 1)].createUnitHere(Unit_Spider_Leader(g))
    g.board[(7, 1)].createUnitHere(Unit_Mountain(g)) # a mountain to block it
    g.board[(8, 1)].createUnitHere(Unit_Spider_Leader(g)) # and a spider boss on the other side which should stay safe
    for y in range(2, 7):
        g.board[(3, y)].createUnitHere(Unit_Spider_Leader(g)) # start branching vertically
    g.board[(3, 7)].createUnitHere(Unit_Building(g))  # a building to block it
    g.board[(3, 8)].createUnitHere(Unit_Spider_Leader(g)) # and another spider boss on the other side which should also stay safe
    assert g.board[(1, 1)].unit.currenthp == 3 # lightning mech
    assert g.board[(2, 1)].unit.currenthp == 6 # spider bosses
    assert g.board[(3, 1)].unit.currenthp == 6
    assert g.board[(4, 1)].unit.currenthp == 6
    assert g.board[(5, 1)].unit.currenthp == 6
    assert g.board[(6, 1)].unit.currenthp == 6
    assert g.board[(3, 2)].unit.currenthp == 6
    assert g.board[(3, 3)].unit.currenthp == 6
    assert g.board[(3, 4)].unit.currenthp == 6
    assert g.board[(3, 5)].unit.currenthp == 6
    assert g.board[(3, 6)].unit.currenthp == 6
    assert g.board[(7, 1)].unit.type == 'mountain'
    assert g.board[(3, 7)].unit.type == 'building'
    assert g.board[(8, 1)].unit.currenthp == 6 # safe spider 1
    assert g.board[(3, 8)].unit.currenthp == 6  # safe spider 2
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # lightning mech untouched
    assert g.board[(2, 1)].unit.currenthp == 4  # spider bosses lose 2 hp
    assert g.board[(3, 1)].unit.currenthp == 4
    assert g.board[(4, 1)].unit.currenthp == 4
    assert g.board[(5, 1)].unit.currenthp == 4
    assert g.board[(6, 1)].unit.currenthp == 4
    assert g.board[(3, 2)].unit.currenthp == 4
    assert g.board[(3, 3)].unit.currenthp == 4
    assert g.board[(3, 4)].unit.currenthp == 4
    assert g.board[(3, 5)].unit.currenthp == 4
    assert g.board[(3, 6)].unit.currenthp == 4
    assert g.board[(7, 1)].unit.type == 'mountain'
    assert g.board[(3, 7)].unit.type == 'building'
    assert g.board[(8, 1)].unit.currenthp == 6  # safe spider 1
    assert g.board[(3, 8)].unit.currenthp == 6  # safe spider 2

def t_WeaponElectricWhipBuildingChainHighPower():
    "Shoot the electric whip with extra damage powered and make sure it goes through units it should and not through units it shouldn't."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Lightning_Mech(g, weapon1=Weapon_ElectricWhip(power1=True)))
    for x in range(2, 7): # spider bosses on x tiles 2-6
        g.board[(x, 1)].createUnitHere(Unit_Spider_Leader(g))
    g.board[(7, 1)].createUnitHere(Unit_Mountain(g)) # a mountain to block it
    g.board[(8, 1)].createUnitHere(Unit_Spider_Leader(g)) # and a spider boss on the other side which should stay safe
    for y in range(2, 7):
        g.board[(3, y)].createUnitHere(Unit_Spider_Leader(g)) # start branching vertically
    g.board[(3, 7)].createUnitHere(Unit_Building(g))  # a building to block it
    g.board[(3, 8)].createUnitHere(Unit_Spider_Leader(g)) # and another spider boss on the other side which should also stay safe
    assert g.board[(1, 1)].unit.currenthp == 3 # lightning mech
    assert g.board[(2, 1)].unit.currenthp == 6 # spider bosses
    assert g.board[(3, 1)].unit.currenthp == 6
    assert g.board[(4, 1)].unit.currenthp == 6
    assert g.board[(5, 1)].unit.currenthp == 6
    assert g.board[(6, 1)].unit.currenthp == 6
    assert g.board[(3, 2)].unit.currenthp == 6
    assert g.board[(3, 3)].unit.currenthp == 6
    assert g.board[(3, 4)].unit.currenthp == 6
    assert g.board[(3, 5)].unit.currenthp == 6
    assert g.board[(3, 6)].unit.currenthp == 6
    assert g.board[(7, 1)].unit.type == 'mountain'
    assert g.board[(3, 7)].unit.type == 'building'
    assert g.board[(8, 1)].unit.currenthp == 6 # safe spider 1
    assert g.board[(3, 8)].unit.currenthp == 6  # building chain  spider 2
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # lightning mech untouched
    assert g.board[(2, 1)].unit.currenthp == 4  # spider bosses lose 2 hp
    assert g.board[(3, 1)].unit.currenthp == 4
    assert g.board[(4, 1)].unit.currenthp == 4
    assert g.board[(5, 1)].unit.currenthp == 4
    assert g.board[(6, 1)].unit.currenthp == 4
    assert g.board[(3, 2)].unit.currenthp == 4
    assert g.board[(3, 3)].unit.currenthp == 4
    assert g.board[(3, 4)].unit.currenthp == 4
    assert g.board[(3, 5)].unit.currenthp == 4
    assert g.board[(3, 6)].unit.currenthp == 4
    assert g.board[(7, 1)].unit.type == 'mountain'
    assert g.board[(3, 7)].unit.type == 'building'
    assert g.board[(8, 1)].unit.currenthp == 6  # safe spider 1
    assert g.board[(3, 8)].unit.currenthp == 4  # building chain spider 2 took damage

def t_WeaponElectricWhipDoesntChainInCicle():
    "Shoot the electric whip with the power2 extra damage and make sure we don't loop through the weaponwielder"
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Lightning_Mech(g, weapon1=Weapon_ElectricWhip(power2=True)))
    g.board[(1, 1)].createUnitHere(Unit_Spider_Leader(g)) # shocked spider
    g.board[(2, 1)].createUnitHere(Unit_Spider_Leader(g))  # shocked spider
    g.board[(1, 2)].createUnitHere(Unit_Spider_Leader(g))  # shocked spider
    g.board[(2, 3)].createUnitHere(Unit_Spider_Leader(g))  # undamaged spider
    assert g.board[(2, 2)].unit.currenthp == 3 # lightning mech
    assert g.board[(1, 1)].unit.currenthp == 6 # spider bosses
    assert g.board[(2, 1)].unit.currenthp == 6
    assert g.board[(1, 2)].unit.currenthp == 6
    assert g.board[(2, 3)].unit.currenthp == 6
    g.board[(2, 2)].unit.weapon1.shoot(Direction.DOWN)
    g.flushHurt()
    assert g.board[(2, 2)].unit.currenthp == 3  # lightning mech
    assert g.board[(1, 1)].unit.currenthp == 3  # spider bosses took 3 damage
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(1, 2)].unit.currenthp == 3
    assert g.board[(2, 3)].unit.currenthp == 6 # this one didn't get hit because we can't chain back through the wielder

def t_WeaponArtemisArtilleryDefault():
    "Do the default power Artillery demo from the game when you mouseover the weapon."
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery()))
    g.board[(3, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(5, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g)) # this one is actually against the wall and cannot be pushed
    g.board[(4, 3)].createUnitHere(Unit_Alpha_Scorpion(g)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert g.board[(2, 2)].unit.currenthp == 2
    assert g.board[(3, 2)].unit.currenthp == 1
    assert g.board[(4, 2)].unit.currenthp == 5
    assert g.board[(5, 2)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 3)].unit.currenthp == 5
    gs = g.board[(2, 2)].unit.weapon1.genShots()
    for i in range(6):
        shot = next(gs) # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 2)].unit.weapon1.shoot(*shot) # (Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(2, 2)].unit.currenthp == 2 # firing unit unchanged
    assert g.board[(3, 2)].unit.currenthp == 1 # mountain unchanged
    assert g.board[(3, 2)].unit.type == 'mountain' # mountain unchanged
    assert g.board[(4, 2)].unit.currenthp == 4 # target square took 1 damage
    assert g.board[(5, 2)].unit == None # vek pushed off this square
    assert g.board[(4, 1)].unit.currenthp == 5 # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert g.board[(4, 3)].unit == None # vek also pushed off this square
    assert g.board[(6, 2)].unit.currenthp == 5 # pushed vek has full health
    assert g.board[(4, 4)].unit.currenthp == 5 # vek pushed has full health

def t_WeaponArtemisArtilleryPower1():
    "Do the Artillery demo from the game when you mouseover the weapon and you have buildings immune powered."
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery(power1=True)))
    g.board[(3, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_Building(g))
    g.board[(5, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g)) # this one is actually against the wall and cannot be pushed
    g.board[(4, 3)].createUnitHere(Unit_Alpha_Scorpion(g)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert g.board[(2, 2)].unit.currenthp == 2
    assert g.board[(3, 2)].unit.currenthp == 1
    assert g.board[(4, 2)].unit.currenthp == 1 # the building
    assert g.board[(5, 2)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 3)].unit.currenthp == 5
    gs = g.board[(2, 2)].unit.weapon1.genShots()
    for i in range(6):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 2)].unit.weapon1.shoot(*shot)
    g.flushHurt()
    assert g.board[(2, 2)].unit.currenthp == 2  # firing unit unchanged
    assert g.board[(3, 2)].unit.currenthp == 1  # mountain unchanged
    assert g.board[(3, 2)].unit.type == 'mountain'  # mountain unchanged
    assert g.board[(4, 2)].unit.currenthp == 1  # target square took no damage since it's a building and power1 prevents damage to it
    assert g.board[(5, 2)].unit == None  # vek pushed off this square
    assert g.board[(4, 1)].unit.currenthp == 5  # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert g.board[(4, 3)].unit == None  # vek also pushed off this square
    assert g.board[(6, 2)].unit.currenthp == 5  # pushed vek has full health
    assert g.board[(4, 4)].unit.currenthp == 5  # vek pushed has full health

def t_WeaponArtemisArtilleryPower2():
    "Do the power Artillery demo from the game when you mouseover the weapon and you have extra damage powered."
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery(power2=True)))
    g.board[(3, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(5, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g)) # this one is actually against the wall and cannot be pushed
    g.board[(4, 3)].createUnitHere(Unit_Alpha_Scorpion(g)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert g.board[(2, 2)].unit.currenthp == 2
    assert g.board[(3, 2)].unit.currenthp == 1
    assert g.board[(4, 2)].unit.currenthp == 5
    assert g.board[(5, 2)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 3)].unit.currenthp == 5
    gs = g.board[(2, 2)].unit.weapon1.genShots()
    for i in range(6):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 2)].unit.weapon1.shoot(*shot)
    g.flushHurt()
    assert g.board[(2, 2)].unit.currenthp == 2 # firing unit unchanged
    assert g.board[(3, 2)].unit.currenthp == 1 # mountain unchanged
    assert g.board[(3, 2)].unit.type == 'mountain' # mountain unchanged
    assert g.board[(4, 2)].unit.currenthp == 2 # target square took 1 damage
    assert g.board[(5, 2)].unit == None # vek pushed off this square
    assert g.board[(4, 1)].unit.currenthp == 5 # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert g.board[(4, 3)].unit == None # vek also pushed off this square
    assert g.board[(6, 2)].unit.currenthp == 5 # pushed vek has full health
    assert g.board[(4, 4)].unit.currenthp == 5 # vek pushed has full health

def t_WeaponArtemisArtilleryFullPower():
    "Do the Artillery demo from the game when you mouseover the weapon and you have buildings immune powered and damage powered."
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery(power1=True)))
    g.board[(3, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_Building(g))
    g.board[(5, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g)) # this one is actually against the wall and cannot be pushed
    g.board[(4, 3)].createUnitHere(Unit_Alpha_Scorpion(g)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert g.board[(2, 2)].unit.currenthp == 2
    assert g.board[(3, 2)].unit.currenthp == 1
    assert g.board[(4, 2)].unit.currenthp == 1 # the building
    assert g.board[(5, 2)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 3)].unit.currenthp == 5
    gs = g.board[(2, 2)].unit.weapon1.genShots()
    for i in range(6):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 2)].unit.weapon1.shoot(*shot)
    g.flushHurt()
    assert g.board[(2, 2)].unit.currenthp == 2  # firing unit unchanged
    assert g.board[(3, 2)].unit.currenthp == 1  # mountain unchanged
    assert g.board[(3, 2)].unit.type == 'mountain'  # mountain unchanged
    assert g.board[(4, 2)].unit.currenthp == 1  # target square took no damage since it's a building and power1 prevents damage to it
    assert g.board[(5, 2)].unit == None  # vek pushed off this square
    assert g.board[(4, 1)].unit.currenthp == 5  # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert g.board[(4, 3)].unit == None  # vek also pushed off this square
    assert g.board[(6, 2)].unit.currenthp == 5  # pushed vek has full health
    assert g.board[(4, 4)].unit.currenthp == 5  # vek pushed has full health

def t_WeaponBurstBeamNoPower():
    "Do the weapon demo with default power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam()))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.currenthp == 3 # vek took 2 damage
    assert g.board[(4, 1)].unit.currenthp == 1 # friendly took 1 damage
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_WeaponBurstBeamAllyPower():
    "Do the weapon demo with ally immune powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power1=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(6, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    assert g.board[(6, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.currenthp == 3 # vek took 2 damage
    assert g.board[(4, 1)].unit.currenthp == 2 # friendly took NO damage
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged
    assert g.board[(6, 1)].unit.currenthp == 5 # this vek was saved by the mountain

def t_WeaponBurstBeamShieldedAllyPower():
    "If you shield a beam ally with allies immune and then shoot it, the shield remains."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power1=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g, effects={Effects.SHIELD}))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(6, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    assert g.board[(6, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.currenthp == 3 # vek took 2 damage
    assert g.board[(4, 1)].unit.currenthp == 2 # friendly took NO damage
    assert g.board[(4, 1)].unit.effects == {Effects.SHIELD}  # friendly still has shield
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged
    assert g.board[(6, 1)].unit.currenthp == 5 # this vek was saved by the mountain

def t_WeaponBurstBeamDamagePower():
    "Do the weapon demo with extra damage powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.currenthp == 2 # vek took 3 damage
    assert g.board[(4, 1)].unit.type == 'mechcorpse' # friendly took 2 damage and died
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_WeaponBurstBeamFullPower():
    "Do the weapon demo with ally immune and extra damage powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.currenthp == 2 # vek took 3 damage
    assert g.board[(4, 1)].unit.currenthp == 2 # friendly took NO damage
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

# def t_WeaponBurstBeamOrder1(): # TODO: Finish this after the blast psion removes explosive from units upon death and Psion receiver is implemented.
#     "Test the order of vek and mechs dying from BurstBeam. Refer to 'explosive burst beam order 1.flv"
#     g = Game()
#     g.board[(3, 2)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power1=False, power2=False)))
#     g.board[(4, 2)].createUnitHere(Unit_Firefly(g))
#     g.board[(5, 2)].createUnitHere(Unit_Defense_Mech(g))
#     g.board[(5, 2)].createUnitHere(Unit_Blast_Psion(g))
#     assert g.board[(1, 1)].unit.currenthp == 3
#     assert g.board[(2, 1)].unit == None
#     assert g.board[(3, 1)].unit.currenthp == 5
#     assert g.board[(4, 1)].unit.currenthp == 2
#     assert g.board[(5, 1)].unit.type == 'mountain'
#     g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
#     g.flushHurt()
#     assert g.board[(1, 1)].unit.currenthp == 3 # wielder untouched
#     assert g.board[(2, 1)].unit == None # still nothing here
#     assert g.board[(2, 1)].effects == set()
#     assert g.board[(3, 1)].unit.currenthp == 2 # vek took 3 damage
#     assert g.board[(4, 1)].unit.currenthp == 2 # friendly took NO damage
#     assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_ExplosiveUnitDies():
    "Test a unit with the explosive effect dying"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam()))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, effects={Effects.EXPLOSIVE}))
    g.board[(3, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(2, 2)].createUnitHere(Unit_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3 # laser mech
    assert g.board[(2, 1)].unit.currenthp == 3 # explosive vek
    assert g.board[(3, 1)].unit.currenthp == 2 # defense mech
    assert g.board[(2, 2)].unit.currenthp == 3 # vek to take damage from explosion
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # laser mech took damage from explosion
    assert g.board[(2, 1)].unit == None  # explosive vek died and exploded
    assert g.board[(3, 1)].unit.type == 'mechcorpse'  # defense mech died from shot, then the corpse got exploded on
    assert g.board[(2, 2)].unit.currenthp == 2  # vek took damage from explosion

def t_WeaponRammingEnginesDefault():
    "Do the weapon demo with no powered upgrades"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 3 # vek pushed here took 2 damage

def t_WeaponRammingEnginesPower1():
    "Do the weapon demo with the first upgrade powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 1  # wielder took 2 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 2 # vek pushed here took 3 damage

def t_WeaponRammingEnginesPower2():
    "Do the weapon demo with the second upgrade powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 2 # vek pushed here took 3 damage

def t_WeaponRammingEnginesFullPower():
    "Do the weapon demo with the both upgrades powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 1  # wielder took 2 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 1 # vek pushed here took 4 damage

def t_WeaponRammingEnginesTileDamage():
    "Do the weapon demo with no powered upgrades but on sand tiles to make sure they get damaged"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(3, 1)].replaceTile(Tile_Sand(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(1, 1)].effects == set() # sand tiles are all normal
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 3 # vek pushed here took 2 damage
    assert g.board[(1, 1)].effects == set() # this one untouched
    assert g.board[(2, 1)].effects == {Effects.SMOKE} # these 2 got smoked from the self damage
    assert g.board[(3, 1)].effects == {Effects.SMOKE} # and vek getting hit

def t_WeaponRammingEnginesShieldedTileDamage():
    "Do the weapon demo with no powered upgrades but on sand tiles with a shield to make sure they don't get damaged"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(1, 1)].applyShield()
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(3, 1)].replaceTile(Tile_Sand(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(1, 1)].effects == set() # sand tiles are all normal
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder took 0 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 3 # vek pushed here took 2 damage
    assert g.board[(1, 1)].effects == set() # this one untouched
    assert g.board[(2, 1)].effects == set() # this sand tile took no damage since the mech was shielded
    assert g.board[(3, 1)].effects == {Effects.SMOKE} # this one does take damage because this is where the vek got hit

def t_WeaponRammingEnginesIntoChasm():
    "Charge but stop at a chasm and die in it"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 1)].replaceTile(Tile_Chasm(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].effects == set() # normal chasm tile
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit == None # wielder and mech corpse died in the chasm
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 3 # vek pushed here took 2 damage
    assert g.board[(3, 1)].effects == set()  # normal chasm tile

def t_WeaponRammingEnginesOverChasm():
    "Charge over a chasm and don't die in it"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(2, 1)].replaceTile(Tile_Chasm(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(2, 1)].effects == set() # normal chasm tile
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    #for x in range(1, 6):
    #    print(g.board[x, 1])
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(3, 1)].unit.currenthp == 2 # wielder took 1 damage
    assert g.board[(4, 1)].unit == None # vek pushed off this tile
    assert g.board[(5, 1)].unit.currenthp == 3 # vek pushed here took 2 damage
    assert g.board[(2, 1)].effects == set()  # normal chasm tile

def t_WeaponRammingEnginesShield():
    "A shielded unit that uses ramming engines takes no self-damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=True, power2=True), effects={Effects.SHIELD}))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder took 0 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 1 # vek pushed here took 4 damage

def t_WeaponRammingEnginesMiss():
    "if ramming engine doesn't hit a unit, it doesn't take self damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=True, power2=True)))
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # wielder moved
    assert g.board[(8, 1)].unit.currenthp == 3  # wielder took 0 damage
    assert g.board[(1, 1)].effects == set() # original forest tile didn't take damage
    assert g.board[(8, 1)].effects == set() # destination forest tile undamaged as well

# These 2 tests were removed because weapon shot generators were changed to not explicitly validate each shot like we tested here
# def t_NoOffBoardShotsGenCorner():
#     "test noOffBoardShotsGen by putting a unit in a corner"
#     g = Game()
#     g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
#     gs = g.board[(1, 1)].unit.weapon1.genShots()
#     g.flushHurt()
#     assert next(gs) == Direction.UP
#     assert next(gs) == Direction.RIGHT
#     try:
#         next(gs)
#     except StopIteration: # no more directions
#         pass # which is good
#     else:
#         assert False # we got another direction?
#
# def t_NoOffBoardShotsGenSide():
#     "test noOffBoardShotsGen by putting a unit against a side"
#     g = Game()
#     g.board[(1, 2)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
#     gs = g.board[(1, 2)].unit.weapon1.genShots()
#     g.flushHurt()
#     assert next(gs) == Direction.UP
#     assert next(gs) == Direction.RIGHT
#     assert next(gs) == Direction.DOWN
#     try:
#         next(gs)
#     except StopIteration: # no more directions
#         pass # which is good
#     else:
#         assert False # we got another direction?

def t_WeaponTaurusCannonDefaultPower():
    "Shoot the Taurus Cannon with default power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g, weapon1=Weapon_TaurusCannon()))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None # vek was pushed off this square
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 4 # vek lost 1 hp

def t_WeaponTaurusCannonDefaultPower1():
    "Shoot the Taurus Cannon with power1"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g, weapon1=Weapon_TaurusCannon(power1=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None # vek was pushed off this square
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 3 # vek lost 2 hp

def t_WeaponTaurusCannonPower2():
    "Shoot the Taurus Cannon with power2"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g, weapon1=Weapon_TaurusCannon(power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None # vek was pushed off this square
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 3 # vek lost 2 hp

def t_WeaponTaurusCannonFullPower():
    "Shoot the Taurus Cannon with full power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g, weapon1=Weapon_TaurusCannon(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None # vek was pushed off this square
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 2 # vek lost 3 hp

def t_WeaponAttractionPulseDefault():
    "Shoot the Attraction Pulse at a unit with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_AttractionPulse(power1=False, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(4, 1)].unit == None # vek was pushed off this square
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set() # pulled 1 square closer
    assert g.board[(3, 1)].unit.currenthp == 5 # vek lost 0 hp

def t_WeaponAttractionPulseFullPower():
    "Shoot the Attraction Pulse at a unit with full power. IRL this gun takes no power, just making sure this doesn't break."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_AttractionPulse(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(4, 1)].unit == None # vek was pushed off this square
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set() # pulled 1 square closer
    assert g.board[(3, 1)].unit.currenthp == 5 # vek lost 0 hp

def t_WeaponAttractionPulseBump():
    "Attraction pulse does not set fire to forest tile if you pull another unit into you for bump damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_AttractionPulse(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    for x in 1, 2:
        g.board[(x, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no fire
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 1 # took 1 damage
    assert g.board[(2, 1)].effects == set() # no fire
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.currenthp == 4 # vek lost 1 hp from bump

def t_WeaponShieldProjectorDefaultPower():
    "Maiden test of the shield projector with no upgrade power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_ShieldProjector(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(5, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    for x in range(1, 6):
        for y in range(1, 3):
            assert g.board[(x, y)].unit.effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.effects == set()  # no change
    assert g.board[(2, 1)].unit.effects == set() # shot over this one
    assert g.board[(3, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(4, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(5, 1)].unit.effects == set()
    assert g.board[(1, 2)].unit.effects == set()  # no change to anything in the 2nd row
    assert g.board[(2, 2)].unit.effects == set()
    assert g.board[(3, 2)].unit.effects == set()
    assert g.board[(4, 2)].unit.effects == set()
    assert g.board[(5, 2)].unit.effects == set()

def t_WeaponShieldProjectorPower2():
    "Shield Projector with power2"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_ShieldProjector(power1=True, power2=True))) # power1 is ignored
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(5, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    for x in range(1, 6):
        for y in range(1, 3):
            assert g.board[(x, y)].unit.effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.effects == set()  # no change
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD} # shot over this one but he got shielded anyway
    assert g.board[(3, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(4, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(5, 1)].unit.effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(2, 2)].unit.effects == set()
    assert g.board[(3, 2)].unit.effects == {Effects.SHIELD}
    assert g.board[(4, 2)].unit.effects == set()
    assert g.board[(5, 2)].unit.effects == set()

def t_WeaponShieldProjectorGen():
    "Test the generator for the shield projector."
    g = Game()
    g.board[(5, 5)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_ShieldProjector(power1=True, power2=True, usesremaining=1)))  # power1 is ignored
    gs = g.board[(5, 5)].unit.weapon1.genShots()
    g.flushHurt()
    assert next(gs) == (Direction.UP, 2) # generator generates what we expect
    g.board[(5, 5)].unit.weapon1.shoot(Direction.UP, 2) # shoot to spend the ammo
    try:
        next(gs)
    except StopIteration:
        pass # what we expect
    else:
        assert False # ya fucked up

def t_WeaponViceFistNoPower():
    "Test the Vice Fist with no power"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 4
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponViceFistPower1():
    "Test the Vice Fist with power1"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 4 # no additional effect since this was an enemy
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponViceFistPower2():
    "Test the Vice Fist with power2"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2 # took additional damage
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponViceFistPower1Friendly():
    "Test the Vice Fist with power1 and a friendly unit"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Siege_Mech(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 2
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2 # friendly unit took no damage
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponViceFistPower1FriendlyChasm():
    "Test the Vice Fist with power1 and a friendly unit, but kill the unit by throwing it into a chasm"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Siege_Mech(g))
    g.board[(1, 1)].replaceTile(Tile_Chasm(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 2
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # friendly unit died in the chasm
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponClusterArtilleryNoPower():
    "Default power test for Cluster Artillery"
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_Siege_Mech(g, weapon1=Weapon_ClusterArtillery(power1=False, power2=False)))
    g.board[(3, 3)].createUnitHere(Unit_Building(g))
    g.board[(4, 3)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 4)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 3)].unit.currenthp == 2
    assert g.board[(3, 3)].unit.currenthp == 1 # building
    assert g.board[(4, 3)].unit.currenthp == 5
    assert g.board[(3, 4)].unit.currenthp == 5
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for i in range(5):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 3)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 3)].unit.currenthp == 2
    assert g.board[(3, 3)].unit.currenthp == 1  # building
    assert g.board[(4, 3)].unit == None # vek pushed
    assert g.board[(5, 3)].unit.currenthp == 4 # took 1 damage
    assert g.board[(3, 4)].unit == None # vek pushed
    assert g.board[(3, 5)].unit.currenthp == 4 # took 1 damage

def t_WeaponClusterArtilleryPower1():
    "power1 test for Cluster Artillery"
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_Siege_Mech(g, weapon1=Weapon_ClusterArtillery(power1=True, power2=False)))
    g.board[(3, 3)].createUnitHere(Unit_Building(g))
    g.board[(4, 3)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 4)].createUnitHere(Unit_Building(g))
    assert g.board[(1, 3)].unit.currenthp == 2
    assert g.board[(3, 3)].unit.currenthp == 1 # building
    assert g.board[(4, 3)].unit.currenthp == 5
    assert g.board[(3, 4)].unit.currenthp == 1 # attacked building
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for i in range(5):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 3)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 3)].unit.currenthp == 2
    assert g.board[(3, 3)].unit.currenthp == 1  # building
    assert g.board[(4, 3)].unit == None # vek pushed
    assert g.board[(5, 3)].unit.currenthp == 4 # took 1 damage
    assert g.board[(3, 4)].unit.currenthp == 1  # attacked building took no damage

def t_WeaponClusterArtilleryFullPower():
    "full power test for Cluster Artillery"
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_Siege_Mech(g, weapon1=Weapon_ClusterArtillery(power1=True, power2=True)))
    g.board[(3, 3)].createUnitHere(Unit_Building(g))
    g.board[(4, 3)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 4)].createUnitHere(Unit_Building(g))
    assert g.board[(1, 3)].unit.currenthp == 2
    assert g.board[(3, 3)].unit.currenthp == 1 # building
    assert g.board[(4, 3)].unit.currenthp == 5
    assert g.board[(3, 4)].unit.currenthp == 1 # attacked building
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for i in range(5):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # (Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 3)].unit.currenthp == 2
    assert g.board[(3, 3)].unit.currenthp == 1  # building
    assert g.board[(4, 3)].unit == None # vek pushed
    assert g.board[(5, 3)].unit.currenthp == 3 # took 2 damage
    assert g.board[(3, 4)].unit.currenthp == 1  # attacked building took no damage

def t_WeaponGravWellNormal():
    "default test for grav well"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Gravity_Mech(g, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # untouched wielder
    assert g.board[(3, 1)].unit == None # vek pushed
    assert g.board[(2, 1)].unit.currenthp == 5 # to here with no damage

def t_WeaponGravWellStable():
    "grav well can't pull stable units"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Gravity_Mech(g, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 1
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # untouched wielder
    assert g.board[(3, 1)].unit.currenthp == 1 # mountain not moved and undamaged
    assert g.board[(3, 1)].unit.type == 'mountain'

def t_WeaponGravWellBump():
    "grav well pulls vek into a mountain"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Gravity_Mech(g, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    g.board[(2, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(2, 1)].unit.currenthp == 1
    assert g.board[(2, 1)].unit.type == 'mountain'
    assert g.board[(3, 1)].unit.currenthp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # untouched wielder
    assert g.board[(3, 1)].unit.currenthp == 4 # vek pushed and bumped for 1 damage
    assert g.board[(2, 1)].unit.currenthp == 1 # damage mountain now
    assert g.board[(2, 1)].unit.type == 'mountaindamaged'

def t_WeaponJanusCannonLow():
    "Shoot the Janus cannon with no power!"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Mirror_Mech(g, weapon1=Weapon_JanusCannon(power1=False, power2=False)))  # this weapon doesn't have power upgrades
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 3
    assert g.board[(5, 1)].unit.currenthp == 5
    g.board[(4, 1)].unit.weapon1.shoot(Direction.RIGHT) # this shoots left and right
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # alpha scorpion pushed from here
    assert g.board[(1, 1)].unit.currenthp == 4 # pushed here and took 1 damage
    assert g.board[(4, 1)].unit.currenthp == 3 # no change to the shooter
    assert g.board[(5, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(6, 1)].unit.currenthp == 4 # took a damage
    # shoot a second time, why not
    g.board[(4, 1)].unit.weapon1.shoot(Direction.LEFT)  # this shoots left and right
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # nowhere else to push, just takes another damage
    assert g.board[(4, 1)].unit.currenthp == 3  # still no change to the shooter
    assert g.board[(6, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(7, 1)].unit.currenthp == 3  # took a damage

def t_WeaponJanusCannon1():
    "Shoot the Janus cannon with 1 power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Mirror_Mech(g, weapon1=Weapon_JanusCannon(power1=True, power2=False)))
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 3
    assert g.board[(5, 1)].unit.currenthp == 5
    g.board[(4, 1)].unit.weapon1.shoot(Direction.RIGHT) # this shoots left and right
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # alpha scorpion pushed from here
    assert g.board[(1, 1)].unit.currenthp == 3 # pushed here and took 2 damage
    assert g.board[(4, 1)].unit.currenthp == 3 # no change to the shooter
    assert g.board[(5, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(6, 1)].unit.currenthp == 3 # took 2 damage
    # shoot a second time, why not
    g.board[(4, 1)].unit.weapon1.shoot(Direction.LEFT)  # this shoots left and right
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 1  # nowhere else to push, just takes another 2 damage
    assert g.board[(4, 1)].unit.currenthp == 3  # still no change to the shooter
    assert g.board[(6, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(7, 1)].unit.currenthp == 1  # took 2 damage

def t_WeaponJanusCannon2():
    "Shoot the Janus cannon with power2 powered."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Mirror_Mech(g, weapon1=Weapon_JanusCannon(power1=False, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 3
    assert g.board[(5, 1)].unit.currenthp == 5
    g.board[(4, 1)].unit.weapon1.shoot(Direction.RIGHT) # this shoots left and right
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # alpha scorpion pushed from here
    assert g.board[(1, 1)].unit.currenthp == 3 # pushed here and took 2 damage
    assert g.board[(4, 1)].unit.currenthp == 3 # no change to the shooter
    assert g.board[(5, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(6, 1)].unit.currenthp == 3 # took 2 damage
    # shoot a second time, why not
    g.board[(4, 1)].unit.weapon1.shoot(Direction.LEFT)  # this shoots left and right
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 1  # nowhere else to push, just takes another 2 damage
    assert g.board[(4, 1)].unit.currenthp == 3  # still no change to the shooter
    assert g.board[(6, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(7, 1)].unit.currenthp == 1  # took 2 damage

def t_WeaponJanusCannonFullPower():
    "Shoot the Janus cannon with Full power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Mirror_Mech(g, weapon1=Weapon_JanusCannon(power1=True, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 3
    assert g.board[(5, 1)].unit.currenthp == 5
    g.board[(4, 1)].unit.weapon1.shoot(Direction.RIGHT) # this shoots left and right
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # alpha scorpion pushed from here
    assert g.board[(1, 1)].unit.currenthp == 2 # pushed here and took 3 damage
    assert g.board[(4, 1)].unit.currenthp == 3 # no change to the shooter
    assert g.board[(5, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(6, 1)].unit.currenthp == 2 # took 3 damage
    # shoot a second time, why not
    g.board[(4, 1)].unit.weapon1.shoot(Direction.LEFT)  # this shoots left and right
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # unit died
    assert g.board[(4, 1)].unit.currenthp == 3  # still no change to the shooter
    assert g.board[(6, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(7, 1)].unit == None # this one also died

def t_WeaponCryoLauncher():
    "Shoot the CryoLauncher cannon."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 1)].createUnitHere(Unit_Ice_Mech(g, weapon1=Weapon_CryoLauncher(power1=True, power2=True))) # this weapon doesn't use power
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(9):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # (Direction.RIGHT, 4)
    g.flushHurt() # not necessary since nothing was hurt
    assert g.board[(1, 1)].type == 'ice' # tile is now frozen
    assert g.board[(1, 1)].effects == set() # not submerged
    assert g.board[(1, 1)].unit.effects == {Effects.ICE} # wielder was frozen
    assert g.board[(5, 1)].unit.effects == {Effects.ICE}  # wielder was frozen

def t_WeaponCryoLauncherShielded():
    "Shoot the CryoLauncher cannon with a shielded wielder."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 1)].createUnitHere(Unit_Ice_Mech(g, weapon1=Weapon_CryoLauncher(power1=True, power2=True), effects={Effects.SHIELD})) # this weapon doesn't use power
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED}
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(9):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 4
    g.flushHurt() # not necessary since nothing was hurt
    assert g.board[(1, 1)].type == 'water' # no change since the wielder's shield prevented ice from being applied to the wielder and the tile it's on
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED} # no change
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD} # wielder was NOT frozen, still shielded
    assert g.board[(5, 1)].unit.effects == {Effects.ICE}  # wielder was frozen as expected

def t_WeaponAerialBombs1():
    "Shoot the AerialBombs with default power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.currenthp == 4 # hit for 1 dmg
    assert g.board[(3, 1)].unit.currenthp == 2 # jet landed here
    assert g.board[(3, 1)].unit.type == 'jet'

def t_WeaponAerialBombs2():
    "Shoot the AerialBombs with more damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.currenthp == 3 # hit for 2 dmg
    assert g.board[(3, 1)].unit.currenthp == 2 # jet landed here
    assert g.board[(3, 1)].unit.type == 'jet'

def t_WeaponAerialBombs3():
    "Shoot the AerialBombs with more range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.currenthp == 4 # hit for 1 dmg
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.currenthp == 4  # hit for 1 dmg
    assert g.board[(4, 1)].unit.currenthp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponAerialBombs4():
    "Shoot the AerialBombs with full power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.currenthp == 3 # hit for 2 dmg
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.currenthp == 3  # hit for 2 dmg
    assert g.board[(4, 1)].unit.currenthp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponAerialBombsForest():
    "Shoot the AerialBombs on a forest and make sure it has smoke and not fire after."
    g = Game()
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.currenthp == 4 # hit for 1 dmg
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.currenthp == 4  # hit for 1 dmg
    assert g.board[(4, 1)].unit.currenthp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponAerialBombsGen1():
    "Test the Aerial Bombs shot generator."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=False, power2=True))) # with range
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 4)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    assert next(gs) == (Direction.UP, 1)
    assert next(gs) == (Direction.UP, 2)
    assert next(gs) == (Direction.RIGHT, 1)
    assert next(gs) == (Direction.RIGHT, 2)
    # try: # weapon gens no longer give you known-good shots, the weapon determines if it's valid or not.
    #     next(gs)
    # except StopIteration:
    #     pass # this is expected
    # else:
    #     assert False # there shouldn't be any more valid shots to generate in this configuration

def t_WeaponRocketArtillery1():
    "Shoot the Rocket Artillery weapon with default power with its back against the edge."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Rocket_Mech(g, weapon1=Weapon_RocketArtillery(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # no change for shooter
    assert g.board[(1, 1)].unit.effects == set() # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(3, 1)].effects == set() # no effects change to the tile
    assert g.board[(4, 1)].unit.currenthp == 3 # vek took 2 dmg
    assert g.board[(4, 1)].effects == set()  # no effects change to the tile

def t_WeaponRocketArtillery2():
    "Shoot the Rocket Artillery weapon with 1 power with its back against the edge."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Rocket_Mech(g, weapon1=Weapon_RocketArtillery(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # no change for shooter
    assert g.board[(1, 1)].unit.effects == set() # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(3, 1)].effects == set() # no effects change to the tile
    assert g.board[(4, 1)].unit.currenthp == 2 # vek took 3 dmg
    assert g.board[(4, 1)].effects == set()  # no effects change to the tile
    
def t_WeaponRocketArtillery3():
    "Shoot the Rocket Artillery weapon with full power with its back against the edge."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Rocket_Mech(g, weapon1=Weapon_RocketArtillery(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3 # no change for shooter
    assert g.board[(1, 1)].unit.effects == set() # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(3, 1)].effects == set() # no effects change to the tile
    assert g.board[(4, 1)].unit.currenthp == 1 # vek took 4 dmg
    assert g.board[(4, 1)].effects == set()  # no effects change to the tile

def t_WeaponRocketArtillery4():
    "Shoot the Rocket Artillery weapon with full power with a tile for it to fart smoke onto"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Rocket_Mech(g, weapon1=Weapon_RocketArtillery(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(2, 1)].unit.currenthp == 3 # no change for shooter
    assert g.board[(2, 1)].unit.effects == set() # no change for shooter
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(4, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].effects == set() # no effects change to the tile
    assert g.board[(5, 1)].unit.currenthp == 1 # vek took 4 dmg
    assert g.board[(5, 1)].effects == set()  # no effects change to the tile
    assert g.board[(1, 1)].effects == {Effects.SMOKE} # smoke was farted behind the wielder

def t_WeaponRepulse1():
    "Shoot the Repulse weapon with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit == None # vek pushed off here
    assert g.board[(3, 1)].unit.currenthp == 5  # no change for vek
    assert g.board[(3, 1)].unit.effects == set()  # no change for vek
    assert g.board[(3, 1)].effects == set()  # no change for vek's tile
    assert g.board[(1, 2)].unit == None  # ally pushed off here
    assert g.board[(1, 3)].unit.currenthp == 3  # no change for ally
    assert g.board[(1, 3)].unit.effects == set()  # no change for vally
    assert g.board[(1, 3)].effects == set()  # no change for ally's tile

def t_WeaponRepulse2():
    "Shoot the Repulse weapon with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD} # shooter shielded
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit == None # vek pushed off here
    assert g.board[(3, 1)].unit.currenthp == 5  # no change for vek
    assert g.board[(3, 1)].unit.effects == set()  # no change for vek
    assert g.board[(3, 1)].effects == set()  # no change for vek's tile
    assert g.board[(1, 2)].unit == None  # ally pushed off here
    assert g.board[(1, 3)].unit.currenthp == 3  # no change for ally
    assert g.board[(1, 3)].unit.effects == set()  # no change for ally
    assert g.board[(1, 3)].effects == set()  # no change for ally's tile

def t_WeaponRepulse3():
    "Shoot the Repulse weapon with 2nd power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set() # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit == None # vek pushed off here
    assert g.board[(3, 1)].unit.currenthp == 5  # no change for vek
    assert g.board[(3, 1)].unit.effects == set()  # no change for vek
    assert g.board[(3, 1)].effects == set()  # no change for vek's tile
    assert g.board[(1, 2)].unit == None  # ally pushed off here
    assert g.board[(1, 3)].unit.currenthp == 3  # no change for ally
    assert g.board[(1, 3)].unit.effects == {Effects.SHIELD}  # ally is shielded
    assert g.board[(1, 3)].effects == set()  # no change for ally's tile

def t_WeaponRepulse4():
    "Shoot the Repulse weapon with full power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}  # shooter shielded
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit == None # vek pushed off here
    assert g.board[(3, 1)].unit.currenthp == 5  # no change for vek
    assert g.board[(3, 1)].unit.effects == set()  # no change for vek
    assert g.board[(3, 1)].effects == set()  # no change for vek's tile
    assert g.board[(1, 2)].unit == None  # ally pushed off here
    assert g.board[(1, 3)].unit.currenthp == 3  # no change for ally
    assert g.board[(1, 3)].unit.effects == {Effects.SHIELD}  # ally is shielded
    assert g.board[(1, 3)].effects == set()  # no change for ally's tile

def t_WeaponRepulse5():
    "Shoot the Repulse weapon with full power and a building to get shielded. And a mountain for the vek to bump into."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 2)].createUnitHere(Unit_Building(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}  # shooter shielded
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit.currenthp == 4  # vek took 1 bump damage
    assert g.board[(2, 1)].unit.effects == set()  # no change for vek
    assert g.board[(2, 1)].effects == set()  # no change for vek's tile
    assert g.board[(3, 1)].unit.type == 'mountaindamaged' # mountain got bumped into
    assert g.board[(1, 2)].unit.currenthp == 1  # no change for building
    assert g.board[(1, 2)].unit.effects == {Effects.SHIELD}  # building is shielded
    assert g.board[(1, 2)].effects == set()  # no change for ally's tile

def t_WeaponGrapplingHook1():
    "Shoot the grappling hook weapon at an enemy with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=False, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # unit moved from here
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.currenthp == 5  # vek is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set()  # no change for vek
    assert g.board[(2, 1)].effects == set()  # no change for vek's tile

def t_WeaponGrapplingHook2():
    "Shoot the grappling hook weapon at an enemy with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=True, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # unit moved from here
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.currenthp == 5  # vek is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set()  # no change for vek
    assert g.board[(2, 1)].effects == set()  # no change for vek's tile

def t_WeaponGrapplingHook3():
    "Shoot the grappling hook weapon at a friendly with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=False, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Hook_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # unit moved from here
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.currenthp == 3  # ally is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set()  # no change for ally
    assert g.board[(2, 1)].effects == set()  # no change for ally's tile

def t_WeaponGrapplingHook4():
    "Shoot the grappling hook weapon at a friendly with power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=True, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Hook_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # unit moved from here
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.currenthp == 3  # ally is now here, took no damage
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD} # ally is shielded
    assert g.board[(2, 1)].effects == set()  # no change for ally's tile

def t_WeaponGrapplingHook5():
    "Shoot the grappling hook weapon at a mountain with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=False, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit == None  # wielder moved from this spot
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(2, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'mountain'
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set() # wielder gets no new effect
    assert g.board[(2, 1)].effects == set()  # no change for wielder's new tile

def t_WeaponGrapplingHook6():
    "Shoot the grappling hook weapon at a mountain with power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=True, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit == None  # wielder moved from this spot
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(2, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'mountain'
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set() # wielder gets no new effect
    assert g.board[(2, 1)].effects == set()  # no change for wielder's new tile

def t_WeaponGrapplingHook7():
    "Shoot the grappling hook weapon at a building with power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=True, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Building(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit == None  # wielder moved from this spot
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(2, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'building'
    assert g.board[(3, 1)].unit.effects == {Effects.SHIELD} # building is now shielded
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set() # wielder gets no new effect
    assert g.board[(2, 1)].effects == set()  # no change for wielder's new tile

def t_WeaponGrapplingHook8():
    "Shoot the grappling hook weapon at a building with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=False, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Building(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit == None  # wielder moved from this spot
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(2, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'building'
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set() # wielder gets no new effect
    assert g.board[(2, 1)].effects == set()  # no change for wielder's new tile

def t_WeaponRockLauncher1():
    "Shoot the Rock Launcher with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.effects == set() # target gets no new effects
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(3, 1)].unit.currenthp == 3 # vek took 2 damage
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.currenthp == 5 # to here, took no damage

def t_WeaponRockLauncher2():
    "Shoot the Rock Launcher with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.effects == set() # target gets no new effects
    assert g.board[(3, 1)].effects == set() # target's tile untouched
    assert g.board[(3, 1)].unit.currenthp == 2 # vek took 3 damage
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.currenthp == 5 # to here, took no damage

def t_WeaponRockLauncher3():
    "Shoot the Rock Launcher with full power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.effects == set() # target gets no new effects
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(3, 1)].unit.currenthp == 1 # vek took 4 damage
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.currenthp == 5 # to here, took no damage

def t_WeaponRockLauncher4():
    "Shoot the Rock Launcher with full power, but with a forest under the target vek"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=True, power2=True)))
    g.board[(3, 1)].replaceTile(Tile_Forest(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE} # target is set on fire
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile on fire
    assert g.board[(3, 1)].unit.currenthp == 1 # vek took 4 damage
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.currenthp == 5 # to here, took no damage

def t_WeaponRockLauncher5():
    "Shoot the Rock Launcher with full power, but with a forest with no target vek on it"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=True, power2=True)))
    g.board[(3, 1)].replaceTile(Tile_Forest(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'rock' # rock landed here and survives
    assert g.board[(3, 1)].effects == set() # tile doesn't catch fire since no damage was actually done to the tile
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.currenthp == 5 # to here, took no damage

def t_WeaponFlameThrower1():
    "Shoot the Flame Thrower with default power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=False, power2=False)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(2, 1)].type == 'ground' # tile converted from sand to ground
    assert g.board[(2, 1)].unit == None # vek pushed
    assert g.board[(3, 1)].effects == set() # no change to destination
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE} # vek is now on fire
    assert g.board[(3, 1)].unit.currenthp == 5  # vek took no damage

def t_WeaponFlameThrower2():
    "Shoot the Flame Thrower with one more range/power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=False)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(2, 1)].type == 'ground' # tile converted from sand to ground
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(2, 1)].unit.currenthp == 5  # vek took no damage
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile past the vek caught fire
    assert g.board[(4, 1)].effects == set() # no change to push destination

def t_WeaponFlameThrower3():
    "Shoot the Flame Thrower with max range/power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=True)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 3)
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(2, 1)].type == 'ground' # tile converted from sand to ground
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(2, 1)].unit.currenthp == 5  # vek took no damage
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile past the vek caught fire
    assert g.board[(4, 1)].effects == {Effects.FIRE} # this tile caught fire too
    assert g.board[(5, 1)].effects == set() # no change to push destination

def t_WeaponFlameThrower4():
    "Shoot the Flame Thrower twice with max range/power to cause damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=True)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 3)
    g.flushHurt()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 3)
    g.flushHurt() # redundant as the first shot didn't kill anything
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(2, 1)].type == 'ground' # tile converted from sand to ground
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(2, 1)].unit.currenthp == 3  # vek took 2 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile past the vek caught fire
    assert g.board[(4, 1)].effects == {Effects.FIRE} # this tile caught fire too
    assert g.board[(5, 1)].effects == set() # no change to push destination

def t_WeaponFlameThrowerMountain():
    "Shoot the Flame Thrower with max range/power through a mountain."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=True)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    try:
        g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 3)
    except NullWeaponShot: # This is expected
        pass
    else:
        assert False # this is not good

def t_WeaponFlameThrowerOffBoard():
    "Shoot the Flame Thrower with max range/power off the board."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=True)))
    g.board[(1, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    try:
        g.board[(2, 1)].unit.weapon1.shoot(Direction.LEFT, 3)
    except NullWeaponShot: # This is expected
        pass
    else:
        assert False # this is not good

def t_WeaponVulcanArtillery1():
    "Shoot the Vulcan Artillery with low power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(3, 1)].unit.currenthp == 5 # no damage
    assert g.board[(3, 2)].unit == None # vek pushed from here
    assert g.board[(3, 3)].effects == set()
    assert g.board[(3, 3)].unit.effects == set()
    assert g.board[(3, 3)].unit.currenthp == 5  # no damage

def t_WeaponVulcanArtillery2():
    "Shoot the Vulcan Artillery with backburn power up against a wall."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(1, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(3, 1)].unit.currenthp == 5 # no damage
    assert g.board[(3, 2)].unit == None # vek pushed from here
    assert g.board[(3, 3)].effects == set()
    assert g.board[(3, 3)].unit.effects == set()
    assert g.board[(3, 3)].unit.currenthp == 5  # no damage

def t_WeaponVulcanArtillery3():
    "Shoot the Vulcan Artillery with backburn power NOT up against a wall."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # (Direction.RIGHT, 2)
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(4, 1)].unit.currenthp == 5 # no damage
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.currenthp == 5  # no damage
    assert g.board[(1, 1)].effects == {Effects.FIRE} # fire farted

def t_WeaponVulcanArtillery4():
    "Shoot the Vulcan Artillery withOUT backburn power NOT up against a wall."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=False, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(4, 1)].unit.currenthp == 5 # no damage
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.currenthp == 5  # no damage
    assert g.board[(1, 1)].effects == set() # NO fire farted

def t_WeaponVulcanArtillery5():
    "Shoot the Vulcan Artillery withOUT backburn power NOT up against a wall and WITH damage power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=False, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(4, 1)].unit.currenthp == 3 # 2 damage
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.currenthp == 5  # no damage
    assert g.board[(1, 1)].effects == set() # NO fire farted

def t_WeaponVulcanArtillery6():
    "Shoot the Vulcan Artillery with backburn power NOT up against a wall and WITH damage power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(4, 1)].unit.currenthp == 3 # 2 damage
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.currenthp == 5  # no damage
    assert g.board[(1, 1)].effects == {Effects.FIRE}  # fire farted

def t_WeaponVulcanArtillery7():
    "Shoot the Vulcan Artillery with full power against a mountain for some reason."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == set()  # mountains can't catch on fire
    assert g.board[(4, 1)].unit.type == 'mountaindamaged'
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.currenthp == 5  # no damage
    assert g.board[(1, 1)].effects == {Effects.FIRE}  # fire farted

def t_WeaponVulcanArtillery8():
    "Shoot the Vulcan Artillery with no damage power against a mountain for some reason."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.currenthp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == set()  # mountains can't catch on fire
    assert g.board[(4, 1)].unit.type == 'mountain'
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.currenthp == 5  # no damage
    assert g.board[(1, 1)].effects == {Effects.FIRE}  # fire farted

def t_WeaponTeleporter1():
    "Shoot the teleporter with no power and no unit to swap with"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Swap_Mech(g, weapon1=Weapon_Teleporter(power1=False, power2=False)))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.currenthp == 2  # no change for shooter who is now here
    assert g.board[(2, 1)].unit.type == 'swap'
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None

def t_WeaponTeleporter2():
    "Shoot the teleporter with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Swap_Mech(g, weapon1=Weapon_Teleporter(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.currenthp == 2  # no change for shooter who is now here
    assert g.board[(2, 1)].unit.type == 'swap'
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 5  # no damage to vek who is now here

def t_WeaponTeleporter3():
    "Shoot the teleporter with full power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Swap_Mech(g, weapon1=Weapon_Teleporter(power1=True, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 4)
    g.flushHurt() # no units actually hurt
    assert g.board[(5, 1)].unit.currenthp == 2  # no change for shooter who is now here
    assert g.board[(5, 1)].unit.type == 'swap'
    assert g.board[(5, 1)].unit.effects == set()
    assert g.board[(5, 1)].effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 5  # no damage to vek who is now here

def t_WeaponTeleporterOffBoard():
    "Shoot the teleporter with some power off the board"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Swap_Mech(g, weapon1=Weapon_Teleporter(power1=True, power2=False)))
    g.board[(5, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    try:
        g.board[(1, 1)].unit.weapon1.shoot(Direction.LEFT, 2)
    except NullWeaponShot:
        pass # expected
    else:
        assert False # WRONG

def t_WeaponHydraulicLegsLowPower():
    "Shoot the Hydraulic Legs with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Leap_Mech(g, weapon1=Weapon_HydraulicLegs(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    for x in range(1, 5):
        for y in range(1, 4):
            g.board[(x, y)].replaceTile(Tile_Forest(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(8):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE} # forest caught fire
    assert g.board[(1, 1)].unit == None # wielder leaped from here
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught fire from self-damage
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE} # wielder caught fire
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == set() # This forest DID NOT catch fire from the vek that was pushed here!
    assert g.board[(4, 1)].unit.effects == set() # This vek never caught fire! He was pushed to the forest tile before it was lit on fire
    assert g.board[(4, 1)].unit.currenthp == 4 # vek took 1 damage
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == set()
    assert g.board[(2, 3)].unit.effects == set()
    assert g.board[(2, 3)].unit.currenthp == 4 # took 1 damage

def t_WeaponHydraulicLegsPower1():
    "Shoot the Hydraulic Legs with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Leap_Mech(g, weapon1=Weapon_HydraulicLegs(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    for x in range(1, 5):
        for y in range(1, 4):
            g.board[(x, y)].replaceTile(Tile_Forest(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(8):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE} # forest caught fire
    assert g.board[(1, 1)].unit == None # wielder leaped from here
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught fire from self-damage
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE} # wielder caught fire
    assert g.board[(2, 1)].unit.currenthp == 1  # wielder took 2 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 3 # vek took 2 damage
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == set()
    assert g.board[(2, 3)].unit.effects == set()
    assert g.board[(2, 3)].unit.currenthp == 3 # took 2 damage

def t_WeaponHydraulicLegsPower2():
    "Shoot the Hydraulic Legs with second power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Leap_Mech(g, weapon1=Weapon_HydraulicLegs(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    for x in range(1, 5):
        for y in range(1, 4):
            g.board[(x, y)].replaceTile(Tile_Forest(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(8):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE} # forest caught fire
    assert g.board[(1, 1)].unit == None # wielder leaped from here
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught fire from self-damage
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE} # wielder caught fire
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 3 # vek took 2 damage
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == set()
    assert g.board[(2, 3)].unit.effects == set()
    assert g.board[(2, 3)].unit.currenthp == 3 # took 2 damage

def t_WeaponHydraulicLegsMaxPower():
    "Shoot the Hydraulic Legs with maximum power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Leap_Mech(g, weapon1=Weapon_HydraulicLegs(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    for x in range(1, 5):
        for y in range(1, 4):
            g.board[(x, y)].replaceTile(Tile_Forest(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(8):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # wielder leaped from here
    assert g.board[(1, 1)].effects == {Effects.FIRE} # forest caught fire
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught fire from self-damage
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE} # wielder caught fire
    assert g.board[(2, 1)].unit.currenthp == 1  # wielder took 2 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == set() # the vek pushed from the tile that caught fire did not catch fire itself!
    assert g.board[(4, 1)].unit.effects == set() # told ya so
    assert g.board[(4, 1)].unit.currenthp == 2 # vek took 3 damage
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == set()
    assert g.board[(2, 3)].unit.effects == set()
    assert g.board[(2, 3)].unit.currenthp == 2 # took 3 damage

def t_WeaponUnstableCannonLowPower():
    "Shoot the Unstable Cannon with no power"
    g = Game()
    for x in range(1, 5):
        g.board[(x, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(2, 1)].unit.currenthp == 3
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from here
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught fire from self-damage
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()  # No new unit effects
    assert g.board[(1, 1)].unit.currenthp == 2  # took 1 self-damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # forest is not on fire
    assert g.board[(4, 1)].unit.effects == set() # vek is not on fire
    assert g.board[(4, 1)].unit.currenthp == 3 # vek took 2 damage

def t_WeaponUnstableCannonPower1():
    "Shoot the Unstable Cannon with first power"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # No new effects
    assert g.board[(1, 1)].unit.currenthp == 1 # took 2 self-damage
    assert g.board[(2, 1)].effects == set() # no tile effects
    assert g.board[(2, 1)].unit == None # wielder pushed from here
    assert g.board[(3, 1)].effects == set() # no tile effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 2 # vek took 3 damage

def t_WeaponUnstableCannonPower2():
    "Shoot the Unstable Cannon with second power"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # No new effects
    assert g.board[(1, 1)].unit.currenthp == 2 # took 1 self-damage
    assert g.board[(2, 1)].effects == set() # no tile effects
    assert g.board[(2, 1)].unit == None # wielder pushed from here
    assert g.board[(3, 1)].effects == set() # no tile effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 2 # vek took 3 damage

def t_WeaponUnstableCannonMaxPower():
    "Shoot the Unstable Cannon with max power"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # No new effects
    assert g.board[(1, 1)].unit.currenthp == 1 # took 2 self-damage
    assert g.board[(2, 1)].effects == set() # no tile effects
    assert g.board[(2, 1)].unit == None # wielder pushed from here
    assert g.board[(3, 1)].effects == set() # no tile effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 1 # vek took 4 damage

def t_WeaponUnstableCannonWielderForest():
    "Shoot the Unstable Cannon with max power with the weapon wielder starting a forest"
    g = Game()
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # No new effects, the wielder does NOT catch on fire because he's pushed off before it happens.
    assert g.board[(1, 1)].unit.currenthp == 1 # took 2 self-damage
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught on fire
    assert g.board[(2, 1)].unit == None # wielder pushed from here
    assert g.board[(3, 1)].effects == set() # no tile effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 1 # vek took 4 damage

def t_WeaponAcidProjector():
    "Shoot the acid projector at a unit."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # not needed here, nothing got hurt.
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].effects == set()  # no tile effects
    assert g.board[(2, 1)].unit == None  # no unit here
    assert g.board[(3, 1)].effects == set()  # no tile effects
    assert g.board[(3, 1)].unit.effects == {Effects.ACID}
    assert g.board[(3, 1)].unit.currenthp == 5

def t_WeaponAcidProjectorShielded():
    "Shoot the acid projector at a shielded unit."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g, effects={Effects.SHIELD}))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # not needed here, nothing got hurt.
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].effects == set()  # no tile effects
    assert g.board[(2, 1)].unit == None  # no unit here
    assert g.board[(3, 1)].effects == set()  # no tile effects
    assert g.board[(3, 1)].unit.effects == {Effects.ACID, Effects.SHIELD} # shield doesn't protect you from acid from this weapon
    assert g.board[(3, 1)].unit.currenthp == 5

def t_WeaponAcidProjectorBumpDeath():
    "Shoot the acid projector at a unit that dies to bump damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g, currenthp=1))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].effects == {Effects.ACID} # dead vek left acid
    assert g.board[(2, 1)].unit == None  # vek died
    assert g.board[(3, 1)].effects == set()  # no tile effects
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.type == 'mountaindamaged'

def t_WeaponRammingSpeedDefault():
    "Fire the RammingSpeed weapon with no powered upgrades"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_RammingSpeed(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder took 0 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 4 # vek pushed here took 1 damage

def t_WeaponRammingSpeedPower1():
    "Fire the RammingSpeed weapon with the first upgrade powered"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_RammingSpeed(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # never was a unit here
    assert g.board[(1, 1)].effects == {Effects.SMOKE} # smoke was farted
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder took 0 damage and didn't move
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 4 # vek pushed here took 1 damage

def t_WeaponRammingSpeedPower2():
    "Fire the RammingSpeed weapon with the second upgrade powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_RammingSpeed(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder took 0 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 2 # vek pushed here took 3 damage

def t_WeaponRammingSpeedFullPower():
    "Fire the RammingSpeed weapon with the both upgrades powered"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_RammingSpeed(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(2, 1)].unit.currenthp == 3
    assert g.board[(3, 1)].unit.currenthp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # never was a unit here
    assert g.board[(1, 1)].effects == {Effects.SMOKE}  # smoke was farted
    assert g.board[(2, 1)].unit.currenthp == 3  # wielder took 0 damage and didn't move
    assert g.board[(3, 1)].unit == None  # vek pushed off this tile
    assert g.board[(4, 1)].unit.currenthp == 2 # vek pushed here took 3 damage

def t_WeaponNeedleShotNoPower():
    "Fire the NeedleShot weapon with the no upgrades powered"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_NeedleShot(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.currenthp == 3 # this vek took 2 damage; 1 from weapon, 1 from bump
    assert g.board[(3, 1)].unit.currenthp == 4 # this one took 1 bump damage
    assert g.board[(4, 1)].unit.currenthp == 5 # this one took none
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None # Nothing got pushed here

def t_WeaponNeedleShot1Power():
    "Fire the NeedleShot weapon with the 1 upgrade powered"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_NeedleShot(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.currenthp == 3 # this vek took 2 damage from weapon, no bump
    assert g.board[(3, 1)].unit.currenthp == 2 # this one took 3 damage; 2 from weapon, 1 from bump
    assert g.board[(4, 1)].unit.currenthp == 4 # this one took 1 bump damage
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None # Nothing got pushed here

def t_WeaponNeedleShot2Power():
    "Fire the NeedleShot weapon with the 2nd upgrade powered. This is no different than just having the first done"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_NeedleShot(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.currenthp == 3 # this vek took 2 damage from weapon, no bump
    assert g.board[(3, 1)].unit.currenthp == 2 # this one took 3 damage; 2 from weapon, 1 from bump
    assert g.board[(4, 1)].unit.currenthp == 4 # this one took 1 bump damage
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None # Nothing got pushed here

def t_WeaponNeedleShotFullPower():
    "Fire the NeedleShot weapon with full upgrade power."
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_NeedleShot(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 3
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.currenthp == 2 # this vek took 3 damage from weapon, no bump
    assert g.board[(3, 1)].unit.currenthp == 2 # this one took 3 damage from weapon
    assert g.board[(4, 1)].unit == None # last vek got pushed from here
    assert g.board[(4, 1)].effects == {Effects.FIRE}  # forest is on fire
    assert g.board[(5, 1)].unit.currenthp == 2 # this one took 3 damage from weapon
    assert g.board[(5, 1)].unit.effects == set() # the vek didn't catch on fire

def t_WeaponExplosiveGooNoPower():
    "Fire the NeedleShot weapon with no upgrade power."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_Alpha_Scorpion(g))
    # replace one with our boi
    g.board[(1, 3)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_ExplosiveGoo(power1=False, power2=False)))
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # RIGHT, 3
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(1, 3)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 3)].unit.effects == set() # no unit effects
    del allunits[(1, 3)]  # delete the wielder from allunits
    assert g.board[(4, 3)].unit.currenthp == 4  # target took 1 damage
    del allunits[(4, 3)]  # delete the target unit from all
    assert g.board[(3, 3)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(3, 3)]  # delete this bumped  unit from all
    assert g.board[(2, 3)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(2, 3)]  # delete this bumped  unit from all
    assert g.board[(4, 4)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(4, 4)]  # delete this bumped  unit from all
    assert g.board[(4, 5)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(4, 5)]  # delete this bumped  unit from all
    assert g.board[(5, 3)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(5, 3)]  # delete this bumped  unit from all
    assert g.board[(6, 3)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(6, 3)]  # delete this bumped  unit from all
    assert g.board[(4, 2)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(4, 2)]  # delete this bumped  unit from all
    assert g.board[(4, 1)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(4, 1)]  # delete this bumped  unit from all
    for u in allunits:
        assert g.board[u].unit.currenthp == 5 # no hp change to all other vek

def t_WeaponExplosiveGooPower2():
    "Fire the NeedleShot weapon with extra damage powered."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_Alpha_Scorpion(g))
    # replace one with our boi
    g.board[(1, 3)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_ExplosiveGoo(power1=False, power2=True)))
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # RIGHT, 3
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(1, 3)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 3)].unit.effects == set() # no unit effects
    del allunits[(1, 3)]  # delete the wielder from allunits
    assert g.board[(4, 3)].unit.currenthp == 2  # target took 3 damage
    del allunits[(4, 3)]  # delete the target unit from all
    assert g.board[(3, 3)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(3, 3)]  # delete this bumped  unit from all
    assert g.board[(2, 3)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(2, 3)]  # delete this bumped  unit from all
    assert g.board[(4, 4)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(4, 4)]  # delete this bumped  unit from all
    assert g.board[(4, 5)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(4, 5)]  # delete this bumped  unit from all
    assert g.board[(5, 3)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(5, 3)]  # delete this bumped  unit from all
    assert g.board[(6, 3)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(6, 3)]  # delete this bumped  unit from all
    assert g.board[(4, 2)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(4, 2)]  # delete this bumped  unit from all
    assert g.board[(4, 1)].unit.currenthp == 4  #  took 1 bump damage
    del allunits[(4, 1)]  # delete this bumped  unit from all
    for u in allunits:
        assert g.board[u].unit.currenthp == 5 # no hp change to all other vek

def t_WeaponExplosiveGooPower1():
    "Fire the NeedleShot weapon with extra tile powered."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_Alpha_Scorpion(g))
    # replace one with our boi
    g.board[(1, 3)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_ExplosiveGoo(power1=True, power2=False)))
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # RIGHT, 3
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(1, 3)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 3)].unit.effects == set() # no unit effects
    del allunits[(1, 3)]  # delete the wielder from allunits
    assert g.board[(4, 3)].unit.currenthp == 4  # target took 1 damage
    del allunits[(4, 3)]  # delete the target unit from all
    assert g.board[(5, 3)].unit.currenthp == 4  # 2nd target took 1 normal damage
    del allunits[(5, 3)]  # delete the target unit from all
    assert g.board[(2, 3)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(2, 3)] # delete this bumped unit from all
    assert g.board[(3, 3)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(3, 3)] # delete this bumped unit from all
    assert g.board[(4, 4)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(4, 4)] # delete this bumped unit from all
    assert g.board[(4, 5)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(4, 5)] # delete this bumped unit from all
    assert g.board[(5, 4)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(5, 4)] # delete this bumped unit from all
    assert g.board[(5, 5)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(5, 5)] # delete this bumped unit from all
    assert g.board[(6, 3)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(6, 3)] # delete this bumped unit from all
    assert g.board[(7, 3)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(7, 3)] # delete this bumped unit from all
    assert g.board[(5, 2)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(5, 2)] # delete this bumped unit from all
    assert g.board[(5, 1)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(5, 1)] # delete this bumped unit from all
    assert g.board[(4, 2)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(4, 2)] # delete this bumped unit from all
    assert g.board[(4, 1)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(4, 1)] # delete this bumped unit from all
    for u in allunits:
        assert g.board[u].unit.currenthp == 5 # no hp change to all other vek

def t_WeaponExplosiveGooFullPower():
    "Fire the NeedleShot weapon with full power."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_Alpha_Scorpion(g))
    # replace one with our boi
    g.board[(1, 3)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_ExplosiveGoo(power1=True, power2=True)))
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # RIGHT, 3
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(1, 3)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 3)].unit.effects == set() # no unit effects
    del allunits[(1, 3)]  # delete the wielder from allunits
    assert g.board[(4, 3)].unit.currenthp == 2  # target took 3 damage
    del allunits[(4, 3)]  # delete the target unit from all
    assert g.board[(5, 3)].unit.currenthp == 2  # 2nd target took 3 normal damage
    del allunits[(5, 3)]  # delete the target unit from all
    assert g.board[(2, 3)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(2, 3)] # delete this bumped unit from all
    assert g.board[(3, 3)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(3, 3)] # delete this bumped unit from all
    assert g.board[(4, 4)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(4, 4)] # delete this bumped unit from all
    assert g.board[(4, 5)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(4, 5)] # delete this bumped unit from all
    assert g.board[(5, 4)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(5, 4)] # delete this bumped unit from all
    assert g.board[(5, 5)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(5, 5)] # delete this bumped unit from all
    assert g.board[(6, 3)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(6, 3)] # delete this bumped unit from all
    assert g.board[(7, 3)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(7, 3)] # delete this bumped unit from all
    assert g.board[(5, 2)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(5, 2)] # delete this bumped unit from all
    assert g.board[(5, 1)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(5, 1)] # delete this bumped unit from all
    assert g.board[(4, 2)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(4, 2)] # delete this bumped unit from all
    assert g.board[(4, 1)].unit.currenthp == 4 # unit took 1 bump damage
    del allunits[(4, 1)] # delete this bumped unit from all
    for u in allunits:
        assert g.board[u].unit.currenthp == 5 # no hp change to all other vek

def t_WeaponSidewinderFistNoPower():
    "Fire Sidewinder fist with no power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=False, power2=False)))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # UP, 1
    g.flushHurt()
    for sq in (2, 1), (2, 2), (1, 2):
        print(g.board[sq])
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(2, 2)].unit == None  # target pushed off this tile
    assert g.board[(1, 2)].unit.currenthp == 3  # target took 2 damage

def t_WeaponSidewinderFistPower1():
    "Fire Sidewinder fist with 1 power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=True, power2=False)))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # UP, 1
    g.flushHurt()
    for sq in (2, 1), (2, 2), (1, 2):
        print(g.board[sq])
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(2, 2)].unit == None  # target pushed off this tile
    assert g.board[(1, 2)].unit.currenthp == 2  # target took 3 damage

def t_WeaponSidewinderFistPower2():
    "Fire Sidewinder fist with the other 1 power (no difference)."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=False, power2=True)))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # UP, 1
    g.flushHurt()
    for sq in (2, 1), (2, 2), (1, 2):
        print(g.board[sq])
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(2, 2)].unit == None  # target pushed off this tile
    assert g.board[(1, 2)].unit.currenthp == 2  # target took 3 damage

def t_WeaponSidewinderFistFullPower():
    "Fire Sidewinder fist with the full power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=True, power2=True)))
    g.board[(2, 2)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # UP, 1
    g.flushHurt()
    assert g.board[(2, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(2, 2)].unit == None  # target pushed off this tile
    assert g.board[(1, 2)].unit.currenthp == 1  # target took 4 damage

def t_WeaponSidewinderFistFullPowerDash():
    "Fire Sidewinder fist with the full power at a different angle and with the dash."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # wielder moved from this square
    assert g.board[(3, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(3, 1)].unit.effects == set() # no unit effects
    assert g.board[(4, 1)].unit == None  # target pushed off this tile
    assert g.board[(4, 2)].unit.currenthp == 1  # target took 4 damage

def t_WeaponRocketFistNoPower():
    "Fire RocketFist with the no power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RocketFist(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from starting square
    assert g.board[(1, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(3, 1)].unit == None  # target pushed from here
    assert g.board[(4, 1)].unit.currenthp == 3  # target took 2 damage
    assert g.board[(4, 1)].unit.effects == set()  # no new effects

def t_WeaponRocketFist2ndPower():
    "Fire RocketFist with extra damage powered."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RocketFist(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from starting square
    assert g.board[(1, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(3, 1)].unit == None  # target pushed from here
    assert g.board[(4, 1)].unit.currenthp == 1  # target took 4 damage
    assert g.board[(4, 1)].unit.effects == set()  # no new effects

def t_WeaponRocketFist1stPower():
    "Fire RocketFist with rocket projectile powered."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RocketFist(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from starting square
    assert g.board[(1, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(4, 1)].unit == None  # target pushed from here
    assert g.board[(5, 1)].unit.currenthp == 3  # target took 2 damage
    assert g.board[(5, 1)].unit.effects == set()  # no new effects

def t_WeaponRocketFistFullPower():
    "Fire RocketFist with full power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RocketFist(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from starting square
    assert g.board[(1, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(4, 1)].unit == None  # target pushed from here
    assert g.board[(5, 1)].unit.currenthp == 1  # target took 4 damage
    assert g.board[(5, 1)].unit.effects == set()  # no new effects

def t_WeaponExplosiveVentsNoPower():
    "Shoot explosive vents with no power."
    g = Game()
    g.board[(1, 2)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ExplosiveVents(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # () no choice!
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 1)].effects == set()  # wielder's tile untouched
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].unit == None  # never was a unit here
    assert g.board[(1, 2)].effects == {Effects.SMOKE} # sand was hit
    assert g.board[(2, 1)].unit == None  # target pushed from here
    assert g.board[(3, 1)].unit.currenthp == 4  # target took 1 damage
    assert g.board[(3, 1)].unit.effects == set()  # no new effects

def t_WeaponExplosiveVents1Power():
    "Shoot explosive vents with 1 power."
    g = Game()
    g.board[(1, 2)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ExplosiveVents(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # () no choice!
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 1)].effects == set()  # wielder's tile untouched
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].unit == None  # never was a unit here
    assert g.board[(1, 2)].effects == {Effects.SMOKE} # sand was hit
    assert g.board[(2, 1)].unit == None  # target pushed from here
    assert g.board[(3, 1)].unit.currenthp == 3  # target took 2 damage
    assert g.board[(3, 1)].unit.effects == set()  # no new effects

def t_WeaponExplosiveVents2ndPower():
    "Shoot explosive vents with 2nd power."
    g = Game()
    g.board[(1, 2)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ExplosiveVents(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # () no choice!
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 1)].effects == set()  # wielder's tile untouched
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].unit == None  # never was a unit here
    assert g.board[(1, 2)].effects == {Effects.SMOKE} # sand was hit
    assert g.board[(2, 1)].unit == None  # target pushed from here
    assert g.board[(3, 1)].unit.currenthp == 3  # target took 2 damage
    assert g.board[(3, 1)].unit.effects == set()  # no new effects

def t_WeaponExplosiveVentsMaxPower():
    "Shoot explosive vents with max power."
    g = Game()
    g.board[(1, 2)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ExplosiveVents(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # () no choice!
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # wielder took no damage
    assert g.board[(1, 1)].effects == set()  # wielder's tile untouched
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].unit == None  # never was a unit here
    assert g.board[(1, 2)].effects == {Effects.SMOKE} # sand was hit
    assert g.board[(2, 1)].unit == None  # target pushed from here
    assert g.board[(3, 1)].unit.currenthp == 2  # target took 3 damage
    assert g.board[(3, 1)].unit.effects == set()  # no new effects

def t_weaponPrimeSpearNoPower():
    "Fire the PrimeSpear weapon with the no upgrades powered"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.currenthp == 3 # this vek took 2 damage; 2 from weapon, 0 from bump
    assert g.board[(3, 1)].unit.currenthp == 2 # this one took 3 damage, 2 weapon, 1 bump damage
    assert g.board[(3, 1)].effects == set() # this tile didn't get acid
    assert g.board[(3, 1)].unit.effects == set()  # this unit didn't get acid
    assert g.board[(4, 1)].unit.currenthp == 4 # this one took 1 bump damage
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None # Nothing got pushed here

def t_weaponPrimeSpear1Power():
    "Fire the PrimeSpear weapon with the 1 upgrade powered"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].effects == set()  # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit.currenthp == 3  # this vek took 2 damage; 2 from weapon, 0 from bump
    assert g.board[(3, 1)].unit.currenthp == 2  # this one took 3 damage, 2 weapon, 1 bump damage
    assert g.board[(3, 1)].effects == set()  # this tile didn't get acid
    assert g.board[(3, 1)].unit.effects == {Effects.ACID}  # this unit DID get acid
    assert g.board[(4, 1)].unit.currenthp == 4  # this one took 1 bump damage
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None  # Nothing got pushed here

def t_weaponPrimeSpear2Power():
    "Fire the PrimeSpear weapon with the 2nd upgrade powered. This increases range."
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].effects == set()  # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 3
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit.currenthp == 3  # this vek took 2 damage; 2 from weapon, 0 from bump
    assert g.board[(3, 1)].unit.currenthp == 3  # this one took 2 damage, 2 weapon, 0 bump damage
    assert g.board[(3, 1)].effects == set()  # this tile didn't get acid
    assert g.board[(3, 1)].unit.effects == set()  # this unit didn't get acid
    assert g.board[(4, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == {Effects.FIRE} # forest is FIRE
    assert g.board[(5, 1)].unit.currenthp == 3  # this one took 2 damage; 2 weapon, 0 bump damage
    assert g.board[(5, 1)].unit.effects == set() # no acid here

def t_weaponPrimeSpearFullPower():
    "Fire the PrimeSpear weapon with full upgrade power."
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Alpha_Scorpion(g))
    assert g.board[(1, 1)].unit.currenthp == 2
    assert g.board[(2, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.currenthp == 5
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.currenthp == 5
    assert g.board[(4, 1)].effects == set()  # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 3
    g.flushHurt()
    assert g.board[(1, 1)].unit.currenthp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit.currenthp == 3  # this vek took 2 damage; 2 from weapon, 0 from bump
    assert g.board[(3, 1)].unit.currenthp == 3  # this one took 2 damage, 2 weapon, 0 bump damage
    assert g.board[(3, 1)].effects == set()  # this tile didn't get acid
    assert g.board[(3, 1)].unit.effects == set()  # this unit didn't get acid
    assert g.board[(4, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == {Effects.FIRE} # forest is FIRE
    assert g.board[(5, 1)].unit.currenthp == 3  # this one took 2 damage; 2 weapon, 0 bump damage
    assert g.board[(5, 1)].unit.effects == {Effects.ACID} # this unit did get acid

########### write tests for these:
# shielded blobber bombs still explode normally
# If a huge charging vek like the beetle leader is on fire and charges over water, he remains on fire.
# mech corpses that fall into chasms cannot be revived.

########## special objective units:
# Satellite Rocket: 2 hp, Not powered, Smoke Immune, stable, "Satellite Launch" weapon kills nearby tiles when it launches.
# Train: 1 hp, Fire immune, smoke immune, stable, "choo choo" weapon move forward 2 spaces but will be destroyed if blocked. kills whatever unit it runs into, stops dead on the tile before that unit. It is multi-tile, shielding one tile shields both.
    # when attacked and killed, becomes a "damaged train" that is also stable and fire immune. When that is damaged again, it becomes a damaged train corpse that can't be shielded, is no longer fire immune, and is flying like a normal corpse.
    # units can bump into the corpse
# ACID Launcher: 2 hp, stable. weapon is "disentegrator": hits 5 tiles killing anything present and leaves acid on them.


########## Weapons stuff for later
# rocks thrown at sand tiles do not create smoke. This means that rocks do damage to units but not tiles at all.
########### write tests for these:
# shielded blobber bombs still explode normally
# If a huge charging vek like the beetle leader is on fire and charges over water, he remains on fire.
# mech corpses that fall into chasms cannot be revived.
# if a vek with acid is on a forest and is then hit with an airstrike, the tile is damaged and catches fire, then the unit dies leaving its acid and removing the fire and forest.

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
# what happens if lightning strikes a sand or forest tile with a vek with acid on it? Does it create smoke first, then kill the enemy, then drop the acid and convert the tile to a regular ground tile? Or does the acid drop first converting the tiel before it does anything?
# Can mech corpses be revived after falling into a chasm?

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
    testTheTests()
