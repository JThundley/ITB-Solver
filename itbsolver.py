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

# strange interactions:
# If a shielded unit is on a forest tile and you attack it, the shield takes the damage and the forest fire does NOT ignite
# If a unit is shielded and on fire, freezing it does nothing, doesn't even put out the fire.

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
    MASSIVE = 1 # prevents drowning in water
    STABLE = 2 # prevents units from being pushed
    FLYING = 3 # prevents drowning in water and allows movement through other units
    ARMORED = 4 # all attacks are reduced by 1
    BURROWER = 5 # unit burrows after taking any damage
    UNPOWERED = 6 # this is for friendly tanks that you can't control until later

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

class Alliance():
    FRIENDLY = 1
    ENEMY = 2
    NEUTRAL = 3

class Events():
    "This is a list of all the events that count towards or against your score."
    # TODO
############### FUNCTIONS #################

############### CLASSES #################
class GameBoard():
    "This represents the game board and some of the most basic rules of the game."
    def __init__(self, powergrid_hp=7):
        self.board = {} # a dictionary of all 64 squares on the board. Each key is a tuple of x,y coordinates and each value is the tile object: {(1, 1): Tile, ...}
            # Each square is called a square. Each square must have a tile assigned to it, an optionally a unit on top of the square. The unit is part of the tile.
        for letter in range(1, 9):
            for num in range(1, 9):
                self.board[(letter, num)] = Tile((letter, num), self)
        self.powergrid_hp = powergrid_hp # max is 7
    def push(self, square, direction):
        "push units on square direction. square is a tuple of (x, y) coordinates, direction is a Direction.UP direction."
        try:
            if Attributes.STABLE in self.board[square].unit.attributes:
                return # stable units can't be pushed
        except AttributeError:
            return # There was no unit to push
        else:
            if direction == Direction.UP:
                destinationsquare = (square[0], square[1] + 1)
            elif direction == Direction.RIGHT:
                destinationsquare = (square[0] + 1, square[1])
            elif direction == Direction.DOWN:
                destinationsquare = (square[0], square[1] - 1)
            elif direction == Direction.LEFT:
                destinationsquare = (square[0] - 1, square[1])
            else:
                raise Exception("Invalid direction given to GameBoard.push()")
            try:
                self.board[destinationsquare]
            except KeyError:
                return # attempted to push unit off the gameboard, no action is taken
            else:
                try:
                    self.board[destinationsquare].unit.takeBumpDamage() # try to have the destination unit take bump damage
                except AttributeError: # raised from None.takeBumpDamage, there is no unit there to bump into
                    self.board[destinationsquare].unit = self.board[square].unit # move the unit from square to destination square
                    self.board[square].unit = None
                else:
                    self.board[square].unit.takeBumpDamage() # The destination took bump damage, now the unit that got pushed also takes damage
    def replaceTile(self, square, newtile, keepeffects=True):
        "replace tile in square with newtile. If keepeffects is True, add them to newtile without calling their apply methods."
        unit = self.board[square].unit
        oldeffects = self.board[square].effects
        self.board[square] = newtile
        if keepeffects:
            newtile.effects.update(oldeffects)
        if unit:
            self.board[square].putUnitHere(unit)
##############################################################################
######################################## TILES ###############################
##############################################################################
class Tile():
    """This object is a normal tile. All other tiles are based on this. Mountains and buildings are considered units since they have HP and block movement on a tile, thus they go on top of the tile."""
    def __init__(self, square, board, type='ground', effects=set(), unit=None):
        self.square = square # This is the (x, y) coordinate of the square.
        self.board = board # this is a link back to the main game board so tiles and units can change it
        self.type = type # the type of tile, the name of it.
        self.effects = effects # Current effect(s) on the tile. Effects are on top of the tile. Some can be removed by having your mech repair while on the tile.
        self.unit = unit # This is the unit on the tile. If it's None, there is no unit on it.
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
    def putUnitHere(self, unit):
        "Run this method whenever a unit lands on this tile whether from the player moving or a unit getting pushed. returns nothing."
        self.unit = unit
        self.unit.square = self.square
        if not Effects.SHIELD in self.unit.effects: # If the unit is not shielded, spread fire to it
            if Effects.FIRE in self.effects:
                self.unit.effects.add(Effects.FIRE)
            if Effects.ACID in self.effects: # same with acid, but also remove it from the tile.
                self.unit.effects.add(Effects.ACID)
                self.removeEffect(Effects.ACID)
        if Effects.MINE in self.effects:
            self.unit.die()
            self.removeEffect(Effects.MINE)
            return
        elif Effects.FREEZEMINE in self.effects:
            self.unit.applyIce()
            self.removeEffect(Effects.FREEZEMINE)

