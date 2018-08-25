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

# TODO
# change PushTile to push multiple tiles and check if the tile that is being pushed is to another tile being pushed then push that other one first.
# change takeDamage on units to take into effect ARMORED and ACID.
# Old Earth Dam has 2 hp, is 2 tiles, is smoke immune, massive, submerged (weapons do not work when submerged in water), and Stable. If you freeze the dam, both dam tiles catch on fire.
# implement fire immunity attribute
############ IMPORTS ######################

############### GLOBALS ###################
DEBUG=True

# def ConstantCounter(): # use this later when we're not debugging.
#     "yields ints starting at 1"
#     num = 0
#     while True:
#         num += 1
#         yield num
#
# CC = ConstantCounter()

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
    SUBMERGED = 9 # I'm twisting the rules here. In the game, submerged is an effect on the unit. Rather than apply and remove it as units move in and out of water, we'll just apply this water tiles and check for it there.
    # These effects can only be applied to units:
    SHIELD = 10
    WEB = 11
    EXPLOSIVE = 12

class Attributes():
    "These are attributes that are applied to units."
    MASSIVE = 1 # prevents drowning in water
    STABLE = 2 # prevents units from being pushed
    FLYING = 3 # prevents drowning in water and allows movement through other units
    ARMORED = 4 # all attacks are reduced by 1
    BURROWER = 5 # unit burrows after taking any damage
    UNPOWERED = 6 # this is for friendly tanks that you can't control until later
    IMMUNEFIRE = 7 # you are immune from fire if you have this attribute, you can't catch fire.

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
    def __init__(self, board=None, powergrid_hp=7):
        if board:
            self.board = board
        else: # create a blank board of normal ground tiles
            self.board = {} # a dictionary of all 64 squares on the board. Each key is a tuple of x,y coordinates and each value is the tile object: {(1, 1): Tile, ...}
                # Each square is called a square. Each square must have a tile assigned to it, an optionally a unit on top of the square. The unit is part of the tile.
            for letter in range(1, 9):
                for num in range(1, 9):
                    self.board[(letter, num)] = Tile_Ground(self, square=(letter, num))
        self.powergrid_hp = powergrid_hp # max is 7
    def push(self, square, direction):
        """push unit on square direction.
        square is a tuple of (x, y) coordinates
        direction is a Direction.UP direction
        This method should only be used when there is NO possibility of a unit being pushed to a square that also needs to be pushed during the same turn.
        returns nothing"""
        try:
            if Attributes.STABLE in self.board[square].unit.attributes:
                return # stable units can't be pushed
        except AttributeError:
            return # There was no unit to push
        else: # push the unit
            destinationsquare = self.getRelTile(square, direction, 1)
            try:
                self.board[destinationsquare].unit.takeBumpDamage() # try to have the destination unit take bump damage
            except AttributeError: # raised from None.takeBumpDamage, there is no unit there to bump into
                self.moveUnit(square, destinationsquare) # move the unit from square to destination square
            except KeyError:
                return  # raised by self.board[None], attempted to push unit off the gameboard, no action is taken
            else:
                self.board[square].unit.takeBumpDamage() # The destination took bump damage, now the unit that got pushed also takes damage
    def replaceTile(self, square, newtile, keepeffects=True):
        "replace tile in square with newtile. If keepeffects is True, add them to newtile without calling their apply methods."
        unit = self.board[square].unit
        if keepeffects:
            newtile.effects.update(self.board[square].effects)
        self.board[square] = newtile
        self.board[square].square = square
        try:
            self.board[square].putUnitHere(unit)
        except AttributeError: # raised by None.putUnitHere()
            return
    def moveUnit(self, srcsquare, destsquare):
        "Move a unit from srcsquare to destsquare, keeping the effects. returns nothing."
        self.board[destsquare].putUnitHere(self.board[srcsquare].unit)
        self.board[srcsquare].putUnitHere(None)
    def getRelTile(self, square, direction, distance):
        """return the coordinates of the tile that starts at square and goes direction direction a certain distance. return False if that tile would be off the board.
        square is a tuple of coordinates (1, 1)
        direction is a Direction.UP type global constant
        distance is an int
        """
        if direction == Direction.UP:
            destinationsquare = (square[0], square[1] + distance)
        elif direction == Direction.RIGHT:
            destinationsquare = (square[0] + distance, square[1])
        elif direction == Direction.DOWN:
            destinationsquare = (square[0], square[1] - distance)
        elif direction == Direction.LEFT:
            destinationsquare = (square[0] - distance, square[1])
        else:
            raise Exception("Invalid direction given.")
        try:
            self.board[destinationsquare]
        except KeyError:
            return False
        return destinationsquare
