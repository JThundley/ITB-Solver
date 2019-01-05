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
        elif line.strip().startswith('print') and funcname.startswith('t_'):
            print("#%s print statment left in" % lineno, funcname)

def t_BumpDamage():
    "2 units bump into each other and take 1 damage each."
    g = Game()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    g.board[(2, 1)].createUnitHere(Unit_AlphaBeetle(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit.hp == 5
    g.board[(2, 1)].push(Direction.LEFT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 4

def t_BumpDamageOnForestNoFire():
    "2 units bump into each other on a forest the forest does NOT catch fire."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    g.board[(2, 1)].createUnitHere(Unit_AlphaBeetle(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit.hp == 5
    g.board[(2, 1)].push(Direction.LEFT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 4
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
    assert g.board[(1, 1)].unit.hp == 3
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
    g.board[(2, 1)].createUnitHere(Unit_BeetleLeader(g)) # massive unit on the bottom next to the water tile
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
    g.board[(1, 2)].createUnitHere(Unit_BeetleLeader(g))
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
    g.board[(1, 2)].createUnitHere(Unit_BeetleLeader(g))
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
    g.board[(1, 2)].createUnitHere(Unit_BeetleLeader(g))
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
    g.board[(1, 2)].createUnitHere(Unit_BeetleLeader(g))
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
    g.board[(2, 1)].createUnitHere(Unit_LargeGoo(g))
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

def t_ShieldBlocksDirectIceFromFire():
    "What happens when a unit is set on fire, shielded, then frozen? Ice has no effect, unit remains shielded and on fire. Tile remains on fire. Here, ice is given directly to the unit."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Blobber(g))
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].applyFire()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    g.board[(1, 1)].applyShield()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.SHIELD}
    g.board[(1, 1)].unit.applyIce()
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
    g.board[(1, 1)].createUnitHere(Unit_HornetLeader(g)) # they instantly swap
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
    assert g.board[(8, 3)].unit.hp == 1
    assert g.board[(8, 4)].unit.hp == 1
    g.board[(8, 4)].takeDamage(1)
    g.flushHurt()
    assert g.board[(8, 3)].unit.type == 'volcano'
    assert g.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 7):
            assert g.board[(x, y)].type == 'water'

def t_DamDiesInstantDeath():
    "In this test, we kill one with an instakill and make sure they both die and flood the map."
    g = Game()
    g.board[(8, 3)].replaceTile(Tile_Water(g))
    g.board[(8, 4)].replaceTile(Tile_Water(g))
    g.board[(8, 3)].createUnitHere(Unit_Dam(g))
    g.board[(8, 4)].createUnitHere(Unit_Dam(g))
    g.board[(7, 4)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SelfDestruct()))  # power is ignored
    assert g.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(8, 4)].effects == {Effects.SUBMERGED}
    assert g.board[(7, 3)].effects == set() # the tiles next to the dam are normal
    assert g.board[(7, 4)].effects == set()
    gs = g.board[(7, 4)].unit.weapon1.genShots()
    g.board[(7, 4)].unit.weapon1.shoot(*next(gs))
    g.flushHurt()
    assert g.board[(8, 3)].unit.type == 'volcano'
    assert g.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 7):
            assert g.board[(x, y)].type == 'water'

def t_DamDiesInstantDeathWebbed():
    "In this test, we kill one with an instakill and make sure they both die and flood the map except it's webbed."
    g = Game()
    g.board[(8, 3)].replaceTile(Tile_Water(g))
    g.board[(8, 4)].replaceTile(Tile_Water(g))
    g.board[(8, 3)].createUnitHere(Unit_Dam(g))
    g.board[(8, 4)].createUnitHere(Unit_Dam(g))
    g.board[(7, 4)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SelfDestruct()))  # power is ignored
    g.board[(7, 4)].unit._makeWeb((8, 4))
    assert g.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(8, 4)].effects == {Effects.SUBMERGED}
    assert g.board[(7, 3)].effects == set() # the tiles next to the dam are normal
    assert g.board[(7, 4)].effects == set()
    gs = g.board[(7, 4)].unit.weapon1.genShots()
    g.board[(7, 4)].unit.weapon1.shoot(*next(gs))
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
    assert g.board[(8, 3)].unit.hp == 1
    assert g.board[(8, 4)].unit.hp == 1
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
    assert g.board[(8, 3)].unit.hp == 1
    assert g.board[(8, 4)].unit.hp == 1
    g.board[(8, 4)].takeDamage(1)
    assert g.board[(8, 3)].unit.type == 'volcano'
    assert g.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 8):
            assert g.board[(x, y)].type == 'water'
    g.flushHurt()
    assert g.board[(7, 3)].effects == {Effects.ACID, Effects.SUBMERGED} # the acid on the ground left acid in the water
    assert g.board[(7, 4)].effects == {Effects.SUBMERGED} # this tile never got acid

def t_DamDiesFromElectricWhip():
    "In this test, we kill the dam by chaning the electric whip through it."
    g = Game()
    g.board[(8, 3)].replaceTile(Tile_Water(g))
    g.board[(8, 4)].replaceTile(Tile_Water(g))
    g.board[(8, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(8, 5)].createUnitHere(Unit_Mountain(g))
    g.board[(8, 3)].createUnitHere(Unit_Dam(g))
    g.board[(8, 4)].createUnitHere(Unit_Dam(g))
    g.board[(7, 4)].createUnitHere(Unit_Scorpion(g))
    g.board[(7, 5)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_ElectricWhip()))
    assert g.board[(8, 3)].effects == {Effects.SUBMERGED}
    assert g.board[(8, 4)].effects == {Effects.SUBMERGED}
    gs = g.board[(7, 5)].unit.weapon1.genShots()
    for i in range(3):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(7, 5)].unit.weapon1.shoot(*shot)  # (Direction.DOWN,)
    g.flushHurt()
    assert g.board[(8, 3)].unit.type == 'volcano'
    assert g.board[(8, 4)].unit.type == 'volcano'
    for y in (3, 4):
        for x in range(1, 8):
            assert g.board[(x, y)].type == 'water'
    g.flushHurt()
    assert g.board[(7, 3)].effects == {Effects.SUBMERGED} # the acid on the ground left acid in the water
    assert g.board[(7, 4)].effects == {Effects.SUBMERGED} # this tile never got acid

# I don't think this is true and was created under a mistaken understanding.
# My guess is that I tested this out with the acid projector before I realized that the weapon gives targets acid regardless of shield.
# By my estimation, the only way the dam can get acid is from an acid weapon which ignores the shield in the case of the acid projector
# and the vek weapons that give acid also do damage which remove the shield. The Dam can't move so it can't get acid from a tile
# def t_ShieldedDamHitWithAcidGetsAcid():
#     "If the dam is shielded and then hit with acid, it's immediately inflicted with acid."
#     g = Game()
#     g.board[(8, 3)].replaceTile(Tile_Water(g))
#     g.board[(8, 4)].replaceTile(Tile_Water(g))
#     g.board[(8, 3)].createUnitHere(Unit_Dam(g))
#     g.board[(8, 4)].createUnitHere(Unit_Dam(g))
#     g.board[(8, 4)].applyShield()
#     assert g.board[(8, 3)].unit.effects == {Effects.SHIELD}
#     assert g.board[(8, 4)].unit.effects == {Effects.SHIELD}
#     g.board[(8, 3)].applyAcid()
#     g.flushHurt()
#     assert g.board[(8, 3)].unit.effects == {Effects.SHIELD, Effects.ACID}
#     assert g.board[(8, 4)].unit.effects == {Effects.SHIELD, Effects.ACID}

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

def t_ShieldedUnitDoesntGetAcidFromWater():
    "if a non-flying shielded unit goes into acid water, it doesn't get acid"
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(2, 1)].createUnitHere(Unit_ScorpionLeader(g))
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
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD,} # Shielded with no acid
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
    assert g.board[(1, 1)].unit.hp == 2
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE, Effects.ACID}
    assert g.board[(1, 1)].unit.hp == 2
    g.board[(1, 1)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3

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
    assert g.board[(1, 1)].unit.hp == 2
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].type == 'ice'
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}
    assert g.board[(1, 1)].unit.hp == 2
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ICE, Effects.ACID}
    assert g.board[(1, 1)].unit.hp == 2
    g.board[(1, 1)].repair(1)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3

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
    g.board[(1, 2)].createUnitHere(Unit_Scorpion(g))
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
    assert g.board[(1, 1)].unit.hp == 1

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
    assert g.board[(1, 1)].unit.hp == 1 # the repair worked properly

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
    g.board[(3, 1)].createUnitHere(Unit_BloodPsion(g))
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
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_BlastPsion(g))
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
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_PsionTyrant(g))
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
    g.board[(2, 1)].createUnitHere(Unit_AlphaFirefly(g))
    g.board[(2, 1)].applyFire()
    g.board[(3, 1)].createUnitHere(Unit_HornetLeader(g))
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
    g.board[(3, 1)].createUnitHere(Unit_ScorpionLeader(g))
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
    assert g.board[(1, 1)].unit.hp == 1 # mech took bump damage
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit == None # he died from the bump
    assert g.board[(3, 1)].effects == {Effects.SMOKE} # smoke remains
    assert g.board[(3, 1)].unit.hp == 6
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.hp == 1 # corpse didn't take damage
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
    g.board[(3, 1)].createUnitHere(Unit_BloodPsion(g))
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
    g.board[(1, 7)].createUnitHere(Unit_SpiderLeader(g))
    g.board[(1, 8)].createUnitHere(Unit_BloodPsion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 2)].unit.hp == 4
    assert g.board[(1, 7)].unit.hp == 6
    assert g.board[(1, 8)].unit.hp == 2
    g.environeffect.run()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # meteor got pushed off this tile
    assert g.board[(1, 2)].unit.hp == 3 # meteor still has 3 hp
    assert g.board[(1, 3)].unit.hp == 4 # beetle took no damage as well
    assert g.board[(1, 7)].unit.hp == 5 # spider leader took a bump when he was pushed into the blood psion, so he didn't move
    assert g.board[(1, 8)].unit.hp == 1 # blood psion tried to get pushed off the board so he stayed put and got bumped

def t_WeaponTitanFistFirst():
    "My very first weapon test. Have a mech punch another!"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist()))
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit == None # judo was pushed off this square
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 2 # he only lost 1 health because of armor

def t_WeaponTitanFistChargeSecond():
    "My very second weapon test. Have a mech dash punch another!"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power1=True)))
    g.board[(6, 1)].createUnitHere(Unit_Judo_Mech(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(6, 1)].effects == set()
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(6, 1)].unit.hp == 3
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None # Combat dashed off of this tile
    assert g.board[(5, 1)].unit.effects == set() # and he's now here
    assert g.board[(5, 1)].unit.hp == 3
    assert g.board[(6, 1)].unit == None # judo was pushed off this square
    assert g.board[(7, 1)].effects == set() # and he's here now
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(7, 1)].unit.hp == 2 # he only lost 1 health because of armor

def t_WeaponTitanFistChargeToEdge():
    "When you charge to the edge of the map without hitting a unit, you do NOT attack the tile at the edge like a projectile does."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power1=True)))
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(8, 1)].effects == set()
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].type == 'forest'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # he's not here anymore
    assert g.board[(8, 1)].effects == set() # still no fire
    assert g.board[(8, 1)].unit.effects == set() # no change
    assert g.board[(8, 1)].unit.hp == 3 # no change
    assert g.board[(8, 1)].type == 'forest'

def t_WeaponTitanFistIceOnIce():
    "if you punch a frozen unit on an ice tile, the ice tile isn't damaged."
    g = Game()
    g.board[(2, 1)].replaceTile(Tile_Ice(g))
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist()))
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, effects={Effects.ICE}))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}
    assert g.board[(2, 1)].unit.hp == 3
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit == None # judo was pushed off this square
    assert g.board[(2, 1)].type == 'ice' # tile wasn't damaged
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 3 # he only lost 0 health because of ice

def t_WeaponTitanFistIceBumpDamage():
    "If a unit is frozen and damaged and bumped against a wall, the damage removes the ice and then the bump damage hurts the unit."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist()))
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, effects={Effects.ICE}, attributes={Attributes.ARMORED}))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}
    assert g.board[(2, 1)].unit.attributes == {Attributes.ARMORED, Attributes.MASSIVE}
    assert g.board[(2, 1)].unit.hp == 3
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT) # POW RIGHT INDA KISSAH
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit.hp == 2 # judo had ice broken by fist damage, then took 1 bump damage which bypassed the armor
    assert g.board[(2, 1)].unit.effects == set() # ice is gone
    assert g.board[(2, 1)].unit.attributes == {Attributes.ARMORED, Attributes.MASSIVE} # this hasn't changed

def t_HurtAndPushedVekOnFireSetsForestOnFire():
    "This is testing the concept of the vek corpse. A vek is lit on fire, and then punched for 4 damage so it's killed, but it's fake corpse is pushed to a forest tile and sets it on fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g, effects={Effects.FIRE}))
    g.board[(3, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'forest'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
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
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.hp == 2
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'forest'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
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
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].effects == {Effects.MINE}
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'ground'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set() # still no effects here
    assert g.board[(2, 1)].unit == None # firefly was pushed off this tile
    assert g.board[(3, 1)].effects == set() # mine is gone
    assert g.board[(3, 1)].unit == None # The firefly died after we did a strong 4 damage punch
    assert g.board[(3, 1)].type == 'ground' # still a forest? lol

def t_HurtAndPushedVekDoesntRemovePod():
    "This is also testing the concept of the vek corpse. A vek is punched for 4 damage so it's killed, but its fake corpse is pushed to a tile with a timepod. The timepod is NOT trampled and removed."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Combat_Mech(g, weapon1=Weapon_TitanFist(power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g))
    g.board[(3, 1)].effects.add(Effects.TIMEPOD)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].effects == {Effects.TIMEPOD}
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'ground'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set() # still no effects here
    assert g.board[(2, 1)].unit == None # firefly was pushed off this tile
    assert g.board[(3, 1)].effects == {Effects.TIMEPOD} # timepod is still there
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
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].effects == {Effects.FREEZEMINE}
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].type == 'ground'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no change for punchbot
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
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
    assert g.board[(1, 1)].unit.hp == 3
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
    assert g.board[(1, 1)].unit.hp == 3
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
        g.board[(x, 1)].createUnitHere(Unit_SpiderLeader(g))
    g.board[(7, 1)].createUnitHere(Unit_Mountain(g)) # a mountain to block it
    g.board[(8, 1)].createUnitHere(Unit_SpiderLeader(g)) # and a spider boss on the other side which should stay safe
    for y in range(2, 7):
        g.board[(3, y)].createUnitHere(Unit_SpiderLeader(g)) # start branching vertically
    g.board[(3, 7)].createUnitHere(Unit_Building(g))  # a building to block it
    g.board[(3, 8)].createUnitHere(Unit_SpiderLeader(g)) # and another spider boss on the other side which should also stay safe
    assert g.board[(1, 1)].unit.hp == 3 # lightning mech
    assert g.board[(2, 1)].unit.hp == 6 # spider bosses
    assert g.board[(3, 1)].unit.hp == 6
    assert g.board[(4, 1)].unit.hp == 6
    assert g.board[(5, 1)].unit.hp == 6
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(3, 2)].unit.hp == 6
    assert g.board[(3, 3)].unit.hp == 6
    assert g.board[(3, 4)].unit.hp == 6
    assert g.board[(3, 5)].unit.hp == 6
    assert g.board[(3, 6)].unit.hp == 6
    assert g.board[(7, 1)].unit.type == 'mountain'
    assert g.board[(3, 7)].unit.type == 'building'
    assert g.board[(8, 1)].unit.hp == 6 # safe spider 1
    assert g.board[(3, 8)].unit.hp == 6  # safe spider 2
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # lightning mech untouched
    assert g.board[(2, 1)].unit.hp == 4  # spider bosses lose 2 hp
    assert g.board[(3, 1)].unit.hp == 4
    assert g.board[(4, 1)].unit.hp == 4
    assert g.board[(5, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.hp == 4
    assert g.board[(3, 2)].unit.hp == 4
    assert g.board[(3, 3)].unit.hp == 4
    assert g.board[(3, 4)].unit.hp == 4
    assert g.board[(3, 5)].unit.hp == 4
    assert g.board[(3, 6)].unit.hp == 4
    assert g.board[(7, 1)].unit.type == 'mountain'
    assert g.board[(3, 7)].unit.type == 'building'
    assert g.board[(8, 1)].unit.hp == 6  # safe spider 1
    assert g.board[(3, 8)].unit.hp == 6  # safe spider 2

def t_WeaponElectricWhipBuildingChainHighPower():
    "Shoot the electric whip with extra damage powered and make sure it goes through units it should and not through units it shouldn't."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Lightning_Mech(g, weapon1=Weapon_ElectricWhip(power1=True)))
    for x in range(2, 7): # spider bosses on x tiles 2-6
        g.board[(x, 1)].createUnitHere(Unit_SpiderLeader(g))
    g.board[(7, 1)].createUnitHere(Unit_Mountain(g)) # a mountain to block it
    g.board[(8, 1)].createUnitHere(Unit_SpiderLeader(g)) # and a spider boss on the other side which should stay safe
    for y in range(2, 7):
        g.board[(3, y)].createUnitHere(Unit_SpiderLeader(g)) # start branching vertically
    g.board[(3, 7)].createUnitHere(Unit_Building(g))  # a building to block it
    g.board[(3, 8)].createUnitHere(Unit_SpiderLeader(g)) # and another spider boss on the other side which should also stay safe
    assert g.board[(1, 1)].unit.hp == 3 # lightning mech
    assert g.board[(2, 1)].unit.hp == 6 # spider bosses
    assert g.board[(3, 1)].unit.hp == 6
    assert g.board[(4, 1)].unit.hp == 6
    assert g.board[(5, 1)].unit.hp == 6
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(3, 2)].unit.hp == 6
    assert g.board[(3, 3)].unit.hp == 6
    assert g.board[(3, 4)].unit.hp == 6
    assert g.board[(3, 5)].unit.hp == 6
    assert g.board[(3, 6)].unit.hp == 6
    assert g.board[(7, 1)].unit.type == 'mountain'
    assert g.board[(3, 7)].unit.type == 'building'
    assert g.board[(8, 1)].unit.hp == 6 # safe spider 1
    assert g.board[(3, 8)].unit.hp == 6  # building chain  spider 2
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # lightning mech untouched
    assert g.board[(2, 1)].unit.hp == 4  # spider bosses lose 2 hp
    assert g.board[(3, 1)].unit.hp == 4
    assert g.board[(4, 1)].unit.hp == 4
    assert g.board[(5, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.hp == 4
    assert g.board[(3, 2)].unit.hp == 4
    assert g.board[(3, 3)].unit.hp == 4
    assert g.board[(3, 4)].unit.hp == 4
    assert g.board[(3, 5)].unit.hp == 4
    assert g.board[(3, 6)].unit.hp == 4
    assert g.board[(7, 1)].unit.type == 'mountain'
    assert g.board[(3, 7)].unit.type == 'building'
    assert g.board[(8, 1)].unit.hp == 6  # safe spider 1
    assert g.board[(3, 8)].unit.hp == 4  # building chain spider 2 took damage

def t_WeaponElectricWhipDoesntChainInCicle():
    "Shoot the electric whip with the power2 extra damage and make sure we don't loop through the weaponwielder"
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Lightning_Mech(g, weapon1=Weapon_ElectricWhip(power2=True)))
    g.board[(1, 1)].createUnitHere(Unit_SpiderLeader(g)) # shocked spider
    g.board[(2, 1)].createUnitHere(Unit_SpiderLeader(g))  # shocked spider
    g.board[(1, 2)].createUnitHere(Unit_SpiderLeader(g))  # shocked spider
    g.board[(2, 3)].createUnitHere(Unit_SpiderLeader(g))  # undamaged spider
    assert g.board[(2, 2)].unit.hp == 3 # lightning mech
    assert g.board[(1, 1)].unit.hp == 6 # spider bosses
    assert g.board[(2, 1)].unit.hp == 6
    assert g.board[(1, 2)].unit.hp == 6
    assert g.board[(2, 3)].unit.hp == 6
    g.board[(2, 2)].unit.weapon1.shoot(Direction.DOWN)
    g.flushHurt()
    assert g.board[(2, 2)].unit.hp == 3  # lightning mech
    assert g.board[(1, 1)].unit.hp == 3  # spider bosses took 3 damage
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(2, 3)].unit.hp == 6 # this one didn't get hit because we can't chain back through the wielder

def t_WeaponArtemisArtilleryDefault():
    "Do the default power Artillery demo from the game when you mouseover the weapon."
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery()))
    g.board[(3, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g)) # this one is actually against the wall and cannot be pushed
    g.board[(4, 3)].createUnitHere(Unit_AlphaScorpion(g)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert g.board[(2, 2)].unit.hp == 2
    assert g.board[(3, 2)].unit.hp == 1
    assert g.board[(4, 2)].unit.hp == 5
    assert g.board[(5, 2)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 3)].unit.hp == 5
    gs = g.board[(2, 2)].unit.weapon1.genShots()
    for i in range(6):
        shot = next(gs) # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 2)].unit.weapon1.shoot(*shot) # (Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(2, 2)].unit.hp == 2 # firing unit unchanged
    assert g.board[(3, 2)].unit.hp == 1 # mountain unchanged
    assert g.board[(3, 2)].unit.type == 'mountain' # mountain unchanged
    assert g.board[(4, 2)].unit.hp == 4 # target square took 1 damage
    assert g.board[(5, 2)].unit == None # vek pushed off this square
    assert g.board[(4, 1)].unit.hp == 5 # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert g.board[(4, 3)].unit == None # vek also pushed off this square
    assert g.board[(6, 2)].unit.hp == 5 # pushed vek has full health
    assert g.board[(4, 4)].unit.hp == 5 # vek pushed has full health

def t_WeaponArtemisArtilleryPower1():
    "Do the Artillery demo from the game when you mouseover the weapon and you have buildings immune powered."
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery(power1=True)))
    g.board[(3, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_Building(g))
    g.board[(5, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g)) # this one is actually against the wall and cannot be pushed
    g.board[(4, 3)].createUnitHere(Unit_AlphaScorpion(g)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert g.board[(2, 2)].unit.hp == 2
    assert g.board[(3, 2)].unit.hp == 1
    assert g.board[(4, 2)].unit.hp == 1 # the building
    assert g.board[(5, 2)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 3)].unit.hp == 5
    gs = g.board[(2, 2)].unit.weapon1.genShots()
    for i in range(6):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 2)].unit.weapon1.shoot(*shot)
    g.flushHurt()
    assert g.board[(2, 2)].unit.hp == 2  # firing unit unchanged
    assert g.board[(3, 2)].unit.hp == 1  # mountain unchanged
    assert g.board[(3, 2)].unit.type == 'mountain'  # mountain unchanged
    assert g.board[(4, 2)].unit.hp == 1  # target square took no damage since it's a building and power1 prevents damage to it
    assert g.board[(5, 2)].unit == None  # vek pushed off this square
    assert g.board[(4, 1)].unit.hp == 5  # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert g.board[(4, 3)].unit == None  # vek also pushed off this square
    assert g.board[(6, 2)].unit.hp == 5  # pushed vek has full health
    assert g.board[(4, 4)].unit.hp == 5  # vek pushed has full health

def t_WeaponArtemisArtilleryPower2():
    "Do the power Artillery demo from the game when you mouseover the weapon and you have extra damage powered."
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery(power2=True)))
    g.board[(3, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g)) # this one is actually against the wall and cannot be pushed
    g.board[(4, 3)].createUnitHere(Unit_AlphaScorpion(g)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert g.board[(2, 2)].unit.hp == 2
    assert g.board[(3, 2)].unit.hp == 1
    assert g.board[(4, 2)].unit.hp == 5
    assert g.board[(5, 2)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 3)].unit.hp == 5
    gs = g.board[(2, 2)].unit.weapon1.genShots()
    for i in range(6):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 2)].unit.weapon1.shoot(*shot)
    g.flushHurt()
    assert g.board[(2, 2)].unit.hp == 2 # firing unit unchanged
    assert g.board[(3, 2)].unit.hp == 1 # mountain unchanged
    assert g.board[(3, 2)].unit.type == 'mountain' # mountain unchanged
    assert g.board[(4, 2)].unit.hp == 2 # target square took 1 damage
    assert g.board[(5, 2)].unit == None # vek pushed off this square
    assert g.board[(4, 1)].unit.hp == 5 # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert g.board[(4, 3)].unit == None # vek also pushed off this square
    assert g.board[(6, 2)].unit.hp == 5 # pushed vek has full health
    assert g.board[(4, 4)].unit.hp == 5 # vek pushed has full health

def t_WeaponArtemisArtilleryFullPower():
    "Do the Artillery demo from the game when you mouseover the weapon and you have buildings immune powered and damage powered."
    g = Game()
    g.board[(2, 2)].createUnitHere(Unit_Artillery_Mech(g, weapon1=Weapon_ArtemisArtillery(power1=True)))
    g.board[(3, 2)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_Building(g))
    g.board[(5, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g)) # this one is actually against the wall and cannot be pushed
    g.board[(4, 3)].createUnitHere(Unit_AlphaScorpion(g)) # an extra vek added above the one that gets hit to make sure he's pushed
    assert g.board[(2, 2)].unit.hp == 2
    assert g.board[(3, 2)].unit.hp == 1
    assert g.board[(4, 2)].unit.hp == 1 # the building
    assert g.board[(5, 2)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 3)].unit.hp == 5
    gs = g.board[(2, 2)].unit.weapon1.genShots()
    for i in range(6):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 2)].unit.weapon1.shoot(*shot)
    g.flushHurt()
    assert g.board[(2, 2)].unit.hp == 2  # firing unit unchanged
    assert g.board[(3, 2)].unit.hp == 1  # mountain unchanged
    assert g.board[(3, 2)].unit.type == 'mountain'  # mountain unchanged
    assert g.board[(4, 2)].unit.hp == 1  # target square took no damage since it's a building and power1 prevents damage to it
    assert g.board[(5, 2)].unit == None  # vek pushed off this square
    assert g.board[(4, 1)].unit.hp == 5  # this vek wasn't pushed because he's on the edge of the map. he took no damage
    assert g.board[(4, 3)].unit == None  # vek also pushed off this square
    assert g.board[(6, 2)].unit.hp == 5  # pushed vek has full health
    assert g.board[(4, 4)].unit.hp == 5  # vek pushed has full health