class Tile_Forest(Tile):
    "If damaged, lights on fire."
    def __init__(self, square, board, effects=set()):
        super().__init__(square, board, type='forest', effects=effects)
    def takeDamage(self, damage):
        "tile gains the fire effect"
        self.applyFire()

class Tile_Sand(Tile):
    "If damaged, turns into Smoke. Units in Smoke cannot attack or repair."
    def __init__(self, square, board, effects=set()):
        super().__init__(square, board, type='sand', effects=effects)
    def takeDamage(self, damage):
        self.applySmoke()

class Tile_Water(Tile):
    "Non-huge land units die when pushed into water. Water cannot be set on fire."
    def __init__(self, square, board, effects=set()):
        super().__init__(square, board, type='water', effects=effects)
    def applyFire(self): # water can't be set on fire
        pass
    def applyIce(self):
        self.board.replaceTile(self.square, Tile_Ice(self.square, self.board)) # XXX TODO freezing acid water kind of gets rid of acid, right?
    def repair(self): # acid cannot be removed from water by repairing it.
        self.removeEffect(Effects.SMOKE)
    def putUnitHere(self, unit):
        self.unit = unit
        self.unit.square = self.square
        if (Attributes.MASSIVE not in unit.attributes) and (Attributes.FLYING not in unit.attributes): # kill non-massive non-flying units that went into the water.
            unit.die()
            if Effects.ACID in unit.effects:
                self.applyAcid()
        else:
            self.unit.removeEffect(Effects.FIRE) # water puts out the fire
            self.unit.removeEffect(Effects.ICE)  # water puts out the fire
            super().putUnitHere(unit)

class Tile_Ice(Tile):
    "Turns into Water when destroyed. Must be hit twice. (Turns into Ice_Damaged.)"
    def __init__(self, square, board, effects=set()):
        super().__init__(square, board, type='ice', effects=effects)
    def takeDamage(self, damage):
        raise ReplaceObj(Tile_Ice_Damaged)
    def applyFire(self):
        self.board.replaceTile(self.square, Tile_Water(self.square, self.board))

class Tile_Ice_Damaged(Tile_Ice):
    def __init__(self, square, board, effects=set()):
        super().__init__(square, board, type='ice_damaged', effects=effects)
    def takeDamage(self, damage):
        raise ReplaceObj(Tile_Water)

class Tile_Chasm(Tile):
    "Non-flying units die when pushed into water. Chasm tiles cannot have acid or fire, but can have smoke."
    def __init__(self, square, board, effects=set()):
        super().__init__(square, board, type='chasm', effects=effects)
    def applyFire(self):
        pass
    def applyIce(self):
        pass
    def applyAcid(self):
        pass
    def putUnitHere(self, unit):
        if Attributes.FLYING not in unit.attributes:
            unit.die()
        else:
            super().putUnitHere(unit)

class Tile_Lava(Tile_Water):
    def __init__(self, square, board, effects={'fire'}):
        super().__init__(square, board, type='lava', effects=effects)
    def repair(self):
        self.removeEffect(Effects.SMOKE)
    # TODO: Can lava be frozen?

class Tile_Grassland(Tile):
    "Your bonus objective is to terraform Grassland tiles into Sand. This is mostly just a regular ground tile."
    def __init__(self, square, board, effects=set()):
        super().__init__(square, board, type='grassland', effects=effects)

class Tile_Terraformed(Tile):
    "This tile was terraformed as part of your bonus objective. Also just a regular ground tile."
    def __init__(self, square, board, effects=set()):
        super().__init__(square, board, type='terraformed', effects=effects)

class Tile_Teleporter(Tile):
    "End movement here to warp to the matching pad. Swap with any present unit."
    def __init__(self, square, board, color, effects=set()):
        super().__init__(square, board, type='teleporter', effects=effects)

class Tile_Conveyor(Tile):
    "This tile will push any unit in the direction marked on the belt."
    def __init__(self, square, board, direction, effects=set()):
        super().__init__(square, board, type='conveyor', effects=effects)
        self.direction = direction

##############################################################################
######################################## UNITS ###############################
##############################################################################