##############################################################################
######################################## TILES ###############################
##############################################################################
class TileUnit_Base():
    "This is the base object that forms both Tiles and Units."
    def __init__(self, gboard, square=None, type=None, effects=None):
        self.gboard = gboard  # this is a link back to the game board instance so tiles and units can change it
        self.square = square # This is the (x, y) coordinate of the Tile or Unit. This is required for Tiles, but not for Units which have their square set when they are placed on a square.
        self.type = type # the name of the unit or tile
        if not effects:
            self.effects = set()
        else:
            self.effects = effects # Current effect(s) on the tile. Effects are on top of the tile. Some can be removed by having your mech repair while on the tile.
    def removeEffect(self, effect):
        "This is just a little helper method to remove effects and ignore errors if the effect wasn't present."
        try:
            self.effects.remove(effect)
        except KeyError:
            pass

class Tile_Base(TileUnit_Base):
    """The base class for all Tiles, all other tiles are based on this. Mountains and buildings are considered units since they have HP and block movement on a tile, thus they go on top of the tile."""
    def __init__(self, gboard, square=None, type=None, effects=None, unit=None):
        super().__init__(gboard, square, type, effects=effects)
        self.unit = unit # This is the unit on the tile. If it's None, there is no unit on it.
    def takeDamage(self, damage):
        """Process the tile taking damage and the unit (if any) on this tile taking damage. Damage should always be done to the tile, the tile will then pass it onto the unit.
        There are a few exceptions when takeDamage() will be called on the unit but not the tile, such as the Psion Tyrant damaging all player mechs which never has an effect on the tile.
        Damage is an int of how much damage to take.
        returns nothing.
        """
        try:
            isshielded = Effects.SHIELD in self.unit.effects
        except AttributeError: # raised from Effects.SHIELD in None
            isshielded = False
        if not isshielded:
            self._tileTakeDamage() # Tile takes damage first.
        if self.gboard.board[self.square].unit: # use the square of the board in case this tile taking damage caused it to get replaced. If we don't do this, then a tile could turn from ice to water and kill the unit but we'd keep operating on
            self.gboard.board[self.square].unit.takeDamage(damage) #  the non-garbage-collected unit that's no longer attached to the gameboard which is a waste.
    def _tileTakeDamage(self):
        "Process the effects of the tile taking damage. returns nothing."
    def applyFire(self):
        "set the current tile on fire"
        self.effects.add(Effects.FIRE)
        self.removeEffect(Effects.SMOKE) # Fire removes smoke
        try:
            self.unit.applyFire()
        except AttributeError:
            return
    def applySmoke(self):
        "make a smoke cloud on the current tile"
        self.removeEffect(Effects.FIRE) # smoke removes fire
        self.effects.add(Effects.SMOKE)
    def applyIce(self):
        "apply ice to the tile and unit."
        if self.unit: # if there's a unit...
            if Effects.SHIELD not in self.unit.effects: # that's not shielded...
                self.removeEffect(Effects.FIRE) # remove fire from the tile
                self.unit.applyIce() # give the unit ice
            # nothing happens to the tile or unit if a unit with a shield is present.
        else: # no unit
            self.removeEffect(Effects.FIRE) # just remove fire from the tile
    def applyAcid(self):
        try:
            self.unit.applyAcid()
        except AttributeError: # the tile doesn't get acid if a unit is present to take it instead
            self.effects.add(Effects.ACID)
            self.removeEffect(Effects.FIRE)
            self.removeEffect(Effects.TIMEPOD)
            self.removeEffect(Effects.MINE)
            self.removeEffect(Effects.FREEZEMINE)
    def applyShield(self):
        try: # Tiles can't be shielded, only units
            self.unit.applyShield()
        except AttributeError:
            return
    def repair(self):
        "process the action of a friendly mech repairing on this tile and removing certain effects."
        self.removeEffect(Effects.FIRE)
    def putUnitHere(self, unit):
        "Run this method whenever a unit lands on this tile whether from the player moving or a unit getting pushed. unit can be None to get rid of a unit. If there's a unit already on the tile, it's overwritten and deleted. returns nothing."
        self.unit = unit
        try:
            self.unit.square = self.square
        except AttributeError: # raised by None.square = blah
            return # bail, the unit has been replaced by nothing which is ok.
        self._spreadEffects()
    def _spreadEffects(self):
        "Spread effects from the tile to a unit that newly landed here. This also executes other things the tile can do to the unit when it lands there, such as dying if it falls into a chasm."
        if not Effects.SHIELD in self.unit.effects: # If the unit is not shielded...
            if Effects.FIRE in self.effects: # and the tile is on fire...
                self.unit.applyFire() # spread fire to it.
            if Effects.ACID in self.effects: # same with acid, but also remove it from the tile.
                self.unit.applyAcid()
                self.removeEffect(Effects.ACID)