def t_WeaponBurstBeamNoPower():
    "Do the weapon demo with default power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.hp == 3 # vek took 2 damage
    assert g.board[(4, 1)].unit.hp == 1 # friendly took 1 damage
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_WeaponBurstBeamAllyPower():
    "Do the weapon demo with ally immune powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power1=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(6, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    assert g.board[(6, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.hp == 3 # vek took 2 damage
    assert g.board[(4, 1)].unit.hp == 2 # friendly took NO damage
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged
    assert g.board[(6, 1)].unit.hp == 5 # this vek was saved by the mountain

def t_WeaponBurstBeamShieldedAllyPower():
    "If you shield a beam ally with allies immune and then shoot it, the shield remains."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power1=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g, effects={Effects.SHIELD}))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(6, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    assert g.board[(6, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.hp == 3 # vek took 2 damage
    assert g.board[(4, 1)].unit.hp == 2 # friendly took NO damage
    assert g.board[(4, 1)].unit.effects == {Effects.SHIELD}  # friendly still has shield
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged
    assert g.board[(6, 1)].unit.hp == 5 # this vek was saved by the mountain

def t_WeaponBurstBeamDamagePower():
    "Do the weapon demo with extra damage powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.hp == 2 # vek took 3 damage
    assert g.board[(4, 1)].unit.type == 'mechcorpse' # friendly took 2 damage and died
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_WeaponBurstBeamFullPower():
    "Do the weapon demo with ally immune and extra damage powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit == None
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # wielder untouched
    assert g.board[(2, 1)].unit == None # still nothing here
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.hp == 2 # vek took 3 damage
    assert g.board[(4, 1)].unit.hp == 2 # friendly took NO damage
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

# def t_WeaponBurstBeamOrder1(): # TODO: Finish this after the blast psion removes explosive from units upon death and Psion receiver is implemented.
#     "Test the order of vek and mechs dying from BurstBeam. Refer to 'explosive burst beam order 1.flv"
#     g = Game()
#     g.board[(3, 2)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam(power1=False, power2=False)))
#     g.board[(4, 2)].createUnitHere(Unit_Firefly(g))
#     g.board[(5, 2)].createUnitHere(Unit_Defense_Mech(g))
#     g.board[(5, 2)].createUnitHere(Unit_BlastPsion(g))
#     assert g.board[(1, 1)].unit.hp == 3
#     assert g.board[(2, 1)].unit == None
#     assert g.board[(3, 1)].unit.hp == 5
#     assert g.board[(4, 1)].unit.hp == 2
#     assert g.board[(5, 1)].unit.type == 'mountain'
#     g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
#     g.flushHurt()
#     assert g.board[(1, 1)].unit.hp == 3 # wielder untouched
#     assert g.board[(2, 1)].unit == None # still nothing here
#     assert g.board[(2, 1)].effects == set()
#     assert g.board[(3, 1)].unit.hp == 2 # vek took 3 damage
#     assert g.board[(4, 1)].unit.hp == 2 # friendly took NO damage
#     assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged

def t_ExplosiveUnitDies():
    "Test a unit with the explosive effect dying"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Laser_Mech(g, weapon1=Weapon_BurstBeam()))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, effects={Effects.EXPLOSIVE}))
    g.board[(3, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(2, 2)].createUnitHere(Unit_Scorpion(g))
    assert g.board[(1, 1)].unit.hp == 3 # laser mech
    assert g.board[(2, 1)].unit.hp == 3 # explosive vek
    assert g.board[(3, 1)].unit.hp == 2 # defense mech
    assert g.board[(2, 2)].unit.hp == 3 # vek to take damage from explosion
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # laser mech took damage from explosion
    assert g.board[(2, 1)].unit == None  # explosive vek died and exploded
    assert g.board[(3, 1)].unit.type == 'mechcorpse'  # defense mech died from shot, then the corpse got exploded on
    assert g.board[(2, 2)].unit.hp == 2  # vek took damage from explosion

def t_WeaponRammingEnginesDefault():
    "Do the weapon demo with no powered upgrades"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 3 # vek pushed here took 2 damage

def t_WeaponRammingEnginesPower1():
    "Do the weapon demo with the first upgrade powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 1  # wielder took 2 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 2 # vek pushed here took 3 damage

def t_WeaponRammingEnginesPower2():
    "Do the weapon demo with the second upgrade powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 2 # vek pushed here took 3 damage

def t_WeaponRammingEnginesFullPower():
    "Do the weapon demo with the both upgrades powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 1  # wielder took 2 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 1 # vek pushed here took 4 damage

def t_WeaponRammingEnginesTileDamage():
    "Do the weapon demo with no powered upgrades but on sand tiles to make sure they get damaged"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(3, 1)].replaceTile(Tile_Sand(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(1, 1)].effects == set() # sand tiles are all normal
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 3 # vek pushed here took 2 damage
    assert g.board[(1, 1)].effects == set() # this one untouched
    assert g.board[(2, 1)].effects == {Effects.SMOKE} # these 2 got smoked from the self damage
    assert g.board[(3, 1)].effects == {Effects.SMOKE} # and vek getting hit

def t_WeaponRammingEnginesShieldedTileDamage():
    "Do the weapon demo with no powered upgrades but on sand tiles with a shield to make sure they don't get damaged"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(1, 1)].applyShield()
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(3, 1)].replaceTile(Tile_Sand(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(1, 1)].effects == set() # sand tiles are all normal
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 3  # wielder took 0 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 3 # vek pushed here took 2 damage
    assert g.board[(1, 1)].effects == set() # this one untouched
    assert g.board[(2, 1)].effects == set() # this sand tile took no damage since the mech was shielded
    assert g.board[(3, 1)].effects == {Effects.SMOKE} # this one does take damage because this is where the vek got hit

def t_WeaponRammingEnginesIntoChasm():
    "Charge but stop at a chasm and die in it"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 1)].replaceTile(Tile_Chasm(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 1)].effects == set() # normal chasm tile
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit == None # wielder and mech corpse died in the chasm
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 3 # vek pushed here took 2 damage
    assert g.board[(3, 1)].effects == set()  # normal chasm tile

def t_WeaponRammingEnginesOverChasm():
    "Charge over a chasm and don't die in it"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=False, power2=False)))
    g.board[(2, 1)].replaceTile(Tile_Chasm(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set() # normal chasm tile
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    #for x in range(1, 6):
    #    print(g.board[x, 1])
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(3, 1)].unit.hp == 2 # wielder took 1 damage
    assert g.board[(4, 1)].unit == None # vek pushed off this tile
    assert g.board[(5, 1)].unit.hp == 3 # vek pushed here took 2 damage
    assert g.board[(2, 1)].effects == set()  # normal chasm tile

def t_WeaponRammingEnginesShield():
    "A shielded unit that uses ramming engines takes no self-damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=True, power2=True), effects={Effects.SHIELD}))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 3  # wielder took 0 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 1 # vek pushed here took 4 damage

def t_WeaponRammingEnginesMiss():
    "if ramming engine doesn't hit a unit, it doesn't take self damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Charge_Mech(g, weapon1=Weapon_RammingEngines(power1=True, power2=True)))
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(8, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # wielder moved
    assert g.board[(8, 1)].unit.hp == 3  # wielder took 0 damage
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
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None # vek was pushed off this square
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 4 # vek lost 1 hp

def t_WeaponTaurusCannonDefaultPower1():
    "Shoot the Taurus Cannon with power1"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g, weapon1=Weapon_TaurusCannon(power1=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None # vek was pushed off this square
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 3 # vek lost 2 hp

def t_WeaponTaurusCannonPower2():
    "Shoot the Taurus Cannon with power2"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g, weapon1=Weapon_TaurusCannon(power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None # vek was pushed off this square
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 3 # vek lost 2 hp

def t_WeaponTaurusCannonFullPower():
    "Shoot the Taurus Cannon with full power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g, weapon1=Weapon_TaurusCannon(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None # vek was pushed off this square
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 2 # vek lost 3 hp

def t_WeaponTaurusCannonHitsEdgeTile():
    "Shoot the Taurus Cannon with to enemy in the way to make sure we hit the edge tile"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Cannon_Mech(g, weapon1=Weapon_TaurusCannon(power1=True, power2=True)))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(8, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(8, 1)].effects == {Effects.FIRE}
    assert g.board[(8, 1)].unit == None

def t_WeaponAttractionPulseDefault():
    "Shoot the Attraction Pulse at a unit with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_AttractionPulse(power1=False, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(4, 1)].unit == None # vek was pushed off this square
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set() # pulled 1 square closer
    assert g.board[(3, 1)].unit.hp == 5 # vek lost 0 hp

def t_WeaponAttractionPulseFullPower():
    "Shoot the Attraction Pulse at a unit with full power. IRL this gun takes no power, just making sure this doesn't break."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_AttractionPulse(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(4, 1)].unit == None # vek was pushed off this square
    assert g.board[(3, 1)].effects == set()
    assert g.board[(3, 1)].unit.effects == set() # pulled 1 square closer
    assert g.board[(3, 1)].unit.hp == 5 # vek lost 0 hp

def t_WeaponAttractionPulseBump():
    "Attraction pulse does not set fire to forest tile if you pull another unit into you for bump damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_AttractionPulse(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    for x in 1, 2:
        g.board[(x, 1)].replaceTile(Tile_Forest(g))
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no fire
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 1 # took 1 damage
    assert g.board[(2, 1)].effects == set() # no fire
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 4 # vek lost 1 hp from bump

def t_WeaponShieldProjectorDefaultPower():
    "Maiden test of the shield projector with no upgrade power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Defense_Mech(g, weapon1=Weapon_ShieldProjector(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 2)].createUnitHere(Unit_AlphaScorpion(g))
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
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 2)].createUnitHere(Unit_AlphaScorpion(g))
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
    for i in gs:
        assert False # This should never be hit as the gs iterator should be at the end

def t_WeaponViceFistNoPower():
    "Test the Vice Fist with no power"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponViceFistPower1():
    "Test the Vice Fist with power1"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4 # no additional effect since this was an enemy
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponViceFistPower2():
    "Test the Vice Fist with power2"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # took additional damage
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponViceFistPower1Friendly():
    "Test the Vice Fist with power1 and a friendly unit"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Siege_Mech(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 2
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # friendly unit took no damage
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponViceFistPower1FriendlyChasm():
    "Test the Vice Fist with power1 and a friendly unit, but kill the unit by throwing it into a chasm"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Judo_Mech(g, weapon1=Weapon_ViceFist(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_Siege_Mech(g))
    g.board[(1, 1)].replaceTile(Tile_Chasm(g))
    assert g.board[(1, 1)].unit == None
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 2
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # friendly unit died in the chasm
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit == None

def t_WeaponClusterArtilleryNoPower():
    "Default power test for Cluster Artillery"
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_Siege_Mech(g, weapon1=Weapon_ClusterArtillery(power1=False, power2=False)))
    g.board[(3, 3)].createUnitHere(Unit_Building(g))
    g.board[(4, 3)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 4)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 3)].unit.hp == 2
    assert g.board[(3, 3)].unit.hp == 1 # building
    assert g.board[(4, 3)].unit.hp == 5
    assert g.board[(3, 4)].unit.hp == 5
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for i in range(5):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 3)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 3)].unit.hp == 2
    assert g.board[(3, 3)].unit.hp == 1  # building
    assert g.board[(4, 3)].unit == None # vek pushed
    assert g.board[(5, 3)].unit.hp == 4 # took 1 damage
    assert g.board[(3, 4)].unit == None # vek pushed
    assert g.board[(3, 5)].unit.hp == 4 # took 1 damage

def t_WeaponClusterArtilleryPower1():
    "power1 test for Cluster Artillery"
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_Siege_Mech(g, weapon1=Weapon_ClusterArtillery(power1=True, power2=False)))
    g.board[(3, 3)].createUnitHere(Unit_Building(g))
    g.board[(4, 3)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 4)].createUnitHere(Unit_Building(g))
    assert g.board[(1, 3)].unit.hp == 2
    assert g.board[(3, 3)].unit.hp == 1 # building
    assert g.board[(4, 3)].unit.hp == 5
    assert g.board[(3, 4)].unit.hp == 1 # attacked building
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for i in range(5):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 3)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 3)].unit.hp == 2
    assert g.board[(3, 3)].unit.hp == 1  # building
    assert g.board[(4, 3)].unit == None # vek pushed
    assert g.board[(5, 3)].unit.hp == 4 # took 1 damage
    assert g.board[(3, 4)].unit.hp == 1  # attacked building took no damage

def t_WeaponClusterArtilleryFullPower():
    "full power test for Cluster Artillery"
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_Siege_Mech(g, weapon1=Weapon_ClusterArtillery(power1=True, power2=True)))
    g.board[(3, 3)].createUnitHere(Unit_Building(g))
    g.board[(4, 3)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 4)].createUnitHere(Unit_Building(g))
    assert g.board[(1, 3)].unit.hp == 2
    assert g.board[(3, 3)].unit.hp == 1 # building
    assert g.board[(4, 3)].unit.hp == 5
    assert g.board[(3, 4)].unit.hp == 1 # attacked building
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for i in range(5):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # (Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 3)].unit.hp == 2
    assert g.board[(3, 3)].unit.hp == 1  # building
    assert g.board[(4, 3)].unit == None # vek pushed
    assert g.board[(5, 3)].unit.hp == 3 # took 2 damage
    assert g.board[(3, 4)].unit.hp == 1  # attacked building took no damage

def t_WeaponGravWellNormal():
    "default test for grav well"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Gravity_Mech(g, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # untouched wielder
    assert g.board[(3, 1)].unit == None # vek pushed
    assert g.board[(2, 1)].unit.hp == 5 # to here with no damage

def t_WeaponGravWellStable():
    "grav well can't pull stable units"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Gravity_Mech(g, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 1
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # untouched wielder
    assert g.board[(3, 1)].unit.hp == 1 # mountain not moved and undamaged
    assert g.board[(3, 1)].unit.type == 'mountain'

def t_WeaponGravWellBump():
    "grav well pulls vek into a mountain"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Gravity_Mech(g, weapon1=Weapon_GravWell(power1=True, power2=True))) # this weapon doesn't have power upgrades
    g.board[(2, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.type == 'mountain'
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # untouched wielder
    assert g.board[(3, 1)].unit.hp == 4 # vek pushed and bumped for 1 damage
    assert g.board[(2, 1)].unit.hp == 1 # damage mountain now
    assert g.board[(2, 1)].unit.type == 'mountaindamaged'

def t_WeaponSpartanShieldNoPower():
    "Shoot SpartanShield with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Aegis_Mech(g, weapon1=Weapon_SpartanShield(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, qshot=(Direction.LEFT,), hp=5, maxhp=5))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.LEFT,)
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # untouched wielder
    assert g.board[(2, 1)].unit.hp == 3 # vek lost 2 hp
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.RIGHT,) # qshot is flipped as we expect

def t_WeaponSpartanShieldNoPower2():
    "Shoot SpartanShield with no power but have the vek shot become invalidated"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Aegis_Mech(g, weapon1=Weapon_SpartanShield(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, qshot=(Direction.UP,), hp=5, maxhp=5))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.UP,)
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # untouched wielder
    assert g.board[(2, 1)].unit.hp == 3 # vek lost 2 hp
    assert g.board[(2, 1)].unit.weapon1.qshot == None # qshot is invalidated as we expect

def t_WeaponSpartanShieldPower1():
    "Shoot SpartanShield with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Aegis_Mech(g, weapon1=Weapon_SpartanShield(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, qshot=(Direction.LEFT,), hp=5, maxhp=5))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.LEFT,)
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # untouched wielder
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(2, 1)].unit.hp == 3 # vek lost 2 hp
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.RIGHT,) # qshot is flipped as we expect

def t_WeaponSpartanShieldPower2():
    "Shoot SpartanShield with 2 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Aegis_Mech(g, weapon1=Weapon_SpartanShield(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, qshot=(Direction.LEFT,), hp=5, maxhp=5))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.LEFT,)
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # untouched wielder
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 2 # vek lost 3 hp
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.RIGHT,) # qshot is flipped as we expect

def t_WeaponSpartanShieldPowerMax():
    "Shoot SpartanShield with max power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Aegis_Mech(g, weapon1=Weapon_SpartanShield(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, qshot=(Direction.LEFT,), hp=5, maxhp=5))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.LEFT,)
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # untouched wielder
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(2, 1)].unit.hp == 2 # vek lost 3 hp
    assert g.board[(2, 1)].unit.weapon1.qshot == (Direction.RIGHT,) # qshot is flipped as we expect

