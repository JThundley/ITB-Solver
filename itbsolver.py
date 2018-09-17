#!/usr/bin/env python3
# This script brute forces the best possible single turn in Into The Breach
############# NOTES ######################
# Order of turn operations:
#   Fire
#   Storm Smoke
#   Psion Tentacle
#   Environment
#   Enemy Actions
#   NPC actions
#   Enemies emerge

############ IMPORTS ######################

############### GLOBALS ###################
DEBUG=True

# this generator and class are out of place and separate from the others, sue me
def numGen():
    "A simple generator to count up from 0."
    num = 0
    while True:
        num += 1
        yield num
thegen = numGen()

class Constant():
    "An object for building global constants."
    def __init__(self, numgen, names):
        "names is a tuple of strings, these are the constants to set. numgen is the number generator to continue from"
        self.value2name = {}
        for n in names:
            num = next(numgen)
            setattr(self, n, num)
            self.value2name[num] = n
    def pprint(self, iter):
        "return a list of iter converted to readable names."
        return [self.value2name[x] for x in iter]

class DirectionConst(Constant):
    def opposite(self, dir):
        "return the opposite of the direction provided as dir."
        dir += 2
        if dir > 4:
            dir -= 4
        return dir
    def gen(self):
        "A generator that yields each direction."
        for d in Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT:
            yield d

# These are up/down/left/right directions with a method to get the opposite direction. THIS SET OF CONSTANTS MUST BE FIRST SO IT GETS THE FIRST 4 NUMBERS!
Direction = DirectionConst(thegen, (
    'UP',
    'RIGHT',
    'DOWN',
    'LEFT'))
assert Direction.UP == 1
assert Direction.RIGHT == 2
assert Direction.DOWN == 3
assert Direction.LEFT == 4

# These are effects that can be applied to tiles and units.
Effects = Constant(thegen,
    # These effects can be applied to both tiles and units:
    ('FIRE',
    'ICE', # if applied to a unit, the unit is frozen
    'ACID',
    # These effects can only be applied to tiles:
    'SMOKE',
    'TIMEPOD',
    'MINE',
    'FREEZEMINE',
    'SUBMERGED', # I'm twisting the rules here. In the game, submerged is an effect on the unit. Rather than apply and remove it as units move in and out of water, we'll just apply this to water tiles and check for it there.
    # These effects can only be applied to units:
    'SHIELD',
    'WEB',
    'EXPLOSIVE'))

# These are attributes that are applied to units.
Attributes = Constant(thegen, (
    'MASSIVE', # prevents drowning in water
    'STABLE', # prevents units from being pushed
    'FLYING', # prevents drowning in water and allows movement through other units
    'ARMORED', # all attacks are reduced by 1
    'BURROWER', # unit burrows after taking any damage
    'UNPOWERED', # this is for friendly tanks that you can't control until later
    'IMMUNEFIRE', # you are immune from fire if you have this attribute, you can't catch fire.
    'IMMUNESMOKE')) # you are immune from smoke, you can fire weapons when clouded by smoke

Alliance = Constant(thegen, (
    'FRIENDLY', # your mechs can move through these
    'ENEMY', # but not these
    'NEUTRAL')) # not these either

# don't need these anymore
del Constant
del numGen
del thegen
del DirectionConst

############### FUNCTIONS #################

############### CLASSES #################
class MissingCompanionTile(Exception):
    "This is raised when something fails due to a missing companion tile."
    def __init__(self, type, square):
        super().__init__()
        self.message = "No companion tile specified for %s on %s" % (type, square)
    def __str__(self):
        return self.message

