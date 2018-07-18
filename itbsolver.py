#!/usr/bin/env python3

# This script brute forces the best possible single turn in Into The Breach
############# NOTES ######################
# Order of turn operations:
#   Fire
#   Storm Smoke
#   Environment
#   Enemy Actions
#   NPC actions
#   Enemies emerge

############ IMPORTS ######################

############### GLOBALS ###################
DEBUG=True

class Effects():
    "These are effects that can be applied to tiles and units."
    # These effects can be applied to both tiles and units:
    FIRE = 1
    ICE = 2 # if applied to a unit, the unit is frozen
    ACID = 3
    # These effects can only be applied to tiles:
    SMOKE = 4
    TIMEPOD = 5
    MINE = 6
    FREEZEMINE = 7
    VEKEMERGE = 8
    # These effects can only be applied to units:
    SHIELD = 9
    WEB = 10
    EXPLOSIVE = 11

class Attributes():
    "These are attributes that are applied to units."
    # possible attributes are: massive, stable, flying, armoured, burrower,
    MASSIVE = 1 # prevents drowning in water
    STABLE = 2 # prevents units from being pushed
    FLYING = 3 # prevents drowning in water and allows movement through other units
    ARMORED = 4 # all attacks are reduced by 1
    BURROWER = 5 # unit burrows after taking any damage

class Direction():
    "These are up/down/left/right directions with a function to get the opposite direction."
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4
    def opposite(dir):
        "return the opposite of the direction provided as dir."
        dir += 2
        if dir > 4:
            dir -= 4
        return dir

############### FUNCTIONS #################

############### CLASSES #################
class ReplaceObj(Exception):
    "Raised by tiles and units to tell the GameBoard to replace the current tile or unit with newobj"
    def __init__(self, newobj):
        self.newobj = newobj

class GameBoard():
    "This represents the game board and some of the most basic rules of the game."
    def __init__(self, powergrid_hp=7):
        self.board = {} # a dictionary of all 64 squares on the board. Each key is a tuple of x,y coordinates and each value is a list of the tile object and unit object: {(1, 1): [Tile, Unit]}
        for letter in range(1, 9):
            for num in range(1, 9):
                self.board[(letter, num)] = [None, None]
        self.powergrid_hp = powergrid_hp # max is 7
    def push(self, tile, direction):
        "push units on tile direction. tile is a tuple of (x, y) coordinates, direction is a Direction.UP direction."
        if Attributes.STABLE not in self.board[tile][1].attributes: # only non-stable units can be pushed.
            if direction == Direction.UP:
                destinationtile = (tile[0], tile[1] + 1)
            elif direction == Direction.RIGHT:
                destinationtile = (tile[0] + 1, tile[1])
            elif direction == Direction.DOWN:
                destinationtile = (tile[0], tile[1] - 1)
            elif direction == Direction.LEFT:
                destinationtile = (tile[0] - 1, tile[1])
            else:
                raise Exception("Invalid direction given to GameBoard.push()")
            try:
                self.board[destinationtile]
            except KeyError:
                return # attempted to push unit off the gameboard, no action is taken
            else:
                try:
                    self.board[destinationtile][1].takeBumpDamage()
                except AttributeError: # raised from None.takeBumpDamage, there is no unit there to bump into
                    self.board[destinationtile][1] = self.board[tile][1] # move the unit from tile to destination tile
                    self.board[tile][1] = None
                else:
                    self.board[tile][1].takeBumpDamage() # The destination took bump damage, now the unit that got pushed also takes damage

