#!/usr/bin/env python3

# This script brute forces the best possible single turn in Into The Breach
############# NOTES ######################
# Order of turn operations:
#   0 Fire
#   1 Environment
#   2 Enemy Actions
#   3 NPC actions
#   4 Enemies emerge

############ IMPORTS ######################

############### GLOBALS ###################
DEBUG=True

############### FUNCTIONS #################

############### CLASSES #################
class ReplaceObj(Exception):
    "Raised by tiles and units to tell the GameBoard to replace the current tile or unit with newobj"
    def __init__(self, newobj):
        self.newobj = newobj

class GameBoard():
    "This represents the game board and some of the most basic rules of the game."
    def __init__(self, powergrid_hp=7):
        self.board = {} # a dictionary of all 64 squares on the board. Each key is a coordinate and each value is a list of the tile object and unit object: {'a1': [Tile, Unit]}
        for letter in 'abcdefgh':
            for num in range(1, 9):
                self.board['%s%i' % (letter, num)] = [None, None]
        self.powergrid_hp = powergrid_hp # max is 7

class Tile():
    """This object is a normal tile. All other tiles are based on this. Mountains and buildings are considered units since they have HP and block movement on a tile, thus they go on top of the tile."""
    def __init__(self, type='ground', effects=set()):
        self.type = type # the type of tile, the name of it.
        self.effects = effects # Current effect(s) on the tile. Effects are on top of the tile. Some can be removed by having your mech repair while on the tile.
            #  fire, smoke, acid, mine, freezemine, timepod. Units can also have shield, ice, web.
    def takeDamage(self, damage):
        "Process the tile taking damage. Damage is an int of how much damage to take, but normal tiles are unaffected by damage."
        self.removeEffect('timepod')
    def applyFire(self):
        "set the current tile on fire"
        self.effects.add('fire')
        self.removeEffect('timepod') # fire kills timepods
    def applySmoke(self):
        "make a smoke cloud on the current tile"
        self.effects.add('smoke')
    def applyIce(self):
        self.removeEffect('fire')
    def applyAcid(self):
        self.effects.add('acid')
    def applyShield(self):
        pass # Tiles can't be shielded, only units
    def removeEffect(self, effect):
        try:
            self.effects.remove(effect)
        except KeyError:
            pass
    def repair(self):
        "process the action of a friendly mech repairing on this tile and removing certain effects."
        for effect in ('fire', 'smoke', 'acid'):
            self.removeEffect(effect)

class Tile_Forest(Tile):
    "If damaged, lights on fire."
    def __init__(self, effects=set()):
        super().__init__(type='forest', effects=effects)
    def takeDamage(self, damage):
        "tile gains the fire effect"
        self.applyFire()

class Tile_Sand(Tile):
    "If damaged, turns into Smoke. Units in Smoke cannot attack or repair."
    def __init__(self, effects=set()):
        super().__init__(type='sand', effects=effects)
    def takeDamage(self, damage):
        self.applySmoke()

class Tile_Water(Tile):
    "Non-huge land units die when pushed into water. Water cannot be set on fire."
    def __init__(self, effects=set()):
        super().__init__(type='water', effects=effects)
    def applyFire(self):
        pass
    def applyIce(self):
        raise ReplaceObj(Tile_Ice)
    def repair(self): # acid cannot be removed from water by repairing it.
        try:
            self.effects.remove('smoke')
        except KeyError:
            pass

class Tile_Ice(Tile):
    "Turns into Water when destroyed. Must be hit twice. (Turns into Ice_Damaged.)"
    def __init__(self, effects=set()):
        super().__init__(type='ice', effects=effects)
    def takeDamage(self, damage):
        raise ReplaceObj(Tile_Ice_Damaged)
    def applyFire(self):
        raise ReplaceObj(Tile_Water)

class Tile_Ice_Damaged(Tile_Ice):
    def __init__(self, effects=set()):
        super().__init__(type='ice_damaged', effects=effects)
    def takeDamage(self, damage):
        raise ReplaceObj(Tile_Water)

class Tile_Chasm(Tile):
    "Non-flying units die when pushed into water. Chasm tiles cannot have acid or fire, but can have smoke."
    def __init__(self, effects=set()):
        super().__init__(type='chasm', effects=effects)
    def applyFire(self):
        pass
    def applyIce(self):
        pass
    def applyAcid(self):
        pass

class Tile_Lava(Tile_Water):
    def __init__(self, effects={'fire'}):
        super().__init__(type='lava', effects=effects)
    def repair(self):
        try:
            self.effects.remove('smoke')
        except KeyError:
            pass