class GameBoard():
    "This represents the game board and some of the most basic rules of the game."
    def __init__(self, board=None, powergrid_hp=7, environmentaleffect=None, vekemerge=None):
        """board is a dict of tiles to use. If it's left blank, a default board full of empty ground tiles is generated.
        powergrid_hp is the amount of power (hp) you as a player have. When this reaches 0, the entire game ends.
        environmentaleffect is an environmental effect object that should be run during a turn.
        vekemerge is the special VekEmerge environmental effect. If left blank, an empty one is created."""
        if board:
            self.board = board
        else: # create a blank board of normal ground tiles
            self.board = {} # a dictionary of all 64 squares on the board. Each key is a tuple of x,y coordinates and each value is the tile object: {(1, 1): Tile, ...}
                # Each square is called a square. Each square must have a tile assigned to it, an optionally a unit on top of the square. The unit is part of the tile.
            for letter in range(1, 9):
                for num in range(1, 9):
                    self.board[(letter, num)] = Tile_Ground(self, square=(letter, num))
        self.powergrid_hp = powergrid_hp # max is 7
        self.environmentaleffect = environmentaleffect
        try:
            self.environmentaleffect.gboard = self
        except AttributeError:
            pass # no environmental effect being used
        if vekemerge:
            self.vekemerge = vekemerge
        else:
            self.vekemerge = Environ_VekEmerge()
        self.vekemerge.gboard = self
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
    def takeDamage(self, damage=1, ignorearmor=False, ignoreacid=False, preventdeath=False):
        """Process the tile taking damage and the unit (if any) on this tile taking damage. Damage should always be done to the tile, the tile will then pass it onto the unit.
        There are a few exceptions when takeDamage() will be called on the unit but not the tile, such as the Psion Tyrant damaging all player mechs which never has an effect on the tile.
        Damage is an int of how much damage to take.
        ignorearmor, ignoreacid, and preventdeath have no effect on the tile and are passed onto the unit's takeDamage method.
        returns nothing.
        """
        try:
            isshielded = Effects.SHIELD in self.unit.effects
        except AttributeError: # raised from Effects.SHIELD in None
            isshielded = False
        if not isshielded:
            self._tileTakeDamage() # Tile takes damage first.
        if self.gboard.board[self.square].unit: # use the square of the board in case this tile taking damage caused it to get replaced. If we don't do this, then a tile could turn from ice to water and kill the unit but we'd keep operating on
            self.gboard.board[self.square].unit.takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid, preventdeath=preventdeath) #  the non-garbage-collected unit that's no longer attached to the gameboard which is a waste.
    def applyFire(self):
        "set the current tile on fire"
        self.effects.add(Effects.FIRE)
        for e in Effects.SMOKE, Effects.ACID:
            self.removeEffect(e) # Fire removes smoke and acid
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
    def applyShield(self):
        try: # Tiles can't be shielded, only units
            self.unit.applyShield()
        except AttributeError:
            return
    def repair(self, hp):
        "Repair this tile and any mech on it. hp is the amount of hp to repair on the present unit. This method should only be used for mechs and not vek as they can be healed but they never repair the tile."
        self.removeEffect(Effects.FIRE)
        if self.unit:
            self.unit.repair(hp)
        # switch to a more efficient try statement when we're sure there aren't bugs :)
        # try:
        #     self.unit.repair(hp)
        # except AttributeError:
        #     return
    def die(self):
        "Instakill whatever unit is on the tile."
        if self.unit:
            self.unit.die()
    def _spreadEffects(self):
        "Spread effects from the tile to a unit that newly landed here. This also executes other things the tile can do to the unit when it lands there, such as dying if it falls into a chasm."
        if not Effects.SHIELD in self.unit.effects: # If the unit is not shielded...
            if Effects.FIRE in self.effects: # and the tile is on fire...
                self.unit.applyFire() # spread fire to it.
            if Effects.ACID in self.effects: # same with acid, but also remove it from the tile.
                self.unit.applyAcid()
                self.removeEffect(Effects.ACID)
    def _tileTakeDamage(self):
        "Process the effects of the tile taking damage. returns nothing."
    def putUnitHere(self, unit):
        """Run this method whenever a unit lands on this tile whether from the player moving or a unit getting pushed. unit can be None to get rid of a unit.
        If there's a unit already on the tile, it's overwritten and deleted. returns nothing."""
        self.unit = unit
        try:
            self.unit.square = self.square
        except AttributeError: # raised by None.square = blah
            return # bail, the unit has been replaced by nothing which is ok.
        self._spreadEffects()
    def replaceTile(self, newtile, keepeffects=True):
        """replace this tile with newtile. If keepeffects is True, add them to newtile without calling their apply methods.
        Warning: effects are given to the new tile even if it can't support them! For example, this will happily give a chasm fire or acid.
        Avoid this by manually removing these effects after the tile is replaced or setting keepeffects False and then manually keep only the effects you want."""
        unit = self.unit
        if keepeffects:
            newtile.effects.update(self.effects)
        self.gboard.board[self.square] = newtile
        self.gboard.board[self.square].square = self.square
        self.gboard.board[self.square].putUnitHere(unit)
    def moveUnit(self, destsquare):
        "Move a unit from this square to destsquare, keeping the effects. This overwrites whatever is on destsquare! returns nothing."
        self.gboard.board[destsquare].putUnitHere(self.unit)
        self.unit = None
    def push(self, direction):
        """push unit on this tile direction.
        direction is a Direction.UP type direction
        This method should only be used when there is NO possibility of a unit being pushed to a square that also needs to be pushed during the same action.
        returns nothing"""
        try:
            if Attributes.STABLE in self.unit.attributes:
                return # stable units can't be pushed
        except AttributeError:
            return # There was no unit to push
        else: # push the unit
            destinationsquare = self.getRelSquare(direction, 1)
            try:
                self.gboard.board[destinationsquare].unit.takeBumpDamage() # try to have the destination unit take bump damage
            except AttributeError: # raised from None.takeBumpDamage, there is no unit there to bump into
                self.moveUnit(destinationsquare) # move the unit from this tile to destination square
            except KeyError:
                return  # raised by self.board[None], attempted to push unit off the gameboard, no action is taken
            else:
                self.unit.takeBumpDamage() # The destination took bump damage, now the unit that got pushed also takes damage
    def getRelSquare(self, direction, distance):
        """return the coordinates of the tile that starts at this tile and goes direction direction a certain distance. return False if that tile would be off the board.
        direction is a Direction.UP type global constant
        distance is an int
        """
        if direction == Direction.UP:
            destinationsquare = (self.square[0], self.square[1] + distance)
        elif direction == Direction.RIGHT:
            destinationsquare = (self.square[0] + distance, self.square[1])
        elif direction == Direction.DOWN:
            destinationsquare = (self.square[0], self.square[1] - distance)
        elif direction == Direction.LEFT:
            destinationsquare = (self.square[0] - distance, self.square[1])
        else:
            raise Exception("Invalid direction given.")
        try:
            self.gboard.board[destinationsquare]
        except KeyError:
            return False
        return destinationsquare
    def teleport(self, destsquare):
        "Teleport from this tile to destsquare, swapping units if there is one on destsquare."
        unitfromdest = self.gboard.board[destsquare].unit # grab the unit that's about to be overwritten on the destination
        self.moveUnit(destsquare) # move unit from this square to destination
        self.putUnitHere(unitfromdest)
    def __str__(self):
        return "%s at %s. Effects: %s Unit: %s" % (self.type, self.square, set(Effects.pprint(self.effects)), self.unit)
    def getEdgeSquare(self, direction):
        "return a tuple of the square at the edge of the board in direction from this tile."
        if direction == Direction.UP:
            return (self.square[0], 8)
        if direction == Direction.RIGHT:
            return (8, self.square[1])
        if direction == Direction.DOWN:
            return (self.square[0], 1)
        if direction == Direction.LEFT:
            return (1, self.square[1])
        raise Exception("Invalid Direction given to getEdgeSquare()")