class Tile():
    """This object is a normal tile. All other tiles are based on this. Mountains and buildings are considered units since they have HP and block movement on a tile, thus they go on top of the tile."""
    def __init__(self, type='ground', effects=set()):
        self.type = type # the type of tile, the name of it.
        self.effects = effects # Current effect(s) on the tile. Effects are on top of the tile. Some can be removed by having your mech repair while on the tile.
    def takeDamage(self, damage):
        "Process the tile taking damage. Damage is an int of how much damage to take, but normal tiles are unaffected by damage."
        self.removeEffect(Effects.TIMEPOD)
    def applyFire(self):
        "set the current tile on fire"
        self.effects.add(Effects.FIRE)
        self.removeEffect(Effects.TIMEPOD) # fire kills timepods
    def applySmoke(self):
        "make a smoke cloud on the current tile"
        self.effects.add(Effects.SMOKE)
    def applyIce(self):
        self.removeEffect(Effects.FIRE)
    def applyAcid(self):
        self.effects.add(Effects.ACID)
    def applyShield(self):
        pass # Tiles can't be shielded, only units
    def removeEffect(self, effect):
        try:
            self.effects.remove(effect)
        except KeyError:
            pass
    def repair(self):
        "process the action of a friendly mech repairing on this tile and removing certain effects."
        for effect in (Effects.FIRE, Effects.SMOKE, Effects.ACID):
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
    def applyFire(self): # water can't be set on fire
        pass
    def applyIce(self):
        raise ReplaceObj(Tile_Ice)
    def repair(self): # acid cannot be removed from water by repairing it.
        self.removeEffect(Effects.SMOKE)

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
        self.removeEffect(Effects.SMOKE)
    # TODO: Can lava be frozen?

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
        effects is a set of effects applied to this unit. Use Effects.EFFECTNAME for this.
        attributes is a set of attributes or properties that the unit has. use Attributes.ATTRNAME for this.
        """
        super().__init__(type=type, effects=effects)
        self.currenthp = currenthp
        self.maxhp = maxhp
        self.attributes = attributes
        self.damage_taken = 0 # This is a running count of how much damage this unit has taken during this turn.
            # This is done so that points awarded to a solution can be removed on a unit's death. We don't want solutions to be more valuable if an enemy is damaged before it's killed. We don't care how much damage was dealt to it if it dies.
    def applyWeb(self):
        self.effects.add(Effects.WEB)
    def applyShield(self):
        self.effects.add(Effects.SHIELD)
    def applyIce(self):
        super().applyIce()
        self.effects.add(Effects.ICE)
    def takeDamage(self, damage):
        self.currenthp -= damage # the unit takes the damage
        self.damage_taken += damage
        if self.currenthp <= 0: # if the unit has no more HP
            self.damage_taken += self.currenthp # currenthp is now negative or 0. Adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead.
            self.die()
    def takeBumpDamage(self):
        "take damage from bumping. This is when you're pushed into something or a vek tries to emerge beneath you."
        self.takeDamage(1) # this is overridden by enemies that take increased bump damage by that one global powerup that increases bump damage to enemies only
    def die(self):
        "Make the unit die."
        raise ReplaceObj(None) # it's dead, replace it with nothing

class Unit_Mountain(Unit):
    def __init__(self, type='mountain', attributes={Attributes.STABLE}, effects=set()):
        super().__init__(type=type, currenthp=1, maxhp=1, attributes=attributes, effects=effects)
    def applyFire(self):
        pass # mountains can't be set on fire
    def applyAcid(self):
        pass # same for acid
    def takeDamage(self, damage=1):
        ReplaceObj(Unit_Mountain_Damaged)

class Unit_Mountain_Damaged(Unit_Mountain):
    def __init__(self, type='mountain_damaged', effects=set()):
        super().__init__(type=type, currenthp=1, maxhp=1, effects=effects)
    def takeDamage(self, damage=1):
        ReplaceObj(Tile)

class Unit_Volcano(Unit_Mountain):
    "Indestructible volcano that blocks movement and projectiles."
    def __init__(self, type='volcano', effects=set()):
        super().__init__(type=type, currenthp=1, maxhp=1, effects=effects)
    def takeDamage(self, damage=1):
        pass # what part of indestructible do you not understand?!

class Unit_Building(Unit):
    def __init__(self, type='building', currenthp=1, maxhp=1, effects=set(), attributes={Attributes.STABLE}):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
    def repairHP(self, hp):
        pass # buildings can't repair, dream on

class Unit_Building_Objective(Unit_Building):
    def __init__(self, type='building_objective', currenthp=1, maxhp=1, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Acid_Vat(Unit_Building_Objective):
    def __init__(self, type='acidvat', currenthp=2, maxhp=2, effects=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
    def die(self):
        "Acid vats turn into acid water when destroyed."
        ReplaceObj(None) # TODO: How do we have a unit replace a tile?

class Unit_Blobber(Unit):
    "This can be considered the base unit of Vek since the Blobber doesn't have a direct attack or effect. The units it spawns are separate units that happens after the simulation's turn."
    def __init__(self, type='blobber', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)
    def repairHP(self, hp=1):
        "Repair hp amount of hp. Does not take you higher than the max. Does not remove any effects."
        self.currenthp += hp
        if self.currenthp > self.maxhp:
            self.currenthp = self.maxhp

class Unit_Alpha_Blobber(Unit_Blobber):
    "Also has no attack."
    def __init__(self, type='alphablobber', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scorpion(Unit_Blobber):
    def __init__(self, type='scorpion', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Acid_Scorpion(Unit_Blobber):
    def __init__(self, type='acidscorpion', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Scorpion(Unit_Blobber):
    def __init__(self, type='alphascorpion', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Firefly(Unit_Blobber):
    def __init__(self, type='firefly', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Firefly(Unit_Blobber):
    def __init__(self, type='alphascorpion', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Leaper(Unit_Blobber):
    def __init__(self, type='leaper', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Leaper(Unit_Blobber):
    def __init__(self, type='alphaleaper', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Beetle(Unit_Blobber):
    def __init__(self, type='beetle', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Beetle(Unit_Blobber):
    def __init__(self, type='alphabeetle', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scarab(Unit_Blobber):
    def __init__(self, type='scarab', currenthp=2, maxhp=2, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Scarab(Unit_Blobber):
    def __init__(self, type='alphascarab', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Crab(Unit_Blobber):
    def __init__(self, type='crab', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Crab(Unit_Blobber):
    def __init__(self, type='alphacrab', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Centipede(Unit_Blobber):
    def __init__(self, type='centipede', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Centipede(Unit_Blobber):
    def __init__(self, type='alphacentipede', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Digger(Unit_Blobber):
    def __init__(self, type='digger', currenthp=2, maxhp=2, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Digger(Unit_Blobber):
    def __init__(self, type='alphadigger', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Hornet(Unit_Blobber):
    def __init__(self, type='hornet', currenthp=2, maxhp=2, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Acid_Hornet(Unit_Blobber):
    def __init__(self, type='acidhornet', currenthp=3, maxhp=3, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Hornet(Unit_Blobber):
    def __init__(self, type='alphahornet', currenthp=4, maxhp=4, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Soldier_Psion(Unit_Blobber):
    def __init__(self, type='soldierpsion', currenthp=2, maxhp=2, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Shell_Psion(Unit_Blobber):
    def __init__(self, type='shellpsion', currenthp=2, maxhp=2, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blood_Psion(Unit_Blobber):
    def __init__(self, type='bloodpsion', currenthp=2, maxhp=2, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blast_Psion(Unit_Blobber):
    def __init__(self, type='blastpsion', currenthp=2, maxhp=2, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Psion_Tyrant(Unit_Blobber):
    def __init__(self, type='psiontyrant', currenthp=2, maxhp=2, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spider(Unit_Blobber):
    def __init__(self, type='spider', currenthp=2, maxhp=2, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Spider(Unit_Blobber):
    def __init__(self, type='alphaspider', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Burrower(Unit_Blobber):
    def __init__(self, type='burrower', currenthp=3, maxhp=3, effects=set(), attributes=set(Attributes.BURROWER, Attributes.STABLE)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Burrower(Unit_Blobber):
    def __init__(self, type='alphaburrower', currenthp=5, maxhp=5, effects=set(), attributes=set(Attributes.BURROWER, Attributes.STABLE)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Beetle_Leader(Unit_Blobber):
    def __init__(self, type='beetleleader', currenthp=6, maxhp=6, effects=set(), attributes=set(Attributes.MASSIVE)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Large_Goo(Unit_Blobber):
    def __init__(self, type='largegoo', currenthp=3, maxhp=3, effects=set(), attributes=set(Attributes.MASSIVE)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Medium_Goo(Unit_Blobber):
    def __init__(self, type='mediumgoo', currenthp=2, maxhp=2, effects=set(), attributes=set(Attributes.MASSIVE)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Small_Goo(Unit_Blobber):
    def __init__(self, type='smallgoo', currenthp=1, maxhp=1, effects=set(), attributes=set(Attributes.MASSIVE)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Hornet_Leader(Unit_Blobber):
    def __init__(self, type='hornetleader', currenthp=6, maxhp=6, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Psion_Abomination(Unit_Blobber):
    def __init__(self, type='psionabomination', currenthp=5, maxhp=5, effects=set(), attributes=set(Attributes.FLYING)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Scorpion_Leader(Unit_Blobber):
    def __init__(self, type='scorpionleader', currenthp=7, maxhp=7, effects=set(), attributes=set(Attributes.MASSIVE)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Firefly_Leader(Unit_Blobber):
    def __init__(self, type='fireflyleader', currenthp=6, maxhp=6, effects=set(), attributes=set(Attributes.MASSIVE)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Spider_Leader(Unit_Blobber):
    def __init__(self, type='spiderleader', currenthp=6, maxhp=6, effects=set(), attributes=set(Attributes.Massive)):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Alpha_Blob(Unit_Blobber):
    def __init__(self, type='alphablob', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Blob(Unit_Blobber):
    def __init__(self, type='blob', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Spiderling_Egg(Unit_Blobber):
    def __init__(self, type='spiderlingegg', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Spiderling(Unit_Blobber):
    def __init__(self, type='spiderling', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)

class Unit_Alpha_Spiderling(Unit_Blobber):
    def __init__(self, type='alphaspiderling', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
############## PROGRAM FLOW FUNCTIONS ###############

############## MAIN ########################
if __name__ == '__main__':
    u = Unit_Mountain_Damaged()
    print(u.attributes)