def t_WeaponJanusCannonLow():
    "Shoot the Janus cannon with no power!"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Mirror_Mech(g, weapon1=Weapon_JanusCannon(power1=False, power2=False)))  # this weapon doesn't have power upgrades
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 3
    assert g.board[(5, 1)].unit.hp == 5
    g.board[(4, 1)].unit.weapon1.shoot(Direction.RIGHT) # this shoots left and right
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # alpha scorpion pushed from here
    assert g.board[(1, 1)].unit.hp == 4 # pushed here and took 1 damage
    assert g.board[(4, 1)].unit.hp == 3 # no change to the shooter
    assert g.board[(5, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(6, 1)].unit.hp == 4 # took a damage
    # shoot a second time, why not
    g.board[(4, 1)].unit.weapon1.shoot(Direction.LEFT)  # this shoots left and right
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # nowhere else to push, just takes another damage
    assert g.board[(4, 1)].unit.hp == 3  # still no change to the shooter
    assert g.board[(6, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(7, 1)].unit.hp == 3  # took a damage

def t_WeaponJanusCannon1():
    "Shoot the Janus cannon with 1 power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Mirror_Mech(g, weapon1=Weapon_JanusCannon(power1=True, power2=False)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 3
    assert g.board[(5, 1)].unit.hp == 5
    g.board[(4, 1)].unit.weapon1.shoot(Direction.RIGHT) # this shoots left and right
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # alpha scorpion pushed from here
    assert g.board[(1, 1)].unit.hp == 3 # pushed here and took 2 damage
    assert g.board[(4, 1)].unit.hp == 3 # no change to the shooter
    assert g.board[(5, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(6, 1)].unit.hp == 3 # took 2 damage
    # shoot a second time, why not
    g.board[(4, 1)].unit.weapon1.shoot(Direction.LEFT)  # this shoots left and right
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # nowhere else to push, just takes another 2 damage
    assert g.board[(4, 1)].unit.hp == 3  # still no change to the shooter
    assert g.board[(6, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(7, 1)].unit.hp == 1  # took 2 damage

def t_WeaponJanusCannon2():
    "Shoot the Janus cannon with power2 powered."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Mirror_Mech(g, weapon1=Weapon_JanusCannon(power1=False, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 3
    assert g.board[(5, 1)].unit.hp == 5
    g.board[(4, 1)].unit.weapon1.shoot(Direction.RIGHT) # this shoots left and right
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # alpha scorpion pushed from here
    assert g.board[(1, 1)].unit.hp == 3 # pushed here and took 2 damage
    assert g.board[(4, 1)].unit.hp == 3 # no change to the shooter
    assert g.board[(5, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(6, 1)].unit.hp == 3 # took 2 damage
    # shoot a second time, why not
    g.board[(4, 1)].unit.weapon1.shoot(Direction.LEFT)  # this shoots left and right
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # nowhere else to push, just takes another 2 damage
    assert g.board[(4, 1)].unit.hp == 3  # still no change to the shooter
    assert g.board[(6, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(7, 1)].unit.hp == 1  # took 2 damage

def t_WeaponJanusCannonFullPower():
    "Shoot the Janus cannon with Full power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Mirror_Mech(g, weapon1=Weapon_JanusCannon(power1=True, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 3
    assert g.board[(5, 1)].unit.hp == 5
    g.board[(4, 1)].unit.weapon1.shoot(Direction.RIGHT) # this shoots left and right
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # alpha scorpion pushed from here
    assert g.board[(1, 1)].unit.hp == 2 # pushed here and took 3 damage
    assert g.board[(4, 1)].unit.hp == 3 # no change to the shooter
    assert g.board[(5, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(6, 1)].unit.hp == 2 # took 3 damage
    # shoot a second time, why not
    g.board[(4, 1)].unit.weapon1.shoot(Direction.LEFT)  # this shoots left and right
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # unit died
    assert g.board[(4, 1)].unit.hp == 3  # still no change to the shooter
    assert g.board[(6, 1)].unit == None  # alpha scorpion pushed from here
    assert g.board[(7, 1)].unit == None # this one also died

def t_WeaponCryoLauncher():
    "Shoot the CryoLauncher cannon."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 1)].createUnitHere(Unit_Ice_Mech(g, weapon1=Weapon_CryoLauncher(power1=True, power2=True))) # this weapon doesn't use power
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
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
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
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
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 4 # hit for 1 dmg
    assert g.board[(3, 1)].unit.hp == 2 # jet landed here
    assert g.board[(3, 1)].unit.type == 'jet'

def t_WeaponAerialBombs2():
    "Shoot the AerialBombs with more damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 3 # hit for 2 dmg
    assert g.board[(3, 1)].unit.hp == 2 # jet landed here
    assert g.board[(3, 1)].unit.type == 'jet'

def t_WeaponAerialBombs3():
    "Shoot the AerialBombs with more range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 4 # hit for 1 dmg
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.hp == 4  # hit for 1 dmg
    assert g.board[(4, 1)].unit.hp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponAerialBombs4():
    "Shoot the AerialBombs with full power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 3 # hit for 2 dmg
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.hp == 3  # hit for 2 dmg
    assert g.board[(4, 1)].unit.hp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponAerialBombsForest():
    "Shoot the AerialBombs on a forest and make sure it has smoke and not fire after."
    g = Game()
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 4 # hit for 1 dmg
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.hp == 4  # hit for 1 dmg
    assert g.board[(4, 1)].unit.hp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponAerialBombsGen1():
    "Test the Aerial Bombs shot generator."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AerialBombs(power1=False, power2=True))) # with range
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 4)].createUnitHere(Unit_AlphaScorpion(g))
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
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # no change for shooter
    assert g.board[(1, 1)].unit.effects == set() # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(3, 1)].effects == set() # no effects change to the tile
    assert g.board[(4, 1)].unit.hp == 3 # vek took 2 dmg
    assert g.board[(4, 1)].effects == set()  # no effects change to the tile

def t_WeaponRocketArtillery2():
    "Shoot the Rocket Artillery weapon with 1 power with its back against the edge."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Rocket_Mech(g, weapon1=Weapon_RocketArtillery(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # no change for shooter
    assert g.board[(1, 1)].unit.effects == set() # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(3, 1)].effects == set() # no effects change to the tile
    assert g.board[(4, 1)].unit.hp == 2 # vek took 3 dmg
    assert g.board[(4, 1)].effects == set()  # no effects change to the tile
    
def t_WeaponRocketArtillery3():
    "Shoot the Rocket Artillery weapon with full power with its back against the edge."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Rocket_Mech(g, weapon1=Weapon_RocketArtillery(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # no change for shooter
    assert g.board[(1, 1)].unit.effects == set() # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(3, 1)].effects == set() # no effects change to the tile
    assert g.board[(4, 1)].unit.hp == 1 # vek took 4 dmg
    assert g.board[(4, 1)].effects == set()  # no effects change to the tile

def t_WeaponRocketArtillery4():
    "Shoot the Rocket Artillery weapon with full power with a tile for it to fart smoke onto"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Rocket_Mech(g, weapon1=Weapon_RocketArtillery(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 3 # no change for shooter
    assert g.board[(2, 1)].unit.effects == set() # no change for shooter
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(4, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].effects == set() # no effects change to the tile
    assert g.board[(5, 1)].unit.hp == 1 # vek took 4 dmg
    assert g.board[(5, 1)].effects == set()  # no effects change to the tile
    assert g.board[(1, 1)].effects == {Effects.SMOKE} # smoke was farted behind the wielder

def t_WeaponRepulse1():
    "Shoot the Repulse weapon with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit == None # vek pushed off here
    assert g.board[(3, 1)].unit.hp == 5  # no change for vek
    assert g.board[(3, 1)].unit.effects == set()  # no change for vek
    assert g.board[(3, 1)].effects == set()  # no change for vek's tile
    assert g.board[(1, 2)].unit == None  # ally pushed off here
    assert g.board[(1, 3)].unit.hp == 3  # no change for ally
    assert g.board[(1, 3)].unit.effects == set()  # no change for vally
    assert g.board[(1, 3)].effects == set()  # no change for ally's tile

def t_WeaponRepulse2():
    "Shoot the Repulse weapon with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD} # shooter shielded
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit == None # vek pushed off here
    assert g.board[(3, 1)].unit.hp == 5  # no change for vek
    assert g.board[(3, 1)].unit.effects == set()  # no change for vek
    assert g.board[(3, 1)].effects == set()  # no change for vek's tile
    assert g.board[(1, 2)].unit == None  # ally pushed off here
    assert g.board[(1, 3)].unit.hp == 3  # no change for ally
    assert g.board[(1, 3)].unit.effects == set()  # no change for ally
    assert g.board[(1, 3)].effects == set()  # no change for ally's tile

def t_WeaponRepulse3():
    "Shoot the Repulse weapon with 2nd power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set() # no change for shooter
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit == None # vek pushed off here
    assert g.board[(3, 1)].unit.hp == 5  # no change for vek
    assert g.board[(3, 1)].unit.effects == set()  # no change for vek
    assert g.board[(3, 1)].effects == set()  # no change for vek's tile
    assert g.board[(1, 2)].unit == None  # ally pushed off here
    assert g.board[(1, 3)].unit.hp == 3  # no change for ally
    assert g.board[(1, 3)].unit.effects == {Effects.SHIELD}  # ally is shielded
    assert g.board[(1, 3)].effects == set()  # no change for ally's tile

def t_WeaponRepulse4():
    "Shoot the Repulse weapon with full power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Rocket_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}  # shooter shielded
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit == None # vek pushed off here
    assert g.board[(3, 1)].unit.hp == 5  # no change for vek
    assert g.board[(3, 1)].unit.effects == set()  # no change for vek
    assert g.board[(3, 1)].effects == set()  # no change for vek's tile
    assert g.board[(1, 2)].unit == None  # ally pushed off here
    assert g.board[(1, 3)].unit.hp == 3  # no change for ally
    assert g.board[(1, 3)].unit.effects == {Effects.SHIELD}  # ally is shielded
    assert g.board[(1, 3)].effects == set()  # no change for ally's tile

def t_WeaponRepulse5():
    "Shoot the Repulse weapon with full power and a building to get shielded. And a mountain for the vek to bump into."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 2)].createUnitHere(Unit_Building(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}  # shooter shielded
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit.hp == 4  # vek took 1 bump damage
    assert g.board[(2, 1)].unit.effects == set()  # no change for vek
    assert g.board[(2, 1)].effects == set()  # no change for vek's tile
    assert g.board[(3, 1)].unit.type == 'mountaindamaged' # mountain got bumped into
    assert g.board[(1, 2)].unit.hp == 1  # no change for building
    assert g.board[(1, 2)].unit.effects == {Effects.SHIELD}  # building is shielded
    assert g.board[(1, 2)].effects == set()  # no change for ally's tile

def t_WeaponRepulse6():
    "Shoot the Repulse weapon with full power and have a friendly gain a shield, then immediately lose it to the bump."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Pulse_Mech(g, weapon1=Weapon_Repulse(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Pulse_Mech(g))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}  # shooter shielded
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(2, 1)].unit.hp == 3  # 2nd mech took NO bump damage
    assert g.board[(2, 1)].unit.effects == set()  # he gained a shield and lose it
    assert g.board[(2, 1)].effects == set()  # no change for 2nd mech's tile
    assert g.board[(3, 1)].unit.type == 'mountaindamaged' # mountain got bumped into

def t_WeaponGrapplingHook1():
    "Shoot the grappling hook weapon at an enemy with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=False, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # unit moved from here
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.hp == 5  # vek is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set()  # no change for vek
    assert g.board[(2, 1)].effects == set()  # no change for vek's tile

def t_WeaponGrapplingHook2():
    "Shoot the grappling hook weapon at an enemy with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=True, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # unit moved from here
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.hp == 5  # vek is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set()  # no change for vek
    assert g.board[(2, 1)].effects == set()  # no change for vek's tile

def t_WeaponGrapplingHook3():
    "Shoot the grappling hook weapon at a friendly with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=False, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Hook_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # unit moved from here
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.hp == 3  # ally is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set()  # no change for ally
    assert g.board[(2, 1)].effects == set()  # no change for ally's tile

def t_WeaponGrapplingHook4():
    "Shoot the grappling hook weapon at a friendly with power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=True, power2=False))) # power2 isn't used
    g.board[(3, 1)].createUnitHere(Unit_Hook_Mech(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # redundant as no units are hurt
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit == None # unit moved from here
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.hp == 3  # ally is now here, took no damage
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
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(2, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'mountain'
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.hp == 3  # wielder is now here, took no damage
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
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(2, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'mountain'
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.hp == 3  # wielder is now here, took no damage
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
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(2, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'building'
    assert g.board[(3, 1)].unit.effects == {Effects.SHIELD} # building is now shielded
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.hp == 3  # wielder is now here, took no damage
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
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(2, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(2, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'building'
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(2, 1)].unit.hp == 3  # wielder is now here, took no damage
    assert g.board[(2, 1)].unit.effects == set() # wielder gets no new effect
    assert g.board[(2, 1)].effects == set()  # no change for wielder's new tile

def t_WeaponGrapplingHook9():
    """Shoot the grappling hook weapon at a unit next to us. I caught a bug where the grappling hook ignore the tile next to you and start searching for a unit on the 2nd square since it couldn't grapple something next to it."""
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Hook_Mech(g, weapon1=Weapon_GrapplingHook(power1=False, power2=False))) # power2 isn't used
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(2):
        shot = next(gs)
    try:
        g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    except NullWeaponShot:
        pass # this is good
    else:
        assert False
    g.flushHurt() # redundant as no units are hurt

def t_WeaponRockLauncher1():
    "Shoot the Rock Launcher with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.effects == set() # target gets no new effects
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(3, 1)].unit.hp == 3 # vek took 2 damage
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.hp == 5 # to here, took no damage

def t_WeaponRockLauncher2():
    "Shoot the Rock Launcher with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.effects == set() # target gets no new effects
    assert g.board[(3, 1)].effects == set() # target's tile untouched
    assert g.board[(3, 1)].unit.hp == 2 # vek took 3 damage
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.hp == 5 # to here, took no damage

def t_WeaponRockLauncher3():
    "Shoot the Rock Launcher with full power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.effects == set() # target gets no new effects
    assert g.board[(3, 1)].effects == set() # targets tile untouched
    assert g.board[(3, 1)].unit.hp == 1 # vek took 4 damage
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.hp == 5 # to here, took no damage

def t_WeaponRockLauncher4():
    "Shoot the Rock Launcher with full power, but with a forest under the target vek"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=True, power2=True)))
    g.board[(3, 1)].replaceTile(Tile_Forest(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE} # target is set on fire
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile on fire
    assert g.board[(3, 1)].unit.hp == 1 # vek took 4 damage
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.hp == 5 # to here, took no damage

def t_WeaponRockLauncher5():
    "Shoot the Rock Launcher with full power, but with a forest with no target vek on it"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Boulder_Mech(g, weapon1=Weapon_RockLauncher(power1=True, power2=True)))
    g.board[(3, 1)].replaceTile(Tile_Forest(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change for shooter
    assert g.board[(1, 1)].unit.effects == set()  # shooter get no new effects
    assert g.board[(1, 1)].effects == set()  # no change for shooter's tile
    assert g.board[(3, 1)].unit.type == 'rock' # rock landed here and survives
    assert g.board[(3, 1)].effects == set() # tile doesn't catch fire since no damage was actually done to the tile
    assert g.board[(3, 2)].unit == None  # 2nd vek pushed from here
    assert g.board[(3, 3)].unit.hp == 5 # to here, took no damage

def t_WeaponFlameThrower1():
    "Shoot the Flame Thrower with default power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=False, power2=False)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(2, 1)].type == 'ground' # tile converted from sand to ground
    assert g.board[(2, 1)].unit == None # vek pushed
    assert g.board[(3, 1)].effects == set() # no change to destination
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE} # vek is now on fire
    assert g.board[(3, 1)].unit.hp == 5  # vek took no damage

def t_WeaponFlameThrower2():
    "Shoot the Flame Thrower with one more range/power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=False)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(2, 1)].type == 'ground' # tile converted from sand to ground
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(2, 1)].unit.hp == 5  # vek took no damage
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile past the vek caught fire
    assert g.board[(4, 1)].effects == set() # no change to push destination

def t_WeaponFlameThrower3():
    "Shoot the Flame Thrower with max range/power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=True)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 3)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(2, 1)].type == 'ground' # tile converted from sand to ground
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(2, 1)].unit.hp == 5  # vek took no damage
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile past the vek caught fire
    assert g.board[(4, 1)].effects == {Effects.FIRE} # this tile caught fire too
    assert g.board[(5, 1)].effects == set() # no change to push destination

def t_WeaponFlameThrower4():
    "Shoot the Flame Thrower twice with max range/power to cause damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=True)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 3)
    g.flushHurt()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 3)
    g.flushHurt() # redundant as the first shot didn't kill anything
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(2, 1)].type == 'ground' # tile converted from sand to ground
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(2, 1)].unit.hp == 3  # vek took 2 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile past the vek caught fire
    assert g.board[(4, 1)].effects == {Effects.FIRE} # this tile caught fire too
    assert g.board[(5, 1)].effects == set() # no change to push destination

def t_WeaponFlameThrowerMountain():
    "Shoot the Flame Thrower with max range/power through a mountain."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Flame_Mech(g, weapon1=Weapon_FlameThrower(power1=True, power2=True)))
    g.board[(2, 1)].replaceTile(Tile_Sand(g))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
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
    g.board[(1, 1)].createUnitHere(Unit_AlphaScorpion(g))
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
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(3, 1)].unit.hp == 5 # no damage
    assert g.board[(3, 2)].unit == None # vek pushed from here
    assert g.board[(3, 3)].effects == set()
    assert g.board[(3, 3)].unit.effects == set()
    assert g.board[(3, 3)].unit.hp == 5  # no damage

def t_WeaponVulcanArtillery2():
    "Shoot the Vulcan Artillery with backburn power up against a wall."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(1, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(3, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(3, 1)].unit.hp == 5 # no damage
    assert g.board[(3, 2)].unit == None # vek pushed from here
    assert g.board[(3, 3)].effects == set()
    assert g.board[(3, 3)].unit.effects == set()
    assert g.board[(3, 3)].unit.hp == 5  # no damage

def t_WeaponVulcanArtillery3():
    "Shoot the Vulcan Artillery with backburn power NOT up against a wall."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # (Direction.RIGHT, 2)
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(4, 1)].unit.hp == 5 # no damage
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.hp == 5  # no damage
    assert g.board[(1, 1)].effects == {Effects.FIRE} # fire farted

def t_WeaponVulcanArtillery4():
    "Shoot the Vulcan Artillery withOUT backburn power NOT up against a wall."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=False, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(4, 1)].unit.hp == 5 # no damage
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.hp == 5  # no damage
    assert g.board[(1, 1)].effects == set() # NO fire farted

def t_WeaponVulcanArtillery5():
    "Shoot the Vulcan Artillery withOUT backburn power NOT up against a wall and WITH damage power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=False, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(4, 1)].unit.hp == 3 # 2 damage
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.hp == 5  # no damage
    assert g.board[(1, 1)].effects == set() # NO fire farted

def t_WeaponVulcanArtillery6():
    "Shoot the Vulcan Artillery with backburn power NOT up against a wall and WITH damage power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}  # vek is now on fire, he was not pushed
    assert g.board[(4, 1)].unit.hp == 3 # 2 damage
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.hp == 5  # no damage
    assert g.board[(1, 1)].effects == {Effects.FIRE}  # fire farted

def t_WeaponVulcanArtillery7():
    "Shoot the Vulcan Artillery with full power against a mountain for some reason."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == set()  # mountains can't catch on fire
    assert g.board[(4, 1)].unit.type == 'mountaindamaged'
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.hp == 5  # no damage
    assert g.board[(1, 1)].effects == {Effects.FIRE}  # fire farted

def t_WeaponVulcanArtillery8():
    "Shoot the Vulcan Artillery with no damage power against a mountain for some reason."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Meteor_Mech(g, weapon1=Weapon_VulcanArtillery(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(4, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for i in range(7):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.hp == 3  # no change for shooter
    assert g.board[(4, 1)].effects == {Effects.FIRE} # tile caught on fire
    assert g.board[(4, 1)].unit.effects == set()  # mountains can't catch on fire
    assert g.board[(4, 1)].unit.type == 'mountain'
    assert g.board[(4, 2)].unit == None # vek pushed from here
    assert g.board[(4, 3)].effects == set()
    assert g.board[(4, 3)].unit.effects == set()
    assert g.board[(4, 3)].unit.hp == 5  # no damage
    assert g.board[(1, 1)].effects == {Effects.FIRE}  # fire farted

def t_WeaponTeleporter1():
    "Shoot the teleporter with no power and no unit to swap with"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Swap_Mech(g, weapon1=Weapon_Teleporter(power1=False, power2=False)))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.hp == 2  # no change for shooter who is now here
    assert g.board[(2, 1)].unit.type == 'swap'
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit == None

def t_WeaponTeleporter2():
    "Shoot the teleporter with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Swap_Mech(g, weapon1=Weapon_Teleporter(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt() # no units actually hurt
    assert g.board[(2, 1)].unit.hp == 2  # no change for shooter who is now here
    assert g.board[(2, 1)].unit.type == 'swap'
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 5  # no damage to vek who is now here

def t_WeaponTeleporter3():
    "Shoot the teleporter with full power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Swap_Mech(g, weapon1=Weapon_Teleporter(power1=True, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 4)
    g.flushHurt() # no units actually hurt
    assert g.board[(5, 1)].unit.hp == 2  # no change for shooter who is now here
    assert g.board[(5, 1)].unit.type == 'swap'
    assert g.board[(5, 1)].unit.effects == set()
    assert g.board[(5, 1)].effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 5  # no damage to vek who is now here

def t_WeaponTeleporterOffBoard():
    "Shoot the teleporter with some power off the board"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Swap_Mech(g, weapon1=Weapon_Teleporter(power1=True, power2=False)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
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
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
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
    assert g.board[(2, 1)].unit.hp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == set() # This forest DID NOT catch fire from the vek that was pushed here!
    assert g.board[(4, 1)].unit.effects == set() # This vek never caught fire! He was pushed to the forest tile before it was lit on fire
    assert g.board[(4, 1)].unit.hp == 4 # vek took 1 damage
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == set()
    assert g.board[(2, 3)].unit.effects == set()
    assert g.board[(2, 3)].unit.hp == 4 # took 1 damage

def t_WeaponHydraulicLegsPower1():
    "Shoot the Hydraulic Legs with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Leap_Mech(g, weapon1=Weapon_HydraulicLegs(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
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
    assert g.board[(2, 1)].unit.hp == 1  # wielder took 2 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 3 # vek took 2 damage
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == set()
    assert g.board[(2, 3)].unit.effects == set()
    assert g.board[(2, 3)].unit.hp == 3 # took 2 damage

def t_WeaponHydraulicLegsPower2():
    "Shoot the Hydraulic Legs with second power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Leap_Mech(g, weapon1=Weapon_HydraulicLegs(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
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
    assert g.board[(2, 1)].unit.hp == 2  # wielder took 1 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 3 # vek took 2 damage
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == set()
    assert g.board[(2, 3)].unit.effects == set()
    assert g.board[(2, 3)].unit.hp == 3 # took 2 damage

def t_WeaponHydraulicLegsMaxPower():
    "Shoot the Hydraulic Legs with maximum power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Leap_Mech(g, weapon1=Weapon_HydraulicLegs(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
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
    assert g.board[(2, 1)].unit.hp == 1  # wielder took 2 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == set() # the vek pushed from the tile that caught fire did not catch fire itself!
    assert g.board[(4, 1)].unit.effects == set() # told ya so
    assert g.board[(4, 1)].unit.hp == 2 # vek took 3 damage
    assert g.board[(2, 2)].effects == {Effects.FIRE}
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == set()
    assert g.board[(2, 3)].unit.effects == set()
    assert g.board[(2, 3)].unit.hp == 2 # took 3 damage

def t_WeaponHydraulicLegsMaxPowerIntoAcid():
    "when hydraulic legs leaps onto an acid tile, he takes the acid first and then takes double damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Leap_Mech(g, weapon1=Weapon_HydraulicLegs(power1=True, power2=True), hp=10))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    for x in range(1, 5):
        for y in range(1, 4):
            g.board[(x, y)].applyAcid()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for i in range(8):
        shot = next(gs)  # iterate through the shotgenerator until it sets self.destinationsquare where we need it
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # wielder leaped from here
    assert g.board[(1, 1)].effects == set() # wielder picked up the acid that was here
    assert g.board[(2, 1)].effects == set() # wielder picked up the acid
    assert g.board[(2, 1)].unit.hp == 6  # wielder took 4 damage because it got acid and THEN took 2 self damage x2
    assert g.board[(2, 1)].unit.effects == {Effects.ACID} # wielder picked up acid
    # I gave the mech more health so we can tell exactly how much HP was lost
    #assert g.board[(2, 1)].unit.effects == set() # wielder DIED from taking 4 self damage on acid
    #assert g.board[(2, 1)].unit.hp == 1  # this is the corpse
    #assert g.board[(2, 1)].unit.type == 'mechcorpse'  # don't believe me?
    assert g.board[(3, 1)].effects == set() # the vek here got the acid
    assert g.board[(3, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == {Effects.ACID} # the vek pushed from the tile died here and dropped acid. he took 6 damage
    assert g.board[(4, 1)].unit == None  # the vek pushed from the tile died here and dropped acid. he took 6 damage
    assert g.board[(2, 2)].effects == set()
    assert g.board[(2, 2)].unit == None # no unit here
    assert g.board[(2, 3)].effects == {Effects.ACID} # vek dropped acid here
    assert g.board[(2, 3)].unit == None # vek took 6 damage

def t_WeaponUnstableCannonLowPower():
    "Shoot the Unstable Cannon with no power"
    g = Game()
    for x in range(1, 5):
        g.board[(x, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(2, 1)].unit.hp == 3
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from here
    assert g.board[(2, 1)].effects == {Effects.FIRE} # tile caught fire from self-damage
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()  # No new unit effects
    assert g.board[(1, 1)].unit.hp == 2  # took 1 self-damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # forest is not on fire
    assert g.board[(4, 1)].unit.effects == set() # vek is not on fire
    assert g.board[(4, 1)].unit.hp == 3 # vek took 2 damage

def t_WeaponUnstableCannonPower1():
    "Shoot the Unstable Cannon with first power"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # No new effects
    assert g.board[(1, 1)].unit.hp == 1 # took 2 self-damage
    assert g.board[(2, 1)].effects == set() # no tile effects
    assert g.board[(2, 1)].unit == None # wielder pushed from here
    assert g.board[(3, 1)].effects == set() # no tile effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 2 # vek took 3 damage

def t_WeaponUnstableCannonPower2():
    "Shoot the Unstable Cannon with second power"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # No new effects
    assert g.board[(1, 1)].unit.hp == 2 # took 1 self-damage
    assert g.board[(2, 1)].effects == set() # no tile effects
    assert g.board[(2, 1)].unit == None # wielder pushed from here
    assert g.board[(3, 1)].effects == set() # no tile effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 2 # vek took 3 damage

def t_WeaponUnstableCannonMaxPower():
    "Shoot the Unstable Cannon with max power"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # No new effects
    assert g.board[(1, 1)].unit.hp == 1 # took 2 self-damage
    assert g.board[(2, 1)].effects == set() # no tile effects
    assert g.board[(2, 1)].unit == None # wielder pushed from here
    assert g.board[(3, 1)].effects == set() # no tile effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 1 # vek took 4 damage

def t_WeaponUnstableCannonWielderForest():
    "Shoot the Unstable Cannon with max power with the weapon wielder starting a forest"
    g = Game()
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].createUnitHere(Unit_Unstable_Mech(g, weapon1=Weapon_UnstableCannon(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # No new effects, the wielder does NOT catch on fire because he's pushed off before it happens.
    assert g.board[(1, 1)].unit.hp == 1 # took 2 self-damage
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught on fire
    assert g.board[(2, 1)].unit == None # wielder pushed from here
    assert g.board[(3, 1)].effects == set() # no tile effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 1 # vek took 4 damage

def t_WeaponAcidProjector():
    "Shoot the acid projector at a unit."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # not needed here, nothing got hurt.
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].effects == set()  # no tile effects
    assert g.board[(2, 1)].unit == None  # no unit here
    assert g.board[(3, 1)].effects == set()  # no tile effects
    assert g.board[(3, 1)].unit.effects == {Effects.ACID}
    assert g.board[(3, 1)].unit.hp == 5

def t_WeaponAcidProjectorShielded():
    "Shoot the acid projector at a shielded unit."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g, effects={Effects.SHIELD}))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt() # not needed here, nothing got hurt.
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].effects == set()  # no tile effects
    assert g.board[(2, 1)].unit == None  # no unit here
    assert g.board[(3, 1)].effects == set()  # no tile effects
    assert g.board[(3, 1)].unit.effects == {Effects.ACID, Effects.SHIELD} # shield doesn't protect you from acid from this weapon
    assert g.board[(3, 1)].unit.hp == 5

def t_WeaponAcidProjectorBumpDeath():
    "Shoot the acid projector at a unit that dies to bump damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g, hp=1))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].effects == {Effects.ACID} # dead vek left acid
    assert g.board[(2, 1)].unit == None  # vek died
    assert g.board[(3, 1)].effects == set()  # no tile effects
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.type == 'mountaindamaged'

def t_WeaponAcidProjectorOutOfWater():
    "If mech stands in water and is hit by the acid gun, the water does not gain acid. The mech is pushed out and gains acid."
    g = Game()
    g.board[(2, 1)].replaceTile(Tile_Water(g))
    g.board[(1, 1)].createUnitHere(Unit_Nano_Mech(g, weapon1=Weapon_AcidProjector(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g, attributes={Attributes.MASSIVE})) # lol massive alpha scorpion
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].effects == {Effects.SUBMERGED} # water didn't get acid
    assert g.board[(2, 1)].unit == None  # vek pushed from here
    assert g.board[(3, 1)].effects == set()  # no tile effects
    assert g.board[(3, 1)].unit.effects == {Effects.ACID} # the unit got acid

def t_WeaponRammingSpeedDefault():
    "Fire the RammingSpeed weapon with no powered upgrades"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_RammingSpeed(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 3  # wielder took 0 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 4 # vek pushed here took 1 damage

def t_WeaponRammingSpeedPower1():
    "Fire the RammingSpeed weapon with the first upgrade powered"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_RammingSpeed(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # never was a unit here
    assert g.board[(1, 1)].effects == {Effects.SMOKE} # smoke was farted
    assert g.board[(2, 1)].unit.hp == 3  # wielder took 0 damage and didn't move
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 4 # vek pushed here took 1 damage

def t_WeaponRammingSpeedPower2():
    "Fire the RammingSpeed weapon with the second upgrade powered"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_RammingSpeed(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder moved
    assert g.board[(2, 1)].unit.hp == 3  # wielder took 0 damage
    assert g.board[(3, 1)].unit == None # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 2 # vek pushed here took 3 damage

def t_WeaponRammingSpeedFullPower():
    "Fire the RammingSpeed weapon with the both upgrades powered"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoBeetle_Mech(g, weapon1=Weapon_RammingSpeed(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None  # never was a unit here
    assert g.board[(1, 1)].effects == {Effects.SMOKE}  # smoke was farted
    assert g.board[(2, 1)].unit.hp == 3  # wielder took 0 damage and didn't move
    assert g.board[(3, 1)].unit == None  # vek pushed off this tile
    assert g.board[(4, 1)].unit.hp == 2 # vek pushed here took 3 damage

def t_WeaponNeedleShotNoPower():
    "Fire the NeedleShot weapon with the no upgrades powered"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_NeedleShot(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.hp == 3 # this vek took 2 damage; 1 from weapon, 1 from bump
    assert g.board[(3, 1)].unit.hp == 4 # this one took 1 bump damage
    assert g.board[(4, 1)].unit.hp == 5 # this one took none
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None # Nothing got pushed here

def t_WeaponNeedleShot1Power():
    "Fire the NeedleShot weapon with the 1 upgrade powered"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_NeedleShot(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.hp == 3 # this vek took 2 damage from weapon, no bump
    assert g.board[(3, 1)].unit.hp == 2 # this one took 3 damage; 2 from weapon, 1 from bump
    assert g.board[(4, 1)].unit.hp == 4 # this one took 1 bump damage
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None # Nothing got pushed here

def t_WeaponNeedleShot2Power():
    "Fire the NeedleShot weapon with the 2nd upgrade powered. This is no different than just having the first done"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_NeedleShot(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.hp == 3 # this vek took 2 damage from weapon, no bump
    assert g.board[(3, 1)].unit.hp == 2 # this one took 3 damage; 2 from weapon, 1 from bump
    assert g.board[(4, 1)].unit.hp == 4 # this one took 1 bump damage
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None # Nothing got pushed here

def t_WeaponNeedleShotFullPower():
    "Fire the NeedleShot weapon with full upgrade power."
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_NeedleShot(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 3
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.hp == 2 # this vek took 3 damage from weapon, no bump
    assert g.board[(3, 1)].unit.hp == 2 # this one took 3 damage from weapon
    assert g.board[(4, 1)].unit == None # last vek got pushed from here
    assert g.board[(4, 1)].effects == {Effects.FIRE}  # forest is on fire
    assert g.board[(5, 1)].unit.hp == 2 # this one took 3 damage from weapon
    assert g.board[(5, 1)].unit.effects == set() # the vek didn't catch on fire

def t_WeaponExplosiveGooNoPower():
    "Fire the NeedleShot weapon with no upgrade power."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
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
    assert g.board[(1, 3)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 3)].unit.effects == set() # no unit effects
    del allunits[(1, 3)]  # delete the wielder from allunits
    assert g.board[(4, 3)].unit.hp == 4  # target took 1 damage
    del allunits[(4, 3)]  # delete the target unit from all
    assert g.board[(3, 3)].unit.hp == 4  #  took 1 bump damage
    del allunits[(3, 3)]  # delete this bumped  unit from all
    assert g.board[(2, 3)].unit.hp == 4  #  took 1 bump damage
    del allunits[(2, 3)]  # delete this bumped  unit from all
    assert g.board[(4, 4)].unit.hp == 4  #  took 1 bump damage
    del allunits[(4, 4)]  # delete this bumped  unit from all
    assert g.board[(4, 5)].unit.hp == 4  #  took 1 bump damage
    del allunits[(4, 5)]  # delete this bumped  unit from all
    assert g.board[(5, 3)].unit.hp == 4  #  took 1 bump damage
    del allunits[(5, 3)]  # delete this bumped  unit from all
    assert g.board[(6, 3)].unit.hp == 4  #  took 1 bump damage
    del allunits[(6, 3)]  # delete this bumped  unit from all
    assert g.board[(4, 2)].unit.hp == 4  #  took 1 bump damage
    del allunits[(4, 2)]  # delete this bumped  unit from all
    assert g.board[(4, 1)].unit.hp == 4  #  took 1 bump damage
    del allunits[(4, 1)]  # delete this bumped  unit from all
    for u in allunits:
        assert g.board[u].unit.hp == 5 # no hp change to all other vek

def t_WeaponExplosiveGooPower2():
    "Fire the NeedleShot weapon with extra damage powered."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
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
    assert g.board[(1, 3)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 3)].unit.effects == set() # no unit effects
    del allunits[(1, 3)]  # delete the wielder from allunits
    assert g.board[(4, 3)].unit.hp == 2  # target took 3 damage
    del allunits[(4, 3)]  # delete the target unit from all
    assert g.board[(3, 3)].unit.hp == 4  #  took 1 bump damage
    del allunits[(3, 3)]  # delete this bumped  unit from all
    assert g.board[(2, 3)].unit.hp == 4  #  took 1 bump damage
    del allunits[(2, 3)]  # delete this bumped  unit from all
    assert g.board[(4, 4)].unit.hp == 4  #  took 1 bump damage
    del allunits[(4, 4)]  # delete this bumped  unit from all
    assert g.board[(4, 5)].unit.hp == 4  #  took 1 bump damage
    del allunits[(4, 5)]  # delete this bumped  unit from all
    assert g.board[(5, 3)].unit.hp == 4  #  took 1 bump damage
    del allunits[(5, 3)]  # delete this bumped  unit from all
    assert g.board[(6, 3)].unit.hp == 4  #  took 1 bump damage
    del allunits[(6, 3)]  # delete this bumped  unit from all
    assert g.board[(4, 2)].unit.hp == 4  #  took 1 bump damage
    del allunits[(4, 2)]  # delete this bumped  unit from all
    assert g.board[(4, 1)].unit.hp == 4  #  took 1 bump damage
    del allunits[(4, 1)]  # delete this bumped  unit from all
    for u in allunits:
        assert g.board[u].unit.hp == 5 # no hp change to all other vek

def t_WeaponExplosiveGooPower1():
    "Fire the NeedleShot weapon with extra tile powered."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
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
    assert g.board[(1, 3)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 3)].unit.effects == set() # no unit effects
    del allunits[(1, 3)]  # delete the wielder from allunits
    assert g.board[(4, 3)].unit.hp == 4  # target took 1 damage
    del allunits[(4, 3)]  # delete the target unit from all
    assert g.board[(5, 3)].unit.hp == 4  # 2nd target took 1 normal damage
    del allunits[(5, 3)]  # delete the target unit from all
    assert g.board[(2, 3)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(2, 3)] # delete this bumped unit from all
    assert g.board[(3, 3)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(3, 3)] # delete this bumped unit from all
    assert g.board[(4, 4)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(4, 4)] # delete this bumped unit from all
    assert g.board[(4, 5)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(4, 5)] # delete this bumped unit from all
    assert g.board[(5, 4)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(5, 4)] # delete this bumped unit from all
    assert g.board[(5, 5)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(5, 5)] # delete this bumped unit from all
    assert g.board[(6, 3)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(6, 3)] # delete this bumped unit from all
    assert g.board[(7, 3)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(7, 3)] # delete this bumped unit from all
    assert g.board[(5, 2)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(5, 2)] # delete this bumped unit from all
    assert g.board[(5, 1)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(5, 1)] # delete this bumped unit from all
    assert g.board[(4, 2)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(4, 2)] # delete this bumped unit from all
    assert g.board[(4, 1)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(4, 1)] # delete this bumped unit from all
    for u in allunits:
        assert g.board[u].unit.hp == 5 # no hp change to all other vek

def t_WeaponExplosiveGooFullPower():
    "Fire the NeedleShot weapon with full power."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
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
    assert g.board[(1, 3)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 3)].unit.effects == set() # no unit effects
    del allunits[(1, 3)]  # delete the wielder from allunits
    assert g.board[(4, 3)].unit.hp == 2  # target took 3 damage
    del allunits[(4, 3)]  # delete the target unit from all
    assert g.board[(5, 3)].unit.hp == 2  # 2nd target took 3 normal damage
    del allunits[(5, 3)]  # delete the target unit from all
    assert g.board[(2, 3)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(2, 3)] # delete this bumped unit from all
    assert g.board[(3, 3)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(3, 3)] # delete this bumped unit from all
    assert g.board[(4, 4)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(4, 4)] # delete this bumped unit from all
    assert g.board[(4, 5)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(4, 5)] # delete this bumped unit from all
    assert g.board[(5, 4)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(5, 4)] # delete this bumped unit from all
    assert g.board[(5, 5)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(5, 5)] # delete this bumped unit from all
    assert g.board[(6, 3)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(6, 3)] # delete this bumped unit from all
    assert g.board[(7, 3)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(7, 3)] # delete this bumped unit from all
    assert g.board[(5, 2)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(5, 2)] # delete this bumped unit from all
    assert g.board[(5, 1)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(5, 1)] # delete this bumped unit from all
    assert g.board[(4, 2)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(4, 2)] # delete this bumped unit from all
    assert g.board[(4, 1)].unit.hp == 4 # unit took 1 bump damage
    del allunits[(4, 1)] # delete this bumped unit from all
    for u in allunits:
        assert g.board[u].unit.hp == 5 # no hp change to all other vek

def t_WeaponSidewinderFistNoPower():
    "Fire Sidewinder fist with no power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=False, power2=False)))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # UP, 1
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(2, 2)].unit == None  # target pushed off this tile
    assert g.board[(1, 2)].unit.hp == 3  # target took 2 damage

def t_WeaponSidewinderFistPower1():
    "Fire Sidewinder fist with 1 power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=True, power2=False)))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # UP, 1
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(2, 2)].unit == None  # target pushed off this tile
    assert g.board[(1, 2)].unit.hp == 2  # target took 3 damage

def t_WeaponSidewinderFistPower2():
    "Fire Sidewinder fist with the other 1 power (no difference)."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=False, power2=True)))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # UP, 1
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(2, 2)].unit == None  # target pushed off this tile
    assert g.board[(1, 2)].unit.hp == 2  # target took 3 damage

def t_WeaponSidewinderFistFullPower():
    "Fire Sidewinder fist with the full power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=True, power2=True)))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # UP, 1
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.effects == set() # no unit effects
    assert g.board[(2, 2)].unit == None  # target pushed off this tile
    assert g.board[(1, 2)].unit.hp == 1  # target took 4 damage

def t_WeaponSidewinderFistFullPowerDash():
    "Fire Sidewinder fist with the full power at a different angle and with the dash."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SidewinderFist(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # wielder moved from this square
    assert g.board[(3, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(3, 1)].unit.effects == set() # no unit effects
    assert g.board[(4, 1)].unit == None  # target pushed off this tile
    assert g.board[(4, 2)].unit.hp == 1  # target took 4 damage

def t_WeaponRocketFistNoPower():
    "Fire RocketFist with the no power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RocketFist(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from starting square
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(3, 1)].unit == None  # target pushed from here
    assert g.board[(4, 1)].unit.hp == 3  # target took 2 damage
    assert g.board[(4, 1)].unit.effects == set()  # no new effects

def t_WeaponRocketFist2ndPower():
    "Fire RocketFist with extra damage powered."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RocketFist(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from starting square
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(3, 1)].unit == None  # target pushed from here
    assert g.board[(4, 1)].unit.hp == 1  # target took 4 damage
    assert g.board[(4, 1)].unit.effects == set()  # no new effects

def t_WeaponRocketFist1stPower():
    "Fire RocketFist with rocket projectile powered."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RocketFist(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from starting square
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(4, 1)].unit == None  # target pushed from here
    assert g.board[(5, 1)].unit.hp == 3  # target took 2 damage
    assert g.board[(5, 1)].unit.effects == set()  # no new effects

def t_WeaponRocketFistFullPower():
    "Fire RocketFist with full power."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RocketFist(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(2, 1)].unit.weapon1.genShots()
    for r in range(2):
        shot = next(gs)
    g.board[(2, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(2, 1)].unit == None  # wielder pushed from starting square
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(4, 1)].unit == None  # target pushed from here
    assert g.board[(5, 1)].unit.hp == 1  # target took 4 damage
    assert g.board[(5, 1)].unit.effects == set()  # no new effects

def t_WeaponExplosiveVentsNoPower():
    "Shoot explosive vents with no power."
    g = Game()
    g.board[(1, 2)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ExplosiveVents(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # () no choice!
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 1)].effects == set()  # wielder's tile untouched
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].unit == None  # never was a unit here
    assert g.board[(1, 2)].effects == {Effects.SMOKE} # sand was hit
    assert g.board[(2, 1)].unit == None  # target pushed from here
    assert g.board[(3, 1)].unit.hp == 4  # target took 1 damage
    assert g.board[(3, 1)].unit.effects == set()  # no new effects

def t_WeaponExplosiveVents1Power():
    "Shoot explosive vents with 1 power."
    g = Game()
    g.board[(1, 2)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ExplosiveVents(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # () no choice!
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 1)].effects == set()  # wielder's tile untouched
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].unit == None  # never was a unit here
    assert g.board[(1, 2)].effects == {Effects.SMOKE} # sand was hit
    assert g.board[(2, 1)].unit == None  # target pushed from here
    assert g.board[(3, 1)].unit.hp == 3  # target took 2 damage
    assert g.board[(3, 1)].unit.effects == set()  # no new effects

def t_WeaponExplosiveVents2ndPower():
    "Shoot explosive vents with 2nd power."
    g = Game()
    g.board[(1, 2)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ExplosiveVents(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # () no choice!
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 1)].effects == set()  # wielder's tile untouched
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].unit == None  # never was a unit here
    assert g.board[(1, 2)].effects == {Effects.SMOKE} # sand was hit
    assert g.board[(2, 1)].unit == None  # target pushed from here
    assert g.board[(3, 1)].unit.hp == 3  # target took 2 damage
    assert g.board[(3, 1)].unit.effects == set()  # no new effects

def t_WeaponExplosiveVentsMaxPower():
    "Shoot explosive vents with max power."
    g = Game()
    g.board[(1, 2)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].replaceTile(Tile_Sand(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ExplosiveVents(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # () no choice!
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(1, 1)].effects == set()  # wielder's tile untouched
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 2)].unit == None  # never was a unit here
    assert g.board[(1, 2)].effects == {Effects.SMOKE} # sand was hit
    assert g.board[(2, 1)].unit == None  # target pushed from here
    assert g.board[(3, 1)].unit.hp == 2  # target took 3 damage
    assert g.board[(3, 1)].unit.effects == set()  # no new effects

def t_WeaponPrimeSpearNoPower():
    "Fire the PrimeSpear weapon with the no upgrades powered"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 1)].effects == set() # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set() # no effects
    assert g.board[(2, 1)].unit.hp == 3 # this vek took 2 damage; 2 from weapon, 0 from bump
    assert g.board[(3, 1)].unit.hp == 2 # this one took 3 damage, 2 weapon, 1 bump damage
    assert g.board[(3, 1)].effects == set() # this tile didn't get acid
    assert g.board[(3, 1)].unit.effects == set()  # this unit didn't get acid
    assert g.board[(4, 1)].unit.hp == 4 # this one took 1 bump damage
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None # Nothing got pushed here