class Unit(Tile):
    "The base class of all units. A unit is anything that occupies a square and stops other ground units from moving through it."
    def __init__(self, board, type, currenthp, maxhp, attributes=set(), effects=set()):
        """
        board is the GameBoard instance
        type is the name of the unit (str)
        currenthp is the unit's current hitpoints (int)
        maxhp is the unit's maximum hitpoints (int)
        effects is a set of effects applied to this unit. Use Effects.EFFECTNAME for this.
        attributes is a set of attributes or properties that the unit has. use Attributes.ATTRNAME for this.
        """
        super().__init__(square=None, board=board, type=type, effects=effects)
        self.currenthp = currenthp
        self.maxhp = maxhp
        self.attributes = attributes
        self.damage_taken = 0 # This is a running count of how much damage this unit has taken during this turn.
            # This is done so that points awarded to a solution can be removed on a unit's death. We don't want solutions to be more valuable if an enemy is damaged before it's killed. We don't care how much damage was dealt to it if it dies.
    def applyFire(self):
        if Effects.SHIELD not in self.effects:
            self.effects.add(Effects.FIRE) # no need to try to remove a timepod from a unit (from super())
    def applyWeb(self):
        self.effects.add(Effects.WEB)
    def applyShield(self):
        self.effects.add(Effects.SHIELD)
    def applyIce(self):
        if Effects.SHIELD not in self.effects: # If a unit has a shield and someone tries to freeze it, NOTHING HAPPENS!
            super().applyIce()
            self.effects.add(Effects.ICE)
    def takeDamage(self, damage):
        for effect in (Effects.SHIELD, Effects.ICE): # let the shield and then ice take the damage instead if present. Frozen units can have a shield over the ice, but not the other way around.
            try:
                self.effects.remove(effect)
            except KeyError:
                pass
            else:
                return
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
    def __init__(self, square, board, type='mountain', attributes={Attributes.STABLE}, effects=set()):
        super().__init__(square, board, type=type, currenthp=1, maxhp=1, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def applyFire(self):
        pass # mountains can't be set on fire
    def applyAcid(self):
        pass # same for acid
    def takeDamage(self, damage=1):
        ReplaceObj(Unit_Mountain_Damaged)

class Unit_Mountain_Damaged(Unit_Mountain):
    def __init__(self, square, board, type='mountain_damaged', effects=set()):
        super().__init__(square, board, type=type, currenthp=1, maxhp=1, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage=1):
        ReplaceObj(Tile)

class Unit_Volcano(Unit_Mountain):
    "Indestructible volcano that blocks movement and projectiles."
    def __init__(self, square, board, type='volcano', effects=set()):
        super().__init__(square, board, type=type, currenthp=1, maxhp=1, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage=1):
        pass # what part of indestructible do you not understand?!

class Unit_Building(Unit):
    def __init__(self, square, board, type='building', currenthp=1, maxhp=1, effects=set(), attributes={Attributes.STABLE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.alliance = Alliance.FRIENDLY
    def repairHP(self, hp):
        pass # buildings can't repair, dream on

class Unit_Building_Objective(Unit_Building):
    def __init__(self, square, board, type='building_objective', currenthp=1, maxhp=1, effects=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
        self.alliance = Alliance.FRIENDLY

class Unit_Acid_Vat(Unit_Building_Objective):
    def __init__(self, square, board, type='acidvat', currenthp=2, maxhp=2, effects=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def die(self):
        "Acid vats turn into acid water when destroyed."
        ReplaceObj(None) # TODO: How do we have a unit replace a tile?

class Unit_Blobber(Unit):
    "This can be considered the base unit of Vek since the Blobber doesn't have a direct attack or effect. The units it spawns are separate units that happens after the simulation's turn."
    def __init__(self, square, board, type='blobber', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)
        self.alliance = Alliance.ENEMY
    def repairHP(self, hp=1):
        "Repair hp amount of hp. Does not take you higher than the max. Does not remove any effects."
        self.currenthp += hp
        if self.currenthp > self.maxhp:
            self.currenthp = self.maxhp

class Unit_Alpha_Blobber(Unit_Blobber):
    "Also has no attack."
    def __init__(self, square, board, type='alphablobber', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scorpion(Unit_Blobber):
    def __init__(self, square, board, type='scorpion', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Acid_Scorpion(Unit_Blobber):
    def __init__(self, square, board, type='acidscorpion', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Scorpion(Unit_Blobber):
    def __init__(self, square, board, type='alphascorpion', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Firefly(Unit_Blobber):
    def __init__(self, square, board, type='firefly', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Firefly(Unit_Blobber):
    def __init__(self, square, board, type='alphascorpion', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Leaper(Unit_Blobber):
    def __init__(self, square, board, type='leaper', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Leaper(Unit_Blobber):
    def __init__(self, square, board, type='alphaleaper', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Beetle(Unit_Blobber):
    def __init__(self, square, board, type='beetle', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Beetle(Unit_Blobber):
    def __init__(self, square, board, type='alphabeetle', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scarab(Unit_Blobber):
    def __init__(self, square, board, type='scarab', currenthp=2, maxhp=2, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Scarab(Unit_Blobber):
    def __init__(self, square, board, type='alphascarab', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Crab(Unit_Blobber):
    def __init__(self, square, board, type='crab', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Crab(Unit_Blobber):
    def __init__(self, square, board, type='alphacrab', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Centipede(Unit_Blobber):
    def __init__(self, square, board, type='centipede', currenthp=3, maxhp=3, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Centipede(Unit_Blobber):
    def __init__(self, square, board, type='alphacentipede', currenthp=5, maxhp=5, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Digger(Unit_Blobber):
    def __init__(self, square, board, type='digger', currenthp=2, maxhp=2, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Digger(Unit_Blobber):
    def __init__(self, square, board, type='alphadigger', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Hornet(Unit_Blobber):
    def __init__(self, square, board, type='hornet', currenthp=2, maxhp=2, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Acid_Hornet(Unit_Blobber):
    def __init__(self, square, board, type='acidhornet', currenthp=3, maxhp=3, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Hornet(Unit_Blobber):
    def __init__(self, square, board, type='alphahornet', currenthp=4, maxhp=4, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Soldier_Psion(Unit_Blobber):
    def __init__(self, square, board, type='soldierpsion', currenthp=2, maxhp=2, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Shell_Psion(Unit_Blobber):
    def __init__(self, square, board, type='shellpsion', currenthp=2, maxhp=2, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blood_Psion(Unit_Blobber):
    def __init__(self, square, board, type='bloodpsion', currenthp=2, maxhp=2, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blast_Psion(Unit_Blobber):
    def __init__(self, square, board, type='blastpsion', currenthp=2, maxhp=2, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Psion_Tyrant(Unit_Blobber):
    def __init__(self, square, board, type='psiontyrant', currenthp=2, maxhp=2, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spider(Unit_Blobber):
    def __init__(self, square, board, type='spider', currenthp=2, maxhp=2, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Spider(Unit_Blobber):
    def __init__(self, square, board, type='alphaspider', currenthp=4, maxhp=4, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Burrower(Unit_Blobber):
    def __init__(self, square, board, type='burrower', currenthp=3, maxhp=3, effects=set(), attributes={Attributes.BURROWER, Attributes.STABLE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Burrower(Unit_Blobber):
    def __init__(self, square, board, type='alphaburrower', currenthp=5, maxhp=5, effects=set(), attributes={Attributes.BURROWER, Attributes.STABLE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Beetle_Leader(Unit_Blobber):
    def __init__(self, square, board, type='beetleleader', currenthp=6, maxhp=6, effects=set(), attributes={Attributes.MASSIVE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Large_Goo(Unit_Blobber):
    def __init__(self, square, board, type='largegoo', currenthp=3, maxhp=3, effects=set(), attributes={Attributes.MASSIVE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Medium_Goo(Unit_Blobber):
    def __init__(self, square, board, type='mediumgoo', currenthp=2, maxhp=2, effects=set(), attributes={Attributes.MASSIVE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Small_Goo(Unit_Blobber):
    def __init__(self, square, board, type='smallgoo', currenthp=1, maxhp=1, effects=set(), attributes={Attributes.MASSIVE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Hornet_Leader(Unit_Blobber):
    def __init__(self, square, board, type='hornetleader', currenthp=6, maxhp=6, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Psion_Abomination(Unit_Blobber):
    def __init__(self, square, board, type='psionabomination', currenthp=5, maxhp=5, effects=set(), attributes={Attributes.FLYING}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scorpion_Leader(Unit_Blobber):
    def __init__(self, square, board, type='scorpionleader', currenthp=7, maxhp=7, effects=set(), attributes={Attributes.MASSIVE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Firefly_Leader(Unit_Blobber):
    def __init__(self, square, board, type='fireflyleader', currenthp=6, maxhp=6, effects=set(), attributes={Attributes.MASSIVE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spider_Leader(Unit_Blobber):
    def __init__(self, square, board, type='spiderleader', currenthp=6, maxhp=6, effects=set(), attributes={Attributes.MASSIVE}):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Blob(Unit_Blobber):
    def __init__(self, square, board, type='alphablob', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blob(Unit_Blobber):
    def __init__(self, square, board, type='blob', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spiderling_Egg(Unit_Blobber):
    def __init__(self, square, board, type='spiderlingegg', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spiderling(Unit_Blobber):
    def __init__(self, square, board, type='spiderling', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Spiderling(Unit_Blobber):
    def __init__(self, square, board, type='alphaspiderling', currenthp=1, maxhp=1, effects=set(), attributes=set()):
        super().__init__(square, board, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)
############## PROGRAM FLOW FUNCTIONS ###############

############## MAIN ########################
if __name__ == '__main__':
    u = Unit_Mountain_Damaged()
    print(u.attributes)