class Tile_Ground(Tile_Base):
    "This is a normal ground tile."
    def __init__(self, gboard, square=None, type='ground', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def applyAcid(self):
        super().applyAcid()
        if not self.unit:
            for e in Effects.TIMEPOD, Effects.MINE, Effects.FREEZEMINE:
                self.removeEffect(e)
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
            self.removeEffect(Effects.FREEZEMINE)
            self.unit.applyIce()
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
            self.gboard.board[self.square].replaceTile(Tile_Ground(self.gboard, effects={Effects.ACID}), keepeffects=True) # Acid removes the forest/sand and makes it no longer flammable/smokable
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
    def applyFire(self):
        "Fire converts the sand tile to a ground tile"
        self.gboard.board[self.square].replaceTile(Tile_Ground(self.gboard, effects={Effects.FIRE}), keepeffects=True)  # Acid removes the forest/sand and makes it no longer flammable/smokable
        super().applyFire()
    def _tileTakeDamage(self):
        self.applySmoke()

class Tile_Water_Ice_Damaged_Base(Tile_Base):
    "This is the base unit for Water tiles, Ice tiles, and Ice_Damaged tiles."
    def __init__(self, gboard, square=None, type=None, effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def applyIce(self):
        "replace the tile with ice and give ice to the unit if present."
        self.gboard.board[self.square].replaceTile(Tile_Ice(self.gboard))
        try:
            self.unit.applyIce()
        except AttributeError:
            return
    def applyFire(self):
        "Fire always removes smoke except over water and it removes acid from frozen acid tiles"
        for e in Effects.SMOKE, Effects.ACID:
            self.removeEffect(e)
        self.gboard.board[self.square].replaceTile(Tile_Water(self.gboard))
        try:
            self.unit.applyFire()
        except AttributeError:
            return
    def _spreadEffects(self):
        "there are no effects to spread from ice or damaged ice to a unit. These tiles can't be on fire and any acid on these tiles is frozen and inert, even if added after freezing."
    def repair(self, hp):
        "acid cannot be removed from water or ice by repairing it. There can't be any fire to repair either."
        if self.unit:
            self.unit.repair(hp)

class Tile_Water(Tile_Water_Ice_Damaged_Base):
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
        super().applyIce()
        self.gboard.board[self.square].removeEffect(Effects.SUBMERGED) # Remove the submerged effect from the newly spawned ice tile.
    def applyAcid(self):
        try:
            self.unit.applyAcid()
        except AttributeError:
            pass
        self.effects.add(Effects.ACID) # water gets acid regardless of a unit being there or not
    def _spreadEffects(self):
        if (Attributes.MASSIVE not in self.unit.attributes) and (Attributes.FLYING not in self.unit.attributes): # kill non-massive non-flying units that went into the water.
            self.unit.die()
        else: # the unit lived
            if Attributes.FLYING not in self.unit.attributes:
                self.unit.removeEffect(Effects.FIRE) # water puts out the fire, but if you're flying you remain on fire
                if Effects.ACID in self.effects: # spread acid from tile to unit but don't remove it from the tile
                    self.unit.effects.add(Effects.ACID) # do not use applyAcid() here. Shielded units get acid from water even though the shield usually blocks acid.
                if Effects.ACID in self.unit.effects: # if the unit has acid and is massive but not flying, spread acid from unit to tile
                    self.effects.add(Effects.ACID) # don't call self.applyAcid() here or it'll give it to the unit and not the tile.
            self.unit.removeEffect(Effects.ICE) # water breaks you out of the ice no matter what

class Tile_Ice(Tile_Water_Ice_Damaged_Base):
    "Turns into Water when destroyed. Must be hit twice. (Turns into Ice_Damaged.)"
    def __init__(self, gboard, square=None, type='ice', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def applyIce(self):
        "Nothing happens when ice is frozen again"
        try:
            self.unit.applyIce()
        except AttributeError:
            return
    def _tileTakeDamage(self):
        self.gboard.board[self.square].replaceTile(Tile_Ice_Damaged(self.gboard))

class Tile_Ice_Damaged(Tile_Water_Ice_Damaged_Base):
    def __init__(self, gboard, square=None, type='ice_damaged', effects=None):
        super().__init__(gboard, square, type, effects=effects)
    def _tileTakeDamage(self):
        self.gboard.board[self.square].replaceTile(Tile_Water(self.gboard))

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
            self.unit = None # set the unit to None even though most units do this. Mech corpses are invincible units that can only be killed by being pushed into a chasm.
        # no need to super()._spreadEffects() here since the only effects a chasm tile can have is smoke and that never spreads to the unit itself.
    def repair(self, hp):
        "There can't be any fire to repair"
        if self.unit:
            self.unit.repair(hp)

class Tile_Lava(Tile_Water):
    def __init__(self, gboard, square=None, type='lava', effects=None):
        super().__init__(gboard, square, type, effects=effects)
        self.effects.add(Effects.FIRE)
    def repair(self, hp):
        "No effects can be removed from lava from repairing on it."
        if self.unit:
            self.unit.repair(hp)
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
    def applySmoke(self):
        "Smoke doesn't remove fire from the lava."
        self.effects.add(Effects.SMOKE)
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
    def __init__(self, gboard, square=None, type='teleporter', effects=None, companion=None):
        "companion is the square of the other tile linked to this one."
        # teleporters can have smoke, fire and acid just like a normal ground tile.
        super().__init__(gboard, square, type, effects=effects)
        self.companion = companion
        self.suppressteleport = False # this is set true when in the process of teleporting so we don't then teleport the unit back and fourth in an infinite loop.
    def _spreadEffects(self):
        "Spread effects like normal but teleport the unit to the companion tile afterward."
        super()._spreadEffects()
        if not self.suppressteleport:
            try:
                if self.unit.suppressteleport:
                    return # no teleporting for you!
            except AttributeError: # unit didn't have suppressteleport attribute, only corpses do.
                self.suppressteleport = True # suppress further teleports here until this finishes
                try:
                    self.gboard.board[self.companion].suppressteleport = True # suppress teleport on the companion too
                except KeyError:
                    raise MissingCompanionTile(self.type, self.square)
                self.teleport(self.companion)
        self.suppressteleport = False

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
        if Effects.SUBMERGED in self.gboard.board[self.square].effects: # if we're in some kind of water...
            self.effects.add(Effects.ACID) # you get acid regardless of shield
        else:
            self.applyEffectUnshielded(Effects.ACID) # you only get acid if you don't have a shield.
    def applyWeb(self):
        self.effects.add(Effects.WEB)
    def applyShield(self):
        self.effects.add(Effects.SHIELD)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False, preventdeath=False):
        """Process this unit taking damage. All effects are considered unless the ignore* flags are set to True in the arguments.
        preventdeath will skip the unit dying and keep it on the board as 0hp or less unit. This is needed for vek units that can be killed and then pushed to do bump damage or spread effects."""
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
        if not preventdeath or self.alliance != Alliance.ENEMY: # only enemies are kept alive longer than they should be
            self._allowDeath()
    def takeBumpDamage(self):
        "take damage from bumping. This is when you're pushed into something or a vek tries to emerge beneath you."
        self.takeDamage(1, ignorearmor=True, ignoreacid=True) # this is overridden by enemies that take increased bump damage by that one global powerup that increases bump damage to enemies only
    def _allowDeath(self):
        "Check if this unit was killed but had it's death supressed. Kill it now if it has 0 or less hp."
        if self.currenthp <= 0:  # if the unit has no more HP and is allowed to die
            self.damage_taken += self.currenthp  # currenthp is now negative or 0. Adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead.
            self.die()
    def die(self):
        "Make the unit die. This method is not ok for mechs to use as they never leave acid where they die. They leave corpses which are also units."
        self.gboard.board[self.square].putUnitHere(None) # it's dead, replace it with nothing
        if Effects.ACID in self.effects: # units that have acid leave acid on the tile when they die:
            self.gboard.board[self.square].applyAcid()
        self.explode()
    def explode(self):
        "Make the unit explode only if it is explosive (to be used after death)."
        if Effects.EXPLOSIVE in self.effects:
            for d in Direction.gen():
                relsquare = self.gboard.board[self.square].getRelSquare(d, 1)
                if relsquare:
                    self.gboard.board[relsquare].takeDamage(1)
    def __str__(self):
        return "%s %s/%s HP. Effects: %s, Attributes: %s" % (self.type, self.currenthp, self.maxhp, set(Effects.pprint(self.effects)), set(Attributes.pprint(self.attributes)))

class Fighting_Unit_Base(Unit_Base):
    "The base class of all units that have weapons."
    def __init__(self, gboard, type, currenthp, maxhp, effects=None, weapon1=None, weapon2=None, attributes=None):
        super().__init__(gboard=gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)
        try: # try to set the wielding unit of this weapon
            weapon1.wieldingunit = self
        except AttributeError: # it's none and that's fine
            pass
        else: # it worked so assign the weapon to this unit and set gboard.
            self.weapon1 = weapon1
            self.weapon1.gboard = self.gboard
        try: # do it again with 2. I'm on the fence if I should do this programmatically. Seems hacky for no benefit, I don't want to go through locals and do string slicing and stuff
            weapon2.wieldingunit = self
        except AttributeError:
            pass
        else:
            self.weapon2 = weapon2
            self.weapon2.gboard = self.gboard

class Repairable_Unit_Base(Fighting_Unit_Base):
    "The base class of all mechs and vek."
    def __init__(self, gboard, type, currenthp, maxhp, effects=None, weapon1=None, weapon2=None, attributes=None):
        super().__init__(gboard=gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, weapon1=weapon1, weapon2=weapon2, attributes=attributes)
    def repairHP(self, hp=1):
        "Repair hp amount of hp. Does not take you higher than the max. Does not remove any effects."
        self.currenthp += hp
        if self.currenthp > self.maxhp:
            self.currenthp = self.maxhp

##############################################################################
################################### MISC UNITS ###############################
##############################################################################
class Unit_Mountain_Building_Base(Unit_Base):
    "The base class for mountains and buildings. They have special properties when it comes to fire and acid."
    def __init__(self, gboard, type, currenthp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.update((Attributes.STABLE, Attributes.IMMUNEFIRE))
        self.blocksbeamshot = True # this unit blocks beam shots that penetrate almost all other units.
    def applyFire(self):
        raise AttributeError # mountains can't be set on fire, but the tile they're on can!. Raise attribute error so the tile that tried to give fire to the present unit gets it instead.

class Unit_Mountain(Unit_Mountain_Building_Base):
    def __init__(self, gboard, type='mountain', attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=1, maxhp=1, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def applyAcid(self):
        pass
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False, preventdeath=True):
        self.gboard.board[self.square].putUnitHere(Unit_Mountain_Damaged(self.gboard))

class Unit_Mountain_Damaged(Unit_Mountain):
    def __init__(self, gboard, type='mountaindamaged', effects=None):
        super().__init__(gboard, type=type, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False, preventdeath=False):
        self.gboard.board[self.square].putUnitHere(None)

class Unit_Volcano(Unit_Mountain):
    "Indestructible volcano that blocks movement and projectiles."
    def __init__(self, gboard, type='volcano', effects=None):
        super().__init__(gboard, type=type, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False, preventdeath=False):
        return # what part of indestructible do you not understand?!
    def die(self):
        return # indestructible!

class Unit_Building(Unit_Mountain_Building_Base):
    def __init__(self, gboard, type='building', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self.isbuilding = True # a flag to indicate this is a building rather than do string comparisons
    def applyAcid(self):
        raise AttributeError # buildings can't gain acid, but the tile they're on can!. Raise attribute error so the tile that tried to give acid to the present unit gets it instead.

class Unit_Building_Objective(Unit_Building):
    def __init__(self, gboard, type='buildingobjective', currenthp=1, maxhp=1, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
        self.alliance = Alliance.NEUTRAL

class Unit_Acid_Vat(Unit_Base):
    def __init__(self, gboard, type='acidvat', currenthp=2, maxhp=2, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def die(self):
        "Acid vats turn into acid water when destroyed."
        self.gboard.board[self.square].putUnitHere(None) # remove the unit before replacing the tile otherwise we get caught in an infinite loop of the vat starting to die, changing the ground to water, then dying again because it drowns in water.
        self.gboard.board[self.square].replaceTile(Tile_Water(self.gboard, effects={Effects.ACID}), keepeffects=True) # replace the tile with a water tile that has an acid effect and keep the old effects
        self.gboard.vekemerge.remove(self.square) # don't let vek emerge from this newly created acid water tile
        self.gboard.board[self.square].removeEffect(Effects.FIRE) # don't keep fire, this tile can't be on fire.

class Unit_Rock(Unit_Base):
    def __init__(self, gboard, type='rock', currenthp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=1, maxhp=1, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL

############################################################################################################################
################################################### FRIENDLY Sub-Units #####################################################
############################################################################################################################
class Sub_Unit_Base(Fighting_Unit_Base):
    "The base unit for smaller sub-units that the player controls as well as objective units that the player controls.."
    def __init__(self, gboard, type, currenthp, maxhp, moves, weapon1=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.moves = moves
        self.alliance = Alliance.FRIENDLY
        self.beamally = True # see isBeamAlly() for explanation

class Unit_AcidTank(Sub_Unit_Base):
    def __init__(self, gboard, type='acidtank', currenthp=1, maxhp=1, moves=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, effects=effects, attributes=attributes)

class Unit_FreezeTank(Sub_Unit_Base):
    def __init__(self, gboard, type='freezetank', currenthp=1, maxhp=1, moves=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, effects=effects, attributes=attributes)

class Unit_ArchiveTank(Sub_Unit_Base):
    def __init__(self, gboard, type='archivetank', currenthp=1, maxhp=1, moves=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, effects=effects, attributes=attributes)

class Unit_OldArtillery(Sub_Unit_Base):
    def __init__(self, gboard, type='oldartillery', currenthp=1, maxhp=1, moves=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, effects=effects, attributes=attributes)

class Unit_ShieldTank(Sub_Unit_Base):
    def __init__(self, gboard, type='shieldtank', currenthp=1, maxhp=1, moves=4, effects=None, attributes=None): # shield tanks can optionally have 3 hp with a power upgrade
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, effects=effects, attributes=attributes)

##############################################################################
################################# OBJECTIVE UNITS ############################
##############################################################################
class Unit_MultiTile_Base(Unit_Base):
    "This is the base class for multi-tile units such as the Dam and Train. Effects and damage to one unit also happens to the other."
    def __init__(self, gboard, type, currenthp, maxhp, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.update((Attributes.STABLE, Attributes.IMMUNEFIRE, Attributes.IMMUNESMOKE)) # these attributes are shared by the dam and train
        self.alliance = Alliance.NEUTRAL
        self.replicate = True # When this is true, we replicate actions to the other companion unit and we don't when False to avoid an infinite loop.
        self.deadfromdamage = False # Set this true when the unit has died from damage. If we don't, takeDamage() can happen to both tiles, triggering die() which would then replicate to the other causing it to die twice.
    def _replicate(self, meth, **kwargs):
        "Replicate an action from this unit to the other. meth is a string of the method to run. Returns nothing."
        if self.replicate:
            try: # Set the companion tile
                self.companion
            except AttributeError: # only once
                self._setCompanion()
            self.gboard.board[self.companion].unit.replicate = False
            try: # try running the companion's method as takeDamage() with keyword arguments
                getattr(self.gboard.board[self.companion].unit, meth)(damage=kwargs['damage'], ignorearmor=kwargs['ignorearmor'], ignoreacid=kwargs['ignoreacid'])
            except KeyError: # else it's an applySomething() method with no args
                #getattr(self.gboard.board[self.companion].unit, meth)() # this is how we used to run the companion unit's method instead of the tile's
                getattr(self.gboard.board[self.companion], meth)()
            self.gboard.board[self.companion].unit.replicate = True
    def applyIce(self):
        self.applyEffectUnshielded(Effects.ICE)
        self._replicate('applyIce')
    def applyAcid(self):
        super().applyAcid()
        self._replicate('applyAcid')
    def applyShield(self):
        super().applyShield()
        self._replicate('applyShield')
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False, preventdeath=False):
        "Process this unit taking damage. All effects are considered unless set to True in the arguments. Yes this is a copy and paste from the base, but we don't need to check for armored here."
        for effect in (Effects.SHIELD, Effects.ICE): # let the shield and then ice take the damage instead if present. Frozen units can have a shield over the ice, but not the other way around.
            try:
                self.effects.remove(effect)
            except KeyError:
                pass
            else:
                self.gboard.board[self.square].putUnitHere(self) # put the unit here again to process effects spreading.
                return # and then stop processing things, the shield or ice took the damage.
        if not ignoreacid and Effects.ACID in self.effects: # if we're not ignoring acid and the unit has acid
            damage *= 2
        self.currenthp -= damage # the unit takes the damage
        self.damage_taken += damage
        if self.currenthp <= 0: # if the unit has no more HP
            self.damage_taken += self.currenthp # currenthp is now negative or 0. Adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead.
            self.deadfromdamage = True
            self.die()
        self._replicate('takeDamage', damage=damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)

class Unit_Dam(Unit_MultiTile_Base):
    "When the Dam dies, it floods the middle of the map."
    def __init__(self, gboard, type='dam', currenthp=2, maxhp=2, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.add(Attributes.MASSIVE)
    def _setCompanion(self):
        "Set self.companion to the square of this unit's companion."
        if self.square[1] == 4:  # set the companion tile without user intervention since the dam is always on the same 2 tiles.
            self.companion = (8, 3)
        else:
            self.companion = (8, 4)
    def die(self):
        "Make the unit die."
        self.gboard.board[self.square].putUnitHere(Unit_Volcano(self.gboard)) # it's dead, replace it with a volcano since there is an unmovable invincible unit there.
        # we also don't care about spreading acid back to the tile, nothing can ever spread them from these tiles.
        for x in range(7, 0, -1): # spread water from the tile closest to the dam away from it
            self.gboard.board[(x, self.square[1])].replaceTile(Tile_Water(self.gboard))
            self.gboard.vekemerge.remove((x, self.square[1])) # don't let vek emerge from these newly created water tiles
        if not self.deadfromdamage: # only replicate death if dam died from an instadeath call to die(). If damage killed this dam, let the damage replicate and kill the other companion.
            self._replicate('die')

class Unit_Train(Unit_MultiTile_Base):
    def __init__(self, gboard, type='train', currenthp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.beamally = True
    def _setCompanion(self):
        "Set the train's companion tile. This has to be run each time it moves forward."
        for xoffset in -1, 1: # check the tiles ahead of and behind this one on the X axis for another train unit.
            if self.gboard.board[(self.square[0]+xoffset, self.square[1])].unit.type == 'train':
                self.companion = (self.square[0]+xoffset, self.square[1])

class Unit_Terraformer(Sub_Unit_Base):
    def __init__(self, gboard, type='terraformer', currenthp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.attributes.add(Attributes.STABLE)

class Unit_DisposalUnit(Unit_Terraformer):
    def __init__(self, gboard, type='disposalunit', currenthp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)

class Unit_SatelliteRocket(Sub_Unit_Base):
    def __init__(self, gboard, type='satelliterocket', currenthp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self.attributes.add(Attributes.STABLE)
        self.beamally = False

class Unit_EarthMover(Sub_Unit_Base):
    def __init__(self, gboard, type='earthmover', currenthp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self.attributes.add(Attributes.STABLE)
        self.beamally = False

class Unit_PrototypeBomb(Unit_Base):
    def __init__(self, gboard, type='prototypebomb', currenthp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self.effects.add(Effects.EXPLOSIVE)
        self.attributes.add(Attributes.IMMUNEFIRE)
        self.beamally = True

############################################################################################################################
###################################################### ENEMY UNITS #########################################################
############################################################################################################################
class Unit_Enemy_Base(Repairable_Unit_Base):
    "This is the base unit of all enemies. Enemies have 1 weapon."
    def __init__(self, gboard, type, currenthp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.alliance = Alliance.ENEMY

class Unit_Enemy_Flying_Base(Unit_Enemy_Base):
    "A simple base unit for flying vek."
    def __init__(self, gboard, type, currenthp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_Enemy_Burrower_Base(Unit_Enemy_Base):
    "A simple base class for the only 2 burrowers in the game."
    def __init__(self, gboard, type, currenthp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.attributes.update((Attributes.BURROWER, Attributes.STABLE))

class Unit_Enemy_Leader_Base(Unit_Enemy_Base):
    "A simple base class for Massive bosses."
    def __init__(self, gboard, type, currenthp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.MASSIVE)

class Unit_Enemy_Flying_Leader_Base(Unit_Enemy_Leader_Base):
    "A simple base class for the 2 Massive flying bosses."
    def __init__(self, gboard, type, currenthp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_Blobber(Unit_Enemy_Base):
    "The Blobber doesn't have a direct attack."
    def __init__(self, gboard, type='blobber', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Blobber(Unit_Enemy_Base):
    "Also has no attack."
    def __init__(self, gboard, type='alphablobber', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scorpion(Unit_Enemy_Base):
    def __init__(self, gboard, type='scorpion', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Acid_Scorpion(Unit_Enemy_Base):
    def __init__(self, gboard, type='acidscorpion', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Scorpion(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphascorpion', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Firefly(Unit_Enemy_Base):
    def __init__(self, gboard, type='firefly', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Firefly(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphascorpion', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Leaper(Unit_Enemy_Base):
    def __init__(self, gboard, type='leaper', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Leaper(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphaleaper', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Beetle(Unit_Enemy_Base):
    def __init__(self, gboard, type='beetle', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Beetle(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphabeetle', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scarab(Unit_Enemy_Base):
    def __init__(self, gboard, type='scarab', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Scarab(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphascarab', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Crab(Unit_Enemy_Base):
    def __init__(self, gboard, type='crab', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Crab(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphacrab', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Centipede(Unit_Enemy_Base):
    def __init__(self, gboard, type='centipede', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Centipede(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphacentipede', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Digger(Unit_Enemy_Base):
    def __init__(self, gboard, type='digger', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Digger(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphadigger', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Hornet(Unit_Enemy_Flying_Base):
    def __init__(self, gboard, type='hornet', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Acid_Hornet(Unit_Enemy_Flying_Base):
    def __init__(self, gboard, type='acidhornet', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Hornet(Unit_Enemy_Flying_Base):
    def __init__(self, gboard, type='alphahornet', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Soldier_Psion(Unit_Enemy_Flying_Base):
    def __init__(self, gboard, type='soldierpsion', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Shell_Psion(Unit_Enemy_Flying_Base):
    def __init__(self, gboard, type='shellpsion', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blood_Psion(Unit_Enemy_Flying_Base):
    def __init__(self, gboard, type='bloodpsion', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blast_Psion(Unit_Enemy_Flying_Base):
    def __init__(self, gboard, type='blastpsion', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Psion_Tyrant(Unit_Enemy_Flying_Base):
    def __init__(self, gboard, type='psiontyrant', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spider(Unit_Enemy_Base):
    def __init__(self, gboard, type='spider', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Spider(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphaspider', currenthp=4, maxhp=4, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Burrower(Unit_Enemy_Burrower_Base):
    def __init__(self, gboard, type='burrower', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Burrower(Unit_Enemy_Burrower_Base):
    def __init__(self, gboard, type='alphaburrower', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Beetle_Leader(Unit_Enemy_Leader_Base):
    def __init__(self, gboard, type='beetleleader', currenthp=6, maxhp=6, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Large_Goo(Unit_Enemy_Leader_Base):
    def __init__(self, gboard, type='largegoo', currenthp=3, maxhp=3, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Medium_Goo(Unit_Enemy_Leader_Base):
    def __init__(self, gboard, type='mediumgoo', currenthp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Small_Goo(Unit_Enemy_Leader_Base):
    def __init__(self, gboard, type='smallgoo', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Hornet_Leader(Unit_Enemy_Leader_Base):
    def __init__(self, gboard, type='hornetleader', currenthp=6, maxhp=6, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_Psion_Abomination(Unit_Enemy_Flying_Leader_Base):
    def __init__(self, gboard, type='psionabomination', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Scorpion_Leader(Unit_Enemy_Leader_Base):
    def __init__(self, gboard, type='scorpionleader', currenthp=7, maxhp=7, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Firefly_Leader(Unit_Enemy_Flying_Leader_Base):
    def __init__(self, gboard, type='fireflyleader', currenthp=6, maxhp=6, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spider_Leader(Unit_Enemy_Leader_Base):
    def __init__(self, gboard, type='spiderleader', currenthp=6, maxhp=6, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Blob(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphablob', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Blob(Unit_Enemy_Base):
    def __init__(self, gboard, type='blob', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spiderling_Egg(Unit_Enemy_Base):
    def __init__(self, gboard, type='spiderlingegg', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Spiderling(Unit_Enemy_Base):
    def __init__(self, gboard, type='spiderling', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_Alpha_Spiderling(Unit_Enemy_Base):
    def __init__(self, gboard, type='alphaspiderling', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_CannonBot(Unit_Enemy_Base):
    def __init__(self, gboard, type='cannonbot', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_CannonMech(Unit_Enemy_Base):
    def __init__(self, gboard, type='cannonmech', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_ArtilleryBot(Unit_Enemy_Base):
    def __init__(self, gboard, type='artillerybot', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_ArtilleryMech(Unit_Enemy_Base):
    def __init__(self, gboard, type='artillerymech', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_LaserBot(Unit_Enemy_Base):
    def __init__(self, gboard, type='laserbot', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_LaserMech(Unit_Enemy_Base):
    def __init__(self, gboard, type='lasermech', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_MineBot(Unit_Enemy_Base):
    def __init__(self, gboard, type='minebot', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_MineMech(Unit_Enemy_Base):
    def __init__(self, gboard, type='minemech', currenthp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_BotLeader(Unit_Enemy_Base):
    def __init__(self, gboard, type='botleader', currenthp=5, maxhp=5, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

class Unit_BotLeaderHard(Unit_Enemy_Base):
    def __init__(self, gboard, type='botleaderhard', currenthp=6, maxhp=6, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, effects=effects, attributes=attributes)

############################################################################################################################
##################################################### FRIENDLY MECHS #######################################################
############################################################################################################################
class Unit_Mech_Base(Repairable_Unit_Base):
    "This is the base unit of Mechs."
    def __init__(self, gboard, type, currenthp, maxhp, moves, weapon1=None, weapon2=None, pilot=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)
        self.moves = moves # how many moves the mech has
        self.pilot = pilot # the pilot in this mech that might provide bonuses or extra abilities
        self.attributes.add(Attributes.MASSIVE) # all mechs are massive
        self.alliance = Alliance.FRIENDLY # and friendly, duh
    def die(self):
        "Make the mech die."
        self.currenthp = 0
        self.gboard.board[self.square].putUnitHere(Unit_Mech_Corpse(self.gboard, oldunit=self)) # it's dead, replace it with a mech corpse
        self.explode()
    def repair(self, hp):
        "Repair the unit healing HP and removing bad effects."
        self.repairHP(hp)
        for e in (Effects.FIRE, Effects.ICE, Effects.ACID):
            self.removeEffect(e)

class Unit_Mech_Flying_Base(Unit_Mech_Base):
    "The base class for flying mechs. Flying mechs typically have 2 hp and 4 moves."
    def __init__(self, gboard, type, currenthp=2, maxhp=2, moves=4, weapon1=None, weapon2=None, pilot=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, weapon1=weapon1, weapon2=weapon2, pilot=pilot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_Mech_Corpse(Unit_Mech_Base):
    "This is a player mech after it dies. It's invincible but can be pushed around. It can be repaired back to an alive mech. It has no weapons."
    def __init__(self, gboard, type='mechcorpse', currenthp=1, maxhp=1, moves=0, oldunit=None, attributes=None, effects=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.oldunit = oldunit # This is the unit that died to create this corpse. You can repair mech corpses to get your mech back.
        self.attributes.add(Attributes.MASSIVE)
        self.suppressteleport = True # Mech corpses can never be teleported through a teleporter. They can be teleported by the teleport mech/weapon however
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False, preventdeath=False):
        "invulnerable to damage"
    def applyShield(self):
        "Mech corpses cannot be shielded."
    def applyIce(self):
        "Mech corpses cannot be frozen."
    def die(self):
        "Nothing happens when a mech corpse is killed again."
    def repair(self, hp):
        "repair the mech corpse back to unit it was."
        self.oldunit.repairHP(hp)
        self.oldunit.removeEffect(Effects.FIRE) # fire is removed revived mechs. They get fire again if they're revived on a fire tile.
        self.gboard.board[self.square].putUnitHere(self.oldunit)

class Unit_Combat_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='combat', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Laser_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='laser', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Lightning_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='lightning', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Judo_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='judo', currenthp=3, maxhp=3, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.ARMORED)

class Unit_Flame_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='flame', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Aegis_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='aegis', currenthp=3, maxhp=3, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Leap_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='leap', currenthp=3, maxhp=3, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Cannon_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='cannon', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Jet_Mech(Unit_Mech_Flying_Base):
    def __init__(self, gboard, type='jet', currenthp=2, maxhp=2, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Charge_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='charge', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Hook_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='hook', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.ARMORED)

class Unit_Mirror_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='mirror', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Unstable_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='unstable', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Artillery_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='artillery', currenthp=2, maxhp=2, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Rocket_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='rocket', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Boulder_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='boulder', currenthp=2, maxhp=2, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Siege_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='siege', currenthp=2, maxhp=2, moves=2, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Meteor_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='meteor', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Ice_Mech(Unit_Mech_Flying_Base):
    def __init__(self, gboard, type='ice', currenthp=2, maxhp=2, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Pulse_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='pulse', currenthp=3, maxhp=3, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Defense_Mech(Unit_Mech_Flying_Base):
    def __init__(self, gboard, type='defense', currenthp=2, maxhp=2, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Gravity_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='gravity', currenthp=3, maxhp=3, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Swap_Mech(Unit_Mech_Flying_Base):
    def __init__(self, gboard, type='swap', currenthp=2, maxhp=2, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Nano_Mech(Unit_Mech_Flying_Base):
    def __init__(self, gboard, type='nano', currenthp=2, maxhp=2, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_TechnoBeetle_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='technobeetle', currenthp=3, maxhp=3, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_TechnoHornet_Mech(Unit_Mech_Flying_Base):
    def __init__(self, gboard, type='technohornet', currenthp=2, maxhp=2, moves=4, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_TechnoScarab_Mech(Unit_Mech_Base):
    def __init__(self, gboard, type='technoscarab', currenthp=2, maxhp=2, moves=3, pilot=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(gboard, type=type, currenthp=currenthp, maxhp=maxhp, moves=moves, pilot=pilot, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

##############################################################################
########################## ENVIRONMENTAL EFFECTS #############################
##############################################################################
# Environmental effects are actions performed on tiles/units after fire damage but before enemy actions. We count emerging vek as an environmental effect here even though it happens last.
class Environ_Base():
    "The base object for environmental effects."
    def __init__(self, squares, effects=None, newtile=None):
        """squares is an iter of tiles that are affected. If they need to be done in a certain order, pass in a tuple of squares, otherwise use a set.
        effects is a tuple of strings. Each string is a method to apply on each tile in squares.
        newtile is a tile class (not object!) that will replace the tiles on squares.
        the attribute self.gboard is set when the GameBoard instance initializes this object."""
        self.squares = squares
        self.effects = effects
        self.newtile = newtile
    def run(self):
        "Run the environmental effect on the gameboard."
        for square in self.squares:
            if self.effects:
                for effect in self.effects:
                    getattr(self.gboard.board[square], effect)()
            if self.newtile:
                self.gboard.board[square].replaceTile(self.newtile(self.gboard))

class Environ_IceStorm(Environ_Base):
    def __init__(self, squares):
        "Use a set of squares here."
        super().__init__(squares, effects=('applyIce',))

class Environ_AirStrike(Environ_Base):
    def __init__(self, squares):
        "Use a set of squares here."
        super().__init__(squares, effects=('takeDamage', 'die'))

class Environ_Tsunami(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, newtile=Tile_Water)

class Environ_Cataclysm(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, newtile=Tile_Chasm)
    def run(self):
        super().run()
        for square in self.squares:
            for e in Effects.FIRE, Effects.ACID: # remove fire and acid from the newly created chasm tiles as they can't have these effects.
                self.gboard.board[square].removeEffect(e)
            self.gboard.vekemerge.remove(square) # don't let vek emerge from this newly created chasm tile

class Environ_FallingRock(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, effects=('die',), newtile=Tile_Ground)

class Environ_Tentacles(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, effects=('die',), newtile=Tile_Lava)

class Environ_LavaFlow(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, newtile=Tile_Lava)

class Environ_VolcanicProjectile(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, effects=('die', 'applyFire'))

Environ_Lightning = Environ_AirStrike # Lightning is really the exact same thing as Air Strike except it hits squares in a spread out pattern while Air Strike hits in that touching cluster of 5 pattern.
# We don't check for the number of squares or the pattern, so fuggit
Environ_TidalWave = Environ_Tsunami # same
Environ_SeismicActivity = Environ_Cataclysm # yeah

class Environ_ConveyorBelts():
    def __init__(self, squaresdirs):
        "squaresdirs is a dict of tuples to direction: {(x, y): Direction.DIR, ...}"
        self.squaresdirs = squaresdirs
        self.sorted = False
    def sort(self):
        """"Sort self.squaresdirs so that the first square pushes to a non-conveyor tile and all the following ones then point to the previous one.
        This is done to prevent 2 units next to each other on a conveyor belt from bumping into each other, just like they don't in the game.
        There can be multiple conveyor paths that are separate, one will just follow the other.
        return nothing and change self.squaresdirs to the sorted list and set self.sorted = True at the end."""
        solution = []
        while self.squaresdirs:
            for c in self.squaresdirs:
                if self.gboard.board[c].getRelSquare(self.squaresdirs[c], 1) not in self.squaresdirs: # if this square does NOT push to another square that needs to be pushed...
                    solution.append((c, self.squaresdirs.pop(c)))
                    break # start a new iter of squaresdirs since we can't iterate over something that changes
        self.squaresdirs = solution
        self.sorted = True
    def run(self):
        "Do it to it!"
        if not self.sorted:
            self.sort()
        for sqd in self.squaresdirs: # this is now a list of [((x, y), Direction.DIR), ...]
            self.gboard.board[sqd[0]].push(sqd[1])

class Environ_VekEmerge():
    "This one is a bit special and different from other environmental effects as you can imagine."
    def __init__(self, squares=None):
        "Use a list of squares here since tiles being replaced will remove squares from this."
        if squares:
            self.squares = squares
        else:
            self.squares = []
    def run(self):
        for square in self.squares:
            try:
                self.gboard.board[square].unit.takeBumpDamage()
            except AttributeError: # there was no unit
                pass # TODO: the vek emerges
    def remove(self, square):
        "remove square from self.squares, ignoring if it wasn't there in the first place. returns nothing."
        try:
            self.squares.remove(square)
        except ValueError:
            pass
        else:
            pass # TODO: Vek emerging cancelled!

##############################################################################
################################## WEAPONS ###################################
##############################################################################
# All weapons must have a shoot() method to shoot the weapon.
# All weapons must have a genShots() method to generate all possible shots the unit with this weapon can take.
# All weapons that deal damage should store the amount of damage as self.damage
# self.gboard will be set by the unit that owns the weapon.
# self.wieldingunit will be set by the unit that owns the weapon.
# All mech weapons are assumed to be enabled whether they require power or not. If your mech has an unpowered weapon, it's totally useless to us here.
class Weapon_Directional_Base():
    "The base class for all weapons that must have a direction to be shot."
    def genShots(self):
        """A shot generator that yields each direction unless the weapon wielder is on the edge and trying to shoot off the board.
        For example, if you have a unit in the bottom left corner (1, 1), you can only shoot up and right, but not left or down."""
        for d in Direction.gen():
            if self.gboard.board[self.wieldingunit.square].getRelSquare(d, 1):  # false if it goes off the board
                yield d

class Weapon_Charge_Base(Weapon_Directional_Base):
    "The base class for charge weapons."
    def shoot(self, direction):
        victimtile = findUnitInDirection(self, direction, edgeok=False)
        try:
            hurtAndPush(self, victimtile, direction)
        except KeyError: # raised from hurtAndPush doing self.gboard.board[False]... meaning there was no unit on victimtile
            self.gboard.board[self.wieldingunit.square].moveUnit(self.gboard.board[self.wieldingunit.square].getEdgeSquare(direction)) # move the wielder to victimtile which is the edge of the board
        else: # victimtile was actually a tile and we hurt and push the unit there
            self.gboard.board[self.wieldingunit.square].moveUnit(self.gboard.board[victimtile].getRelSquare(Direction.opposite(direction), 1)) # move wielder to the square before the victimsquare

class Weapon_Artillery_Base():
    "The base class for artillery weapons."
    def genShots(self):
        "Generate every possible shot that the weapon wielder can take from their position with an artillery weapon. Yields a tuple of (direction, relativedistance)."
        for direction in Direction.gen():
            relativedistance = 2  # artillery weapons can't shoot the tile next to them, they start at one tile past that.
            while True:
                if self.gboard.board[self.wieldingunit.square].getRelSquare(direction, relativedistance):
                    yield (direction, relativedistance)
                    relativedistance += 1
                else:  # square was false, we went off the board
                    break  # move onto the next direction

class Weapon_LimitedUse_Base():
    

# the below are loose methods that weapon objects can use. The weapons are bit too varied to make base classes from these.
def hurtAndPush(self, square, direction):
    "have a tile takeDamage() and get pushed. This should be used whenever a tile needs to have both done at once because we treat vek specially."
    self.gboard.board[square].takeDamage(self.damage, preventdeath=True) # takes damage
    hurtunit = self.gboard.board[square].unit # It's fine if this is None
    self.gboard.board[square].push(direction) # hurtunit is pushed
    try:
        hurtunit._allowDeath()
    except AttributeError: # raised by None._allowDeath()
        pass

def findUnitInDirection(self, direction, edgeok=False):
    """Travel from the weapon wielder's tile in direction, returning the square of the first unit we find.
    If none is found, return False.
    If none is found and edgeok is True, return the square on the edge of the board.
    :type edgeok: bool"""
    attackedsquare = self.gboard.board[self.wieldingunit.square].getRelSquare(direction, 1)  # start the projectile at square in direction from the unit that used the weapon...
    while True:
        try:
            if self.gboard.board[attackedsquare].unit:
                return attackedsquare  # found the unit
        except KeyError:  # raised from if gboard.board[False].unit: attackedsquare being false means we never found a unit and went off the board
            if edgeok:
                return attackedsquare
            return False
        attackedsquare = self.gboard.board[attackedsquare].getRelSquare(direction, 1)  # the next tile in direction of the last square

def isBuilding(unit):
    "Return True if unit is a building or objectivebuilding, False if it is not."
    try:
        return unit.isbuilding
    except AttributeError: # unit was None or was missing the attribute
        return False

##################### Actual weapons #####################
class Weapon_TitanFist(Weapon_Charge_Base):
    """Combat mech's default weapon.
    Dashing does not damage the edge tile if it doesn't come in contact with a unit like projectiles do."""
    def __init__(self, power1=False, power2=False):
        super().__init__()
        if not power1: # Weapon_Charge_Base already has self.shoot set to the charge attack
            self.shoot = self.shoot_normal # punch by default
        if power2: # increase damage by 2
            self.damage = 4
        else: # it's 2 by default
            self.damage = 2
    def shoot_normal(self, direction):
        hurtAndPush(self, self.gboard.board[self.wieldingunit.square].getRelSquare(direction, 1), direction)

class Weapon_TaurusCannon(Weapon_Directional_Base):
    "Cannon Mech's default weapon."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        for p in power1, power2:
            if p:
                self.damage += 1
    def shoot(self, direction):
        hurtAndPush(self, self.findUnitInDirection(direction, edgeok=True), direction)

class Weapon_ArtemisArtillery(Weapon_Artillery_Base):
    "Artillery Mech's default weapon."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self.buildingsimmune = True
        else:
            self.buildingsimmune = False
        if power2:
            self.damage += 2
    def shoot(self, direction, distance):
        "Shoot in direction distance number of tiles. Artillery can never shoot 1 tile away from the wielder."
        targetsquare = self.gboard.board[self.wieldingunit.square].getRelSquare(direction, distance)
        if self.buildingsimmune and isBuilding(self.gboard.board[targetsquare].unit):
           pass
        else:
            self.gboard.board[targetsquare].takeDamage(self.damage)
        for d in Direction.gen(): # now push all the tiles around targetsquare
            self.gboard.board[self.gboard.board[targetsquare].getRelSquare(d, 1)].push(d)

class Weapon_BurstBeam(Weapon_Directional_Base):
    """Laser Mech's default weapon.
    If ally immune is powered and you have a friendly on a forest tile, the forest tile does NOT ignite from damage when you shoot.
    If ally immune is powered, it will not hurt *some* objective units like:
        terraformer
        earth mover
        archive tank
        train
        prototype renfield bombs
        earth mover
        acid launcher
    The following friendly units DO take damage from the beam:
        satellite rocket
        acid vat"""
    def __init__(self, power1=False, power2=False):
        self.damage = 3
        if power1:
            self.allyimmune = True
        else:
            self.allyimmune = False
        if power2:
            self.damage += 1
    def shoot(self, direction):
        relsquare = 1 # start 1 square from the wielder
        currentdamage = self.damage # damage being dealt as the beam travels. This decreases the further we go until we reach 1
        while True:
            try:
                targettile = self.gboard.board[self.gboard.board[self.wieldingunit.square].getRelSquare(direction, relsquare)] # get the target tile, not square
            except KeyError: # self.gboard.board[False] means we went off the board
                return # no more pew pew
            if self.allyimmune and self.isBeamAlly(targettile.unit):
                pass # no damage
            else:
                targettile.takeDamage(currentdamage) # damage the tile
            if self.blocksBeamShot(targettile.unit):
                return # no more pew pew
            currentdamage -= 1
            if currentdamage < 1:
                currentdamage = 1
            relsquare += 1
    def isBeamAlly(self, unit):
        "return True if unit is considered an ally to the beam weapon when it has the first upgrade powered."
        try:
            return unit.alliance == Alliance.FRIENDLY or unit.beamally
        except AttributeError:  # units that allow penetration don't have this attribute set at all
            return False
    def blocksBeamShot(self, unit):
        "Return True if unit will block a beam shot that usually penetrates, False if we can penetrate through it."
        try:
            return unit.blocksbeamshot
        except AttributeError:  # units that allow penetration don't have this attribute set at all
            return False

class Weapon_RammingEngines(Weapon_Charge_Base):
    "Charge Mech's default weapon."
    def __init__(self, power1=False, power2=False):
        self.selfdamage = 1
        self.damage = 2
        if power1:
            self.damage += 1
            self.selfdamage += 1
        if power2:
            self.damage += 1
    def shoot(self, direction):
        super().shoot(direction)
        self.gboard.board[self.wieldingunit.square].takeDamage(self.selfdamage)

class Weapon_ElectricWhip():
    """This is the lightning mech's default weapon.
    When building chain is not powered (power1), you cannot hurt buildings or chain through them with this at all.
    It does not go through mountains or supervolcano either. It does go through rocks.
    Cannot attack mines on the ground.
    Reddit said you can attack a building if it's webbed, this is not true. Even if you attack the scorpion webbing the building, the building won't pass the attack through or take damage.
    When you chain through units that are explosive, they explode in the reverse order in which they were shocked.
    You can never chain through yourself when you shoot!"""
    def __init__(self, power1=False, power2=False):
        if power1:
            self.buildingchain = True
        else:
            self.buildingchain = False
        if power2:
            self.damage = 3
        else:
            self.damage = 2
    def shoot(self, direction):
        self.hitsquares = [False, self.wieldingunit.square]  # squares that have already been hit so we don't travel back through them in circles.
        # False is included because getRelSquare will return False when you go off the board. We can use this in the branching logic to tell it that anything off the board has been visited.
        # we also include the unit that shot the weapon since you can NEVER chain through yourself!
        self.branchChain(backwards=Direction.opposite(direction), targetsquare=self.gboard.board[self.wieldingunit.square].getRelSquare(direction, 1))
        # done with the recursive method, now skip False and and the wielder's square and make all the units that need to take damage take damage
        for hs in self.hitsquares[2:]:
            if self.gboard.board[hs].unit.type not in ('building', 'buildingobjective'): # don't damage buildings. If they're here they're already not effected.
                self.gboard.board[hs].takeDamage(self.damage)
    def gen(self):
        for dir in Direction.gen():
            if self.unitIsChainable(self.gboard.board[self.gboard.board[self.wieldingunit.square].getRelSquare(dir, 1)].unit):
                yield dir
    def unitIsChainable(self, unit):
        "Pass a unit to this method and it will return true if you can chain through it, false if not or if there is no unit."
        if unit:
            if (self.buildingchain and isBuilding(unit)) or \
                    (self.buildingchain and unit.type not in ('mountain', 'mountaindamaged', 'volcano')) or \
                    (unit.type not in ('building', 'buildingobjective', 'mountain', 'mountaindamaged', 'volcano')):
                return True
        return False
    def branchChain(self, backwards, targetsquare):
        """"A recursive method to facilitate the branching out of the electric whip shot.
        backwards is the direction that the shock came from to avoid doubling back.
        targetsquare is the current square being hit and branched out from.
        self.hitsquares will be built out to a set of squares that need to be hit without ever backwards.
        returns nothing."""
        self.hitsquares.append(targetsquare)
        for d in Direction.gen():
            if d == backwards:
                continue
            nextsquare = self.gboard.board[targetsquare].getRelSquare(d, 1)
            if nextsquare in self.hitsquares:
                continue
            if self.unitIsChainable(self.gboard.board[nextsquare].unit):
                self.branchChain(backwards=Direction.opposite(d), targetsquare=nextsquare)