def t_WeaponPrimeSpear1Power():
    "Fire the PrimeSpear weapon with the 1 upgrade powered"
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 1)].effects == set()  # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit.hp == 3  # this vek took 2 damage; 2 from weapon, 0 from bump
    assert g.board[(3, 1)].unit.hp == 2  # this one took 3 damage, 2 weapon, 1 bump damage
    assert g.board[(3, 1)].effects == set()  # this tile didn't get acid
    assert g.board[(3, 1)].unit.effects == {Effects.ACID}  # this unit DID get acid
    assert g.board[(4, 1)].unit.hp == 4  # this one took 1 bump damage
    assert g.board[(4, 1)].effects == set()  # forest is fine
    assert g.board[(5, 1)].unit == None  # Nothing got pushed here

def t_WeaponPrimeSpear2Power():
    "Fire the PrimeSpear weapon with the 2nd upgrade powered. This increases range."
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 1)].effects == set()  # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 3
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit.hp == 3  # this vek took 2 damage; 2 from weapon, 0 from bump
    assert g.board[(3, 1)].unit.hp == 3  # this one took 2 damage, 2 weapon, 0 bump damage
    assert g.board[(3, 1)].effects == set()  # this tile didn't get acid
    assert g.board[(3, 1)].unit.effects == set()  # this unit didn't get acid
    assert g.board[(4, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == {Effects.FIRE} # forest is FIRE
    assert g.board[(5, 1)].unit.hp == 3  # this one took 2 damage; 2 weapon, 0 bump damage
    assert g.board[(5, 1)].unit.effects == set() # no acid here

def t_WeaponPrimeSpearFullPower():
    "Fire the PrimeSpear weapon with full upgrade power."
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(4, 1)].effects == set()  # forest is fine
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(6):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 3
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit.hp == 3  # this vek took 2 damage; 2 from weapon, 0 from bump
    assert g.board[(3, 1)].unit.hp == 3  # this one took 2 damage, 2 weapon, 0 bump damage
    assert g.board[(3, 1)].effects == set()  # this tile didn't get acid
    assert g.board[(3, 1)].unit.effects == set()  # this unit didn't get acid
    assert g.board[(4, 1)].unit == None # unit pushed from here
    assert g.board[(4, 1)].effects == {Effects.FIRE} # forest is FIRE
    assert g.board[(5, 1)].unit.hp == 3  # this one took 2 damage; 2 weapon, 0 bump damage
    assert g.board[(5, 1)].unit.effects == {Effects.ACID} # this unit did get acid

def t_WeaponPrimeSpearAcidWeirdness1():
    "Fire the PrimeSpear weapon and test the weirdness that happens when the unit that gets acid dies from this attack."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g, hp=2))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.effects == set() # no acid on unit
    assert g.board[(2, 1)].effects == set()  # no acid on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit == None  # vek pushed from here
    assert g.board[(2, 1)].effects == {Effects.ACID}  # this tile got acid from the buggy/weird behavior of the acid spear
    assert g.board[(3, 1)].unit == None # the vek pushed here died
    assert g.board[(3, 1)].effects == {Effects.ACID}  # this tile got acid from the vek that got it and then died here

def t_WeaponPrimeSpearAcidWeirdness2():
    "Fire the PrimeSpear weapon and test the weirdness that happens when a mountain that gets acid dies from this attack."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.effects == set() # no acid on unit
    assert g.board[(2, 1)].effects == set()  # no acid on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit.type == 'mountaindamaged'
    assert g.board[(2, 1)].effects == set()  # no acid here yet
    assert g.board[(2, 1)].unit.effects == set() # none here yet
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit == None # mountain died
    assert g.board[(2, 1)].effects == {Effects.ACID}  # Acid left here from dead mountain or something

def t_WeaponPrimeSpearAcidWeirdness3():
    "Fire the PrimeSpear weapon and test the non-weirdness that happens when a unit dies from this attack but doesn't move tiles."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PrimeSpear(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaBeetle(g, hp=1))
    g.board[(3, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.effects == set() # no acid on unit
    assert g.board[(2, 1)].effects == set()  # no acid on tile
    assert g.board[(3, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.effects == set()  # no acid on unit
    assert g.board[(3, 1)].effects == set()  # no acid on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for r in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to the wielder
    assert g.board[(1, 1)].unit.effects == set()  # no effects
    assert g.board[(2, 1)].unit == None # this unit died
    assert g.board[(2, 1)].effects == {Effects.ACID}  # acid on tile
    assert g.board[(3, 1)].unit.type == 'mountaindamaged'
    assert g.board[(3, 1)].effects == set()  # no acid here yet
    assert g.board[(3, 1)].unit.effects == set() # none here yet

def t_WeaponVortexFistNoPower():
    "Fire the VortexFist weapon with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_VortexFist(power1=False, power2=False), hp=5))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5 # gave it more health so it doesn't die
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set() # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(1, 2)].unit.hp == 5
    assert g.board[(1, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(1, 2)].effects == set()  # no effects on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in gs: # this should only yield one empty value
        g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 1
        g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # 2 self-damage
    assert g.board[(2, 1)].unit == None # vek pushed from here
    assert g.board[(2, 2)].unit.hp == 3 # took 2 damage
    assert g.board[(2, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 2)].effects == set()  # no effects on tile
    assert g.board[(1, 2)].unit.hp == 3 # this one wasn't pushed because there's nowhere to go
    assert g.board[(1, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(1, 2)].effects == set()  # no effects on tile

def t_WeaponVortexFist1Power():
    "Fire the VortexFist weapon with 1 power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_VortexFist(power1=True, power2=False), hp=5))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5 # gave it more health so it doesn't die
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set() # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(1, 2)].unit.hp == 5
    assert g.board[(1, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(1, 2)].effects == set()  # no effects on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in gs: # this should only yield one empty value
        g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 1
        g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4 # 1 self-damage
    assert g.board[(2, 1)].unit == None # vek pushed from here
    assert g.board[(2, 2)].unit.hp == 3 # took 2 damage
    assert g.board[(2, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 2)].effects == set()  # no effects on tile
    assert g.board[(1, 2)].unit.hp == 3 # this one wasn't pushed because there's nowhere to go
    assert g.board[(1, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(1, 2)].effects == set()  # no effects on tile

def t_WeaponVortexFist2Power():
    "Fire the VortexFist weapon with 2nd power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_VortexFist(power1=False, power2=True), hp=5))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5 # gave it more health so it doesn't die
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set() # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(1, 2)].unit.hp == 5
    assert g.board[(1, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(1, 2)].effects == set()  # no effects on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in gs: # this should only yield one empty value
        g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 1
        g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # 2 self-damage
    assert g.board[(2, 1)].unit == None # vek pushed from here
    assert g.board[(2, 2)].unit.hp == 2 # took 3 damage
    assert g.board[(2, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 2)].effects == set()  # no effects on tile
    assert g.board[(1, 2)].unit.hp == 2 # this one wasn't pushed because there's nowhere to go
    assert g.board[(1, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(1, 2)].effects == set()  # no effects on tile

def t_WeaponVortexFistFullPower():
    "Fire the VortexFist weapon with full power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_VortexFist(power1=True, power2=True), hp=5))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5 # gave it more health so it doesn't die
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set() # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(1, 2)].unit.hp == 5
    assert g.board[(1, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(1, 2)].effects == set()  # no effects on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in gs: # this should only yield one empty value
        g.board[(1, 1)].unit.weapon1.shoot(*shot)  # RIGHT, 1
        g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4 # 1 self-damage
    assert g.board[(2, 1)].unit == None # vek pushed from here
    assert g.board[(2, 2)].unit.hp == 2 # took 3 damage
    assert g.board[(2, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 2)].effects == set()  # no effects on tile
    assert g.board[(1, 2)].unit.hp == 2 # this one wasn't pushed because there's nowhere to go
    assert g.board[(1, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(1, 2)].effects == set()  # no effects on tile

def t_WeaponTitaniteBladeNoPower():
    "Fire the TitaniteBlade weapon with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_TitaniteBlade(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set() # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(2, 2)].unit.hp == 5
    assert g.board[(2, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 2)].effects == set()  # no effects on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in gs: # this should yield (UP) only since we only have one use
        g.board[(1, 1)].unit.weapon1.shoot(*shot)
        g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5 # this vek was untouched
    assert g.board[(2, 1)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(2, 2)].unit == None # vek pushed from here
    assert g.board[(2, 3)].unit.hp == 3 # took 2 damage
    assert g.board[(2, 3)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 3)].effects == set()  # no effects on tile

def t_WeaponTitaniteBlade1Power():
    "Fire the TitaniteBlade weapon with 1 power. This has no effect on the outcome."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_TitaniteBlade(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set() # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(2, 2)].unit.hp == 5
    assert g.board[(2, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 2)].effects == set()  # no effects on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in gs: # this should yield (UP) only since we only have one use
        g.board[(1, 1)].unit.weapon1.shoot(*shot)
        g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5 # this vek was untouched
    assert g.board[(2, 1)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(2, 2)].unit == None # vek pushed from here
    assert g.board[(2, 3)].unit.hp == 3 # took 2 damage
    assert g.board[(2, 3)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 3)].effects == set()  # no effects on tile

def t_WeaponTitaniteBladeExtraUse():
    "Fire the TitaniteBlade weapon with 1 power and an extra use given."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_TitaniteBlade(power1=True, power2=False, usesremaining=2)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set() # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(2, 2)].unit.hp == 5
    assert g.board[(2, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 2)].effects == set()  # no effects on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in gs: # this should yield (UP) and (RIGHT) since we now have 2 uses
        g.board[(1, 1)].unit.weapon1.shoot(*shot)
        g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit == None # Pushed from this square
    assert g.board[(3, 1)].unit.hp == 3  # this vek took 2 damage
    assert g.board[(3, 1)].unit.effects == set()  # no effects on unit
    assert g.board[(3, 1)].effects == set()  # no effects on tile
    assert g.board[(2, 2)].unit == None # vek pushed from here
    assert g.board[(2, 3)].unit.hp == 3 # took 2 damage
    assert g.board[(2, 3)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 3)].effects == set()  # no effects on tile

def t_WeaponTitaniteBlade2Power():
    "Fire the TitaniteBlade weapon with extra damage powered."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_TitaniteBlade(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set() # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(2, 2)].unit.hp == 5
    assert g.board[(2, 2)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 2)].effects == set()  # no effects on tile
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in gs: # this should yield (UP) only since we only have one use and firing uses it
        g.board[(1, 1)].unit.weapon1.shoot(*shot)
        g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5 # this vek was untouched
    assert g.board[(2, 1)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 1)].effects == set()  # no effects on tile
    assert g.board[(2, 2)].unit == None # vek pushed from here
    assert g.board[(2, 3)].unit.hp == 1 # took 4 damage
    assert g.board[(2, 3)].unit.effects == set()  # no effects on unit
    assert g.board[(2, 3)].effects == set()  # no effects on tile

def t_WeaponTitaniteBlade2Power2():
    "Fire the TitaniteBlade weapon with extra damage powered powered and hit 3 vek at the same time."
    g = Game()
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_TitaniteBlade(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 3)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 2)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 2)].unit.hp == 5
    assert g.board[(2, 3)].unit.hp == 5
    gs = g.board[(1, 2)].unit.weapon1.genShots()
    for s in range(2):
        shot = next(gs)
    g.board[(1, 2)].unit.weapon1.shoot(*shot) # (RIGHT)
    g.flushHurt()
    assert g.board[(1, 2)].unit.hp == 2
    for sq in (2, 1), (2, 2), (2, 3):
        assert g.board[sq].unit == None # unit pushed from here
    for sq in (3, 1), (3, 2), (3, 3):
        assert g.board[sq].unit.hp == 1 # unit took 4 damage and pushed here

def t_WeaponMercuryFistNoPower():
    "Fire the MercuryFist weapon with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_MercuryFist(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1 # this vek took 4 damage
    assert g.board[(2, 2)].unit == None # vek pushed from here
    assert g.board[(2, 3)].unit.hp == 5 # took 0 damage

def t_WeaponMercuryFist2Power():
    "Fire the MercuryFist weapon with extra damage powered."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_MercuryFist(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit == None # this vek took 5 damage and died
    assert g.board[(2, 2)].unit == None # vek pushed from here
    assert g.board[(2, 3)].unit.hp == 5 # took 0 damage

def t_WeaponPhaseCannonNoPower():
    "Fire the PhaseCannon weapon with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PhaseCannon(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1 # building unaffected
    assert g.board[(2, 1)].unit.effects == set() # no shield for building
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].unit.hp == 4 # took 1 damage

def t_WeaponPhaseCannonNoPowerEdgeHit():
    "Fire the PhaseCannon weapon with no power and no enemy to hit."
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PhaseCannon(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(8, 1)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1 # building unaffected
    assert g.board[(2, 1)].unit.effects == set() # no shield for building
    assert g.board[(8, 1)].effects == {Effects.FIRE}

def t_WeaponPhaseCannon1Power():
    "Fire the PhaseCannon weapon with 1 power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PhaseCannon(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1 # building unaffected
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD} # building got shielded
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].unit.hp == 4 # took 1 damage

def t_WeaponPhaseCannon2Power():
    "Fire the PhaseCannon weapon with 2nd power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PhaseCannon(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1 # building unaffected
    assert g.board[(2, 1)].unit.effects == set() # no shield for building
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].unit.hp == 3 # took 2 damage

def t_WeaponPhaseCannonMaxPower():
    "Fire the PhaseCannon weapon with max power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PhaseCannon(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1 # building unaffected
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD} # building got shielded
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].unit.hp == 3 # took 2 damage

def t_WeaponDefShrapnel1():
    "Fire the Def. Shrapnel weapon."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_DefShrapnel(power1=False, power2=False))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 1 # building unaffected
    assert g.board[(2, 1)].unit.effects == set() # no new effects
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(4, 1)].unit.hp == 5 # took 0 damage

