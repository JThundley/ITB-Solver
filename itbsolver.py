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
            #  fire, smoke, acid, mine, freezemine
    def takeDamage(self, damage):
        "Process the tile taking damage. Damage is an int of how much damage to take, but normal tiles are unaffected by damage."
        return
    def addFire(self):
        "set the current tile on fire"
        self.effects.add('fire')
    def addSmoke(self):
        "make a smoke cloud on the current tile"
        self.effects.add('smoke')
    def addIce(self):
        try:
            self.affects.remove('fire')
        except KeyError:
            pass
    def addAcid(self):
        self.effects.add('acid')
    def removeAcid(self):
        try:
            self.effects.remove('acid')
        except KeyError:
            pass
    def repair(self):
        "process the action of a friendly mech repairing on this tile and removing certain effects."
        for effect in ('fire', 'smoke', 'acid'):
            try:
                self.effects.remove(effect)
            except KeyError:
                pass

class Tile_Forest(Tile):
    "If damaged, lights on fire."
    def __init__(self, effects=set()):
        super().__init__(type='forest', effects=effects)
    def takeDamage(self, damage):
        "tile gains the fire effect"
        self.addFire()

class Tile_Sand(Tile):
    "If damaged, turns into Smoke. Units in Smoke cannot attack or repair."
    def __init__(self, effects=set()):
        super().__init__(type='sand', effects=effects)
    def takeDamage(self, damage):
        self.addSmoke()

class Tile_Water(Tile):
    "Non-huge land units die when pushed into water. Water cannot be set on fire."
    def __init__(self, effects=set()):
        super().__init__(type='water', effects=effects)
    def addFire(self):
        pass
    def addIce(self):
        raise ReplaceObj(Tile_Ice)
    def repair(self): # acid cannot be removed from water by repairing it.
        for effect in ('fire', 'smoke'):
            try:
                self.effects.remove(effect)
            except KeyError:
                pass

class Tile_Chasm(Tile):
    "Non-flying units die when pushed into water. Chasm tiles cannot have acid or fire, but can have smoke."
    def __init__(self, effects=set()):
        super().__init__(type='chasm', effects=effects)
    def addFire(self):
        pass
    def addIce(self):
        pass

class Tile_Ice(Tile):
    "Turns into Water when destroyed. Must be hit twice. (Turns into Ice_Damaged.)"
    def __init__(self, effects=set()):
        super().__init__(type='ice', effects=effects)
    def takeDamage(self, damage):
        raise ReplaceObj(Tile_Ice_Damaged)
    def addFire(self):
        raise ReplaceObj(Tile_Water)

class Tile_Ice_Damaged(Tile_Ice):
    def __init__(self, effects=set()):
        super().__init__(type='ice_damaged', effects=effects)
    def takeDamage(self, damage):
        raise ReplaceObj(Tile_Water)

class Tile_Lava(Tile_Water):
    def __init__(self, effects=set('fire')):
        super().__init__(type='ice_lava', effects=effects)
    def repair(self):
        try:
            self.effects.remove('smoke')
        except KeyError:
            pass

class Unit(Tile):
    "The base class of all units. A unit is anything that occupies a square and stops other ground units from moving through it."
    def __init__(self, type, currenthp, maxhp, effects=set()):
        """type is the name of the unit (str)
        currenthp is the unit's current hitpoints (int)
        maxhp is the unit's maximum hitpoints (int)
        effects is a set of effects applied to this unit
        """
        super().__init__(type=type, effects=effects)
        self.currenthp = currenthp
        self.maxhp = maxhp
    def takeDamage(self, damage):
        self.currenthp -= damage # the unit takes the damage
        if self.currenthp <= 0: # if the unit has no more HP
            raise ReplaceObj(None) # it's dead, replace it with nothing
    def takeBumpDamage(self):
        "take damage from bumping. This is when you're pushed into something or a vek tries to emerge beneath you."
        self.takeDamage(1) # this is overridden by enemies that take increased bump damage by that one global powerup that increases bump damage to enemies only
    def repairHP(self, hp=1): # TODO move this out of the base, not all units can be repaired
        "Repair hp amount of hp. Does not take you higher than the max. Do not remove any effects."
        self.currenthp += hp
        if self.currenthp > self.maxhp:
            self.currenthp = self.maxhp

class Unit_Mountain(Unit):
    def __init__(self, type='mountain', currenthp=1, maxhp=1, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
    def addFire(self):
        pass # mountains can't be set on fire
    def addAcid(self):
        pass # same for acid
    def takeDamage(self, damage=1):
        ReplaceObj(Unit_Mountain_Damaged)

class Unit_Mountain_Damaged(Unit_Mountain):
    def __init__(self, type='mountain_damaged', currenthp=1, maxhp=1, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
    def takeDamage(self, damage=1):
        ReplaceObj(Tile)

class Unit_building(Unit):
    def __init__(self, type='building', currenthp=1, maxhp=1, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
    def repairHP(self, hp):
        pass # buildings can't repair, dream on

############## PROGRAM FLOW FUNCTIONS ###############

############## MAIN ########################
if __name__ == '__main__':
    i = Tile_Ice()
    try:
        i.takeDamage(1)
    except ReplaceObj as whatsnew:
        print(whatsnew)
        whatsnew.newobj = whatsnew