class Tile_Ground(Tile_Base):
    "This is a normal ground tile."
    def __init__(self, gboard, square=None, type='ground', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def applyFire(self):
        self._tileTakeDamage() # fire removes timepods and mines just like damage does
        super().applyFire()
    def _spreadEffects(self):
        "Ground tiles can have mines on them, but many other tile types can't."
        super()._spreadEffects()
        if Effects.MINE in self.effects:
            self.unit.die()
            self.removeEffect(Effects.MINE)
        elif Effects.FREEZEMINE in self.effects:
            self.unit.applyIce()
            self.removeEffect(Effects.FREEZEMINE)
    def _tileTakeDamage(self):
        for effect in Effects.TIMEPOD, Effects.FREEZEMINE, Effects.MINE:
            self.removeEffect(effect)

class Tile_Forest_Sand_Base(Tile_Base):
    "This is the base class for both Forest and Sand Tiles since they both share the same applyAcid mechanics."
    def __init__(self, gboard, square=None, type=None, effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def applyAcid(self):
        try:
            self.unit.applyAcid() # give the unit acid if present
        except AttributeError:
            self.gboard.replaceTile(self.square, Tile_Ground(self.gboard, effects={Effects.ACID}), keepeffects=True) # Acid removes the forest/sand and makes it no longer flammable/smokable
        # The tile doesn't get acid effects if the unit takes it instead.

class Tile_Forest(Tile_Forest_Sand_Base):
    "If damaged, lights on fire."
    def __init__(self, gboard, square=None, type='forest', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def _tileTakeDamage(self):
        "tile gains the fire effect"
        self.applyFire()
    def _spreadEffects(self):
        "Spread effects from the tile to a unit that newly landed here. Units that are on fire spread fire to a forest."
        if Effects.FIRE in self.unit.effects: # if the unit is on fire...
            self.applyFire() # the forest catches fire, removing smoke if there is any
        elif not Effects.SHIELD in self.unit.effects: # If the unit is not on fire and not shielded...
            if Effects.FIRE in self.effects: # and the tile is on fire...
                self.unit.applyFire() # spread fire to the unit.

class Tile_Sand(Tile_Forest_Sand_Base):
    "If damaged, turns into Smoke. Units in Smoke cannot attack or repair."
    def __init__(self, gboard, square=None, type='sand', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def _tileTakeDamage(self):
        self.applySmoke()

class Tile_Water(Tile_Base):
    "Non-huge land units die when pushed into water. Water cannot be set on fire."
    def __init__(self, gboard, square=None, type='water', effects=None):
        super().__init__(gboard, square, type, effects=effects)
        self.effects.add(Effects.SUBMERGED)
    def applyFire(self):
        "Water can't be set on fire"
        try: # spread the fire to the unit
            self.unit.applyFire()
        except AttributeError:
            return # but not the tile. Fire does NOT remove smoke from a water tile!
    def applyIce(self):
        self.removeEffect(Effects.ACID) # freezing acid water gets rid of acid
        self.gboard.replaceTile(self.square, Tile_Ice(self.gboard))
        try:
            self.unit.applyIce()
        except AttributeError:
            return
    def repair(self): # acid cannot be removed from water by repairing it.
        pass # fire can't be removed from water
    def _spreadEffects(self):
        if (Attributes.MASSIVE not in self.unit.attributes) and (Attributes.FLYING not in self.unit.attributes): # kill non-massive non-flying units that went into the water.
            self.unit.die()
        else: # the unit lived
            if Attributes.FLYING not in self.unit.attributes:
                self.unit.removeEffect(Effects.FIRE) # water puts out the fire, but if you're flying you remain on fire
                if Effects.ACID in self.effects: # spread acid but don't remove it from the tile
                    self.unit.applyAcid()
            self.unit.removeEffect(Effects.ICE) # water breaks you out of the ice no matter what

class Tile_Ice(Tile_Base):
    "Turns into Water when destroyed. Must be hit twice. (Turns into Ice_Damaged.)"
    def __init__(self, gboard, square=None, type='ice', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def _tileTakeDamage(self):
        self.gboard.replaceTile(self.square, Tile_Ice_Damaged(self.gboard))
    def applyFire(self):
        self.removeEffect(Effects.SMOKE)
        self.gboard.replaceTile(self.square, Tile_Water(self.gboard))
        try:
            self.unit.applyFire()
        except AttributeError:
            return

class Tile_Ice_Damaged(Tile_Ice):
    def __init__(self, gboard, square=None, type='ice_damaged', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def _tileTakeDamage(self):
        self.gboard.replaceTile(self.square, Tile_Water(self.gboard))

class Tile_Chasm(Tile_Base):
    "Non-flying units die when pushed into a chasm. Chasm tiles cannot have acid or fire, but can have smoke."
    def __init__(self, gboard, square=None, type='chasm', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def applyFire(self):
        try:
            self.unit.applyFire()
        except AttributeError:
            return # fire does not remove smoke on a chasm. Seems like it only does this on solid surfaces which include ice but not water.
    def applyIce(self):
        try:
            self.unit.applyIce()
        except AttributeError:
            return
    def applyAcid(self):
        try:
            self.unit.applyAcid
        except AttributeError:
            return
    def _spreadEffects(self):
        if (Attributes.FLYING in self.unit.attributes) and (Effects.ICE not in self.unit.effects): # if the unit can fly and is not frozen...
            pass # congratulations, you live!
        else:
            self.unit.die()
        # no need to super()._spreadEffects() here since the only effects a chasm tile can have is smoke and that never spreads to the unit itself.

class Tile_Lava(Tile_Water):
    def __init__(self, gboard, square=None, type='lava', effects=None):
        super().__init__(gboard, square, type, effects=effects)
        self.effects.add(Effects.FIRE)
    def repair(self):
        return # No effects can be removed from lava from repairing on it.
    def applyIce(self):
        return # Ice does nothing
    def applyFire(self):
        try: # spread the fire to the unit
            self.unit.applyFire()
        except AttributeError:
            return  # but not the tile, it's always on fire
    def applyAcid(self):
        try: # spread the fire to the unit
            self.unit.applyAcid()
        except AttributeError:
            return # but not the tile
    def _spreadEffects(self):
        if (Attributes.MASSIVE not in self.unit.attributes) and (Attributes.FLYING not in self.unit.attributes): # kill non-massive non-flying units that went into the water.
            self.unit.die()
        else: # the unit lived
            if Attributes.FLYING not in self.unit.attributes:
                self.unit.applyFire() # lava is always on fire, now you are too!
            self.unit.removeEffect(Effects.ICE) # water and lava breaks you out of the ice no matter what

class Tile_Grassland(Tile_Base):
    "Your bonus objective is to terraform Grassland tiles into Sand. This is mostly just a regular ground tile."
    def __init__(self, gboard, square=None, type='grassland', effects=None):
        super().__init__(gboard, square, type, effects=effects)

class Tile_Terraformed(Tile_Base):
    "This tile was terraformed as part of your bonus objective. Also just a regular ground tile."
    def __init__(self, gboard, square=None, type='terraformed', effects=None):
        super().__init__(gboard, square, type, effects=effects)

class Tile_Teleporter(Tile_Base):
    "End movement here to warp to the matching pad. Swap with any present unit."
    def __init__(self, gboard, square=None, type='teleporter', effects=None):
        super().__init__(gboard, square, type, effects=effects)
        # TODO: implement this

class Tile_Conveyor(Tile_Base):
    "This tile will push any unit in the direction marked on the belt."

##############################################################################
######################################## UNITS ###############################
##############################################################################

class Unit_Base(TileUnit_Base):
    "The base class of all units. A unit is anything that occupies a square and stops other ground units from moving through it."
    def __init__(self, gboard, type, currenthp, maxhp, effects=None, attributes=None):
        """
        gboard is the GameBoard instance
        type is the name of the unit (str)
        currenthp is the unit's current hitpoints (int)
        maxhp is the unit's maximum hitpoints (int)
        effects is a set of effects applied to this unit. Use Effects.EFFECTNAME for this.
        attributes is a set of attributes or properties that the unit has. use Attributes.ATTRNAME for this.
        """
        super().__init__(gboard=gboard, type=type, effects=effects)
        self.currenthp = currenthp
        self.maxhp = maxhp
        if not attributes:
            self.attributes = set()
        else:
            self.attributes = attributes
        self.damage_taken = 0 # This is a running count of how much damage this unit has taken during this turn.
            # This is done so that points awarded to a solution can be removed on a unit's death. We don't want solutions to be more valuable if an enemy is damaged before it's killed. We don't care how much damage was dealt to it if it dies.
    def applyEffectUnshielded(self, effect):
        "A helper method to check for the presence of a shield before applying an effect."
        if Effects.SHIELD not in self.effects:
            self.effects.add(effect)
    def applyFire(self):
        self.removeEffect(Effects.ICE)
        if not Attributes.IMMUNEFIRE in self.attributes:
            self.applyEffectUnshielded(Effects.FIRE) # no need to try to remove a timepod from a unit (from super())
    def applyIce(self):
        self.applyEffectUnshielded(Effects.ICE) # If a unit has a shield and someone tries to freeze it, NOTHING HAPPENS!
        self.removeEffect(Effects.FIRE)
        self.gboard.board[self.square]._spreadEffects() # spread effects after freezing because flying units frozen over chasms need to die
    def applyAcid(self):
        self.applyEffectUnshielded(Effects.ACID)
    def applyWeb(self):
        self.effects.add(Effects.WEB)
    def applyShield(self):
        self.effects.add(Effects.SHIELD)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "Process this unit taking damage. All effects are considered unless set to True in the arguments."
        for effect in (Effects.SHIELD, Effects.ICE): # let the shield and then ice take the damage instead if present. Frozen units can have a shield over the ice, but not the other way around.
            try:
                self.effects.remove(effect)
            except KeyError:
                pass
            else:
                self.gboard.board[self.square].putUnitHere(self) # put the unit here again to process effects spreading
                return # and then stop processing things, the shield or ice took the damage.
        if Attributes.ARMORED in self.attributes and Effects.ACID in self.effects: # if you have both armor and acid...
            pass # acid cancels out armored
        elif not ignorearmor and Attributes.ARMORED in self.attributes: # if we aren't ignoring armor and you're armored...
            damage -= 1 # damage reduced by 1
        elif not ignoreacid and Effects.ACID in self.effects: # if we're not ignoring acid and the unit has acid
            damage *= 2
        self.currenthp -= damage # the unit takes the damage
        self.damage_taken += damage
        if self.currenthp <= 0: # if the unit has no more HP
            self.damage_taken += self.currenthp # currenthp is now negative or 0. Adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead.
            self.die()
    def takeBumpDamage(self):
        "take damage from bumping. This is when you're pushed into something or a vek tries to emerge beneath you."
        self.takeDamage(1, ignorearmor=True, ignoreacid=True) # this is overridden by enemies that take increased bump damage by that one global powerup that increases bump damage to enemies only
    def die(self):
        "Make the unit die."
        self.gboard.board[self.square].putUnitHere(None) # it's dead, replace it with nothing
        if Effects.ACID in self.effects: # units that have acid leave acid on the tile when they die:
            self.gboard.board[self.square].applyAcid()
    def repairHP(self, hp=1):
        "Repair hp amount of hp. Does not take you higher than the max. Does not remove any effects."
        self.currenthp += hp
        if self.currenthp > self.maxhp:
            self.currenthp = self.maxhp

class Unit_Mountain_Building_Base(Unit_Base):
    "The base class for mountains and buildings. They have special properties when it comes to fire and acid."
    def __init__(self, gboard, type, currenthp=1, maxhp=1, attributes=None, effects=None):
        try:
            attributes.add(Attributes.STABLE)
        except AttributeError:
            attributes = {Attributes.STABLE}
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
    def applyFire(self):
        raise AttributeError # mountains can't be set on fire, but the tile they're on can!. Raise attribute error so the tile that tried to give fire to the present unit gets it instead.

class Unit_Mountain(Unit_Mountain_Building_Base):
    def __init__(self, gboard, type='mountain', attributes=None, effects=None):
        try:
            attributes.add(Attributes.STABLE)
        except AttributeError:
            attributes = {Attributes.STABLE}
        super().__init__(gboard, type=type, currenthp=1, maxhp=1, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def applyAcid(self):
        pass
    def takeDamage(self, damage=1):
        self.gboard.board[self.square].putUnitHere(Unit_Mountain_Damaged(self.gboard))

class Unit_Mountain_Damaged(Unit_Mountain):
    def __init__(self, gboard, type='mountain_damaged', effects=None):
        super().__init__(gboard, type=type, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage=1):
        self.gboard.board[self.square].putUnitHere(None)

class Unit_Volcano(Unit_Mountain):
    "Indestructible volcano that blocks movement and projectiles."
    def __init__(self, gboard, type='volcano', effects=None):
        super().__init__(gboard, type=type, currenthp=1, maxhp=1, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage=1):
        return # what part of indestructible do you not understand?!

class Unit_Building(Unit_Mountain_Building_Base):
    def __init__(self, gboard, type='building', currenthp=1, maxhp=1, effects=None, attributes=None):
        try:
            attributes.add(Attributes.STABLE)
        except AttributeError:
            attributes = {Attributes.STABLE}
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.alliance = Alliance.FRIENDLY
    def applyAcid(self):
        raise AttributeError # buildings can't gain acid, but the tile they're on can!. Raise attribute error so the tile that tried to give acid to the present unit gets it instead.
    def repairHP(self, hp):
        return # buildings can't repair, dream on

class Unit_Building_Objective(Unit_Building):
    def __init__(self, gboard, type='building_objective', currenthp=1, maxhp=1, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
        self.alliance = Alliance.FRIENDLY

class Unit_Acid_Vat(Unit_Base):
    def __init__(self, gboard, type='acidvat', currenthp=2, maxhp=2, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def die(self):
        "Acid vats turn into acid water when destroyed."
        self.gboard.board[self.square].putUnitHere(None) # remove the unit before replacing the tile otherwise we get caught in an infinite loop of the vat starting to die, changing the ground to water, then dying again because it drowns in water.
        self.gboard.replaceTile(self.square, Tile_Water(self.gboard, effects={Effects.ACID}), keepeffects=True) # replace the tile with a water tile that has an acid effect and keep the old effects
        self.gboard.board[self.square].removeEffect(Effects.FIRE) # don't keep fire, this tile can't be on fire.

class Unit_Rock(Unit_Base):
    def __init__(self, gboard, type='rock', currenthp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=1, maxhp=1, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL

############################################################################################################################
###################################################### ENEMY UNITS #########################################################
############################################################################################################################
class Unit_Blobber(Unit_Base):
    "This can be considered the base unit of Vek since the Blobber doesn't have a direct attack or effect. The units it spawns are separate units that happens after the simulation's turn."
    def __init__(self, gboard, type='blobber', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)
        self.alliance = Alliance.ENEMY

class Unit_Alpha_Blobber(Unit_Blobber):
    "Also has no attack."
    def __init__(self, gboard, type='alphablobber', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scorpion(Unit_Blobber):
    def __init__(self, gboard, type='scorpion', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Acid_Scorpion(Unit_Blobber):
    def __init__(self, gboard, type='acidscorpion', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Scorpion(Unit_Blobber):
    def __init__(self, gboard, type='alphascorpion', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Firefly(Unit_Blobber):
    def __init__(self, gboard, type='firefly', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Firefly(Unit_Blobber):
    def __init__(self, gboard, type='alphascorpion', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Leaper(Unit_Blobber):
    def __init__(self, gboard, type='leaper', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Leaper(Unit_Blobber):
    def __init__(self, gboard, type='alphaleaper', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Beetle(Unit_Blobber):
    def __init__(self, gboard, type='beetle', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Beetle(Unit_Blobber):
    def __init__(self, gboard, type='alphabeetle', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scarab(Unit_Blobber):
    def __init__(self, gboard, type='scarab', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Scarab(Unit_Blobber):
    def __init__(self, gboard, type='alphascarab', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Crab(Unit_Blobber):
    def __init__(self, gboard, type='crab', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Crab(Unit_Blobber):
    def __init__(self, gboard, type='alphacrab', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Centipede(Unit_Blobber):
    def __init__(self, gboard, type='centipede', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Centipede(Unit_Blobber):
    def __init__(self, gboard, type='alphacentipede', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Digger(Unit_Blobber):
    def __init__(self, gboard, type='digger', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Digger(Unit_Blobber):
    def __init__(self, gboard, type='alphadigger', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Hornet(Unit_Blobber): # this is the base class for flying units
    def __init__(self, gboard, type='hornet', currenthp=2, maxhp=2, effects=None, attributes=None):
        try:
            attributes.add(Attributes.FLYING)
        except AttributeError:
            attributes = {Attributes.FLYING}
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Acid_Hornet(Unit_Hornet):
    def __init__(self, gboard, type='acidhornet', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Hornet(Unit_Hornet):
    def __init__(self, gboard, type='alphahornet', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Soldier_Psion(Unit_Hornet):
    def __init__(self, gboard, type='soldierpsion', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Shell_Psion(Unit_Hornet):
    def __init__(self, gboard, type='shellpsion', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blood_Psion(Unit_Hornet):
    def __init__(self, gboard, type='bloodpsion', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blast_Psion(Unit_Hornet):
    def __init__(self, gboard, type='blastpsion', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Psion_Tyrant(Unit_Hornet):
    def __init__(self, gboard, type='psiontyrant', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spider(Unit_Blobber):
    def __init__(self, gboard, type='spider', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Spider(Unit_Blobber):
    def __init__(self, gboard, type='alphaspider', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Burrower(Unit_Blobber): # Base unit for burrowers
    def __init__(self, gboard, type='burrower', currenthp=3, maxhp=3, effects=None, attributes=None):
        try:
            attributes.update((Attributes.BURROWER, Attributes.STABLE))
        except AttributeError:
            attributes = {Attributes.BURROWER, Attributes.STABLE}
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Burrower(Unit_Burrower):
    def __init__(self, gboard, type='alphaburrower', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Beetle_Leader(Unit_Blobber): # Base unit for massive bosses
    def __init__(self, gboard, type='beetleleader', currenthp=6, maxhp=6, effects=None, attributes=None):
        try:
            attributes.add(Attributes.MASSIVE)
        except AttributeError:
            attributes = {Attributes.MASSIVE}
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Large_Goo(Unit_Beetle_Leader):
    def __init__(self, gboard, type='largegoo', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Medium_Goo(Unit_Beetle_Leader):
    def __init__(self, gboard, type='mediumgoo', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Small_Goo(Unit_Beetle_Leader):
    def __init__(self, gboard, type='smallgoo', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Hornet_Leader(Unit_Beetle_Leader): # base class for flying and massive units
    def __init__(self, gboard, type='hornetleader', currenthp=6, maxhp=6, effects=None, attributes=None):
        try:
            attributes.add(Attributes.FLYING)
        except AttributeError:
            attributes = {Attributes.FLYING}
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Psion_Abomination(Unit_Hornet_Leader):
    def __init__(self, gboard, type='psionabomination', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scorpion_Leader(Unit_Hornet_Leader):
    def __init__(self, gboard, type='scorpionleader', currenthp=7, maxhp=7, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Firefly_Leader(Unit_Hornet_Leader):
    def __init__(self, gboard, type='fireflyleader', currenthp=6, maxhp=6, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spider_Leader(Unit_Hornet_Leader):
    def __init__(self, gboard, type='spiderleader', currenthp=6, maxhp=6, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Blob(Unit_Blobber):
    def __init__(self, gboard, type='alphablob', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blob(Unit_Blobber):
    def __init__(self, gboard, type='blob', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spiderling_Egg(Unit_Blobber):
    def __init__(self, gboard, type='spiderlingegg', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spiderling(Unit_Blobber):
    def __init__(self, gboard, type='spiderling', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Spiderling(Unit_Blobber):
    def __init__(self, gboard, type='alphaspiderling', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)
############## PROGRAM FLOW FUNCTIONS ###############

############## MAIN ########################
if __name__ == '__main__':
    pass