def t_WeaponRailCannonNoPower():
    "Fire the RailCannon weapon with no power with the enemy at maximum effective range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RailCannon(power1=False, power2=False)))
    g.board[(6, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit == None # vek pushed from here
    assert g.board[(7, 1)].unit.hp == 3 # took 2 damage

def t_WeaponRailCannon1Power():
    "Fire the RailCannon weapon with 1 power with the enemy at maximum effective range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RailCannon(power1=True, power2=False)))
    g.board[(6, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit == None # vek pushed from here
    assert g.board[(7, 1)].unit.hp == 2 # took 3 damage

def t_WeaponRailCannon2Power():
    "Fire the RailCannon weapon with 2nd power with the enemy at maximum effective range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RailCannon(power1=False, power2=True)))
    g.board[(6, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit == None # vek pushed from here
    assert g.board[(7, 1)].unit.hp == 2 # took 3 damage

def t_WeaponRailCannonMaxPower():
    "Fire the RailCannon weapon with max power with the enemy at maximum effective range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RailCannon(power1=True, power2=True)))
    g.board[(6, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit == None # vek pushed from here
    assert g.board[(7, 1)].unit.hp == 1 # took 4 damage

def t_WeaponRailCannonMaxPowerFar():
    "Fire the RailCannon weapon with max power with the enemy at maximum range to make sure it doesn't take extra damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RailCannon(power1=True, power2=True)))
    g.board[(7, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(7, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(7, 1)].unit == None # vek pushed from here
    assert g.board[(8, 1)].unit.hp == 1 # took 4 damage

def t_WeaponRailCannonMaxPowerClose():
    "Fire the RailCannon weapon with max power with the enemy at minimum range to make sure it doesn't take ANY damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RailCannon(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit == None # vek pushed from here
    assert g.board[(3, 1)].unit.hp == 5 # took 0 damage! pushed only!

def t_WeaponRailCannonMaxPowerMiss():
    "Fire the RailCannon weapon with max power with no enemy to make sure the edge tile is damaged."
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RailCannon(power1=True, power2=True)))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(8, 1)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(8, 1)].effects == {Effects.FIRE}

def t_WeaponShockCannonNoPower():
    "Fire the ShockCannon with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShockCannon(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # wielder took 1 bump damage
    assert g.board[(2, 1)].unit.hp == 3 # vek took 1 damage from gun and 1 bump damage
    assert g.board[(3, 1)].unit == None # this vek pushed
    assert g.board[(4, 1)].unit.hp == 4  # took 1 damage from weapon

def t_WeaponShockCannon1Power():
    "Fire the ShockCannon with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShockCannon(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # wielder took 1 bump damage
    assert g.board[(2, 1)].unit.hp == 2 # vek took 2 damage from gun and 1 bump damage
    assert g.board[(3, 1)].unit == None # this vek pushed
    assert g.board[(4, 1)].unit.hp == 3  # took 2 damage from weapon

def t_WeaponShockCannon2Power():
    "Fire the ShockCannon with 2 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShockCannon(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # wielder took 1 bump damage
    assert g.board[(2, 1)].unit.hp == 2 # vek took 2 damage from gun and 1 bump damage
    assert g.board[(3, 1)].unit == None # this vek pushed
    assert g.board[(4, 1)].unit.hp == 3  # took 2 damage from weapon

def t_WeaponShockCannonMaxPower():
    "Fire the ShockCannon with max power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShockCannon(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # wielder took 1 bump damage
    assert g.board[(2, 1)].unit.hp == 1 # vek took 3 damage from gun and 1 bump damage
    assert g.board[(3, 1)].unit == None # this vek pushed
    assert g.board[(4, 1)].unit.hp == 2  # took 3 damage from weapon

def t_WeaponShockCannonEdge():
    "Fire the ShockCannon and hit the edge"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShockCannon(power1=True, power2=True)))
    g.board[(8, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(8, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder took 0 damage
    assert g.board[(8, 1)].unit == None # this vek pushed
    assert g.board[(7, 1)].unit.hp == 2  # took 3 damage from weapon

def t_WeaponHeavyRocketNoPower():
    "Fire the HeavyRocket with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_HeavyRocket(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder took 0 damage
    assert g.board[(3, 1)].unit.hp == 2 # 3 weapon damage
    assert g.board[(3, 2)].unit == None  # vek pushed from here
    assert g.board[(3, 3)].unit.hp == 5  # took 0 damage, pushed here

def t_WeaponHeavyRocket2Power():
    "Fire the HeavyRocket with extra damage powered."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_HeavyRocket(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g, hp=6))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 6
    assert g.board[(3, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder took 0 damage
    assert g.board[(3, 1)].unit.hp == 1 # 5 weapon damage
    assert g.board[(3, 2)].unit == None  # vek pushed from here
    assert g.board[(3, 3)].unit.hp == 5  # took 0 damage, pushed here

def t_WeaponShrapnelCannonMaxPower():
    "Fire the ShrapnelCannon with extra damage powered."
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShrapnelCannon(power1=True, power2=True)))
    g.board[(3, 4)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 3)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 3)].unit.hp == 2
    assert g.board[(3, 4)].unit.hp == 5
    assert g.board[(3, 3)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 3)].unit.hp == 2 # wielder took 0 damage
    assert g.board[(3, 4)].unit == None # pushed from here
    assert g.board[(3, 3)].unit == None # pushed from here
    assert g.board[(3, 2)].unit == None # pushed from here
    assert g.board[(3, 5)].unit.hp == 2 # 3 weapon damage
    assert g.board[(4, 3)].unit.hp == 2 # 3 weapon damage
    assert g.board[(3, 1)].unit.hp == 2 # 3 weapon damage

def t_WeaponShrapnelCannonNoPower():
    "Fire the ShrapnelCannon with no power."
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShrapnelCannon(power1=False, power2=False)))
    g.board[(3, 4)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 3)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 3)].unit.hp == 2
    assert g.board[(3, 4)].unit.hp == 5
    assert g.board[(3, 3)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 3)].unit.hp == 2 # wielder took 0 damage
    assert g.board[(3, 4)].unit == None # pushed from here
    assert g.board[(3, 3)].unit == None # pushed from here
    assert g.board[(3, 2)].unit == None # pushed from here
    assert g.board[(3, 5)].unit.hp == 3 # 2 weapon damage
    assert g.board[(4, 3)].unit.hp == 3 # 2 weapon damage
    assert g.board[(3, 1)].unit.hp == 3 # 2 weapon damage

def t_WeaponAstraBombsNoPower():
    "Fire the AstraBombs weapon with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AstraBombs(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # (RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder jumped from start position
    assert g.board[(2, 1)].unit.hp == 4 # vek took 1 weapon damage
    assert g.board[(3, 1)].unit.hp == 2  # wielder took 0 damage and jumped to here

def t_WeaponAstraBombsMaxPower():
    "Fire the AstraBombs weapon with Max power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AstraBombs(power1=True, power2=True))) # power1 is ignored
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # (RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder jumped from start position
    assert g.board[(2, 1)].unit.hp == 2 # vek took 3 weapon damage
    assert g.board[(3, 1)].unit.hp == 2  # wielder took 0 damage and jumped to here

def t_WeaponAstraBombsMaxPowerAndRange():
    "Fire the AstraBombs weapon with Max power and hitting as many tiles as possible."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AstraBombs(power1=True, power2=True))) # power1 is ignored
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(6, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(7, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(12):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # (RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder jumped from start position
    assert g.board[(2, 1)].unit.hp == 2 # vek took 3 weapon damage
    assert g.board[(3, 1)].unit.hp == 2  # vek took 3 weapon damage
    assert g.board[(4, 1)].unit.hp == 2  # vek took 3 weapon damage
    assert g.board[(5, 1)].unit.hp == 2  # vek took 3 weapon damage
    assert g.board[(6, 1)].unit.hp == 2  # vek took 3 weapon damage
    assert g.board[(7, 1)].unit.hp == 2  # vek took 3 weapon damage
    assert g.board[(8, 1)].unit.hp == 2  # wielder took 0 damage and jumped to here

def t_WeaponAstraBombsOccupiedTarget():
    "Fire the AstraBombs weapon with the destination spot occupied."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AstraBombs(power1=True, power2=True))) # power1 is ignored
    g.board[(8, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(8, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(12):
        shot = next(gs)
    try:
        g.board[(1, 1)].unit.weapon1.shoot(*shot) # (RIGHT, 7)
    except NullWeaponShot:
        pass # expected
    else:
        assert False # ya fucked up

def t_WeaponHermesEngines1():
    "Fire the HermesEngines weapon."
    g = Game()
    g.board[(1, 3)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_HermesEngines(power1=True, power2=True))) # power1 and power2 is ignored
    for sq in (1, 2), (2, 4), (3, 2), (4, 4), (5, 2), (6, 4), (7, 2), (8, 3):
        g.board[sq].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 3)].unit.hp == 2
    for sq in (1, 2), (2, 4), (3, 2), (4, 4), (5, 2), (6, 4), (7, 2), (8, 3):
        assert g.board[sq].unit.hp == 5
    gs = g.board[(1, 3)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 3)].unit.weapon1.shoot(*shot) # (RIGHT,)
    assert g.board[(1, 3)].unit == None # wielder zoomed from here
    for sq in (1, 2), (2, 4), (3, 2), (4, 4), (5, 2), (6, 4), (7, 2):
        assert g.board[sq].unit == None # all vek pushed from their starting locations except for the final one
    assert g.board[(8, 3)].unit.hp == 5 # this vek untouched
    assert g.board[(7, 3)].unit.hp == 2 # wielder moved here
    for sq in (1, 1), (2, 5), (3, 1), (4, 5), (5, 1), (6, 5), (7, 1):
        assert g.board[sq].unit.hp == 5 # all vek pushed here from their starting locations (except for the end one)

def t_WeaponMicroArtilleryNoPower():
    "Fire the MicroArtillery weapon with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_MicroArtillery(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    assert shot == (Direction.RIGHT, 2)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # (RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to wielder
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(3, 2)].unit.hp == 5 # vek untouched
    assert g.board[(4, 1)].unit.hp == 4 # vek pushed here took 1 damage

def t_WeaponMicroArtilleryPower2():
    "Fire the MicroArtillery weapon with extra damage powered."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_MicroArtillery(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    assert shot == (Direction.RIGHT, 2)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # (RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to wielder
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(3, 2)].unit.hp == 5 # vek untouched
    assert g.board[(4, 1)].unit.hp == 3 # vek pushed here took 2 damage

def t_WeaponMicroArtilleryPower1():
    "Fire the MicroArtillery weapon with extra tiles powered."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_MicroArtillery(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    assert shot == (Direction.RIGHT, 2)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # (RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to wielder
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(3, 2)].unit == None  # vek pushed from here
    assert g.board[(4, 2)].unit.hp == 4 # vek pushed here took 1 damage
    assert g.board[(4, 1)].unit.hp == 4 # vek pushed here took 1 damage

def t_WeaponMicroArtilleryMaxPower():
    "Fire the MicroArtillery weapon with max power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_MicroArtillery(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    assert shot == (Direction.RIGHT, 2)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # (RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # no change to wielder
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(3, 2)].unit == None  # vek pushed from here
    assert g.board[(4, 2)].unit.hp == 3 # vek pushed here took 2 damage
    assert g.board[(4, 1)].unit.hp == 3 # vek pushed here took 2 damage

def t_WeaponAegonMortarNoPower():
    "Fire the AegonMortar with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AegonMortar(power1=False, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder took 0 bump damage
    assert g.board[(3, 1)].unit == None # vek pushed from here
    assert g.board[(2, 1)].unit.hp == 4 # vek took 1 damage from gun
    assert g.board[(3, 1)].unit == None # this vek pushed
    assert g.board[(4, 1)].unit == None  # took 1 damage from weapon
    assert g.board[(5, 1)].unit.hp == 4  # took 1 damage from weapon

def t_WeaponAegonMortar1Power():
    "Fire the AegonMortar with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AegonMortar(power1=True, power2=False)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder took no damage
    assert g.board[(2, 1)].unit.hp == 3 # vek took 2 damage from gun
    assert g.board[(3, 1)].unit == None # this vek pushed
    assert g.board[(4, 1)].unit == None  # this vek pushed
    assert g.board[(5, 1)].unit.hp == 3  # took 2 damage from weapon

def t_WeaponAegonMortar2Power():
    "Fire the AegonMortar with 2 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AegonMortar(power1=False, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder took no damage
    assert g.board[(3, 1)].unit == None  # this vek pushed
    assert g.board[(2, 1)].unit.hp == 3 # vek took 2 damage from gun
    assert g.board[(4, 1)].unit == None # this vek pushed
    assert g.board[(5, 1)].unit.hp == 3  # took 2 damage from weapon

def t_WeaponAegonMortarMaxPower():
    "Fire the AegonMortar with max power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AegonMortar(power1=True, power2=True)))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(3, 1)].unit == None  # this vek pushed
    assert g.board[(2, 1)].unit.hp == 2  # vek took 3 damage from gun
    assert g.board[(4, 1)].unit == None  # this vek pushed
    assert g.board[(5, 1)].unit.hp == 2  # took 3 damage from weapon

def t_WeaponAegonMortarEdge():
    "Fire the AegonMortar and hit the edge"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_AegonMortar(power1=True, power2=True)))
    g.board[(8, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(8, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(12):
        shot = next(gs)
    assert shot == (2, 7)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 7
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder took 0 damage
    assert g.board[(8, 1)].unit == None # this vek pushed
    assert g.board[(7, 1)].unit.hp == 2  # took 3 damage from weapon

def t_WeaponSmokeMortar1():
    "Fire the SmokeMortar similar to the ingame demo."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SmokeMortar(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # wielder took 1 bump damage
    assert g.board[(2, 1)].effects == set() # no tile effects
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 4 # 1 bump damage
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 5 # no damage
    assert g.board[(4, 1)].effects == set() # no tile effects
    assert g.board[(4, 1)].unit == None # no unit here
    assert g.board[(5, 1)].effects == set() # no tile effects
    assert g.board[(5, 1)].unit.effects == set() #
    assert g.board[(5, 1)].unit.hp == 5 # no damage

def t_WeaponSmokeMortar2():
    "Fire the SmokeMortar off board."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SmokeMortar(power1=True, power2=True))) # power is ignored for this weapon
    assert g.board[(1, 1)].unit.hp == 2
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(6):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # UP, 7
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took 0 damage
    assert g.board[(1, 8)].effects == {Effects.SMOKE}

def t_WeaponBurningMortarNoPower():
    "Fire the BurningMortar with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_BurningMortar(power1=False, power2=False))) # power2 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # wielder took 1 self damage
    assert g.board[(1, 1)].unit.effects == set()  # no fire here
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.hp == 5 # 0 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit.hp == 5 # no damage
    assert g.board[(4, 1)].effects == {Effects.FIRE} # no tile effects
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(4, 1)].unit.hp == 5 # no damage
    assert g.board[(3, 2)].effects == {Effects.FIRE}

def t_WeaponBurningMortar1Power():
    "Fire the BurningMortar with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_BurningMortar(power1=True, power2=False))) # power2 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took 0 self damage
    assert g.board[(1, 1)].unit.effects == set()  # no fire here
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].unit.hp == 5 # 0 damage
    assert g.board[(3, 1)].effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(3, 1)].unit.hp == 5 # no damage
    assert g.board[(4, 1)].effects == {Effects.FIRE} # no tile effects
    assert g.board[(4, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(4, 1)].unit.hp == 5 # no damage
    assert g.board[(3, 2)].effects == {Effects.FIRE}

def t_WeaponRainingDeathNoPower():
    "Fire the RainingDeath similar to the ingame demo with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(5, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(9):
        shot = next(gs)
    assert shot == (Direction.RIGHT, 4)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 4
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 self damage
    assert g.board[(2, 1)].unit == None  # Building died
    assert g.board[(3, 1)].unit.hp == 4 # 1 damage
    assert g.board[(4, 1)].unit.hp == 4  # 1 damage
    assert g.board[(5, 1)].unit.hp == 3  # 2 damage on final tile

def t_WeaponRainingDeath1Power():
    "Fire the RainingDeath similar to the ingame demo with 1 power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=True, power2=False), hp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(5, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(9):
        shot = next(gs)
    assert shot == (Direction.RIGHT, 4)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 4
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 self damage
    assert g.board[(2, 1)].unit.hp == 1 # building took no damage
    assert g.board[(3, 1)].unit.hp == 4 # 1 damage
    assert g.board[(4, 1)].unit.hp == 4  # 1 damage
    assert g.board[(5, 1)].unit.hp == 3  # 2 damage on final tile

def t_WeaponRainingDeath2Power():
    "Fire the RainingDeath similar to the ingame demo with 2nd power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=True), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(5, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(9):
        shot = next(gs)
    assert shot == (Direction.RIGHT, 4)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 4
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # wielder took 2 self damage
    assert g.board[(2, 1)].unit == None  # Building died
    assert g.board[(3, 1)].unit.hp == 3 # 2 damage
    assert g.board[(4, 1)].unit.hp == 3  # 2 damage
    assert g.board[(5, 1)].unit.hp == 2  # 3 damage on final tile

def t_WeaponRainingDeathMaxPower():
    "Fire the RainingDeath similar to the ingame demo with MAX power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=True, power2=True), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Building(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(5, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(9):
        shot = next(gs)
    assert shot == (Direction.RIGHT, 4)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 4
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # wielder took 2 self damage
    assert g.board[(2, 1)].unit.hp == 1 # building took no damage
    assert g.board[(3, 1)].unit.hp == 3 # 2 damage
    assert g.board[(4, 1)].unit.hp == 3  # 2 damage
    assert g.board[(5, 1)].unit.hp == 2  # 3 damage on final tile

def t_WeaponHeavyArtilleryNoPower():
    "Fire the HeavyArtillery with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_HeavyArtillery(power1=False, power2=False))) # power1 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.hp == 3 # 2 damage
    assert g.board[(3, 1)].unit.hp == 3 # 2 damage
    assert g.board[(4, 1)].unit.hp == 3 # 2 damage

def t_WeaponHeavyArtillery1Power():
    "Fire the HeavyArtillery with 1 power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_HeavyArtillery(power1=False, power2=True))) # power1 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(2, 1)].unit.hp == 2 # 3 damage
    assert g.board[(3, 1)].unit.hp == 2 # 3 damage
    assert g.board[(4, 1)].unit.hp == 2 # 3 damage

def t_WeaponGeminiMissilesNoPower():
    "Fire the GeminiMissiles with no power"
    g = Game()
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_GeminiMissiles(power1=False, power2=False))) # power1 is ignored for this weapon
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 3)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 2)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 3)].unit.hp == 5
    gs = g.board[(1, 2)].unit.weapon1.genShots()
    for shot in range(6):
        shot = next(gs)
    g.board[(1, 2)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 2)].unit.hp == 2  # wielder took no damage
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 3)].unit == None
    assert g.board[(4, 1)].unit.hp == 2 # 3 damage
    assert g.board[(4, 3)].unit.hp == 2 # 3 damage

def t_WeaponGeminiMissilesMaxPower():
    "Fire the GeminiMissiles with Max power"
    g = Game()
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_GeminiMissiles(power1=True, power2=True))) # power1 is ignored for this weapon
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 3)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 2)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 3)].unit.hp == 5
    gs = g.board[(1, 2)].unit.weapon1.genShots()
    for shot in range(6):
        shot = next(gs)
    g.board[(1, 2)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(1, 2)].unit.hp == 2  # wielder took no damage
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 3)].unit == None
    assert g.board[(4, 1)].unit.hp == 1 # 4 damage
    assert g.board[(4, 3)].unit.hp == 1 # 4 damage

def t_WeaponGeminiMissilesMaxPowerOffBoard():
    "Fire the GeminiMissiles with Max power so that one of the missiles is off board"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_GeminiMissiles(power1=True, power2=True))) # power1 is ignored for this weapon
    g.board[(2, 8)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 8)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(6):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # UP, 7
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took no damage
    assert g.board[(2, 8)].unit.hp == 1 # 4 damage

def t_WeaponSmokePelletsNoPower():
    "Fire the SmokePellets with no power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SmokePellets(power1=False, power2=False))) # power2 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Flame_Mech(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(1, 2)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # ()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(1, 2)].effects == {Effects.SMOKE}

def t_WeaponSmokePelletsMaxPower():
    "Fire the SmokePellets with max power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_SmokePellets(power1=True, power2=True))) # power2 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Flame_Mech(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(1, 2)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # ()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set() # self not smoked
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(1, 2)].effects == set() # friendly not smoked

def t_WeaponFireBeam():
    "Fire the FireBeam with max power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_FireBeam(power1=False, power2=False))) # power2 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Flame_Mech(g))
    g.board[(4, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(4, 1)].unit.hp == 1
    assert g.board[(4, 1)].effects == set()
    assert g.board[(5, 1)].unit == None
    assert g.board[(5, 1)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(4, 1)].unit.hp == 1
    assert g.board[(4, 1)].effects == {Effects.FIRE}
    assert g.board[(5, 1)].unit == None
    assert g.board[(5, 1)].effects == set() # mountain blocked this tile from catching on fire

def t_WeaponFrostBeam():
    "Fire the FrostBeam with max power"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_FrostBeam(power1=False, power2=False))) # power2 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Flame_Mech(g))
    g.board[(4, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(4, 1)].unit.hp == 1
    assert g.board[(4, 1)].effects == set()
    assert g.board[(5, 1)].unit == None
    assert g.board[(5, 1)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}
    assert g.board[(4, 1)].unit.hp == 1
    assert g.board[(4, 1)].unit.effects == {Effects.ICE}
    assert g.board[(5, 1)].unit == None
    assert g.board[(5, 1)].effects == set() # mountain blocked this tile from catching on fire

def t_WeaponShieldArrayNoPower():
    "Fire the ShieldArray with no power in the corner of the map"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShieldArray(power1=False, power2=False)))  # power2 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Flame_Mech(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(1, 2)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # ()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(1, 2)].unit.effects == {Effects.SHIELD}
    assert g.board[(2, 2)].unit.hp == 5
    assert g.board[(2, 2)].unit.effects == set() # this unit not shielded

def t_WeaponShieldArrayMaxPower():
    "Fire the ShieldArray with max power in the corner of the map"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ShieldArray(power1=True, power2=True)))  # power2 is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_Flame_Mech(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(1, 2)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # ()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(1, 2)].unit.hp == 3
    assert g.board[(1, 2)].unit.effects == {Effects.SHIELD}
    assert g.board[(2, 2)].unit.hp == 5
    assert g.board[(2, 2)].unit.effects == {Effects.SHIELD}

def t_WeaponShieldArrayCenterLow():
    "Fire the ShieldArray with no power in the center of the map"
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
    # replace one with our boi
    g.board[(4, 4)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_ShieldArray(power1=False, power2=False)))
    gs = g.board[(4, 4)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(4, 4)].unit.weapon1.shoot(*shot) # ()
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(4, 4)].unit.hp == 2  # no change to the wielder
    assert g.board[(4, 4)].unit.effects == {Effects.SHIELD}
    del allunits[(4, 4)]  # delete the wielder from allunits
    for sq in (3, 4), (4, 3), (4, 5), (5, 4):
        assert g.board[sq].unit.effects == {Effects.SHIELD}
        del allunits[sq]  # delete the target unit from all
    for u in allunits:
        assert g.board[u].unit.effects == set() # no change in effects to all other vek

def t_WeaponShieldArrayCenterHigh():
    "Fire the ShieldArray with power power in the center of the map"
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
    # replace one with our boi
    g.board[(4, 4)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_ShieldArray(power1=True, power2=False)))
    gs = g.board[(4, 4)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(4, 4)].unit.weapon1.shoot(*shot) # ()
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(4, 4)].unit.hp == 2  # no change to the wielder
    assert g.board[(4, 4)].unit.effects == {Effects.SHIELD}
    del allunits[(4, 4)]  # delete the wielder from allunits
    for sq in (3, 4), (4, 3), (4, 5), (5, 4), (4, 6), (5, 5), (6, 4), (5, 3), (4, 2), (3, 3), (2, 4), (3, 5):
        assert g.board[sq].unit.effects == {Effects.SHIELD}
        del allunits[sq]  # delete the target unit from all
    for u in allunits:
        assert g.board[u].unit.effects == set() # no change in effects to all other vek

def t_WeaponPushBeamMountain():
    "Fire the PushBeam with a mountain blocking some of the shot"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PushBeam(power1=False, power2=False))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Flame_Mech(g))
    g.board[(4, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(4, 1)].unit.hp == 1
    assert g.board[(4, 1)].effects == set()
    assert g.board[(5, 1)].unit.hp == 5
    assert g.board[(5, 1)].effects == set()
    assert g.board[(6, 1)].unit == None
    assert g.board[(6, 1)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 4 # 1 bump damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 1  # 2 bump damage
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 1
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.type == 'mountaindamaged'
    assert g.board[(5, 1)].unit.hp == 5 # this unit was not pushed because of the mountain
    assert g.board[(5, 1)].effects == set()

def t_WeaponPushBeamBuilding():
    "Fire the PushBeam with a building blocking some of the shot"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PushBeam(power1=False, power2=False))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Flame_Mech(g))
    g.board[(4, 1)].createUnitHere(Unit_Building(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(4, 1)].unit.hp == 1
    assert g.board[(4, 1)].effects == set()
    assert g.board[(5, 1)].unit.hp == 5
    assert g.board[(5, 1)].effects == set()
    assert g.board[(6, 1)].unit == None
    assert g.board[(6, 1)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 4 # 1 bump damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 1  # 2 bump damage
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit == None # building destroyed
    assert g.board[(4, 1)].effects == set()
    assert g.board[(5, 1)].unit.hp == 5 # this unit was not pushed because of the building. The building died after this square was considered for pushing
    assert g.board[(5, 1)].effects == set()

def t_WeaponPushBeamNoMountain():
    "Fire the PushBeam with no mountain blocking it"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_PushBeam(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_Flame_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].effects == set()
    assert g.board[(4, 1)].effects == set()
    assert g.board[(5, 1)].unit.hp == 5
    assert g.board[(5, 1)].effects == set()
    assert g.board[(6, 1)].unit == None
    assert g.board[(6, 1)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit == None # pushed from here
    assert g.board[(3, 1)].unit.hp == 5 # to here
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 3  # flame pushed here
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(5, 1)].unit == None  # pushed from here
    assert g.board[(6, 1)].unit.hp == 5 # this unit was not pushed because of the mountain
    assert g.board[(6, 1)].effects == set()

def t_WeaponBoosters():
    "Fire the Boosters"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_Boosters(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(2, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(8):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 1
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # wielder lept from here
    assert g.board[(2, 1)].unit.hp == 2 # to here
    assert g.board[(3, 1)].unit == None # pushed from here
    assert g.board[(4, 1)].unit.hp == 5 # to here
    assert g.board[(2, 2)].unit == None  # pushed from here
    assert g.board[(2, 3)].unit.hp == 5  # to here

def t_WeaponBoostersNullShot():
    "Fire the Boosters but try to land on an occupied tile"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_Boosters(power1=True, power2=True))) # power is ignored for this weapon
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(2, 2)].unit.hp == 5
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(9):
        shot = next(gs)
    try:
        g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    except NullWeaponShot:
        pass # expected
    else:
        assert False

def t_WeaponSmokeBombs1():
    "Shoot the SmokeBombs with default power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SmokeBombs(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 5 # no damage
    assert g.board[(3, 1)].unit.hp == 2 # jet landed here
    assert g.board[(3, 1)].unit.type == 'jet'

def t_WeaponSmokeBombs2():
    "Shoot the SmokeBombs with more damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SmokeBombs(power1=True, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 1)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 2 # jet landed here
    assert g.board[(3, 1)].unit.type == 'jet'

def t_WeaponSmokeBombs3():
    "Shoot the SmokeBombs with more range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SmokeBombs(power1=False, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponSmokeBombs4():
    "Shoot the SmokeBombs with full power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SmokeBombs(power1=True, power2=True)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponSmokeBombsForest():
    "Shoot the SmokeBombs on a forest and make sure it has smoke and not fire after."
    g = Game()
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SmokeBombs(power1=False, power2=False)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT, 2)
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # jet moved from starting position
    assert g.board[(2, 1)].effects == {Effects.SMOKE}
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].effects == {Effects.SMOKE}
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2 # jet landed here
    assert g.board[(4, 1)].unit.type == 'jet'

def t_WeaponSmokeBombsGen1():
    "Test the SmokeBombs shot generator with max range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SmokeBombs(power1=True, power2=True))) # with range
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 4)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    assert next(gs) == (Direction.UP, 1)
    assert next(gs) == (Direction.UP, 2)
    assert next(gs) == (Direction.UP, 3)
    assert next(gs) == (Direction.RIGHT, 1)
    assert next(gs) == (Direction.RIGHT, 2)
    assert next(gs) == (Direction.RIGHT, 3)

def t_WeaponHeatConverter1():
    "Shoot the HeatConverter but have the fire be off-board"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_HeatConverter(power1=False, power2=False))) # power is ignored
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].unit.effects == set() # no change
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}

def t_WeaponHeatConverter2():
    "Shoot the HeatConverter but have the fire NOT be off-board"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_HeatConverter(power1=False, power2=False)))  # power is ignored
    g.board[(2, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.flushHurt()
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit == None
    assert g.board[(3, 1)].effects == set() # nothing here to freeze

def t_WeaponSelfDestruct1():
    "Shoot SelfDestruct."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 2)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SelfDestruct(power1=False, power2=False))) # power is ignored
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g, effects={Effects.ACID}))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    g.board[(1, 1)].unit.weapon1.shoot(*next(gs))
    g.flushHurt()
    assert g.board[(1, 1)].unit.type == 'mechcorpse' # wielder died
    assert g.board[(1, 1)].effects == {Effects.FIRE}  # forest caught fire
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught fire
    assert g.board[(2, 1)].unit == None # vek died
    assert g.board[(1, 2)].effects == {Effects.ACID}  # forest caught fire, but then the vek died and dropped its acid here
    assert g.board[(1, 2)].unit == None  # vek died