class Tile_Grassland(Tile):
    "Your bonus objective is to terraform Grassland tiles into Sand. This is mostly just a regular ground tile."
    def __init__(self, effects=set()):
        super().__init__(type='grassland', effects=effects)

class Tile_Terraformed(Tile):
    "This tile was terraformed as part of your bonus objective. Also just a regular ground tile."
    def __init__(self, effects=set()):
        super().__init__(type='terraformed', effects=effects)

class Tile_Teleporter(Tile):
    "End movement here to warp to the matching pad. Swap with any present unit."
    def __init__(self, color, effects=set()):
        super().__init__(type='teleporter', effects=effects)
        self.color = color # Either red or blue
        self.exittile = None # Set by the gameboard when initializing. This is a gameboard coordinate like 'a1'

class Tile_Conveyor(Tile):
    "This tile will push any unit in the direction marked on the belt."
    def __init__(self, direction, effects=set()):
        "direction must be u, r, d, l for up, right, down, left"
        super().__init__(type='conveyor', effects=effects)
        self.direction = direction

class Unit(Tile):
    "The base class of all units. A unit is anything that occupies a square and stops other ground units from moving through it."
    def __init__(self, type, currenthp, maxhp, attributes=set(), effects=set()):
        """type is the name of the unit (str)
        currenthp is the unit's current hitpoints (int)
        maxhp is the unit's maximum hitpoints (int)
        effects is a set of effects applied to this unit
        attributes is a set of attributes or properties that the unit has.
        """
        super().__init__(type=type, effects=effects)
        self.currenthp = currenthp
        self.maxhp = maxhp
        self.attributes = attributes # possible attributes are: massive, stable, flying, armoured, burrower,
        self.damage_taken = 0 # This is a running count of how much damage this unit has taken during this turn.
            # This is done so that points awarded to a solution can be removed on a unit's death. We don't want solutions to be more valuable if an enemy is damaged before it's killed. We don't care how much damage was dealt to it if it dies.
    def applyWeb(self):
        self.effects.add('web')
    def applyShield(self):
        self.effects.add('shield')
    def applyIce(self):
        super().applyIce()
        self.effects.add('ice')
    def takeDamage(self, damage):
        self.currenthp -= damage # the unit takes the damage
        self.damage_taken += damage
        if self.currenthp <= 0: # if the unit has no more HP
            self.damage_taken -= self.currenthp # adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead. # TODO! This math is wrong
            self.die()
    def takeBumpDamage(self):
        "take damage from bumping. This is when you're pushed into something or a vek tries to emerge beneath you."
        self.takeDamage(1) # this is overridden by enemies that take increased bump damage by that one global powerup that increases bump damage to enemies only
    def repairHP(self, hp=1): # TODO move this out of the base, not all units can be repaired
        "Repair hp amount of hp. Does not take you higher than the max. Do not remove any effects."
        self.currenthp += hp
        if self.currenthp > self.maxhp:
            self.currenthp = self.maxhp
    def die(self):
        "Make the unit die."
        raise ReplaceObj(None) # it's dead, replace it with nothing

class Unit_Mountain(Unit):
    def __init__(self, type='mountain', currenthp=1, maxhp=1, attributes={'stable'}, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
    def applyFire(self):
        pass # mountains can't be set on fire
    def applyAcid(self):
        pass # same for acid
    def takeDamage(self, damage=1):
        ReplaceObj(Unit_Mountain_Damaged)

class Unit_Mountain_Damaged(Unit_Mountain):
    def __init__(self, type='mountain_damaged', currenthp=1, maxhp=1, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
    def takeDamage(self, damage=1):
        ReplaceObj(Tile)

class Unit_Volcano(Unit_Mountain):
    "Indestructible volcano that blocks movement and projectiles."
    def __init__(self, type='volcano', currenthp=1, maxhp=1, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
    def takeDamage(self, damage=1):
        pass # what part of indestructible do you not understand?!

class Unit_Building(Unit):
    def __init__(self, type='building', currenthp=1, maxhp=1, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
    def repairHP(self, hp):
        pass # buildings can't repair, dream on

class Unit_Building_Objective(Unit_Building):
    def __init__(self, type='building_objective', currenthp=1, maxhp=1, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Blobber(Unit):
    "This can be considered the base unit of Vek since the Blobber doesn't have a direct attack or effect. The units it spawns are separate units that happens after the simulation's turn."
    def __init__(self, type='blobber', currenthp=3, maxhp=3, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
############## PROGRAM FLOW FUNCTIONS ###############

############## MAIN ########################
if __name__ == '__main__':
    u = Unit_Mountain_Damaged()
    print(u.attributes)