def t_WeaponTargetedStrike1():
    "Shoot TargetedStrike."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 2)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_TargetedStrike(power1=False, power2=False))) # power is ignored
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g, effects={Effects.ACID}))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    g.board[(1, 1)].unit.weapon1.shoot(*next(gs))
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # wielder took 1 damage
    assert g.board[(1, 1)].effects == {Effects.FIRE}  # forest did catch fire
    assert g.board[(2, 1)].effects == set()  # forest did not catch fire
    assert g.board[(2, 1)].unit == None # vek pushed from here
    assert g.board[(3, 1)].unit.hp == 5 # to here, took no damage
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(1, 2)].effects == set()  # forest did not catch fire
    assert g.board[(1, 2)].unit == None  # vek pushed from here
    assert g.board[(1, 3)].effects == set()  # no tile effects
    assert g.board[(1, 3)].unit.effects == {Effects.ACID} # never lost acid
    assert g.board[(1, 3)].unit.hp == 5

def t_WeaponSmokeDrop1():
    "Shoot SmokeDrop."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 2)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_SmokeDrop(power1=False, power2=False))) # power is ignored
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g, effects={Effects.ACID}))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    g.board[(1, 1)].unit.weapon1.shoot(*next(gs))
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder took 0 damage
    assert g.board[(1, 1)].effects == {Effects.SMOKE}  # forest did not catch fire
    assert g.board[(2, 1)].effects == {Effects.SMOKE}  # forest did not catch fire
    assert g.board[(2, 1)].unit.hp == 5 # to here, took no damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 2)].effects == {Effects.SMOKE}  # forest did not catch fire
    assert g.board[(1, 2)].unit.effects == {Effects.ACID} # never lost acid
    assert g.board[(1, 2)].unit.hp == 5

def t_WeaponMissileBarrageLowPower():
    "Shoot MissileBarrage with no power."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 2)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_MissileBarrage(power1=False, power2=False))) # power2 is ignored
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g, effects={Effects.ACID}))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    g.board[(1, 1)].unit.weapon1.shoot(*next(gs))
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder untouched
    assert g.board[(1, 1)].effects == set()  # forest untouched
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught fire
    assert g.board[(2, 1)].unit.hp == 4 # vek took 1 damage
    assert g.board[(1, 2)].effects == {Effects.FIRE}  # forest caught fire,
    assert g.board[(1, 2)].unit.hp == 3  # vek took 2 damage because of acid

def t_WeaponMissileBarrageMaxPower():
    "Shoot MissileBarrage with extra damage."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(2, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 2)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_MissileBarrage(power1=True, power2=False))) # power2 is ignored
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaScorpion(g, effects={Effects.ACID}))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    g.board[(1, 1)].unit.weapon1.shoot(*next(gs))
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # wielder untouched
    assert g.board[(1, 1)].effects == set()  # forest untouched
    assert g.board[(2, 1)].effects == {Effects.FIRE} # forest caught fire
    assert g.board[(2, 1)].unit.hp == 3 # vek took 2 damage
    assert g.board[(1, 2)].effects == {Effects.FIRE}  # forest caught fire,
    assert g.board[(1, 2)].unit.hp == 1  # vek took 4 damage because of acid

def t_WeaponWindTorrentUp():
    "Shoot WindTorrent Up."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_WindTorrent(power1=True, power2=False))) # power2 is ignored
    g.board[(2, 7)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 6)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # UP
    g.flushHurt()
    assert g.board[(2, 8)].unit.hp == 5  # vek took no bump damage
    assert g.board[(2, 7)].unit.hp == 5  # vek took no bump damage
    assert g.board[(2, 6)].unit == None  # vek pushed from here

def t_WeaponWindTorrentRight():
    "Shoot WindTorrent RIGHT."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_WindTorrent(power1=True, power2=False))) # power2 is ignored
    g.board[(7, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(6, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT
    g.flushHurt()
    assert g.board[(8, 2)].unit.hp == 5  # vek took no bump damage
    assert g.board[(7, 2)].unit.hp == 5  # vek took no bump damage
    assert g.board[(6, 2)].unit == None  # vek pushed from here

def t_WeaponWindTorrentDown():
    "Shoot WindTorrent Down."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_WindTorrent(power1=True, power2=False))) # power2 is ignored
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(2, 3)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(3):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # Down
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 5  # vek took no bump damage
    assert g.board[(2, 2)].unit.hp == 5  # vek took no bump damage
    assert g.board[(2, 3)].unit == None  # vek pushed from here

def t_WeaponWindTorrentLeft():
    "Shoot WindTorrent Left."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_WindTorrent(power1=True, power2=False))) # power2 is ignored
    g.board[(2, 2)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 2)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(4):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # Left
    g.flushHurt()
    assert g.board[(1, 2)].unit.hp == 5  # vek took no bump damage
    assert g.board[(2, 2)].unit.hp == 5  # vek took no bump damage
    assert g.board[(3, 2)].unit == None  # vek pushed from here

def t_WeaponIceGeneratorLowPower():
    "Fire the IceGenerator with no power in the center of the map"
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
    # replace one with our boi
    g.board[(4, 4)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_IceGenerator(power1=False, power2=False)))
    gs = g.board[(4, 4)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(4, 4)].unit.weapon1.shoot(*shot) # ()
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(4, 4)].unit.hp == 2  # no damage to the wielder
    assert g.board[(4, 4)].unit.effects == {Effects.ICE} # wielder now in ice
    del allunits[(4, 4)]  # delete the wielder from allunits
    for sq in (3, 4), (4, 3), (4, 5), (5, 4):
        assert g.board[sq].unit.effects == {Effects.ICE}
        del allunits[sq]  # delete the target unit from all
    for u in allunits:
        assert g.board[u].unit.effects == set() # no change in effects to all other vek

def t_WeaponIceGeneratorMedPower1():
    "Fire the IceGenerator with power1 in the center of the map"
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
    # replace one with our boi
    g.board[(4, 4)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_IceGenerator(power1=True, power2=False)))
    gs = g.board[(4, 4)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(4, 4)].unit.weapon1.shoot(*shot) # ()
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(4, 4)].unit.hp == 2  # no damage to the wielder
    assert g.board[(4, 4)].unit.effects == {Effects.ICE} # wielder now in ice
    del allunits[(4, 4)]  # delete the wielder from allunits
    for sq in (3, 4), (4, 3), (4, 5), (5, 4), (4, 6), (5, 5), (6, 4), (5, 3), (4, 2), (3, 3), (2, 4), (3, 5):
        assert g.board[sq].unit.effects == {Effects.ICE}
        del allunits[sq]  # delete the target unit from all
    for u in allunits:
        assert g.board[u].unit.effects == set() # no change in effects to all other vek

def t_WeaponIceGeneratorMedPower2():
    "Fire the IceGenerator with power2 in the center of the map. Outcome is the same as last test"
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
    # replace one with our boi
    g.board[(4, 4)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_IceGenerator(power1=False, power2=True)))
    gs = g.board[(4, 4)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(4, 4)].unit.weapon1.shoot(*shot) # ()
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(4, 4)].unit.hp == 2  # no damage to the wielder
    assert g.board[(4, 4)].unit.effects == {Effects.ICE} # wielder now in ice
    del allunits[(4, 4)]  # delete the wielder from allunits
    for sq in (3, 4), (4, 3), (4, 5), (5, 4), (4, 6), (5, 5), (6, 4), (5, 3), (4, 2), (3, 3), (2, 4), (3, 5):
        assert g.board[sq].unit.effects == {Effects.ICE}
        del allunits[sq]  # delete the target unit from all
    for u in allunits:
        assert g.board[u].unit.effects == set() # no change in effects to all other vek

def t_WeaponIceGeneratorMaxPower():
    "Fire the IceGenerator with max powerin the center of the map."
    g = Game()
    for x in range(1, 9): # fuckit, put vek on every tile
        for y in range(1, 9):
            g.board[(x, y)].createUnitHere(Unit_AlphaScorpion(g))
    # replace one with our boi
    g.board[(4, 4)].createUnitHere(Unit_TechnoScarab_Mech(g, weapon1=Weapon_IceGenerator(power1=True, power2=True)))
    gs = g.board[(4, 4)].unit.weapon1.genShots()
    for r in range(1):
        shot = next(gs)
    g.board[(4, 4)].unit.weapon1.shoot(*shot) # ()
    g.flushHurt()
    allunits = {} # build a dict of all units
    for x in range(1, 9):
        for y in range(1, 9):
            allunits[(x, y)] = g.board[(x, y)].unit
    assert g.board[(4, 4)].unit.hp == 2  # no damage to the wielder
    assert g.board[(4, 4)].unit.effects == {Effects.ICE} # wielder now in ice
    del allunits[(4, 4)]  # delete the wielder from allunits
    for sq in (3, 4), (4, 3), (4, 5), (5, 4), (4, 6), (5, 5), (6, 4), (5, 3), (4, 2), (3, 3), (2, 4), (3, 5), (4, 7), (5, 6), (6, 5), (7, 4), (6, 3), (5, 2), (4, 1), (3, 2), (2, 3), (1, 4), (2, 5), (3, 6):
        assert g.board[sq].unit.effects == {Effects.ICE}
        del allunits[sq]  # delete the target unit from all
    for u in allunits:
        assert g.board[u].unit.effects == set() # no change in effects to all other vek

def t_WeaponDeployableGenSwallow():
    "Test genShots() for deployable weapons to make sure it skips over water, lava, and chasms"
    g = Game()
    g.board[(1, 3)].replaceTile(Tile_Water(g))
    g.board[(1, 5)].replaceTile(Tile_Lava(g))
    g.board[(1, 7)].replaceTile(Tile_Chasm(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_LightTank(power1=False, power2=False)))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    assert next(gs) == (Direction.UP, 3)
    assert next(gs) == (Direction.UP, 5)
    assert next(gs) == (Direction.UP, 7)
    assert next(gs) == (Direction.RIGHT, 2)

def t_WeaponLightTankLowPower():
    "Shoot and deploy a LightTank with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_LightTank(power1=False, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 1  # this is the light tank
    assert g.board[(3, 1)].unit.type == 'lighttank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(4, 1)].unit  # vek pushed from here
    assert g.board[(5, 1)].unit.hp == 5  # vek pushed here, but no damage done

def t_WeaponLightTank1Power():
    "Shoot and deploy a LightTank with power 1 powered for more hp."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_LightTank(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the light tank
    assert g.board[(3, 1)].unit.type == 'lighttank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(4, 1)].unit  # vek pushed from here
    assert g.board[(5, 1)].unit.hp == 5  # vek pushed here, but no damage done

def t_WeaponLightTankPower2():
    "Shoot and deploy a LightTank with power2 activated for damage."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_LightTank(power1=False, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 1  # this is the light tank
    assert g.board[(3, 1)].unit.type == 'lighttank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(4, 1)].unit  # vek pushed from here
    assert g.board[(5, 1)].unit.hp == 3  # vek pushed here, but WITH damage done

def t_WeaponLightTankMaxPower():
    "Shoot and deploy a LightTank with Max power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_LightTank(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the light tank
    assert g.board[(3, 1)].unit.type == 'lighttank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(4, 1)].unit  # vek pushed from here
    assert g.board[(5, 1)].unit.hp == 3  # vek pushed here, but WITH damage done

def t_WeaponLightTankMaxPowerMiss():
    "Shoot and deploy a LightTank with Max power with no vek to hit."
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_LightTank(power1=True, power2=True)))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(3, 1)].unit.hp == 3  # this is the light tank
    assert g.board[(3, 1)].unit.type == 'lighttank'
    assert g.board[(8, 1)].effects == set()
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert g.board[(8, 1)].effects == {Effects.FIRE}

def t_WeaponShieldTankLowPower():
    "Shoot and deploy a ShieldTank with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_ShieldTank(power1=False, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 1  # this is the shieldtank
    assert g.board[(3, 1)].unit.type == 'shieldtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek is here, but no damage done
    assert g.board[(4, 1)].unit.effects == {Effects.SHIELD}  # vek is now shielded

def t_WeaponShieldTankPower1():
    "Shoot and deploy a ShieldTank with power1."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_ShieldTank(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the shieldtank
    assert g.board[(3, 1)].unit.type == 'shieldtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek is here, but no damage done
    assert g.board[(4, 1)].unit.effects == {Effects.SHIELD}  # vek is now shielded

def t_WeaponShieldTankPower1Miss():
    "Shoot and deploy a ShieldTank with power1 but with the vek out of range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_ShieldTank(power1=True, power2=False)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(5, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the shieldtank
    assert g.board[(3, 1)].unit.type == 'shieldtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    try:
        g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    except NullWeaponShot:
        return # expected
    else:
        assert False, "expected a NullWeaponShot"

def t_WeaponShieldTankMaxPower():
    "Shoot and deploy a ShieldTank with max power and the vek at range."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_ShieldTank(power1=True, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(5, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the shieldtank
    assert g.board[(3, 1)].unit.type == 'shieldtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert g.board[(5, 1)].unit.hp == 5  # vek is here, but no damage done
    assert g.board[(5, 1)].unit.effects == {Effects.SHIELD}  # vek is now shielded

def t_WeaponShieldTankMaxPowerMiss():
    "Shoot and deploy a ShieldTank with max power but without a vek to hit."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_ShieldTank(power1=True, power2=True)))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(3, 1)].unit.hp == 3  # this is the shieldtank
    assert g.board[(3, 1)].unit.type == 'shieldtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    try:
        g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    except NullWeaponShot:
        return # good
    else:
        assert False # bad

def t_WeaponAcidTankLowPower():
    "Shoot and deploy a AcidTank with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AcidTank(power1=False, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(4, 1)].unit.effects == set()  # vek untouched
    assert g.board[(3, 1)].unit.hp == 1  # this is the acidtank
    assert g.board[(3, 1)].unit.type == 'acidtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # no damage done
    assert g.board[(4, 1)].unit.effects == {Effects.ACID}

def t_WeaponAcidTank1Power():
    "Shoot and deploy a AcidTank with power 1 powered for more hp."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AcidTank(power1=True, power2=False)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(4, 1)].unit.effects == set()  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the acidtank
    assert g.board[(3, 1)].unit.type == 'acidtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # no damage done
    assert g.board[(4, 1)].unit.effects == {Effects.ACID}

def t_WeaponAcidTankPower2():
    "Shoot and deploy a AcidTank with power2 activated for pushing."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AcidTank(power1=False, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 1  # this is the acidtank
    assert g.board[(3, 1)].unit.type == 'acidtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(4, 1)].unit  # vek pushed from here
    assert g.board[(5, 1)].unit.hp == 5  # vek pushed here
    assert g.board[(5, 1)].unit.effects == {Effects.ACID} # vek pushed here

def t_WeaponAcidTankMaxPower():
    "Shoot and deploy a AcidTank with Max power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AcidTank(power1=True, power2=True)))
    g.board[(4, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(4, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the acidtank
    assert g.board[(3, 1)].unit.type == 'acidtank'
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(4, 1)].unit  # vek pushed from here
    assert g.board[(5, 1)].unit.hp == 5  # vek pushed here
    assert g.board[(5, 1)].unit.effects == {Effects.ACID}  # vek pushed here

def t_WeaponAcidTankMaxPowerMiss():
    "Shoot and deploy a AcidTank with Max power with no vek to hit."
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_AcidTank(power1=True, power2=True)))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(3, 1)].unit.hp == 3  # this is the acidtank
    assert g.board[(3, 1)].unit.type == 'acidtank'
    assert g.board[(8, 1)].effects == set()
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert g.board[(8, 1)].effects == {Effects.ACID}

def t_WeaponPullTankLowPower():
    "Shoot and deploy a PullTank with no power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_PullTank(power1=False, power2=False)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(5, 1)].unit.hp == 5  # vek untouched
    assert g.board[(5, 1)].unit.effects == set()  # vek untouched
    assert g.board[(3, 1)].unit.hp == 1  # this is the PullTank
    assert g.board[(3, 1)].unit.type == 'pulltank'
    assert g.board[(3, 1)].unit.attributes == set()
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(5, 1)].unit # vek pulled from here
    assert g.board[(4, 1)].unit.hp == 5  # no damage done
    assert g.board[(4, 1)].unit.effects == set()

def t_WeaponPullTank1Power():
    "Shoot and deploy a PullTank with power 1 powered for more hp."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_PullTank(power1=True, power2=False)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(5, 1)].unit.hp == 5  # vek untouched
    assert g.board[(5, 1)].unit.effects == set()  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the PullTank
    assert g.board[(3, 1)].unit.type == 'pulltank'
    assert g.board[(3, 1)].unit.attributes == set()
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(5, 1)].unit  # vek pulled from here
    assert g.board[(4, 1)].unit.hp == 5  # no damage done
    assert g.board[(4, 1)].unit.effects == set()

def t_WeaponPullTankPower2():
    "Shoot and deploy a PullTank with power2 activated for flying."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_PullTank(power1=False, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(5, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 1  # this is the PullTank
    assert g.board[(3, 1)].unit.type == 'pulltank'
    assert g.board[(3, 1)].unit.attributes == {Attributes.FLYING}
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(5, 1)].unit  # vek pulled from here
    assert g.board[(4, 1)].unit.hp == 5  # vek pushed here
    assert g.board[(4, 1)].unit.effects == set() # vek pushed here

def t_WeaponPullTankMaxPower():
    "Shoot and deploy a PullTank with Max power."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_PullTank(power1=True, power2=True)))
    g.board[(5, 1)].createUnitHere(Unit_AlphaScorpion(g))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(5, 1)].unit.hp == 5  # vek untouched
    assert g.board[(3, 1)].unit.hp == 3  # this is the PullTank
    assert g.board[(3, 1)].unit.type == 'pulltank'
    assert g.board[(3, 1)].unit.attributes == {Attributes.FLYING}
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    g.flushHurt()
    assert not g.board[(5, 1)].unit  # vek pulled from here
    assert g.board[(4, 1)].unit.hp == 5  # vek pushed here
    assert g.board[(4, 1)].unit.effects == set()  # vek pushed here

def t_WeaponPullTankMaxPowerMiss():
    "Shoot and deploy a PullTank with Max power with no vek to hit."
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, weapon1=Weapon_PullTank(power1=True, power2=True)))
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot) # RIGHT, 2
    g.flushHurt()
    assert g.board[(3, 1)].unit.hp == 3  # this is the PullTank
    assert g.board[(3, 1)].unit.type == 'pulltank'
    assert g.board[(3, 1)].unit.attributes == {Attributes.FLYING}
    assert g.board[(8, 1)].effects == set()
    gs = g.board[(3, 1)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    try:
        g.board[(3, 1)].unit.weapon1.shoot(*shot)  # RIGHT
    except NullWeaponShot:
        pass # expected
    else:
        assert False # bad

def t_WeaponRepair():
    "Have a unit take damage and then repair."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, hp=10, maxhp=10)) # no weapons added, unit should have a Weapon_Repair set as it's default repweapon
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 10
    g.board[(1, 1)].takeDamage(3)
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 7 # took 3 damage
    gs = g.board[(1, 1)].unit.repweapon.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.repweapon.shoot(*shot) # ()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 8  # repaired 1 damage

def t_WeaponRepairFire():
    "Have a unit take damage on a forest and then repair."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, hp=10, maxhp=10)) # no weapons added, unit should have a Weapon_Repair set as it's default repweapon
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 10
    g.board[(1, 1)].takeDamage(3)
    assert g.board[(1, 1)].effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(1, 1)].unit.hp == 7 # took 3 damage
    gs = g.board[(1, 1)].unit.repweapon.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.repweapon.shoot(*shot) # ()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 8  # repaired 1 damage

def t_WeaponRepairAcid():
    "Have a unit take damage on acid and then repair."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, hp=10, maxhp=10)) # no weapons added, unit should have a Weapon_Repair set as it's default repweapon
    g.board[(1, 1)].applyAcid()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}
    assert g.board[(1, 1)].unit.hp == 10
    g.board[(1, 1)].takeDamage(3)
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == {Effects.ACID}
    assert g.board[(1, 1)].unit.hp == 4 # took 6 damage
    gs = g.board[(1, 1)].unit.repweapon.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.repweapon.shoot(*shot) # ()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 5  # repaired 1 damage

def t_WeaponRepairIce():
    "Have a unit get frozen and then repair."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, hp=10, maxhp=10)) # no weapons added, unit should have a Weapon_Repair set as it's default repweapon
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}
    assert g.board[(1, 1)].unit.hp == 10
    gs = g.board[(1, 1)].unit.repweapon.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.repweapon.shoot(*shot) # ()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set() # no more ice
    assert g.board[(1, 1)].unit.hp == 10  # hp was never lost and we didn't repair over the max

def t_WeaponFrenziedRepair():
    "Have a unit take damage and then repair and push a nearby vek."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, repweapon=Weapon_FrenziedRepair(), hp=10, maxhp=10))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 10
    g.board[(1, 1)].takeDamage(3)
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 7 # took 3 damage
    gs = g.board[(1, 1)].unit.repweapon.genShots()
    for shot in range(1):
        shot = next(gs)
    g.board[(1, 1)].unit.repweapon.shoot(*shot) # ()
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 8  # repaired 1 damage
    assert g.board[(2, 1)].unit == None  # vek pushed from here
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 5

def t_WeaponMantisSlash():
    "Have a unit take damage and then use the repair weapon to hurt a nearby vek."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, repweapon=Weapon_MantisSlash(), hp=10, maxhp=10))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 10
    g.board[(1, 1)].takeDamage(3)
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 7 # took 3 damage
    gs = g.board[(1, 1)].unit.repweapon.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.repweapon.shoot(*shot) # (RIGHT,)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 7  # repaired 0 damage
    assert g.board[(2, 1)].unit == None  # vek pushed from here
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 3 # vek took 2 damage

def t_WeaponMantisSlashIce():
    "Have a get frozen and then use the repair weapon to break the ice and hurt a nearby vek."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Jet_Mech(g, repweapon=Weapon_MantisSlash(), hp=10, maxhp=10))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].effects == set() # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 10
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}
    assert g.board[(1, 1)].unit.hp == 10 # unit wasn't attacked at all this time
    gs = g.board[(1, 1)].unit.repweapon.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(1, 1)].unit.repweapon.shoot(*shot) # (RIGHT,)
    g.flushHurt()
    assert g.board[(1, 1)].effects == set()  # no tile effects
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 10  # repaired 0 damage
    assert g.board[(2, 1)].unit == None  # vek pushed from here
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 3 # vek took 2 damage

def t_WeaponUnstableGuts():
    "Have a blob do its thing"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Blob(g, qshot=()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot() # ()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # mech took 1 damage
    assert g.board[(2, 1)].unit == None  # blob exploded
    assert g.board[(3, 1)].unit.hp == 4 # 1 damage

def t_WeaponUnstableGutsShielded():
    "Have a blob do its thing but it's shielded"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Blob(g, qshot=(), effects={Effects.SHIELD}))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD}
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot() # ()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # mech took 1 damage
    assert g.board[(2, 1)].unit == None  # blob exploded
    assert g.board[(3, 1)].unit.hp == 4 # 1 damage

def t_WeaponVolatileGuts():
    "Have an alpha blob do its thing"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaBlob(g, qshot=()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took 3 damage
    assert g.board[(2, 1)].unit == None  # blob exploded
    assert g.board[(3, 1)].unit.hp == 2 # 3 damage

def t_WeaponVolatileGutsFlip():
    "Have an alpha blob get flipped by ConfuseShot which raises NullWeaponShot"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ConfuseShot(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaBlob(g, qshot=()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    try:
        g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    except NullWeaponShot:
        pass # expected
    else:
        raise # ya fucked up
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took 3 damage
    assert g.board[(2, 1)].unit == None  # blob exploded
    assert g.board[(3, 1)].unit.hp == 2 # 3 damage

def t_WeaponVolatileGutsSmokeInvalidates():
    "Have an alpha blob get smoked and cancel its shot"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaBlob(g, qshot=()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].applySmoke()
    g.board[(2, 1)].unit.weapon1.shoot() # None
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # wielder took no damage since there was no shot
    assert g.board[(2, 1)].unit.hp == 1 # blob did NOT explode
    assert g.board[(3, 1)].unit.hp == 5 # 0 damage

def t_WeaponVolatileGutsIceInvalidates():
    "Have an alpha blob get frozen and cancel its shot"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaBlob(g, qshot=()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].applyIce()
    g.board[(2, 1)].unit.weapon1.shoot() # None
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # wielder took no damage since there was no shot
    assert g.board[(2, 1)].unit.hp == 1 # blob did NOT explode
    assert g.board[(3, 1)].unit.hp == 5 # 0 damage

def t_WebPush():
    "Have a scorpion web a mech and then get pushed to break the web"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g))
    g.board[(2, 1)].unit._makeWeb((1, 1))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.web == {(2, 1)}
    assert g.board[(2, 1)].unit.web == {(1, 1)}
    g.board[(2, 1)].push(Direction.UP)
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit == None # pushed from here
    assert g.board[(2, 2)].unit.hp == 3
    assert g.board[(1, 1)].unit.web == set()
    assert g.board[(2, 2)].unit.web == set()

def t_DefaultAssignedWeapon():
    "Make sure that vek weapon objects aren't shared too much since a weapon object is hard-coded to be created in __init__"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_Scorpion(g))
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g))
    g.board[(1, 1)].unit.weapon1.qshot = (Direction.UP,)
    g.board[(3, 1)].createUnitHere(Unit_Scorpion(g))
    assert g.board[(1, 1)].unit.weapon1.qshot == (Direction.UP,)
    assert g.board[(2, 1)].unit.weapon1.qshot == None
    assert g.board[(3, 1)].unit.weapon1.qshot == None

def t_WeaponStingingSpinneret():
    "Have a scorpion do his attack"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Scorpion(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

# def t_WeaponStingingSpinneretAcid(): # acid units aren't really implemented in the game
#     "Have an  AcidScorpion do his attack"
#     g = Game()
#     g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
#     g.board[(2, 1)].createUnitHere(Unit_AcidScorpion(g, qshot=(Direction.LEFT,)))
#     assert g.board[(1, 1)].unit.hp == 5
#     assert g.board[(2, 1)].unit.hp == 4
#     assert g.board[(1, 1)].unit.effects == set()
#     assert g.board[(2, 1)].unit.effects == set()
#     g.board[(2, 1)].unit.weapon1.shoot()
#     g.flushHurt()
#     assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 damage
#     assert g.board[(1, 1)].unit.effects == {Effects.ACID}
#     assert g.board[(2, 1)].unit.hp == 4 # vek took no damage
#     assert g.board[(2, 1)].unit.effects == set()

def t_WeaponGoringSpinneret():
    "Have an AlphaScorpion do his attack"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took 3 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

def t_WeaponAcceleratingThorax():
    "Have a Firefly do his attack against our mech"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(8, 1)].effects == set() # forest did not catch on fire

def t_WeaponAcceleratingThoraxFlip():
    "Have a Firefly do his attack but it got flipped and hit the forest instead"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ConfuseShot(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # wielder took 0 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(8, 1)].effects == {Effects.FIRE} # forest did catch on fire

def t_WeaponAcceleratingThoraxInvalidFlip():
    "Have a Firefly do his attack but it got flipped and invalidated instead"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ConfuseShot(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Firefly(g, qshot=(Direction.UP,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert g.board[(2, 1)].unit.weapon1.qshot is None
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # wielder took 0 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(8, 1)].effects == set() # forest did not catch on fire

# def t_WeaponAcceleratingThoraxAcid(): # acid units aren't really implemented in the game
#     "Have an AcidFirefly do his attack against our mech"
#     g = Game()
#     g.board[(8, 1)].replaceTile(Tile_Forest(g))
#     g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
#     g.board[(2, 1)].createUnitHere(Unit_AcidFirefly(g, qshot=(Direction.LEFT,)))
#     assert g.board[(1, 1)].unit.hp == 5
#     assert g.board[(2, 1)].unit.hp == 3
#     assert g.board[(1, 1)].unit.effects == set()
#     assert g.board[(2, 1)].unit.effects == set()
#     g.board[(2, 1)].unit.weapon1.shoot()
#     g.flushHurt()
#     assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 damage
#     assert g.board[(1, 1)].unit.effects == {Effects.ACID}
#     assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
#     assert g.board[(2, 1)].unit.effects == set()
#     assert g.board[(8, 1)].effects == set() # forest did not catch on fire

# def t_WeaponAcceleratingThoraxAcidFlip(): # acid units aren't really implemented in the game
#     "Have an AcidFirefly do his attack but it got flipped and hit the forest instead"
#     g = Game()
#     g.board[(8, 1)].replaceTile(Tile_Forest(g))
#     g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ConfuseShot(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
#     g.board[(2, 1)].createUnitHere(Unit_AcidFirefly(g, qshot=(Direction.LEFT,)))
#     assert g.board[(1, 1)].unit.hp == 5
#     assert g.board[(2, 1)].unit.hp == 3
#     assert g.board[(1, 1)].unit.effects == set()
#     assert g.board[(2, 1)].unit.effects == set()
#     g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
#     g.board[(2, 1)].unit.weapon1.shoot()
#     g.flushHurt()
#     assert g.board[(1, 1)].unit.hp == 5  # wielder took 0 damage
#     assert g.board[(1, 1)].unit.effects == set()
#     assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
#     assert g.board[(2, 1)].unit.effects == set()
#     assert g.board[(8, 1)].effects == {Effects.ACID} # forest erased by acid

# def t_WeaponAcceleratingThoraxAcidInvalidFlip(): # acid units aren't really implemented in the game
#     "Have an AcidFirefly do his attack but it got flipped and invalidated instead"
#     g = Game()
#     g.board[(8, 1)].replaceTile(Tile_Forest(g))
#     g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ConfuseShot(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
#     g.board[(2, 1)].createUnitHere(Unit_AcidFirefly(g, qshot=(Direction.UP,)))
#     assert g.board[(1, 1)].unit.hp == 5
#     assert g.board[(2, 1)].unit.hp == 3
#     assert g.board[(1, 1)].unit.effects == set()
#     assert g.board[(2, 1)].unit.effects == set()
#     g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
#     assert g.board[(2, 1)].unit.weapon1.qshot is None
#     g.board[(2, 1)].unit.weapon1.shoot()
#     g.flushHurt()
#     assert g.board[(1, 1)].unit.hp == 5  # wielder took 0 damage
#     assert g.board[(1, 1)].unit.effects == set()
#     assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
#     assert g.board[(2, 1)].unit.effects == set()
#     assert g.board[(8, 1)].effects == set() # forest did not catch on fire

def t_WeaponEnhancedThorax():
    "Have an AlphaFirefly do his attack against our mech"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaFirefly(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took 3 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(8, 1)].effects == set() # forest did not catch on fire

def t_WeaponEnhancedThoraxFlip():
    "Have an AlphaFirefly do his attack but it got flipped and hit the forest instead"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ConfuseShot(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaFirefly(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # wielder took 0 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(8, 1)].effects == {Effects.FIRE} # forest did catch on fire

def t_WeaponEnhancedThoraxInvalidFlip():
    "Have an AlphaFirefly do his attack but it got flipped and invalidated instead"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ConfuseShot(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaFirefly(g, qshot=(Direction.UP,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    assert g.board[(2, 1)].unit.weapon1.qshot is None
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # wielder took 0 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(8, 1)].effects == set() # forest did not catch on fire

def t_WeaponFangs():
    "Have a Leaper do his attack"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Leaper(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2  # wielder took 3 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 1 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

def t_WeaponSharpenedFangs():
    "Have an AlphaLeaper do his attack"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaLeaper(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 6
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # wielder took 5 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

def t_WeaponPincersNormal():
    "Have a Beetle do his attack against a unit"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Beetle(g, qshot=(Direction.RIGHT,)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # vek dashed from here
    assert g.board[(7, 1)].unit.hp == 5  # mech took 1 damage
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(5, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(5, 1)].unit.effects == set()

def t_WeaponPincersMine():
    "Have a Beetle do his attack against a unit but there's a mine in the way"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Beetle(g, qshot=(Direction.RIGHT,)))
    g.board[(4, 1)].effects.add(Effects.MINE)
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # vek dashed from here
    assert g.board[(7, 1)].unit.hp == 5  # mech took 1 damage
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(5, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(5, 1)].unit.effects == set()  # vek froze from the mine and took no damage
    assert g.board[(4, 1)].effects == {Effects.MINE} # mine is still there

def t_WeaponPincersFreezeMine():
    "Have a Beetle do his attack against a unit but there's a freezemine in the way which it goes over"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Beetle(g, qshot=(Direction.RIGHT,)))
    g.board[(4, 1)].effects.add(Effects.FREEZEMINE)
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # vek dashed from here
    assert g.board[(7, 1)].unit.hp == 5  # mech took 1 damage
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(5, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(5, 1)].unit.effects == set()  # vek froze from the mine and took no damage
    assert g.board[(4, 1)].effects == {Effects.FREEZEMINE} # mine is still there

def t_WeaponPincersWater():
    "Have a Beetle do his attack against a unit but there's a water tile in the way"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Beetle(g, qshot=(Direction.RIGHT,)))
    g.board[(4, 1)].replaceTile(Tile_Water(g))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # vek dashed from here
    assert g.board[(6, 1)].unit.hp == 6  # mech took NO damage
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit == None # vek died in the water
    assert g.board[(4, 1)].effects == {Effects.SUBMERGED} # water still wet

def t_WeaponPincersLava():
    "Have a Beetle do his attack against a unit but there's a Lava tile in the way"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Beetle(g, qshot=(Direction.RIGHT,)))
    g.board[(4, 1)].replaceTile(Tile_Lava(g))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # vek dashed from here
    assert g.board[(6, 1)].unit.hp == 6  # mech took NO damage
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit == None # vek died in the lava
    assert g.board[(4, 1)].effects == {Effects.SUBMERGED, Effects.FIRE} # water still wet

def t_WeaponPincersChasm():
    "Have a Beetle do his attack against a unit but there's a chasm tile in the way"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Beetle(g, qshot=(Direction.RIGHT,)))
    g.board[(4, 1)].replaceTile(Tile_Chasm(g))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # vek dashed from here
    assert g.board[(6, 1)].unit.hp == 6  # mech took NO damage
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit == None # vek died in the chasm
    assert g.board[(4, 1)].effects == set() # never had effects

def t_WeaponPincersFlip():
    "Have a Beetle do his attack against a unit but it gets flipped and invalidated"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Beetle(g, qshot=(Direction.RIGHT,)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.flip()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.weapon1.qshot is None
    assert g.board[(6, 1)].unit.hp == 6  # mech took NO damage
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 4 # vek didn't move
    assert g.board[(1, 1)].effects == set() # never had effects

def t_WeaponSharpenedPincersNormal():
    "Have an AlphaBeetle do his attack against a unit"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_AlphaBeetle(g, qshot=(Direction.RIGHT,)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit == None # vek dashed from here
    assert g.board[(7, 1)].unit.hp == 3  # mech took 3 damage
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(5, 1)].unit.hp == 5 # vek took no damage
    assert g.board[(5, 1)].unit.effects == set()

def t_WeaponSpittingGlandsNormal():
    "Have a Scarab do his attack against a unit"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Scarab(g, qshot=(Direction.RIGHT, 5)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(6, 1)].unit.hp == 5  # mech took 1 damage
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2 # vek took no damage
    assert g.board[(1, 1)].unit.effects == set()

def t_WeaponSpittingGlandsFlip():
    "Have a Scarab do his attack against a unit but it got flipped and did nothing"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Scarab(g, qshot=(Direction.RIGHT, 5)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.flip()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(6, 1)].unit.hp == 6  # mech took 0 damage
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 2 # vek took no damage
    assert g.board[(1, 1)].unit.effects == set()

def t_WeaponSpittingGlandsFlipValid():
    "Have a Scarab do his attack against a unit but it got flipped and hit a different tile"
    g = Game()
    g.board[(4, 4)].createUnitHere(Unit_Scarab(g, qshot=(Direction.RIGHT, 3)))
    g.board[(1, 4)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6))  # extra hp given
    g.board[(4, 4)].unit.weapon1.flip()
    g.board[(4, 4)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 4)].unit.hp == 5  # mech took 1 damage
    assert g.board[(4, 4)].unit.hp == 2 # vek took no damage

def t_WeaponAlphaSpittingGlandsNormal():
    "Have an AlphaScarab do his attack against a unit"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_AlphaScarab(g, qshot=(Direction.RIGHT, 5)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 4
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(6, 1)].unit.hp == 3  # mech took 3 damage
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(1, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(1, 1)].unit.effects == set()

def t_WeaponExplosiveExpulsionsNormal():
    "Have a Crab do his attack against 2 units"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(7, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Crab(g, qshot=(Direction.RIGHT, 5)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(7, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 3
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(6, 1)].unit.hp == 5  # mech took 1 damage
    assert g.board[(7, 1)].unit.hp == 5  # mech took 1 damage
    assert g.board[(1, 1)].unit.hp == 3 # vek took no damage

def t_WeaponAlphaExplosiveExpulsionsNormal():
    "Have a AlphaCrab do his attack against 2 units"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6)) # extra hp given
    g.board[(7, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=6, maxhp=6))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_AlphaCrab(g, qshot=(Direction.RIGHT, 5)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(7, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(6, 1)].unit.hp == 3  # mech took 3 damage
    assert g.board[(7, 1)].unit.hp == 3  # mech took 3 damage
    assert g.board[(1, 1)].unit.hp == 5 # vek took no damage

def t_WeaponAcidicVomit():
    "Have a Centipede do his attack against a unit"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=6, maxhp=6)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Centipede(g, qshot=(Direction.RIGHT,)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(6, 2)].effects == set() # no tile effects next to mech
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 3  # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()  # vek picked up no new effects
    assert g.board[(6, 1)].unit.hp == 5  # mech took 1 damage
    assert g.board[(6, 1)].unit.effects == {Effects.ACID} # and now has acid
    assert g.board[(6, 2)].effects == {Effects.ACID}  # tile next to mech now has acid

def t_WeaponAcidicVomitFlipped():
    "Have a Centipede do his attack but he got flipped"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=6, maxhp=6)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Centipede(g, qshot=(Direction.RIGHT,)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(6, 2)].effects == set() # no tile effects next to mech
    g.board[(2, 1)].unit.weapon1.flip()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 3  # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()  # vek picked up no new effects
    assert g.board[(6, 1)].unit.hp == 6  # mech took 0 damage
    assert g.board[(6, 1)].unit.effects == set() # and didn't get acid
    assert g.board[(6, 2)].effects == set()  # tile next to mech unaffected
    assert g.board[(1, 1)].effects == {Effects.ACID}  # tile now has acid
    assert g.board[(1, 2)].effects == {Effects.ACID}  # tile now has acid

def t_WeaponCorrosiveVomit():
    "Have an AlphaCentipede do his attack against a unit"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=6, maxhp=6)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaCentipede(g, qshot=(Direction.RIGHT,)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(6, 2)].effects == set() # no tile effects next to mech
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 5  # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()  # vek picked up no new effects
    assert g.board[(6, 1)].unit.hp == 4  # mech took 2 damage
    assert g.board[(6, 1)].unit.effects == {Effects.ACID} # and now has acid
    assert g.board[(6, 2)].effects == {Effects.ACID}  # tile next to mech now has acid

def t_WeaponCorrosiveVomitFlipped():
    "Have an AlphaCentipede do his attack but he got flipped"
    g = Game()
    g.board[(6, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=6, maxhp=6)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaCentipede(g, qshot=(Direction.RIGHT,)))
    assert g.board[(6, 1)].unit.hp == 6
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(6, 2)].effects == set() # no tile effects next to mech
    g.board[(2, 1)].unit.weapon1.flip()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 5  # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()  # vek picked up no new effects
    assert g.board[(6, 1)].unit.hp == 6  # mech took 0 damage
    assert g.board[(6, 1)].unit.effects == set() # and didn't get acid
    assert g.board[(6, 2)].effects == set()  # tile next to mech unaffected
    assert g.board[(1, 1)].effects == {Effects.ACID}  # tile now has acid
    assert g.board[(1, 2)].effects == {Effects.ACID}  # tile now has acid

def t_WeaponDiggingTusks():
    "Have a digger do its thing"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Digger(g, qshot=()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 2
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot() # ()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 damage
    assert g.board[(2, 1)].unit.hp == 2 # no damage to vek
    assert g.board[(3, 1)].unit.hp == 4 # 1 damage

def t_WeaponAlphaDiggingTusks():
    "Have an alpha digger do its thing"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaDigger(g, qshot=()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 4
    assert g.board[(3, 1)].unit.hp == 5
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # wielder took 2 damage
    assert g.board[(2, 1)].unit.hp == 4  # vek took no damage
    assert g.board[(3, 1)].unit.hp == 3 # 2 damage

def t_WeaponAlphaDiggingTusksFlip():
    "Have an alpha digger get flipped by ConfuseShot which raises NullWealonShot"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_ConfuseShot(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaDigger(g, qshot=()))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 4
    assert g.board[(3, 1)].unit.hp == 5
    try:
        g.board[(1, 1)].unit.weapon1.shoot(Direction.RIGHT)
    except NullWeaponShot:
        pass # this is expected
    else:
        raise # oh noes
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # wielder took 2 damage
    assert g.board[(2, 1)].unit.hp == 4 # no damage to vek
    assert g.board[(3, 1)].unit.hp == 3 # 2 damage

def t_WeaponStinger():
    "Have a Hornet do his attack"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Hornet(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 2 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

# def t_WeaponStingerAcid(): # acid units aren't really implemented in the game
#     "Have an  AcidHornet do his attack"
#     g = Game()
#     g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, weapon1=Weapon_RainingDeath(power1=False, power2=False), hp=5, maxhp=5)) # extra hp given
#     g.board[(2, 1)].createUnitHere(Unit_AcidHornet(g, qshot=(Direction.LEFT,)))
#     assert g.board[(1, 1)].unit.hp == 5
#     assert g.board[(2, 1)].unit.hp == 3
#     assert g.board[(1, 1)].unit.effects == set()
#     assert g.board[(2, 1)].unit.effects == set()
#     g.board[(2, 1)].unit.weapon1.shoot()
#     g.flushHurt()
#     assert g.board[(1, 1)].unit.hp == 4  # wielder took 1 damage
#     assert g.board[(1, 1)].unit.effects == {Effects.ACID}
#     assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
#     assert g.board[(2, 1)].unit.effects == set()

def t_WeaponLaunchingStinger():
    "Have an AlphaHornet do his attack but the secondary tile is offboard"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaHornet(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 4
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

def t_WeaponLaunchingStinger2():
    "Have an AlphaHornet do his attack where he actually hits 2 tiles"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 1)].createUnitHere(Unit_AlphaHornet(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 4
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    g.board[(3, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(2, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(3, 1)].unit.effects == set()

def t_WeaponLaunchingStinger3():
    "Have an AlphaHornet do his attack where he actually hits 2 tiles and doesn't hit a third unit that is present"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(4, 1)].createUnitHere(Unit_AlphaHornet(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 4
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    g.board[(4, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # mech took NO damage
    assert g.board[(2, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(3, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(4, 1)].unit.effects == set()

def t_WeaponLaunchingStingerFlip():
    "Have an AlphaHornet do his attack where he was going to miss but flipping makes him hit"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 1)].createUnitHere(Unit_AlphaHornet(g, qshot=(Direction.RIGHT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 4
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    g.board[(3, 1)].unit.weapon1.flip()
    g.board[(3, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(2, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(3, 1)].unit.effects == set()

def t_WeaponLaunchingStingerFlipInvalidated():
    "Have an AlphaHornet do his attack where he was going to miss but flipping makes him cancel his shot"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 1)].createUnitHere(Unit_AlphaHornet(g, qshot=(Direction.UP,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 4
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.weapon1.qshot == (Direction.UP,)
    g.board[(3, 1)].unit.weapon1.flip()
    assert g.board[(3, 1)].unit.weapon1.qshot == None
    g.board[(3, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # mech took 0 damage
    assert g.board[(2, 1)].unit.hp == 5  # mech took 0 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 4 # vek took no damage
    assert g.board[(3, 1)].unit.effects == set()

def t_WeaponSpikedCaparace():
    "Have a Burrower do his attack"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_Burrower(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(1, 2)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 4  # mech took 1 damage
    assert g.board[(1, 2)].unit.hp == 4  # mech took 1 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 3 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

def t_WeaponBladedCaparace():
    "Have an AlphaBurrower do his attack"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_AlphaBurrower(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(1, 2)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 2)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 2)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 5 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

def t_WeaponFlamingAbdomen():
    "Have a BeetleLeader do his attack"
    g = Game()
    g.board[(7, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_BeetleLeader(g, qshot=(Direction.RIGHT,)))
    assert g.board[(7, 1)].unit.hp == 5
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(7, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 6
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # vek charged from here
    assert g.board[(2, 1)].effects == {Effects.FIRE} # vek starting point caught fire
    assert g.board[(6, 1)].unit.hp == 6 # to here, took no damage
    assert g.board[(6, 1)].unit.effects == set()
    assert g.board[(6, 1)].effects == set()
    assert g.board[(7, 1)].unit == None # mech pushed from here
    assert g.board[(7, 1)].effects == set() # no fire here
    assert g.board[(8, 1)].unit.hp == 2 # mech took 2 damage
    assert g.board[(8, 1)].unit.effects == set()
    assert g.board[(8, 1)].effects == set()
    for x in range(2, 6):
        assert g.board[(x, 1)].effects == {Effects.FIRE}

def t_WeaponBeetleLeaderOnFireChargesOverWater():
    "If a huge charging vek like the beetle leader is on fire and charges over water, he remains on fire."
    g = Game()
    g.board[(4, 1)].replaceTile(Tile_Water(g))
    g.board[(7, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_BeetleLeader(g, qshot=(Direction.RIGHT,), effects={Effects.FIRE}))
    assert g.board[(7, 1)].unit.hp == 5
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(7, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 6
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit == None # vek charged from here
    assert g.board[(2, 1)].effects == {Effects.FIRE} # vek starting point caught fire
    assert g.board[(6, 1)].unit.hp == 6 # to here, took no damage
    assert g.board[(6, 1)].unit.effects == {Effects.FIRE} # beetle still on fire
    assert g.board[(6, 1)].effects == set()
    assert g.board[(7, 1)].unit == None # mech pushed from here
    assert g.board[(7, 1)].effects == set() # no fire here
    assert g.board[(8, 1)].unit.hp == 2 # mech took 2 damage
    assert g.board[(8, 1)].unit.effects == set()
    assert g.board[(8, 1)].effects == set()
    for x in range(2, 6):
        if x == 4:
            assert g.board[(x, 1)].effects == {Effects.SUBMERGED} # the water tile
        else:
            assert g.board[(x, 1)].effects == {Effects.FIRE}


def t_WeaponGooAttackMechSurvive():
    "Have a Goo do his attack against a mech that survives."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_LargeGoo(g, qshot=(Direction.RIGHT,)))
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 1 # unit took 4 damage
    assert g.board[(2, 1)].unit.effects == set() # no new effects
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.type == 'technohornet' # not a corpse
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()

def t_WeaponGooAttackMechDies():
    "Have a Goo do his attack against a mech that dies."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=4, maxhp=4)) # less hp given
    g.board[(1, 1)].createUnitHere(Unit_LargeGoo(g, qshot=(Direction.RIGHT,)))
    assert g.board[(2, 1)].unit.hp == 4
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 1 # unit took 4 damage, died and is now a mech corpse
    assert g.board[(2, 1)].unit.effects == set() # no new effects
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.type == 'mechcorpse' # is a corpse
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()

def t_WeaponGooAttackSubTank():
    "Have a Goo do his attack against a deployable tank that dies."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_PullTank(g, hp=1, maxhp=1)) # less hp given
    g.board[(1, 1)].createUnitHere(Unit_LargeGoo(g, qshot=(Direction.RIGHT,)))
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 3 # goo took the spot of the pull tank
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit == None # goo moved from here

def t_WeaponGooAttackEnemyDies():
    "Have a Goo do his attack against a vek that dies."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g, hp=1, maxhp=1)) # less hp given
    g.board[(1, 1)].createUnitHere(Unit_LargeGoo(g, qshot=(Direction.RIGHT,)))
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 3 # goo took the spot of the vek
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit == None # goo moved from here

def t_WeaponGooAttackEnemySurvives():
    "Have a Goo do his attack against a vek that survives."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g, hp=5, maxhp=5)) # more hp given
    g.board[(1, 1)].createUnitHere(Unit_LargeGoo(g, qshot=(Direction.RIGHT,)))
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # goo took the spot of the vek
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 1  # unit took 4 damage
    assert g.board[(2, 1)].unit.effects == set()  # no new effects
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.type == 'alphascorpion'

def t_WeaponGooAttackEnemySurvivesIce():
    "Have a Goo do his attack against a frozen vek with low health that survives."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g, hp=1, maxhp=1, effects={Effects.ICE})) # less hp given
    g.board[(1, 1)].createUnitHere(Unit_LargeGoo(g, qshot=(Direction.RIGHT,)))
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3 # goo took the spot of the vek
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].unit.hp == 1  # unit took no damage
    assert g.board[(2, 1)].unit.effects == set()  # lost its ice
    assert g.board[(2, 1)].effects == set()
    assert g.board[(2, 1)].unit.type == 'alphascorpion'

def t_WeaponGooAttackBuildingDies():
    "Have a Goo do his attack against a building that dies."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Building(g, hp=2, maxhp=2)) # more hp given
    g.board[(1, 1)].createUnitHere(Unit_LargeGoo(g, qshot=(Direction.RIGHT,)))
    assert g.board[(2, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 3 # goo took the spot of the building
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit == None # goo moved from here

def t_WeaponGooAttackMountainDies():
    "Have a Goo do his attack against a mountain that dies. The mountain does NOT become a mountaindamaged!"
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 1)].createUnitHere(Unit_LargeGoo(g, qshot=(Direction.RIGHT,)))
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit.hp == 3
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(2, 1)].unit.hp == 3 # goo took the spot of the mountain
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(1, 1)].unit == None # goo moved from here

def t_WeaponSuperStinger():
    "Have a HornetLeader do his attack but the secondary tile is offboard"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_HornetLeader(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.hp == 6 # vek took no damage
    assert g.board[(2, 1)].unit.effects == set()

def t_WeaponSuperStinger2():
    "Have a HornetLeader do his attack where he actually hits 2 tiles"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 1)].createUnitHere(Unit_HornetLeader(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    g.board[(3, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(2, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.hp == 6 # vek took no damage
    assert g.board[(3, 1)].unit.effects == set()

def t_WeaponSuperStinger3():
    "Have a HornetLeader do his attack where he actually hits 3 tiles"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(4, 1)].createUnitHere(Unit_HornetLeader(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    g.board[(4, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(2, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(3, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.hp == 6 # vek took no damage
    assert g.board[(4, 1)].unit.effects == set()

def t_WeaponSuperStinger4():
    "Have a HornetLeader do his attack where he actually hits 3 tiles and there's a 4th that isn't hit"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(4, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(5, 1)].createUnitHere(Unit_HornetLeader(g, qshot=(Direction.LEFT,)))
    assert g.board[(1, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 5
    assert g.board[(5, 1)].unit.hp == 6
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(5, 1)].unit.effects == set()
    g.board[(5, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5  # mech took NO damage
    assert g.board[(2, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(3, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(4, 1)].unit.hp == 3  # mech took 2 damage
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(3, 1)].unit.effects == set()
    assert g.board[(4, 1)].unit.effects == set()
    assert g.board[(5, 1)].unit.hp == 6 # vek took no damage
    assert g.board[(5, 1)].unit.effects == set()

def t_WeaponMassiveSpinneret():
    "Have a ScorpionLeader do his attack."
    g = Game()
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_ScorpionLeader(g, qshot=()))
    assert g.board[(1, 1)].unit.hp == 7
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 2)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 7  # Vek took no damage
    assert g.board[(2, 1)].unit == None # mech pushed from here
    assert g.board[(1, 2)].unit == None # mech pushed from here
    assert g.board[(3, 1)].unit.hp == 3 # mech took 2 damage
    assert g.board[(1, 3)].unit.hp == 3 # mech took 2 damage

def t_WeaponMassiveSpinneretOnIceFire():
    "Have a ScorpionLeader web his nearby targets while on ice, then the ice is melted by fire causing his attack to be cancelled but the web remains."
    g = Game()
    g.board[(1, 1)].replaceTile(Tile_Ice(g))
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5, weapon1=Weapon_FlameThrower()))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_ScorpionLeader(g, qshot=()))
    g.board[(1, 1)].unit._makeWeb((1, 2))
    g.board[(1, 1)].unit._makeWeb((2, 1))
    assert g.board[(1, 1)].unit.hp == 7
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 2)].unit.hp == 5
    assert g.board[(2, 1)].unit.web == {(1, 1)}
    assert g.board[(1, 2)].unit.web == {(1, 1)}
    assert g.board[(1, 1)].unit.web == {(2, 1), (1, 2)}
    assert g.board[(1, 1)].effects == set()
    assert g.board[(1, 1)].unit.effects == set()
    g.board[(2, 1)].unit.weapon1.shoot(Direction.LEFT, 1) # this should sink the scorpion boss into the water, disabling his attack.
    g.flushHurt()
    g.board[(1, 1)].unit.weapon1.shoot() # this did nothing
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 7  # Vek took no damage
    assert g.board[(2, 1)].unit.hp == 5 # mech took NO damage
    assert g.board[(1, 2)].unit.hp == 5 # mech took NO damage
    assert g.board[(2, 1)].unit.web == {(1, 1)} # webs remain
    assert g.board[(1, 2)].unit.web == {(1, 1)}
    assert g.board[(1, 1)].unit.web == {(2, 1), (1, 2)}
    assert g.board[(1, 1)].effects == {Effects.SUBMERGED} # tile is now water
    assert g.board[(1, 1)].unit.effects == set() # no fire on the boss

def t_WeaponBurningThorax():
    "Have a FireflyLeader do his attack."
    g = Game()
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_FireflyLeader(g, qshot=(Direction.RIGHT,)))
    assert g.board[(1, 1)].unit.hp == 6
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 2)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 6  # Vek took no damage
    assert g.board[(2, 1)].unit.hp == 1 # mech took 4 damage
    assert g.board[(1, 2)].unit.hp == 5 # mech took no damage

def t_WeaponTinyMandibles():
    "Have a Spiderling do his attack."
    g = Game()
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_Spiderling(g, qshot=(Direction.RIGHT,)))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 2)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # Vek took no damage
    assert g.board[(2, 1)].unit.hp == 4 # mech took 1 damage
    assert g.board[(1, 2)].unit.hp == 5 # mech took no damage

def t_WeaponTinyMandiblesAlpha():
    "Have an AlphaSpiderling do his attack."
    g = Game()
    g.board[(1, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5)) # extra hp given
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_AlphaSpiderling(g, qshot=(Direction.RIGHT,)))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(1, 2)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # Vek took no damage
    assert g.board[(2, 1)].unit.hp == 3 # mech took 2 damage
    assert g.board[(1, 2)].unit.hp == 5 # mech took no damage

def t_WeaponCannon8RMarkI1():
    "Have a CannonBot do his attack."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_CannonBot(g, qshot=(Direction.RIGHT,)))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # bot took no damage
    assert g.board[(2, 1)].unit.hp == 4 # mech took 1 damage
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].effects == set()

def t_WeaponCannon8RMarkI2():
    "Have a CannonBot do his attack but not hit a unit."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_CannonBot(g, qshot=(Direction.RIGHT,)))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].effects == set()
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # bot took no damage
    assert g.board[(2, 1)].effects == set()
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].effects == {Effects.FIRE}

def t_WeaponCannon8RMarkII1():
    "Have a CannonMech do his attack."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_CannonMech(g, qshot=(Direction.RIGHT,)))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # bot took no damage
    assert g.board[(2, 1)].unit.hp == 2 # mech took 3 damage
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].effects == set()

def t_WeaponCannon8RMarkIIShielded():
    "Have a CannonMech do his attack against a shielded unit."
    g = Game()
    g.board[(2, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5, effects={Effects.SHIELD,}))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_CannonMech(g, qshot=(Direction.RIGHT,)))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(2, 1)].unit.effects == {Effects.SHIELD,}
    assert g.board[(2, 1)].effects == set()
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].effects == set()
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1  # bot took no damage
    assert g.board[(2, 1)].unit.hp == 5 # mech took 0 damage
    assert g.board[(2, 1)].unit.effects == {Effects.FIRE}
    assert g.board[(2, 1)].effects == {Effects.FIRE}
    assert g.board[(8, 1)].unit == None
    assert g.board[(8, 1)].effects == set()

def t_WeaponVk8RocketsMarkI():
    "Have an ArtilleryBot do his attack."
    g = Game()
    g.board[(3, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_ArtilleryBot(g, qshot=(Direction.RIGHT, 2)))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # Vek took no damage
    assert g.board[(3, 1)].unit.hp == 4 # mech took 1 damage
    assert g.board[(3, 2)].unit.hp == 4 # mech took 1 damage

def t_WeaponVk8RocketsMarkII():
    "Have an ArtilleryMech do his attack."
    g = Game()
    g.board[(3, 1)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(3, 2)].createUnitHere(Unit_TechnoHornet_Mech(g, hp=5, maxhp=5))  # extra hp given
    g.board[(1, 1)].createUnitHere(Unit_ArtilleryMech(g, qshot=(Direction.RIGHT, 2)))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(3, 2)].unit.hp == 5
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # Vek took no damage
    assert g.board[(3, 1)].unit.hp == 2 # mech took 3 damage
    assert g.board[(3, 2)].unit.hp == 2 # mech took 3 damage

def t_WeaponBKRBeamMarkI():
    "Do the BurstBeam weapon demo with a LaserBot instead"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_LaserBot(g, qshot=(Direction.RIGHT,)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    assert g.board[(8, 1)].effects == set() # forest not on fire
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # wielder untouched
    assert g.board[(2, 1)].unit.hp == 3 # vek took 2 damage
    assert g.board[(3, 1)].unit.hp == 4 # vek took 1 damage
    assert g.board[(4, 1)].unit.hp == 1 # friendly took 1 damage
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged
    assert g.board[(8, 1)].effects == set()  # forest still not on fire

def t_WeaponBKRBeamMarkII():
    "Do the BurstBeam weapon demo with a LaserMech instead"
    g = Game()
    g.board[(8, 1)].replaceTile(Tile_Forest(g))
    g.board[(1, 1)].createUnitHere(Unit_LaserMech(g, qshot=(Direction.RIGHT,)))
    g.board[(2, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(3, 1)].createUnitHere(Unit_AlphaScorpion(g))
    g.board[(4, 1)].createUnitHere(Unit_Defense_Mech(g))
    g.board[(5, 1)].createUnitHere(Unit_Mountain(g))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 5
    assert g.board[(3, 1)].unit.hp == 5
    assert g.board[(4, 1)].unit.hp == 2
    assert g.board[(5, 1)].unit.type == 'mountain'
    assert g.board[(8, 1)].effects == set() # forest not on fire
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # wielder untouched
    assert g.board[(2, 1)].unit.hp == 1 # vek took 4 damage
    assert g.board[(3, 1)].unit.hp == 2 # vek took 3 damage
    assert g.board[(4, 1)].unit.type == 'mechcorpse' # friendly mech died from 2 damage
    assert g.board[(5, 1)].unit.type == 'mountaindamaged' # mountain was damaged
    assert g.board[(8, 1)].effects == set()  # forest still not on fire

def t_WeaponSelfRepair():
    "Have a BotLeader heal himself."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_BotLeader_Healing(g, qshot=()))
    assert g.board[(1, 1)].unit.hp == 5
    g.board[(1, 1)].takeDamage(3)
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.effects == set()  # no unit effects
    assert g.board[(1, 1)].effects == set()  # no tile effects
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5 # BotLeader healed to full
    assert g.board[(1, 1)].unit.effects == set() # no unit effects
    assert g.board[(1, 1)].effects == set() # no tile effects

def t_WeaponSelfRepairIce():
    "Have a BotLeader try to heal himself but he gets frozen."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_BotLeader_Healing(g, qshot=()))
    assert g.board[(1, 1)].unit.hp == 5
    g.board[(1, 1)].takeDamage(3)
    g.board[(1, 1)].applyIce()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.effects == {Effects.ICE} # shit's cold
    assert g.board[(1, 1)].effects == set()  # no tile effects
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 2 # BotLeader didn't heal
    assert g.board[(1, 1)].unit.effects == {Effects.ICE} # still frozen
    assert g.board[(1, 1)].effects == set() # no tile effects

def t_WeaponSelfRepairFireTile():
    "Have a BotLeader heal himself but him and his tile is on fire."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_BotLeader_Healing(g, qshot=()))
    assert g.board[(1, 1)].unit.hp == 5
    g.board[(1, 1)].takeDamage(3)
    g.board[(1, 1)].applyFire() # apply fire to tile and unit
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE} # shit's hot
    assert g.board[(1, 1)].effects == {Effects.FIRE} # tile's on fire
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5 # BotLeader healed
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE} # still on fire
    assert g.board[(1, 1)].effects == {Effects.FIRE} # tile still on fire

def t_WeaponSelfRepairFireNotTile():
    "Have a BotLeader heal himself but he's fire (but not his tile)."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_BotLeader_Healing(g, qshot=(), effects={Effects.FIRE}))
    assert g.board[(1, 1)].unit.hp == 5
    g.board[(1, 1)].takeDamage(3)
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.effects == {Effects.FIRE} # shit's hot
    assert g.board[(1, 1)].effects == set() # tile's not
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5 # BotLeader healed
    assert g.board[(1, 1)].unit.effects == set() # repair put out the fire
    assert g.board[(1, 1)].effects == set() # tile still not on fire

def t_WeaponSelfRepairAcid():
    "Have a BotLeader heal himself but and he keeps acid."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_BotLeader_Healing(g, qshot=(), effects={Effects.ACID}))
    assert g.board[(1, 1)].unit.hp == 5
    g.board[(1, 1)].takeDamage(2)
    assert g.board[(1, 1)].unit.hp == 1 # 4 damage taken because of acid
    assert g.board[(1, 1)].unit.effects == {Effects.ACID} # shit's acidy
    assert g.board[(1, 1)].effects == set() # tile's not
    g.board[(1, 1)].unit.weapon1.shoot()
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 5 # BotLeader healed
    assert g.board[(1, 1)].unit.effects == {Effects.ACID} # still has acid
    assert g.board[(1, 1)].effects == set() # tile still normal

def t_TrainPainGauntlet():
    "Have a train get hit with acid and attacked 3 times to ensure it progresses through its stages correctly."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TrainCaboose(g))
    g.board[(2, 1)].createUnitHere(Unit_Train(g))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    g.board[(1, 1)].unit.applyAcid() # acid has no effect on the train in our sim
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    g.board[(1, 1)].takeDamage(2)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traindamagedcaboose'
    assert g.board[(2, 1)].unit.type == 'traindamaged'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    g.board[(2, 1)].takeDamage(2)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincorpse'
    assert g.board[(2, 1)].unit.type == 'traincorpse'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    g.board[(1, 1)].takeDamage(2) # damaging the corpse to make sure nothing weird happens
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincorpse'
    assert g.board[(2, 1)].unit.type == 'traincorpse'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()

def t_WeaponChooChoo1():
    "Use the train's Choo Choo weapon with no unit in the way."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TrainCaboose(g))
    g.board[(2, 1)].createUnitHere(Unit_Train(g))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    g.board[(2, 1)].unit.weapon1.shoot()
    # The train no longer actually moves because it doesn't need to
    #assert g.board[(1, 1)].unit == None # caboose moved from here
    #assert g.board[(2, 1)].unit == None # train front moved from here
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()

def t_WeaponChooChoo2():
    "Use the train's Choo Choo weapon with a unit directly in front of the train."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TrainCaboose(g))
    g.board[(2, 1)].createUnitHere(Unit_Train(g))
    g.board[(3, 1)].createUnitHere(Unit_Scorpion(g))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit.hp == 3
    g.board[(2, 1)].unit.weapon1.shoot()
    #assert g.board[(1, 1)].unit == None # caboose moved from here
    #assert g.board[(2, 1)].unit == None # train front moved from here
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traindamagedcaboose'
    assert g.board[(2, 1)].unit.type == 'traindamaged'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(3, 1)].unit == None # vek died

def t_WeaponChooChoo3():
    "Use the train's Choo Choo weapon with a unit 1 square in front of the train."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TrainCaboose(g))
    g.board[(2, 1)].createUnitHere(Unit_Train(g))
    g.board[(4, 1)].createUnitHere(Unit_Scorpion(g))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(4, 1)].unit.hp == 3
    g.board[(2, 1)].unit.weapon1.shoot()
    # Train no longer moves
    #assert g.board[(1, 1)].unit == None # caboose moved from here
    #assert g.board[(2, 1)].unit == None # train front moved from here
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traindamagedcaboose'
    assert g.board[(2, 1)].unit.type == 'traindamaged'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(4, 1)].unit == None # vek died

def t_WeaponChooChoo4():
    "Use the train's Choo Choo weapon with a unit 2 square in front of the train. (out of harm's way)"
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TrainCaboose(g))
    g.board[(2, 1)].createUnitHere(Unit_Train(g))
    g.board[(5, 1)].createUnitHere(Unit_Scorpion(g))
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(5, 1)].unit.hp == 3
    g.board[(2, 1)].unit.weapon1.shoot()
    # Train no longer moves
    #assert g.board[(1, 1)].unit == None # caboose moved from here
    #assert g.board[(2, 1)].unit == None # train front moved from here
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == set()
    assert g.board[(2, 1)].unit.effects == set()
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(5, 1)].unit.hp == 3 # vek untouched

def t_WeaponChooChooIce():
    "Use the train's Choo Choo weapon with a unit 2 square in front of the train but the train gets frozen."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_TrainCaboose(g))
    g.board[(2, 1)].createUnitHere(Unit_Train(g))
    g.board[(5, 1)].createUnitHere(Unit_Scorpion(g))
    assert g.board[(2, 1)].unit.weapon1.qshot == ()
    g.board[(2, 1)].applyIce()
    assert g.board[(2, 1)].unit.weapon1.qshot == None
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == {Effects.ICE}
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(5, 1)].unit.hp == 3
    g.board[(2, 1)].unit.weapon1.shoot() # this should have done nothing
    assert g.board[(2, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'traincaboose'
    assert g.board[(2, 1)].unit.type == 'train'
    assert g.board[(1, 1)].unit.effects == {Effects.ICE} # still frozen
    assert g.board[(2, 1)].unit.effects == {Effects.ICE}
    assert g.board[(1, 1)].effects == set()
    assert g.board[(2, 1)].effects == set()
    assert g.board[(5, 1)].unit.hp == 3 # vek untouched

def t_WeaponChooChooOffboard():
    "Use the train's Choo Choo weapon and properly handle it trying to go offboard"
    g = Game()
    g.board[(7, 1)].createUnitHere(Unit_TrainCaboose(g))
    g.board[(8, 1)].createUnitHere(Unit_Train(g))
    assert g.board[(8, 1)].unit.weapon1.qshot == ()
    assert g.board[(7, 1)].unit.hp == 1
    assert g.board[(8, 1)].unit.hp == 1
    assert g.board[(7, 1)].unit.type == 'traincaboose'
    assert g.board[(8, 1)].unit.type == 'train'
    assert g.board[(7, 1)].unit.effects == set()
    assert g.board[(8, 1)].unit.effects == set()
    assert g.board[(7, 1)].effects == set()
    assert g.board[(8, 1)].effects == set()
    try:
        g.board[(8, 1)].unit.weapon1.shoot()
    except CantHappenInGame:
        pass # this is expected
    else:
        assert False # ya fucked up

def t_WeaponSatelliteLaunch():
    "Do the satellite launch from the satellite rocket."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_SatelliteRocket(g))
    g.board[(1, 1)].unit.weapon1.qshot = () # we have to manually tell the rocket that it will shoot when told since it doesn't by default.
    g.board[(2, 1)].createUnitHere(Unit_AlphaHornet(g))
    g.board[(1, 2)].createUnitHere(Unit_AlphaHornet(g))
    assert g.board[(1, 1)].unit.weapon1.qshot == ()
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(2, 1)].unit.hp == 4
    assert g.board[(1, 2)].unit.hp == 4
    g.board[(1, 1)].unit.weapon1.shoot()
    assert g.board[(1, 1)].unit.hp == 2 # the rocket is left there because we only simulate 1 turn
    assert g.board[(2, 1)].unit == None # both vek died
    assert g.board[(1, 2)].unit == None

def t_SatelliteRocketDies():
    "Have the satelite rocket take damage to test its stages of pain."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_SatelliteRocket(g))
    assert g.board[(1, 1)].unit.weapon1.qshot == None
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.type == 'satelliterocket'
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].unit.weapon1.qshot == None
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'satelliterocket'
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1
    assert g.board[(1, 1)].unit.type == 'satelliterocketcorpse'
    g.board[(1, 1)].takeDamage(1)
    g.flushHurt()
    assert g.board[(1, 1)].unit.hp == 1 # nothing happens to the corpse when it takes damage
    assert g.board[(1, 1)].unit.type == 'satelliterocketcorpse'

def t_WeaponDisintegrator():
    "Have the Disintegrator shoot it's weapon."
    g = Game()
    g.board[(1, 1)].createUnitHere(Unit_AcidLauncher(g))
    g.board[(1, 6)].createUnitHere(Unit_Hornet(g))
    g.board[(1, 7)].createUnitHere(Unit_Mountain(g))
    g.board[(1, 8)].createUnitHere(Unit_Flame_Mech(g))
    assert g.board[(1, 1)].unit.hp == 2
    assert g.board[(1, 1)].unit.type == 'acidlauncher'
    assert g.board[(1, 6)].effects == set()
    assert g.board[(1, 6)].unit.hp == 2
    assert g.board[(1, 7)].effects == set()
    assert g.board[(1, 7)].unit.hp == 1
    assert g.board[(1, 8)].effects == set()
    assert g.board[(1, 8)].unit.hp == 3
    assert g.board[(2, 7)].effects == set()
    gs = g.board[(1, 1)].unit.weapon1.genShots()
    for shot in range(7):
        shot = next(gs)
    g.board[(1, 1)].unit.weapon1.shoot(*shot)  # (1, 7)
    g.flushHurt()
    assert g.board[(1, 6)].effects == {Effects.ACID}
    assert g.board[(1, 6)].unit == None # vek killed
    assert g.board[(1, 7)].effects == {Effects.ACID}
    assert g.board[(1, 7)].unit == None # mountain is gone
    assert g.board[(1, 8)].effects == set() # acid is on the mech corpse
    assert g.board[(1, 8)].unit.type == 'mechcorpse'
    assert g.board[(2, 7)].effects == {Effects.ACID}
    assert g.board[(2, 7)].unit == None # never was a unit here

def t_WeaponTerraformer():
    "Have the Terraformer shoot it's weapon."
    g = Game()
    for x in range(5, 7):
        for y in range(2, 5):
            g.board[(x, y)].replaceTile(Tile_Grassland(g))
    g.board[(5, 4)].replaceTile(Tile_Ground(g)) # put the mountain's tile back to ground lol
    g.board[(4, 3)].createUnitHere(Unit_Terraformer(g))
    g.board[(5, 3)].createUnitHere(Unit_Hornet(g))
    g.board[(5, 4)].createUnitHere(Unit_Mountain(g))
    g.board[(6, 2)].createUnitHere(Unit_Flame_Mech(g))
    assert g.board[(4, 3)].unit.hp == 2
    assert g.board[(4, 3)].unit.type == 'terraformer'
    assert g.board[(5, 3)].effects == set()
    assert g.board[(5, 3)].unit.hp == 2
    assert g.board[(5, 3)].isGrassland()
    assert g.board[(5, 4)].effects == set()
    assert g.board[(5, 4)].unit.hp == 1
    assert g.board[(5, 4)].type == 'ground'
    assert g.board[(6, 2)].effects == set()
    assert g.board[(6, 2)].unit.hp == 3
    assert g.board[(6, 2)].isGrassland()
    assert not g.board[(7, 3)].isGrassland()
    gs = g.board[(4, 3)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(4, 3)].unit.weapon1.shoot(*shot)  # (RIGHT,)
    g.flushHurt()
    assert g.board[(5, 3)].effects == set()
    assert g.board[(5, 3)].unit == None # vek killed
    assert g.board[(5, 3)].type == "sand"
    assert g.board[(5, 4)].effects == set()
    assert g.board[(5, 4)].unit == None # mountain is gone
    assert g.board[(5, 4)].type == 'ground' # mountains leave ground tiles when destroyed, NOT sand
    assert g.board[(6, 2)].effects == set()
    assert g.board[(6, 2)].unit.type == 'mechcorpse'
    assert g.board[(6, 2)].type == "sand"

def t_WeaponTerraformer2():
    "Have the Terraformer shoot it's weapon but there's an explosive unit that dies."
    g = Game()
    for x in range(5, 7):
        for y in range(2, 5):
            g.board[(x, y)].replaceTile(Tile_Grassland(g))
    g.board[(5, 4)].replaceTile(Tile_Ground(g)) # put the mountain's tile back to ground lol
    g.board[(4, 3)].createUnitHere(Unit_Terraformer(g))
    g.board[(5, 3)].createUnitHere(Unit_Hornet(g, effects=(Effects.EXPLOSIVE,)))
    g.board[(5, 4)].createUnitHere(Unit_Mountain(g))
    g.board[(6, 2)].createUnitHere(Unit_Flame_Mech(g))
    assert g.board[(4, 3)].unit.hp == 2
    assert g.board[(4, 3)].unit.type == 'terraformer'
    assert g.board[(5, 3)].effects == set()
    assert g.board[(5, 3)].unit.hp == 2
    assert g.board[(5, 3)].isGrassland()
    assert g.board[(5, 4)].effects == set()
    assert g.board[(5, 4)].unit.hp == 1
    assert g.board[(5, 4)].type == 'ground'
    assert g.board[(6, 2)].effects == set()
    assert g.board[(6, 2)].unit.hp == 3
    assert g.board[(6, 2)].isGrassland()
    assert not g.board[(7, 3)].isGrassland()
    gs = g.board[(4, 3)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(4, 3)].unit.weapon1.shoot(*shot)  # (RIGHT,)
    g.flushHurt()
    assert g.board[(5, 3)].effects == {Effects.SMOKE}
    assert g.board[(5, 3)].unit == None # vek killed
    assert g.board[(5, 3)].type == "sand"
    assert g.board[(5, 4)].unit == None # mountain is gone
    assert g.board[(5, 4)].effects == set() # destroyed mountain doesn't leave smoke since there was never sand here.
    assert g.board[(5, 4)].type == 'ground' # mountains leave ground tiles when destroyed
    assert g.board[(5, 4)].effects == set() # no smoke here, never became a sand tile
    assert g.board[(6, 2)].effects == set() # this sand tile wasn't hit by the explosion
    assert g.board[(6, 2)].unit.type == 'mechcorpse'
    assert g.board[(6, 2)].type == "sand"

def t_WeaponTerraformer3():
    """Have the Terraformer shoot it's weapon but it's converting sand to sand.
    When this happens in game, you see smoke arise from the sand being damaged, but then the tiles are replaced by new sand tiles without smoke."""
    g = Game()
    for x in range(5, 7):
        for y in range(2, 5):
            g.board[(x, y)].replaceTile(Tile_Sand(g))
    g.board[(4, 3)].createUnitHere(Unit_Terraformer(g))
    assert g.board[(4, 3)].unit.hp == 2
    assert g.board[(4, 3)].unit.type == 'terraformer'
    assert g.board[(5, 3)].effects == set()
    assert g.board[(5, 4)].effects == set()
    assert g.board[(5, 4)].type == 'sand'
    assert g.board[(6, 2)].effects == set()
    gs = g.board[(4, 3)].unit.weapon1.genShots()
    for shot in range(2):
        shot = next(gs)
    g.board[(4, 3)].unit.weapon1.shoot(*shot)  # (RIGHT,)
    g.flushHurt()
    assert g.board[(5, 3)].effects == set()
    assert g.board[(5, 3)].type == "sand"
    assert g.board[(5, 4)].effects == set()
    assert g.board[(5, 4)].type == 'sand'
    assert g.board[(5, 4)].effects == set()
    assert g.board[(6, 2)].effects == set()
    assert g.board[(6, 2)].type == "sand"

########### write tests for these:
# mech corpses that fall into chasms cannot be revived.

########## special objective units:
# Satellite Rocket: 2 hp, Not powered, Smoke Immune, stable, "Satellite Launch" weapon kills nearby tiles when it launches.
# Train: 1 hp, Fire immune, smoke immune, stable, "choo choo" weapon move forward 2 spaces but will be destroyed if blocked. kills whatever unit it runs into, stops dead on the tile before that unit. It is multi-tile, shielding one tile shields both.
    # when attacked and killed, becomes a "damaged train" that is also stable and fire immune. When that is damaged again, it becomes a damaged train corpse that can't be shielded, is no longer fire immune, and is flying like a normal corpse.
    # units can bump into the corpse
# ACID Launcher: 2 hp, stable. weapon is "disentegrator": hits 5 tiles killing anything present and leaves acid on them.
# Terraformer weapon "terraformer" kills any unit in a 2x3 grid around it, converts tiles to sand tile.
# Earth Mover expands toward 0 and 8 on X 2 squares at a time. It does this on the y row that it's on and the row right below it.

########## Weapons stuff for later
# if you use the burst beam (laser mech) and kill an armor psion and hit another unit behind it, the armor is removed from the other unit after it takes damage from the laser.
# viscera nanobots do not repair tiles or remove bad effects, it only heals HP.

# Satellite launches happen after enemy attacks.
# robots do not benefit from psion vek passives such as explosive.
# buildings do block mech movement
# a burrower taking damage from fire cancels its attack and makes it burrow, but again it does lose fire when it re-emerges.
# the little bombs that the blobber throws out are not considered enemies when your objective is to kill 7 enemies.
# blobbers will move out of smoke and throw out a bomb after you take your turn. This means you can't smoke them to stop them from throwing out a blob unless they can't move

########## Research these:
# You can heal allies with the Repair Field passive - when you tell a mech to heal, your other mechs are also healed for 1 hp, even if they're currently disabled.
# What happens when objective units die? specifically: terraformer, disposal unit, satellite rocket (leaves a corpse that is invincible and can't be pushed. It's friendly so you can move through it), earth mover.

########## Do these ones even matter?
# Spiderling eggs with acid hatch into spiders with acid.
# Timepods can only be on ground tiles, they convert sand and forest to ground upon landing.

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
