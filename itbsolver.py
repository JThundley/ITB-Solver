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
    "This is the up/down/left/right directions with a couple other methods. THIS SET OF CONSTANTS MUST BE FIRST SO IT GETS THE FIRST 4 NUMBERS!"
    def opposite(self, dir):
        "return the opposite of the direction provided as dir."
        try:
            dir += 2
        except TypeError:
            raise InvalidDirection
        if dir > 4:
            dir -= 4
        return dir
    def gen(self):
        "A generator that yields each direction."
        for d in Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT:
            yield d
    def genPerp(self, dir):
        "A generator that yields 2 directions that are perpendicular to dir"
        try:
            dir += 1
        except TypeError:
            raise InvalidDirection
        if dir == 5:
            dir = 1
        yield dir
        yield self.opposite(dir)
    def getClockwise(self, dir):
        "return the next direction clockwise of dir"
        try:
            dir += 1
        except TypeError:
            raise InvalidDirection
        if dir > 4:
            return 1
        return dir
    def getCounterClockwise(self, dir):
        "return the next direction counter clockwise of dir"
        try:
            dir -= 1
        except TypeError:
            raise InvalidDirection
        if not dir:
            return 4
        return dir

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
    'ICE', # sometimes does nothing to tile or unit
    'ACID',
    # These effects can only be applied to tiles:
    'SMOKE',
    'TIMEPOD',
    'MINE',
    'FREEZEMINE',
    'SUBMERGED', # I'm twisting the rules here. In the game, submerged is an effect on the unit. Rather than apply and remove it as units move in and out of water, we'll just apply this to water tiles and check for it there.
    # These effects can only be applied to units:
    'SHIELD',
    # 'WEB', # web is no longer an effect
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

Passives = Constant(thegen, (
    'FLAMESHIELDING', # mech passives (from weapons)
    'STORMGENERATOR',
    'VISCERANANOBOTS',
    'NETWORKEDARMOR',
    'REPAIRFIELD',
    'AUTO-SHIELDS',
    'STABILIZERS',
    'PSIONICRECEIVER',
    'KICKOFFBOOSTERS',
    'MEDICALSUPPLIES',
    'VEKHORMONES',
    'FORCEAMP',
    'AMMOGENERATOR',
    'CRITICALSHIELDS',
    'INVIGORATINGSPORES', # vek passives
    'HARDENEDCARAPACE',
    'REGENERATION',
    'EXPLOSIVEDECAY',
    'HIVETARGETING'))

# don't need these anymore
del Constant
del numGen
del thegen
del DirectionConst

############### FUNCTIONS #################

############### CLASSES #################
# Exceptions
class MissingCompanionTile(Exception):
    "This is raised when something fails due to a missing companion tile."
    def __init__(self, type, square):
        super().__init__()
        self.message = "No companion tile specified for %s on %s" % (type, square)
    def __str__(self):
        return self.message

class NullWeaponShot(Exception):
    """This is raised when a friendly unit fires a weapon that has no effect at all on the game or an invalid shot (like one that went off the board).
    This prompts the logic to avoid continuing the current simulation. It's a bug if a user ever sees this."""

class InvalidDirection(Exception):
    "This is raised when an invalid direction is given to something."

class FakeException(Exception):
    "This is raised to do some more effecient try/except if/else statements"
############# THE MAIN GAME BOARD!
class Game():
    "This represents the a single instance of a game. This is the highest level of the game."
    def __init__(self, board=None, powergrid_hp=7, environeffect=None, vekemerge=None):
        """board is a dict of tiles to use. If it's left blank, a default board full of empty ground tiles is generated.
        powergrid_hp is the amount of power (hp) you as a player have. When this reaches 0, the entire game ends.
        environeffect is an environmental effect object that should be run during a turn.
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
        self.environeffect = environeffect
        try:
            self.environeffect.game = self
        except AttributeError:
            pass # no environmental effect being used
        if vekemerge:
            self.vekemerge = vekemerge
        else:
            self.vekemerge = Environ_VekEmerge()
        self.vekemerge.game = self
        self.playerpassives = {} # a dict of passive effects being applied to the player's mechs
        self.vekpassives = {}
        self.playerunits = set() # All the units that the player has direct control over, including dead mech corpses
        self.enemyunits = set() # all the enemy units
        self.hurtplayerunits = [] # a list of the player's units hurt by a single action. All units here must be checked for death after they all take damage and then this is reset.
        self.hurtpsion = None # This is set to a single psion that was damaged since there can never be more than 1 psion on the board at at time
        self.hurtenemies = [] # a list of all enemy units that were hurt during a single action. This includes robots
    def flushHurt(self):
        "resolve the effects of hurt units, returns nothing. Tiles are damaged first, then Psions are killed, then your mechs can explode, then vek/bots can die"
        # print("hurtenemies:", self.hurtenemies)
        # print("hurtplayerunits:", self.hurtplayerunits)
        # print("hurtpsion:", self.hurtpsion)
        while True:
            hurtplayerunits = self.hurtplayerunits
            hurtenemies = self.hurtenemies
            self.hurtplayerunits = []
            self.hurtenemies = []
            try:
                self.hurtpsion._allowDeath()
                self.hurtpsion = None
            except AttributeError:
                pass
            for hpu in hurtplayerunits:
                hpu.explode()
            for he in hurtenemies:
                he._allowDeath()
            if not (self.hurtenemies or self.hurtplayerunits or self.hurtpsion):
                return
##############################################################################
######################################## TILES ###############################
##############################################################################
class TileUnit_Base():
    "This is the base object that forms both Tiles and Units."
    def __init__(self, game, square=None, type=None, effects=None):
        self.game = game  # this is a link back to the game board instance so tiles and units can change it
        self.square = square # This is the (x, y) coordinate of the Tile or Unit. This is required for Tiles, but not for Units which have their square set when they are placed on a square.
        self.type = type # the name of the unit or tile
        if not effects:
            self.effects = set()
        else:
            self.effects = set(effects) # Current effect(s) on the tile. Effects are on top of the tile. Some can be removed by having your mech repair while on the tile.
    def removeEffect(self, effect):
        "This is just a little helper method to remove effects and ignore errors if the effect wasn't present."
        try:
            self.effects.remove(effect)
        except KeyError:
            pass

class Tile_Base(TileUnit_Base):
    """The base class for all Tiles, all other tiles are based on this. Mountains and buildings are considered units since they have HP and block movement on a tile, thus they go on top of the tile."""
    def __init__(self, game, square=None, type=None, effects=None, unit=None):
        super().__init__(game, square, type, effects=effects)
        self.unit = unit # This is the unit on the tile. If it's None, there is no unit on it.
    def takeDamage(self, damage=1, ignorearmor=False, ignoreacid=False):
        """Process the tile taking damage and the unit (if any) on this tile taking damage. Damage is usually done to the tile, the tile will then pass it onto the unit.
        There are a few exceptions when takeDamage() will be called on the unit but not the tile, such as the Psion Tyrant damaging all player mechs which never has an effect on the tile.
        Damage is an int of how much damage to take. DO NOT PASS 0 DAMAGE TO THIS or the tile will still take damage!
        ignorearmor and ignoreacid have no effect on the tile and are passed onto the unit's takeDamage method.
        returns nothing.
        """
        try:
            if (Effects.SHIELD not in self.unit.effects) and (Effects.ICE not in self.unit.effects): # if the unit on this tile was NOT shielded...
                raise FakeException
        except AttributeError: # raised from Effects.SHIELD in self.None.effects meaning there was no unit to check for shields/ice
            self._tileTakeDamage()
            return
        except FakeException: # there was an unshielded unit present
            self._tileTakeDamage()
        self.game.board[self.square].unit.takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid) # then the unit takes damage. If the unit was shielded, then only the unit took damage and not the tile
    def hasShieldedUnit(self):
        "If there is a unit on this tile that is shielded, return True, return False otherwise."
        try:
            return Effects.SHIELD in self.unit.effects
        except AttributeError:
            return False
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
        try: # invalidate qshots of enemies that get smoked
            self.unit.weapon1.qshot = None
        except AttributeError:
            pass
        else: # this was an enemy that was smoked, let's also break all its webs:
            self.unit._breakAllWebs()
    def applyIce(self):
        "apply ice to the tile and unit."
        if not self.hasShieldedUnit():
            self.removeEffect(Effects.FIRE) # remove fire from the tile
            try:
                self.unit.applyIce() # give the unit ice
            except AttributeError: # None.applyIce()
                pass
    def applyAcid(self):
        try:
            self.unit.applyAcid()
        except AttributeError: # the tile doesn't get acid if a unit is present to take it instead
            self.effects.add(Effects.ACID)
            self.removeEffect(Effects.FIRE)
    def applyShield(self):
        "Try to give a shield to a unit present. return True if a unit was shielded, False if there was no unit."
        try: # Tiles can't be shielded, only units
            self.unit.applyShield()
            return True
        except AttributeError:
            return False
    def repair(self, hp):
        "Repair this tile and any mech on it. hp is the amount of hp to repair on the present unit. This method should only be used for mechs and not vek as they can be healed but they never repair the tile."
        self.removeEffect(Effects.FIRE)
        try:
            self.unit.repair(hp)
        except AttributeError:
            return
    def die(self):
        "Instakill whatever unit is on the tile and damage the tile."
        self._tileTakeDamage()
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
        pass
    def _putUnitHere(self, unit):
        """Run this method whenever a unit lands on this tile whether from the player moving or a unit getting pushed. unit can be None to get rid of a unit.
        If there's a unit already on the tile, it's overwritten and deleted. returns nothing."""
        self.unit = unit
        try:
            self.unit._breakAllWebs() # TODO: override _breakAllWebs in units that will never be webbed, such as rocks
        except AttributeError: # raised by None.square = blah
            return  # bail, the unit has been replaced by nothing which is ok.
        self.unit.square = self.square
        self._spreadEffects()
        try:
            self.unit.weapon1.validate()
        except AttributeError: # None.weapon1, _spreadEffects killed the unit or unit.None.validate(), unit didn't have a weapon1 somehow
            pass
    def createUnitHere(self, unit):
        "Run this method when putting a unit on the board for the first time. This ensures that the unit is sorted into the proper set in the game."
        if unit.alliance == Alliance.FRIENDLY:
            self.game.playerunits.add(unit)
        elif unit.alliance == Alliance.ENEMY:
            self.game.enemyunits.add(unit)
        self._putUnitHere(unit)
    def replaceTile(self, newtile, keepeffects=True):
        """replace this tile with newtile. If keepeffects is True, add them to newtile without calling their apply methods.
        Warning: effects are given to the new tile even if it can't support them! For example, this will happily give a chasm fire or acid.
        Avoid this by manually removing these effects after the tile is replaced or setting keepeffects False and then manually keep only the effects you want."""
        unit = self.unit
        if keepeffects:
            newtile.effects.update(self.effects)
        self.game.board[self.square] = newtile
        self.game.board[self.square].square = self.square
        self.game.board[self.square]._putUnitHere(unit)
    def moveUnit(self, destsquare):
        "Move a unit from this square to destsquare, keeping the effects. This overwrites whatever is on destsquare! returns nothing."
        assert Attributes.STABLE not in self.unit.attributes
        if destsquare == self.square:
            return # tried to move a unit to the same square it's already one. This has the unintended consequence of leaving the square blank!
        self.game.board[destsquare]._putUnitHere(self.unit)
        self.unit = None
    def push(self, direction):
        """push unit on this tile in direction.
        direction is a Direction.UP type direction
        This method should only be used when there is NO possibility of a unit being pushed to a square that also needs to be pushed during the same action e.g. conveyor belts or wind torrent
        returns True if a unit was pushed or took bump damage, False if nothing happened."""
        try:
            if Attributes.STABLE in self.unit.attributes:
                return False # stable units can't be pushed
        except AttributeError:
            return False# There was no unit to push
        else: # push the unit
            destinationsquare = self.getRelSquare(direction, 1)
            try:
                self.game.board[destinationsquare].unit.takeBumpDamage() # try to have the destination unit take bump damage
            except AttributeError: # raised from None.takeBumpDamage, there is no unit there to bump into
                self.moveUnit(destinationsquare) # move the unit from this tile to destination square
            except KeyError:
                return False # raised by self.board[None], attempted to push unit off the Game, no action is taken
            else:
                self.unit.takeBumpDamage() # The destination took bump damage, now the unit that got pushed also takes damage
            return True
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
            raise InvalidDirection
        try:
            self.game.board[destinationsquare]
        except KeyError:
            return False
        return destinationsquare
    def teleport(self, destsquare):
        "Teleport from this tile to destsquare, swapping units if there is one on destsquare. This method does NOT make sure the unit is not stable!"
        assert Attributes.STABLE not in self.unit.attributes
        unitfromdest = self.game.board[destsquare].unit # grab the unit that's about to be overwritten on the destination
        self.moveUnit(destsquare) # move unit from this square to destination
        self._putUnitHere(unitfromdest)
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
        raise InvalidDirection
    def isSwallow(self):
        "return True if this tile kills non-massive non-flying units like water and chasm"
        try:
            return self._swallow
        except AttributeError:
            return False
    def __str__(self):
        return "%s at %s. Effects: %s Unit: %s" % (self.type, self.square, set(Effects.pprint(self.effects)), self.unit)

class Tile_Ground(Tile_Base):
    "This is a normal ground tile."
    def __init__(self, game, square=None, type='ground', effects=None):
        super().__init__(game, square, type, effects=effects)
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
    def __init__(self, game, square=None, type=None, effects=None):
        super().__init__(game, square, type, effects=effects)
    def applyAcid(self):
        try:
            self.unit.applyAcid() # give the unit acid if present
        except AttributeError:
            self.game.board[self.square].replaceTile(Tile_Ground(self.game, effects=(Effects.ACID,)), keepeffects=True) # Acid removes the forest/sand and makes it no longer flammable/smokable
            self.game.board[self.square].removeEffect(Effects.FIRE) # fire is put out by acid.
        # The tile doesn't get acid effects if the unit takes it instead.

class Tile_Forest(Tile_Forest_Sand_Base):
    "If damaged, lights on fire."
    def __init__(self, game, square=None, type='forest', effects=None):
        super().__init__(game, square, type, effects=effects)
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
    def __init__(self, game, square=None, type='sand', effects=None):
        super().__init__(game, square, type, effects=effects)
    def applyFire(self):
        "Fire converts the sand tile to a ground tile"
        self.game.board[self.square].replaceTile(Tile_Ground(self.game, effects=(Effects.FIRE,)), keepeffects=True)  # Acid removes the forest/sand and makes it no longer flammable/smokable
        super().applyFire()
    def _tileTakeDamage(self):
        self.applySmoke()

class Tile_Water_Ice_Damaged_Base(Tile_Base):
    "This is the base unit for Water tiles, Ice tiles, and Ice_Damaged tiles."
    def __init__(self, game, square=None, type=None, effects=None):
        super().__init__(game, square, type, effects=effects)
    def applyIce(self):
        "replace the tile with ice and give ice to the unit if present."
        if not self.hasShieldedUnit():
            self.game.board[self.square].replaceTile(Tile_Ice(self.game))
            self.game.board[self.square].removeEffect(Effects.SUBMERGED) # Remove the submerged effect from the newly spawned ice tile in case we just froze water.
        try:
            self.unit.applyIce()
        except AttributeError:
            return
    def applyFire(self):
        "Fire always removes smoke except over water and it removes acid from frozen acid tiles"
        for e in Effects.SMOKE, Effects.ACID:
            self.removeEffect(e)
        self.game.board[self.square].replaceTile(Tile_Water(self.game))
        try:
            self.unit.applyFire()
        except AttributeError:
            return
    def _spreadEffects(self):
        "there are no effects to spread from ice or damaged ice to a unit. These tiles can't be on fire and any acid on these tiles is frozen and inert, even if added after freezing."
        pass
    def repair(self, hp):
        "acid cannot be removed from water or ice by repairing it. There can't be any fire to repair either."
        try:
            self.unit.repair(hp)
        except AttributeError:
            return

class Tile_Water(Tile_Water_Ice_Damaged_Base):
    "Non-huge land units die when pushed into water. Water cannot be set on fire."
    def __init__(self, game, square=None, type='water', effects=None):
        super().__init__(game, square, type, effects=effects)
        self.effects.add(Effects.SUBMERGED)
        self._swallow = True
    def applyFire(self):
        "Water can't be set on fire"
        try: # spread the fire to the unit
            self.unit.applyFire()
        except AttributeError:
            return # but not the tile. Fire does NOT remove smoke from a water tile!
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
    def __init__(self, game, square=None, type='ice', effects=None):
        super().__init__(game, square, type, effects=effects)
    def applyIce(self):
        "Nothing happens when ice is frozen again"
        try:
            self.unit.applyIce()
        except AttributeError:
            return
    def _tileTakeDamage(self):
        self.game.board[self.square].replaceTile(Tile_Ice_Damaged(self.game))

class Tile_Ice_Damaged(Tile_Water_Ice_Damaged_Base):
    def __init__(self, game, square=None, type='ice_damaged', effects=None):
        super().__init__(game, square, type, effects=effects)
    def _tileTakeDamage(self):
        self.game.board[self.square].replaceTile(Tile_Water(self.game))

class Tile_Chasm(Tile_Base):
    "Non-flying units die when pushed into a chasm. Chasm tiles cannot have acid or fire, but can have smoke."
    def __init__(self, game, square=None, type='chasm', effects=None):
        super().__init__(game, square, type, effects=effects)
        self._swallow = True
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
        try:
            self.unit.repair(hp)
        except AttributeError:
            return

class Tile_Lava(Tile_Water):
    def __init__(self, game, square=None, type='lava', effects=None):
        super().__init__(game, square, type, effects=effects)
        self.effects.add(Effects.FIRE)
    def repair(self, hp):
        "No effects can be removed from lava from repairing on it."
        try:
            self.unit.repair(hp)
        except AttributeError:
            return
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
        self.effects.add(Effects.SMOKE) # we don't break webs here since only flying units can be on lava and no flying units can web
    def _spreadEffects(self):
        if (Attributes.MASSIVE not in self.unit.attributes) and (Attributes.FLYING not in self.unit.attributes): # kill non-massive non-flying units that went into the water.
            self.unit.die()
        else: # the unit lived
            if Attributes.FLYING not in self.unit.attributes:
                self.unit.applyFire() # lava is always on fire, now you are too!
            self.unit.removeEffect(Effects.ICE) # water and lava breaks you out of the ice no matter what

class Tile_Grassland(Tile_Base):
    "Your bonus objective is to terraform Grassland tiles into Sand. This is mostly just a regular ground tile."
    def __init__(self, game, square=None, type='grassland', effects=None):
        super().__init__(game, square, type, effects=effects)

class Tile_Terraformed(Tile_Base):
    "This tile was terraformed as part of your bonus objective. Also just a regular ground tile."
    def __init__(self, game, square=None, type='terraformed', effects=None):
        super().__init__(game, square, type, effects=effects)

class Tile_Teleporter(Tile_Base):
    "End movement here to warp to the matching pad. Swap with any present unit."
    def __init__(self, game, square=None, type='teleporter', effects=None, companion=None):
        "companion is the square of the other tile linked to this one."
        # teleporters can have smoke, fire and acid just like a normal ground tile.
        super().__init__(game, square, type, effects=effects)
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
                    self.game.board[self.companion].suppressteleport = True # suppress teleport on the companion too
                except KeyError:
                    raise MissingCompanionTile(self.type, self.square)
                self.teleport(self.companion)
        self.suppressteleport = False

##############################################################################
######################################## UNITS ###############################
##############################################################################
class Unit_Base(TileUnit_Base):
    "The base class of all units. A unit is anything that occupies a square and stops other ground units from moving through it."
    def __init__(self, game, type, hp, maxhp, effects=None, attributes=None, web=None):
        """
        game is the Game instance
        type is the name of the unit (str)
        hp is the unit's current hitpoints (int)
        maxhp is the unit's maximum hitpoints (int)
        effects is a set of effects applied to this unit. Use Effects.EFFECTNAME for this.
        attributes is a set of attributes or properties that the unit has. use Attributes.ATTRNAME for this.
        web is a set of squares with which this unit is webbed to/from
        """
        super().__init__(game=game, type=type, effects=effects)
        self.hp = hp
        self.maxhp = maxhp
        if not attributes:
            self.attributes = set()
        else:
            self.attributes = set(attributes)
        self.damage_taken = 0 # This is a running count of how much damage this unit has taken during this turn.
            # This is done so that points awarded to a solution can be removed on a unit's death. We don't want solutions to be more valuable if an enemy is damaged before it's killed. We don't care how much damage was dealt to it if it dies.
        if not web:
            self.web = set()
        else:
            self.web = set(web)
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
        self.game.board[self.square]._spreadEffects() # spread effects after freezing because flying units frozen over chasms need to die
    def applyAcid(self):
        if Effects.SUBMERGED in self.game.board[self.square].effects: # if we're in some kind of water...
            self.effects.add(Effects.ACID) # you get acid regardless of shield
        else:
            self.applyEffectUnshielded(Effects.ACID) # you only get acid if you don't have a shield.
    def applyWeb(self):
        self.effects.add(Effects.WEB)
    def applyShield(self):
        self.effects.add(Effects.SHIELD)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        """Process this unit taking damage. All effects are considered unless the ignore* flags are set in the arguments.
        Units will not die after reaching 0 hp here, run _allowDeath() to allow them to die. This is needed for vek units that can be killed and then pushed to do bump damage or spread effects.
        return False if ice or a shield blocked the damage, True otherwise."""
        # if self._blockDamage():
        #     return False
        for effect in (Effects.SHIELD, Effects.ICE): # let the shield and then ice take the damage instead if present. Frozen units can have a shield over the ice, but not the other way around.
            try:
                self.effects.remove(effect)
            except KeyError:
                pass
            else:
                self.game.board[self.square]._spreadEffects() # spread effects now that they lost a shield or ice
                return False # and then stop processing things, the shield or ice took the damage.
        if Attributes.ARMORED in self.attributes and Effects.ACID in self.effects: # if you have both armor and acid...
            pass # acid cancels out armored
        elif not ignorearmor and Attributes.ARMORED in self.attributes: # if we aren't ignoring armor and you're armored...
            damage -= 1 # damage reduced by 1
        elif not ignoreacid and Effects.ACID in self.effects: # if we're not ignoring acid and the unit has acid
            damage *= 2
        self.hp -= damage # the unit takes the damage
        self.damage_taken += damage
        return True
    def takeBumpDamage(self):
        "take damage from bumping. This is when you're pushed into something or a vek tries to emerge beneath you."
        self.takeDamage(1, ignorearmor=True, ignoreacid=True) # this is overridden by enemies that take increased bump damage by that one global powerup that increases bump damage to enemies only
    def _allowDeath(self):
        "Check if this unit was killed but had it's death supressed. Kill it now if it has 0 or less hp."
        if self.hp <= 0:  # if the unit has no more HP and is allowed to die
            self.damage_taken += self.hp  # hp is now negative or 0. Adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead.
            self.die()
    def die(self):
        "Make the unit die. This method is not ok for mechs to use as they never leave acid where they die. They leave corpses which are also units."
        self.game.board[self.square].unit = None # it's dead, replace it with nothing
        if Effects.ACID in self.effects: # units that have acid leave acid on the tile when they die:
            self.game.board[self.square].applyAcid()
        self._breakAllWebs()
        self.explode()
    def explode(self):
        "Make the unit explode only if it is explosive (to be used after death). Explosion damage ignores acid and armor."
        if Effects.EXPLOSIVE in self.effects:
            for d in Direction.gen():
                relsquare = self.game.board[self.square].getRelSquare(d, 1)
                if relsquare:
                    self.game.board[relsquare].takeDamage(1, ignorearmor=True, ignoreacid=True)
    def isBuilding(self):
        "Return True if unit is a building or objectivebuilding, False if it is not."
        try:
            return self._building
        except AttributeError:  # unit was missing the attribute
            return False
    def isMountain(self):
        "Return True if unit is a mountain, mountaindamaged, or volcano. False if it is not."
        try:
            return self._mountain
        except AttributeError:  # unit was missing the attribute
            return False
    def _makeWeb(self, compsquare, prop=True):
        """Make a web binding this unit to a unit on another square.
        compsquare is a tuple of the companion square that is also webbed with this unit.
        when prop is True, propagate this webbing to the companion.
        returns nothing
        """
        self.web.add(compsquare)
        if prop:
            self.game.board[compsquare].unit._makeWeb(self.square, prop=False)
    def _breakWeb(self, compsquare, prop=True):
        "Same as MakeWeb except we remove the web."
        self.web.remove(compsquare)
        if prop:
            self.game.board[compsquare].unit._breakWeb(self.square, prop=False)
    def _breakAllWebs(self):
        "same as breakWeb except we remove all webs that this unit has. This method doesn't use argumens and propagates by default"
        for sq in self.web:
            self.game.board[sq].unit._breakWeb(self.square, prop=False)
        self.web = set()
    def __str__(self):
        return "%s %s/%s HP. Effects: %s, Attributes: %s" % (self.type, self.hp, self.maxhp, set(Effects.pprint(self.effects)), set(Attributes.pprint(self.attributes)))

class Unit_Fighting_Base(Unit_Base):
    "The base class of all units that have at least 1 weapon."
    def __init__(self, game, type, hp, maxhp, effects=None, weapon1=None, attributes=None):
        super().__init__(game=game, type=type, hp=hp, maxhp=maxhp, effects=effects, attributes=attributes)
        try: # try to set the wielding unit of this weapon
            weapon1.wieldingunit = self
        except AttributeError: # it's none and that's fine
            pass
        else: # it worked so assign the weapon to this unit and set game.
            self.weapon1 = weapon1
            self.weapon1.game = self.game

class Unit_Repairable_Base(Unit_Fighting_Base):
    "The base class of all mechs and vek."
    def __init__(self, game, type, hp, maxhp, effects=None, weapon1=None, attributes=None):
        super().__init__(game=game, type=type, hp=hp, maxhp=maxhp, effects=effects, weapon1=weapon1, attributes=attributes)
    def repairHP(self, hp=1):
        "Repair hp amount of hp. Does not take you higher than the max. Does not remove any effects."
        self.hp += hp
        if self.hp > self.maxhp:
            self.hp = self.maxhp

class Unit_NoDelayedDeath_Base(Unit_Base):
    "A base class for units that get to bypass the hurt queues such as buildings and other neutral units."
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        res = super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
        super()._allowDeath()
        return res

##############################################################################
################################### MISC UNITS ###############################
##############################################################################
class Unit_Mountain_Building_Base(Unit_NoDelayedDeath_Base):
    "The base class for mountains and buildings. They have special properties when it comes to fire and acid."
    def __init__(self, game, type, hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.update((Attributes.STABLE, Attributes.IMMUNEFIRE))
        self.blocksbeamshot = True # this unit blocks beam shots that penetrate almost all other units.
    def applyFire(self):
        pass # mountains can't be set on fire, but the tile they're on can!

class Unit_Mountain(Unit_Mountain_Building_Base):
    def __init__(self, game, type='mountain', attributes=None, effects=None):
        super().__init__(game, type=type, hp=1, maxhp=1, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self._mountain = True
    def applyAcid(self):
        pass
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        self.game.board[self.square]._putUnitHere(Unit_Mountain_Damaged(self.game))

class Unit_Mountain_Damaged(Unit_Mountain):
    def __init__(self, game, type='mountaindamaged', effects=None):
        super().__init__(game, type=type, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        self.hp = 0 # required for PrimeSpear to detect a unit that died
        self.game.board[self.square]._putUnitHere(None)

class Unit_Volcano(Unit_Mountain):
    "Indestructible volcano that blocks movement and projectiles."
    def __init__(self, game, type='volcano', effects=None):
        super().__init__(game, type=type, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        return # what part of indestructible do you not understand?!
    def die(self):
        return # indestructible!

class Unit_Building(Unit_Mountain_Building_Base):
    def __init__(self, game, type='building', hp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self._building = True # a flag to indicate this is a building rather than do string comparisons
    def applyAcid(self):
        raise AttributeError # buildings can't gain acid, but the tile they're on can!. Raise attribute error so the tile that tried to give acid to the present unit gets it instead.

class Unit_Building_Objective(Unit_Building):
    def __init__(self, game, type='buildingobjective', hp=1, maxhp=1, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self._building = True

class Unit_Acid_Vat(Unit_NoDelayedDeath_Base):
    def __init__(self, game, type='acidvat', hp=2, maxhp=2, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def die(self):
        "Acid vats turn into acid water when destroyed."
        self._breakAllWebs()
        self.game.board[self.square]._putUnitHere(None) # remove the unit before replacing the tile otherwise we get caught in an infinite loop of the vat starting to die, changing the ground to water, then dying again because it drowns in water.
        self.game.board[self.square].replaceTile(Tile_Water(self.game, effects=(Effects.ACID,)), keepeffects=True) # replace the tile with a water tile that has an acid effect and keep the old effects
        self.game.vekemerge.remove(self.square) # don't let vek emerge from this newly created acid water tile
        self.game.board[self.square].removeEffect(Effects.FIRE) # don't keep fire, this tile can't be on fire.

class Unit_Rock(Unit_NoDelayedDeath_Base):
    def __init__(self, game, type='rock', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=1, maxhp=1, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL

############################################################################################################################
################################################### FRIENDLY Sub-Units #####################################################
############################################################################################################################
class Sub_Unit_Base(Unit_Fighting_Base):
    "The base unit for smaller sub-units that the player controls as well as objective units that the player controls.."
    def __init__(self, game, type, hp, maxhp, moves, weapon1=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.moves = moves
        self.alliance = Alliance.FRIENDLY
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        self.game.hurtplayerunits.append(self)
        return super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
    def die(self):
        self.game.playerunits.remove(self)
        super().die()

class Unit_AcidTank(Sub_Unit_Base):
    def __init__(self, game, type='acidtank', hp=1, maxhp=1, weapon1=None, moves=3, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_FreezeTank(Sub_Unit_Base):
    def __init__(self, game, type='freezetank', hp=1, maxhp=1, weapon1=None, moves=4, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_ArchiveTank(Sub_Unit_Base):
    def __init__(self, game, type='archivetank', hp=1, maxhp=1, weapon1=None, moves=4, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_OldArtillery(Sub_Unit_Base):
    def __init__(self, game, type='oldartillery', hp=1, maxhp=1, weapon1=None, moves=1, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_ShieldTank(Sub_Unit_Base):
    def __init__(self, game, type='shieldtank', hp=1, maxhp=1, weapon1=None, moves=3, effects=None, attributes=None): # shield tanks can optionally have 3 hp with a power upgrade
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_LightTank(Sub_Unit_Base):
    def __init__(self, game, type='lighttank', hp=1, maxhp=1, weapon1=None, moves=3, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_PullTank(Sub_Unit_Base):
    def __init__(self, game, type='pulltank', hp=1, maxhp=1, weapon1=None, moves=3, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

##############################################################################
################################# OBJECTIVE UNITS ############################
##############################################################################
class Unit_MultiTile_Base(Unit_Base):
    "This is the base class for multi-tile units such as the Dam and Train. Effects and damage to one unit also happens to the other."
    def __init__(self, game, type, hp, maxhp, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
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
            self.game.board[self.companion].unit.replicate = False
            try: # try running the companion's method as takeDamage() with keyword arguments
                getattr(self.game.board[self.companion].unit, meth)(damage=kwargs['damage'], ignorearmor=kwargs['ignorearmor'], ignoreacid=kwargs['ignoreacid'])
            except KeyError: # else it's an applySomething() method with no args
                #getattr(self.game.board[self.companion].unit, meth)() # this is how we used to run the companion unit's method instead of the tile's
                getattr(self.game.board[self.companion], meth)()
            self.game.board[self.companion].unit.replicate = True
    def applyIce(self):
        self.applyEffectUnshielded(Effects.ICE)
        self._replicate('applyIce')
    def applyAcid(self):
        super().applyAcid()
        self._replicate('applyAcid')
    def applyShield(self):
        super().applyShield()
        self._replicate('applyShield')
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "Process this unit taking damage. All effects are considered unless set to True in the arguments. Yes this is copypasta from the base, but we don't need to check for armored here."
        for effect in (Effects.SHIELD, Effects.ICE): # let the shield and then ice take the damage instead if present. Frozen units can have a shield over the ice, but not the other way around.
            try:
                self.effects.remove(effect)
            except KeyError:
                pass
            else:
                self.game.board[self.square]._putUnitHere(self) # put the unit here again to process effects spreading.
                return False# and then stop processing things, the shield or ice took the damage.
        if not ignoreacid and Effects.ACID in self.effects: # if we're not ignoring acid and the unit has acid
            damage *= 2
        self.hp -= damage # the unit takes the damage
        self.damage_taken += damage
        if self.hp <= 0: # if the unit has no more HP
            self.damage_taken += self.hp # hp is now negative or 0. Adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead.
            self.deadfromdamage = True
            self.die()
        self._replicate('takeDamage', damage=damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
        return True

class Unit_Dam(Unit_MultiTile_Base):
    "When the Dam dies, it floods the middle of the map."
    def __init__(self, game, type='dam', hp=2, maxhp=2, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.add(Attributes.MASSIVE)
    def _setCompanion(self):
        "Set self.companion to the square of this unit's companion."
        if self.square[1] == 4:  # set the companion tile without user intervention since the dam is always on the same 2 tiles.
            self.companion = (8, 3)
        else:
            self.companion = (8, 4)
    def die(self):
        "Make the unit die."
        self._breakAllWebs()
        self.game.board[self.square]._putUnitHere(Unit_Volcano(self.game)) # it's dead, replace it with a volcano since there is an unmovable invincible unit there.
        # we also don't care about spreading acid back to the tile, nothing can ever spread them from these tiles.
        for x in range(7, 0, -1): # spread water from the tile closest to the dam away from it
            self.game.board[(x, self.square[1])].replaceTile(Tile_Water(self.game))
            self.game.vekemerge.remove((x, self.square[1])) # don't let vek emerge from these newly created water tiles
        if not self.deadfromdamage: # only replicate death if dam died from an instadeath call to die(). If damage killed this dam, let the damage replicate and kill the other companion.
            self._replicate('die')

class Unit_Train(Unit_MultiTile_Base):
    def __init__(self, game, type='train', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.beamally = True
    def _setCompanion(self):
        "Set the train's companion tile. This has to be run each time it moves forward."
        for xoffset in -1, 1: # check the tiles ahead of and behind this one on the X axis for another train unit.
            if self.game.board[(self.square[0]+xoffset, self.square[1])].unit.type == 'train':
                self.companion = (self.square[0]+xoffset, self.square[1])

class Unit_Terraformer(Sub_Unit_Base):
    def __init__(self, game, type='terraformer', hp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.attributes.add(Attributes.STABLE)

class Unit_DisposalUnit(Unit_Terraformer):
    def __init__(self, game, type='disposalunit', hp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)

class Unit_SatelliteRocket(Sub_Unit_Base):
    def __init__(self, game, type='satelliterocket', hp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self.attributes.add(Attributes.STABLE)
        self.beamally = False

class Unit_EarthMover(Sub_Unit_Base):
    def __init__(self, game, type='earthmover', hp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self.attributes.add(Attributes.STABLE)
        self.beamally = True

class Unit_PrototypeRenfieldBomb(Unit_Base):
    def __init__(self, game, type='prototypebomb', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self.effects.add(Effects.EXPLOSIVE)
        self.attributes.add(Attributes.IMMUNEFIRE)
        self.beamally = True

class Unit_RenfieldBomb(Unit_Base):
    def __init__(self, game, type='renfieldbomb', hp=4, maxhp=4, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self.attributes.add(Attributes.IMMUNEFIRE)
        self.beamally = True
############################################################################################################################
###################################################### ENEMY UNITS #########################################################
############################################################################################################################
class Unit_Enemy_Base(Unit_Repairable_Base):
    "A base class for almost all enemies."
    def __init__(self, game, type, hp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.alliance = Alliance.ENEMY
    def die(self):
        try:
            self.game.enemyunits.remove(self) # try to remove this dead unit from enemyunits
        except KeyError: # It's possible for an enemy to "die twice" in some circumstances, e.g. when you punch a vek and push him onto a mine.
            return  # the killing damage is dealt by the weapon, but the vek isn't killed by flushHurt() yet. It lands on the mine tile first where the mine detonates and kills it, removing it from game.enemyunits
                    # if this is the case we can stop processing its death here.
        super().die()

class Unit_EnemyNonPsion_Base(Unit_Enemy_Base):
    "This is the base unit of all enemies that are not psions. Enemies have 1 weapon."
    def __init__(self, game, type, hp, maxhp, weapon1=None, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        try:
            self.weapon1.qshot = qshot
        except AttributeError:
            pass
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "Take damage like a normal unit except add it to hurtunits and don't die yet."
        self.game.hurtenemies.append(self)  # add it to the queue of units to be killed at the same time
        return super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
    def applyIce(self):
        super().applyIce()
        try: # TODO: Can we get rid of this try once every vek has a weapon?
            self.weapon1.qshot = None
        except AttributeError: # ice cancels enemy shots
            pass

class Unit_EnemyFlying_Base(Unit_EnemyNonPsion_Base):
    "A simple base unit for flying vek."
    def __init__(self, game, type, hp, maxhp, weapon1=None, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_Psion_Base(Unit_EnemyFlying_Base):
    "Base unit for vek psions. When psions are hurt, their deaths are resolved first before your mechs or other vek/bots."
    def __init__(self, game, type, hp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "Take damage like a normal unit except add it to hurtunits and don't die yet."
        self.game.hurtpsion = self
        return super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)

class Unit_EnemyBurrower_Base(Unit_EnemyNonPsion_Base):
    "A simple base class for the only 2 burrowers in the game."
    def __init__(self, game, type, hp, maxhp, weapon1=None, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.update((Attributes.BURROWER, Attributes.STABLE))

class Unit_EnemyLeader_Base(Unit_EnemyNonPsion_Base):
    "A simple base class for Massive bosses."
    def __init__(self, game, type, hp, maxhp, weapon1=None, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.MASSIVE)

class Unit_Blobber(Unit_EnemyNonPsion_Base):
    "The Blobber doesn't have a direct attack."
    def __init__(self, game, type='blobber', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_UnstableGrowths(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaBlobber(Unit_EnemyNonPsion_Base):
    "Also has no direct attack."
    def __init__(self, game, type='alphablobber', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_UnstableGuts(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Scorpion(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='scorpion', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_StingingSpinneret(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AcidScorpion(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='acidscorpion', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_StingingSpinneretAcid(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaScorpion(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphascorpion', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_GoringSpinneret(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Firefly(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='firefly', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AcceleratingThorax(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AcidFirefly(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='acidfirefly', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AcceleratingThoraxAcid(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaFirefly(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphascorpion', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_EnhancedThorax(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Leaper(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='leaper', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Fangs(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaLeaper(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphaleaper', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SharpenedFangs(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Beetle(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='beetle', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Pincers(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaBeetle(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphabeetle', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SharpenedPincers(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Scarab(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='scarab', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SpittingGlands(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaScarab(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphascarab', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AlphaSpittingGlands(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Crab(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='crab', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_ExplosiveExpulsions(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaCrab(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphacrab', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AlphaExplosiveExpulsions(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Centipede(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='centipede', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AcidicVomit(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaCentipede(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphacentipede', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_CorrosiveVomit(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Digger(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='digger', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_DiggingTusks(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaDigger(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphadigger', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AlphaDiggingTusks(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Hornet(Unit_EnemyFlying_Base):
    def __init__(self, game, type='hornet', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Stinger(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AcidHornet(Unit_EnemyFlying_Base):
    def __init__(self, game, type='acidhornet', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AcidStinger(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaHornet(Unit_EnemyFlying_Base):
    def __init__(self, game, type='alphahornet', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_LaunchingStinger(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_SoldierPsion(Unit_Psion_Base):
    def __init__(self, game, type='soldierpsion', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", effects=effects, attributes=attributes)

class Unit_ShellPsion(Unit_Psion_Base):
    def __init__(self, game, type='shellpsion', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", effects=effects, attributes=attributes)

class Unit_BloodPsion(Unit_Psion_Base):
    def __init__(self, game, type='bloodpsion', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", effects=effects, attributes=attributes)

class Unit_BlastPsion(Unit_Psion_Base):
    def __init__(self, game, type='blastpsion', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", effects=effects, attributes=attributes)

class Unit_PsionTyrant(Unit_Psion_Base):
    def __init__(self, game, type='psiontyrant', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", effects=effects, attributes=attributes)

class Unit_Spider(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='spider', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_TinyOffspring(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaSpider(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphaspider', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_LargeOffspring(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Burrower(Unit_EnemyBurrower_Base): # TODO: implement a special takeDamage() that causes the unit to burrow after taking damage
    def __init__(self, game, type='burrower', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SpikedCarapace(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaBurrower(Unit_EnemyBurrower_Base): # TODO: implement a special takeDamage() that causes the unit to burrow after taking damage
    def __init__(self, game, type='alphaburrower', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_BladedCarapace(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_BeetleLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='beetleleader', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_FlamingAbdomen(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_LargeGoo(Unit_EnemyLeader_Base):
    def __init__(self, game, type='largegoo', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_MediumGoo(Unit_EnemyLeader_Base):
    def __init__(self, game, type='mediumgoo', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_SmallGoo(Unit_EnemyLeader_Base):
    def __init__(self, game, type='smallgoo', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_HornetLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='hornetleader', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_PsionAbomination(Unit_Psion_Base):
    def __init__(self, game, type='psionabomination', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.MASSIVE)

class Unit_ScorpionLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='scorpionleader', hp=7, maxhp=7, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_FireflyLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='fireflyleader', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_SpiderLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='spiderleader', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaBlob(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphablob', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_VolatileGuts(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Blob(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='blob', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_UnstableGuts(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_SpiderlingEgg(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='spiderlingegg', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_Spiderling(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='spiderling', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaSpiderling(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphaspiderling', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_EnemyBot_Base(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type, hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)
        self.robot = True # we must identify these enemy bots as separately since they don't get vek passives.

class Unit_CannonBot(Unit_EnemyBot_Base):
    def __init__(self, game, type='cannonbot', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_CannonMech(Unit_EnemyBot_Base):
    def __init__(self, game, type='cannonmech', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_ArtilleryBot(Unit_EnemyBot_Base):
    def __init__(self, game, type='artillerybot', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_ArtilleryMech(Unit_EnemyBot_Base):
    def __init__(self, game, type='artillerymech', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_LaserBot(Unit_EnemyBot_Base):
    def __init__(self, game, type='laserbot', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_LaserMech(Unit_EnemyBot_Base):
    def __init__(self, game, type='lasermech', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_MineBot(Unit_EnemyBot_Base):
    def __init__(self, game, type='minebot', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_MineMech(Unit_EnemyBot_Base):
    def __init__(self, game, type='minemech', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_BotLeader(Unit_EnemyBot_Base):
    def __init__(self, game, type='botleader', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

class Unit_BotLeaderHard(Unit_EnemyBot_Base):
    def __init__(self, game, type='botleaderhard', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1="TODO", qshot=qshot, effects=effects, attributes=attributes)

############################################################################################################################
##################################################### FRIENDLY MECHS #######################################################
############################################################################################################################
class Unit_Mech_Base(Unit_Repairable_Base):
    "This is the base unit of Mechs."
    def __init__(self, game, type, hp, maxhp, moves, repweapon=None, weapon1=None, weapon2=None, pilot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.moves = moves # how many moves the mech has
        self.pilot = pilot # the pilot in this mech that might provide bonuses or extra abilities
        self.attributes.add(Attributes.MASSIVE) # all mechs are massive
        self.alliance = Alliance.FRIENDLY # and friendly, duh
        # repweapon is the weapon that is fired when a mech repairs itself. Every mech must have some type of repair weapon
        try:
            repweapon.wieldingunit = self
        except AttributeError:
            repweapon = Weapon_Repair()
            repweapon.wieldingunit = self
        self.repweapon = repweapon
        self.repweapon.game = self.game
        try:
            weapon2.wieldingunit = self
        except AttributeError:
            pass
        else:
            self.weapon2 = weapon2
            self.weapon2.game = self.game
    def die(self):
        "Make the mech die."
        self.hp = 0
        if self.game.board[self.square].isSwallow() and Effects.SUBMERGED not in self.game.board[self.square].effects: # if tile is a chasm
            pass # the unit is really dead, don't bother creating a mech corpse since it too will die
        else: # make a mech corpse
            self.game.board[self.square]._putUnitHere(Unit_Mech_Corpse(self.game, oldunit=self)) # it's dead, replace it with a mech corpse
        self.game.playerunits.discard(self)
    def repair(self, hp):
        "Repair the unit healing HP and removing bad effects."
        self.repairHP(hp)
        for e in (Effects.FIRE, Effects.ICE, Effects.ACID):
            self.removeEffect(e)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        res = super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
        self._allowDeath()  # mechs die right away, but explosions are delayed so the corpse actually explodes
        return res

class Unit_MechFlying_Base(Unit_Mech_Base):
    "The base class for flying mechs. Flying mechs typically have 2 hp and 4 moves."
    def __init__(self, game, type, hp=2, maxhp=2, moves=4, repweapon=None, weapon1=None, weapon2=None, pilot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, pilot=pilot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_Mech_Corpse(Unit_Mech_Base):
    "This is a player mech after it dies. It's invincible but can be pushed around. It can be repaired back to an alive mech. It has no weapons."
    def __init__(self, game, type='mechcorpse', hp=1, maxhp=1, moves=0, oldunit=None, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.oldunit = oldunit # This is the unit that died to create this corpse. You can repair mech corpses to get your mech back.
        self.attributes.add(Attributes.MASSIVE)
        self.suppressteleport = True # Mech corpses can never be teleported through a teleporter. They can be teleported by the teleport mech/weapon however
        self.game.hurtplayerunits.append(self) # this is done so the mech corpse can explode if needed
        if Passives.PSIONICRECEIVER in self.game.playerpassives and Passives.EXPLOSIVEDECAY in self.game.vekpassives:
            self.effects.add(Effects.EXPLOSIVE)
        self.game.playerunits.add(self)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "invulnerable to damage"
        return True
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
        self.game.board[self.square].createUnitHere(self.oldunit)

class Unit_Combat_Mech(Unit_Mech_Base):
    def __init__(self, game, type='combat', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Laser_Mech(Unit_Mech_Base):
    def __init__(self, game, type='laser', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Lightning_Mech(Unit_Mech_Base):
    def __init__(self, game, type='lightning', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Judo_Mech(Unit_Mech_Base):
    def __init__(self, game, type='judo', hp=3, maxhp=3, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.ARMORED)

class Unit_Flame_Mech(Unit_Mech_Base):
    def __init__(self, game, type='flame', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Aegis_Mech(Unit_Mech_Base):
    def __init__(self, game, type='aegis', hp=3, maxhp=3, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Leap_Mech(Unit_Mech_Base):
    def __init__(self, game, type='leap', hp=3, maxhp=3, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Cannon_Mech(Unit_Mech_Base):
    def __init__(self, game, type='cannon', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Jet_Mech(Unit_MechFlying_Base):
    def __init__(self, game, type='jet', hp=2, maxhp=2, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Charge_Mech(Unit_Mech_Base):
    def __init__(self, game, type='charge', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Hook_Mech(Unit_Mech_Base):
    def __init__(self, game, type='hook', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.ARMORED)

class Unit_Mirror_Mech(Unit_Mech_Base):
    def __init__(self, game, type='mirror', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Unstable_Mech(Unit_Mech_Base):
    def __init__(self, game, type='unstable', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Artillery_Mech(Unit_Mech_Base):
    def __init__(self, game, type='artillery', hp=2, maxhp=2, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Rocket_Mech(Unit_Mech_Base):
    def __init__(self, game, type='rocket', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Boulder_Mech(Unit_Mech_Base):
    def __init__(self, game, type='boulder', hp=2, maxhp=2, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Siege_Mech(Unit_Mech_Base):
    def __init__(self, game, type='siege', hp=2, maxhp=2, moves=2, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Meteor_Mech(Unit_Mech_Base):
    def __init__(self, game, type='meteor', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Ice_Mech(Unit_MechFlying_Base):
    def __init__(self, game, type='ice', hp=2, maxhp=2, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Pulse_Mech(Unit_Mech_Base):
    def __init__(self, game, type='pulse', hp=3, maxhp=3, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Defense_Mech(Unit_MechFlying_Base):
    def __init__(self, game, type='defense', hp=2, maxhp=2, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Gravity_Mech(Unit_Mech_Base):
    def __init__(self, game, type='gravity', hp=3, maxhp=3, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Swap_Mech(Unit_MechFlying_Base):
    def __init__(self, game, type='swap', hp=2, maxhp=2, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_Nano_Mech(Unit_MechFlying_Base):
    def __init__(self, game, type='nano', hp=2, maxhp=2, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_TechnoBeetle_Mech(Unit_Mech_Base):
    def __init__(self, game, type='technobeetle', hp=3, maxhp=3, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_TechnoHornet_Mech(Unit_MechFlying_Base):
    def __init__(self, game, type='technohornet', hp=2, maxhp=2, moves=4, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

class Unit_TechnoScarab_Mech(Unit_Mech_Base):
    def __init__(self, game, type='technoscarab', hp=2, maxhp=2, moves=3, pilot=None, repweapon=None, weapon1=None, weapon2=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, pilot=pilot, repweapon=repweapon, weapon1=weapon1, weapon2=weapon2, effects=effects, attributes=attributes)

##############################################################################
########################## ENVIRONMENTAL EFFECTS #############################
##############################################################################
# Environmental effects are actions performed on tiles/units after fire damage but before enemy actions. We count emerging vek as an environmental effect here even though it happens last.
class Environ_Base():
    "The base object for environmental effects."
    def __init__(self, squares, effects=None, newtile=None, removevekemerge=False):
        """squares is an iter of tiles that are affected. If they need to be done in a certain order, pass in a tuple of squares, otherwise use a set.
        effects is a tuple of strings. Each string is a method to apply on each tile in squares.
        newtile is a tile class (not object!) that will replace the tiles on squares.
        removevekemerge will remove emerging vek from self.squares if set true
        the attribute self.game is set when the Game instance initializes this object."""
        self.squares = squares
        if not effects:
            self.effects = []
        else:
            self.effects = effects
        self.newtile = newtile
        self.removevekemerge = removevekemerge
    def run(self):
        "Run the environmental effect on the Game."
        for square in self.squares:
            for effect in self.effects:
                getattr(self.game.board[square], effect)()
            if self.newtile:
                self.game.board[square].replaceTile(self.newtile(self.game))
            if self.removevekemerge:
                self.game.vekemerge.remove(square)

class Environ_IceStorm(Environ_Base):
    def __init__(self, squares):
        "Use a set of squares here."
        super().__init__(squares, effects=('applyIce',))

class Environ_AirStrike(Environ_Base):
    def __init__(self, squares):
        "Use a set of squares here."
        super().__init__(squares, effects=('_tileTakeDamage', 'die'))
    def run(self):
        super().run()
        self.game.hurtplayerunits = [] # reset all the hurt units that took damage from this since they're dead anyway.
        self.game.hurtenemies = []
        self.game.hurtpsion = None

class Environ_Tsunami(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, newtile=Tile_Water, removevekemerge=True)

class Environ_Cataclysm(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, newtile=Tile_Chasm, removevekemerge=True)
    def run(self):
        super().run()
        for square in self.squares:
            for e in Effects.FIRE, Effects.ACID: # remove fire and acid from the newly created chasm tiles as they can't have these effects.
                self.game.board[square].removeEffect(e)

class Environ_FallingRock(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, effects=('die',), newtile=Tile_Ground)

class Environ_Tentacles(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, effects=('die',), newtile=Tile_Lava, removevekemerge=True)

class Environ_LavaFlow(Environ_Base):
    def __init__(self, squares):
        "Use a tuple of squares here."
        super().__init__(squares, newtile=Tile_Lava, removevekemerge=True)

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
                if self.game.board[c].getRelSquare(self.squaresdirs[c], 1) not in self.squaresdirs: # if this square does NOT push to another square that needs to be pushed...
                    solution.append((c, self.squaresdirs.pop(c)))
                    break # start a new iter of squaresdirs since we can't iterate over something that changes
        self.squaresdirs = solution
        self.sorted = True
    def run(self):
        "Do it to it!"
        if not self.sorted:
            self.sort()
        for sqd in self.squaresdirs: # this is now a list of [((x, y), Direction.DIR), ...]
            self.game.board[sqd[0]].push(sqd[1])

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
                self.game.board[square].unit.takeBumpDamage()
            except AttributeError: # there was no unit
                pass # TODO: the vek emerges
            else:
                self.game.flushHurt() # let units that took this bump damage die
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
# all weapons must accept power1 and power2 arguments even if the weapon doesn't actually support upgrades.
# All weapons must have a shoot() method to shoot the weapon.
# All weapons must have a genShots() method to generate all possible shots the wieldingunit in its current position with this weapon can take. It must yield tuples which are arguments to the weapon's shoot() method.
    # genShots() should generate a shot to take, but not test the entire state of the board to ensure it is valid. It makes more sense to have shoot() invalidate the shot when it discovers that it's invalid.
    # That way if it is valid, we may have temporary variables ready to go for the shot and we avoided checking to see if it's valid twice.
    # The weapon should raise NullWeaponShot when it detects an invalid shot. The board should NOT be changed before NullWeaponShot is raised.
# Any weapons that deal damage must store the amount of damage as self.damage
# Any weapons that deal self damage must store the amount of damage as self.selfdamage
# Any weapons that have limited range must store their range as self.range
# Weapons with limited uses must accept the argument usesremaining=int() in __init__(). Set the number of uses left as self.usesremaining
# self.game will be set by the unit that owns the weapon.
# self.wieldingunit is the unit that owns the weapon. It will be set by the unit that owns the weapon.
# All mech weapons are assumed to be enabled whether they require power or not. If your mech has an unpowered weapon, it's totally useless to us here.

# Generator base classes:
class Weapon_DirectionalGen_Base():
    "The base class for weapons that only need a direction to be shot, like projectiles."
    def genShots(self):
        for d in Direction.gen():
            yield (d,)

class Weapon_DirectionalLimitedGen_Base():
    "A genshots for weapons that use the DirectionalGen but with limited uses."
    def genShots(self):
        for d in Direction.gen():
            if self.usesremaining:
                yield (d,)
            else:
                #raise StopIteration # doing this is wrong: https://www.python.org/dev/peps/pep-0479/
                return

class Weapon_ArtilleryGen_Base():
    "The generator for artillery weapons."
    def genShots(self, minimumdistance=2):
        """Generate every possible shot that the weapon wielder can take from their position with an artillery weapon. Yields a tuple of (direction, relativedistance) and sets self.targetsquare.
        minimumdistance is how near the wielder the weapon can shoot. Artillery weapons typically can't shoot the square next to them, but Hydraulic Legs can.
        genShots() methods usually don't take arguments, only child objects should use this argument.
        This genShots can only return valid shots by nature, no need to validate them in weapons that use this."""
        for direction in Direction.gen():
            relativedistance = minimumdistance  # artillery weapons can't shoot the tile next to them, they start at one tile past that.
            while True:
                self.targetsquare = self.game.board[self.wieldingunit.square].getRelSquare(direction, relativedistance)
                if self.targetsquare:
                    yield (direction, relativedistance)
                    relativedistance += 1
                else:  # square was false, we went off the board
                    break  # move onto the next direction

class Weapon_ArtilleryGenLimited_Base(Weapon_ArtilleryGen_Base):
    "A generator for artillery weapons that only yields shots if there is a use (ammo) available."
    def genShots(self):
        for i in super().genShots():
            if self.usesremaining:
                yield i
            else:
                return

class Weapon_NoChoiceGen_Base():
    "A generator for weapons that give you no options of how you can fire it, e.g. Repulse, Self-destruct"
    def genShots(self):
        yield ()

class Weapon_NoChoiceLimitedGen_Base():
    "A generator for weapons that give you no options of how you can fire it and also have limited uses, e.g. SmokePellets"
    def genShots(self):
        if self.usesremaining:
            yield ()

class Weapon_RangedGen_Base(Weapon_DirectionalGen_Base):
    "A generator for weapons with a limited range. The weapon must use self.range and check to make sure the destination square exists."
    def genShots(self):
        for d in super().genShots():
            for r in range(1, self.range+1):
                yield (d[0], r)

class Weapon_MirrorGen_Base():
    "A base class for weapons that shoot out of both sides of the wielder"
    def genShots(self):
        "There are only 2 possible shots here since it shoots out of both sides at once. Being in a corner can't invalidate a shot."
        yield (Direction.UP,)
        yield (Direction.RIGHT,)

class Weapon_AnyTileGen_Base():
    def genShots(self):
        "A generator that can target any square on the board."
        for x in range(1, 9):
            for y in range(1, 9):
                yield (x, y)

# Low-level shared weapon functionality:
class Weapon_hurtAndPush_Base():
    "A base class for weapons that need to hurt and push a unit."
    def _hurtAndPush(self, square, direction, damage):
        """have a tile takeDamage() from damage and get pushed.
        It's important to use this when you have to push and attack a unit at the same time, otherwise a unit could gain effects from the damaged tile it was pushed off of.
        This will raise NullWeaponShot if square is not on the board.
        This base should not be used by a weapon directly, but only by the 2 others below.
        returns nothing."""
        try: # damage the unit directly, not the tile
            if self.game.board[square].unit.takeDamage(damage):
                raise AttributeError
        except AttributeError: # there was no unit or there was an unshielded unit
            dmgtile = True
        except KeyError: # game.board[False]
            raise NullWeaponShot # invalid shot detected
        else: # The unit had a shield or ice and protected the tile
            dmgtile = False
        self.game.board[square].push(direction) # now push it
        if dmgtile:
            self.game.board[square]._tileTakeDamage() # now the tile is directly hurt after the unit's been pushed so it doesn't pick up bad effects.

class Weapon_hurtAndPushEnemy_Base(Weapon_hurtAndPush_Base):
    def _hurtAndPushEnemy(self, square, direction):
        "Hurt and push an enemy dealing self.damage damage to them."
        super()._hurtAndPush(square, direction, self.damage)

class Weapon_hurtAndPushSelf_Base(Weapon_hurtAndPush_Base):
    "A base class for weapons that need to hurt and push themselves."
    def _hurtAndPushSelf(self, square, direction):
        "have a tile takeDamage() from self.damage and get pushed. This will raise KeyError if square is not on the board."
        super()._hurtAndPush(square, direction, self.selfdamage)

class Weapon_getSquareOfUnitInDirection_Base():
    def _getSquareOfUnitInDirection(self, direction, edgeok=False, startrel=1):
        """Travel from the weapon wielder's tile in direction, returning the square of the first unit we find.
        If none is found, return False.
        If none is found and edgeok is True, return the square on the edge of the board.
        startrel is which relative tile to start on by default. Most weapons use 1, but the grappling hook can't grab a unit that's already next to it."""
        targetsquare = self.game.board[self.wieldingunit.square].getRelSquare(direction, startrel)  # start the projectile at square in direction from the unit that used the weapon...
        if not targetsquare:
            raise NullWeaponShot # the first square we tried to get was off the board, this is an invalid shot.
        while True:
            try:
                if self.game.board[targetsquare].unit:
                    return targetsquare  # found the unit
            except KeyError:  # raised from if game.board[False].unit: targetsquare being false means we never found a unit and went off the board
                if edgeok:
                    return lasttargetsquare
                return False
            lasttargetsquare = targetsquare
            targetsquare = self.game.board[targetsquare].getRelSquare(direction, 1)  # the next tile in direction of the last square

class Weapon_getRelSquare_Base():
    "A base class that provides a helper method to get the relative square from the weaponwielder"
    def _getRelSquare(self, direction, distance):
        "return the target square in direction and distance of wieldingunit. returns false if it's off the board."
        return self.game.board[self.wieldingunit.square].getRelSquare(direction, distance)

class Weapon_IncreaseDamageWithPowerInit_Base():
    "A base class that increases self.damage by 1 for each power that present. self.damage must be set by the child class first."
    def __init__(self, power1=False, power2=False):
        for p in power1, power2:
            if p:
                self.damage += 1

class Weapon_PushAdjacent_Base():
    "A base class that provides a method to push all tiles around a target."
    def _pushAdjacent(self, targetsquare):
        for d in Direction.gen(): # push all the tiles around targetsquare
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(d, 1)].push(d)
            except KeyError: # game.board[False]
                pass

class Weapon_hurtPushAdjacent_Base(Weapon_hurtAndPushEnemy_Base):
    "A base class that provides a method to hurt and push all tiles around a target."
    def _hurtPushAdjacent(self, targetsquare):
        for d in Direction.gen(): # push all the tiles around targetsquare
            try:
                self._hurtAndPushEnemy(square=self.game.board[targetsquare].getRelSquare(d, 1), direction=d)
            except (KeyError, NullWeaponShot): # raised from game.board[False] trying to hurt and push off the board or the relative square being False inside of _hurtAndPush(), just ignore it and continue
                pass

class Weapon_FartSmoke_Base(Weapon_getRelSquare_Base):
    def _fartSmoke(self, shotdirection):
        "smoke the tile behind the weapon wielder. Ignore errors if that would be off-board"
        try:
            self.game.board[self._getRelSquare(Direction.opposite(shotdirection), 1)].applySmoke()
        except KeyError: # self.game.board[False].applySmoke()
            pass # totally fine, if your butt is against the wall you just don't fart out any smoke

class Weapon_NoUpgradesInit_Base():
    "an init that ignores power upgrades passed to it for use with weapons lacking upgrade options."
    def __init__(self, power1=False, power2=False):
        pass

class Weapon_NoUpgradesLimitedInit_Base():
    "an init that ignores power upgrades passed to it for use with weapons lacking upgrade options and have a limited amount of uses."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining

class Weapon_PushProjectile_Base():
    def _pushProjectile(self, direction, targetsquare):
        "Push targetsquare all directions except for the one the shot came from."
        for d in list(Direction.genPerp(direction)) + [direction]:  # push all BUT ONE of the tiles around targetsquare. The excluded tile is the one opposite the direction of fire
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(d, 1)].push(d)
            except KeyError:  # game.board[False]
                pass

class Weapon_LimitedUnlimitedInit_Base():
    def __init__(self, power1=False, power2=False, usesremaining=1):
        "an init where power1 provides infinite uses and power2 does nothing."
        self.usesremaining = usesremaining
        if power1:
            self.usesremaining = -1 # easier than making it actually unlimited.

class Weapon_DeploySelfEffectLimitedSmall_Base():
    def shoot(self, methname):
        "A shared shoot method for weapons that deploy an effect on themselves and to tiles around the weapon wielder. methname is a string of the effect method to call like 'applySmoke'"
        self.usesremaining -= 1
        getattr(self.game.board[self.wieldingunit.square], methname)() # do the effect on yourself
        for dir in Direction.gen():
            try:
                getattr(self.game.board[self._getRelSquare(dir, 1)], methname)()
            except KeyError: # board[False]
                pass

class Weapon_DeploySelfEffectLimitedLarge_Base():
    def shoot_big(self, methname):
        "A shared shoot method for weapons that deploy an effect on themselves and to a larger area of tiles around the weapon wielder. methname is a string of the effect method to call like 'applySmoke'"
        self.usesremaining -= 1
        getattr(self.game.board[self.wieldingunit.square], methname)() # do it to yourself first
        for dir in Direction.gen():
            branchsq = self._getRelSquare(dir, 1)
            try:
                getattr(self.game.board[branchsq], methname)()
            except KeyError:  # board[False]
                continue  # if the branch square was off the board, no point in try ones further than it and next to it, continue in the next direction
            else:  # branch was valid, so now we hit one tile in the same direction and one tile clockwise of it
                for d in dir, Direction.getClockwise(dir):
                    try:
                        getattr(self.game.board[self.game.board[branchsq].getRelSquare(d, 1)], methname)()
                    except KeyError:  # board[False]
                        pass  # this is fine

# High level weapon bases:
class Weapon_Charge_Base(Weapon_DirectionalGen_Base, Weapon_hurtAndPushEnemy_Base, Weapon_getSquareOfUnitInDirection_Base):
    "The base class for charge weapons."
    def shoot(self, direction):
        "return True if we hit a unit (in case wielder needs to take self-damage) False if there was no unit and the wielder only moved."
        victimtile = self._getSquareOfUnitInDirection(direction, edgeok=False)
        try:
            self._hurtAndPushEnemy(victimtile, direction)
        except NullWeaponShot: # raised from _hurtAndPushEnemy doing self.game.board[False]... meaning there was no unit on victimtile
            self.game.board[self.wieldingunit.square].moveUnit(self.game.board[self.wieldingunit.square].getEdgeSquare(direction)) # move the wielder to victimtile which is the edge of the board
            return False
        else: # victimtile was actually a tile and we hurt and push the unit there
            self.game.board[self.wieldingunit.square].moveUnit(self.game.board[victimtile].getRelSquare(Direction.opposite(direction), 1)) # move wielder to the square before the victimsquare
            return True

#class Weapon_Artillery_Base(Weapon_ArtilleryGen_Base, Weapon_getRelSquare_Base):
class Weapon_Artillery_Base(Weapon_ArtilleryGen_Base):
    "The base class for Artillery weapons."

class Weapon_Projectile_Base(Weapon_DirectionalGen_Base, Weapon_getSquareOfUnitInDirection_Base):
    "The base class for Projectile weapons."

class Weapon_HydraulicLegsUnstableInit_Base():
    "init shared by Hydraulic Legs and Unstable Cannon."
    def __init__(self, power1=False, power2=False):
        self.selfdamage = 1
        self.damage = 1
        if power1:
            self.selfdamage += 1
            self.damage += 1
        if power2:
            self.damage += 1

class Weapon_Punch_Base():
    "shoot_punch method shared by TitanFist, RocketFist, and MantisSlash"
    def shoot_punch(self, direction):
        self._hurtAndPushEnemy(self.game.board[self.wieldingunit.square].getRelSquare(direction, 1), direction)

class Weapon_RangedAttack_Base(Weapon_RangedGen_Base, Weapon_hurtAndPushEnemy_Base, Weapon_getRelSquare_Base):
    "A base class for weapons that attack in a limited range and push the last square like NeedleShot and PrimeSpear. FlameThrower is too special to use this."
    def shoot(self, direction, distance):
        "returns a tuple of (unit, square) where unit is the unit that was pushed from the last square, square is that square that was hit."
        hitsquares = []  # a list of squares to damage. Build the list first so we can determine if this is an invalid shot
        for r in range(1, distance + 1):
            targetsquare = self._getRelSquare(direction, r)
            if not targetsquare:
                raise NullWeaponShot  # bail since this shot was already taken with less distance
            hitsquares.append(targetsquare)
        # Now we know this is a valid shot.
        for targetsquare in hitsquares[:-1]:  # don't actually damage the last square
            self.game.board[targetsquare].takeDamage(self.damage)
        pushedunit = self.game.board[hitsquares[-1]].unit
        self._hurtAndPushEnemy(hitsquares[-1], direction)  # and finally hurtAndPush the last tile
        return (pushedunit, hitsquares[-1])

class Weapon_TemperatureBeam_Base(Weapon_DirectionalLimitedGen_Base):
    "A base class for both the FireBeam and FrostBeam."
    def __init__(self, power1=False, power2=False, usesremaining=1, effectmeth=None):
        "effectmeth must be a string of either applyFire or applyIce"
        self.usesremaining = usesremaining # power1 and 2 ignored for this weapon
        self.effectmeth = effectmeth
    def shoot(self, direction):
        currenttarget = self.game.board[self.wieldingunit.square].getRelSquare(direction, 1)
        if not currenttarget: # first square attacked was offboard and therefor
            raise NullWeaponShot
        self.usesremaining -= 1
        while True:
            try:
                getattr(self.game.board[currenttarget], self.effectmeth)()
            except KeyError: # board[False]
                return # went off the board, we lit everything up
            try:
                if self.game.board[currenttarget].unit.isBuilding() or self.game.board[currenttarget].unit.isMountain():
                    return # buildings and mountains end the shot
            except AttributeError: # None.isBuilding()
                pass # continue on
            currenttarget = self.game.board[currenttarget].getRelSquare(direction, 1)

class Weapon_Deployable_Base(Weapon_ArtilleryGenLimited_Base):
    "methods shared by weapons that deploy small tanks"
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.hp = 1 # the deployed tank's HP
        if power1:
            self.hp += 2
        self.power2 = power2 # this is passed onto the deployed tank's weapon
    def genShots(self):
        "A genshots for limited deployable tanks that doesn't allow you to shoot into swallowing tiles and immediately kill your deployable."
        for i in super().genShots():
            if not self.game.board[self.targetsquare].isSwallow():
                yield i
    def shoot(self, unit): # this should only ever be called by child objects so the non-standard arg should be fine
        if self.game.board[self.targetsquare].unit:
            raise NullWeaponShot # can't deploy a tank to an occupied square
        self.usesremaining -= 1
        self.game.board[self.targetsquare].createUnitHere(unit)

class Weapon_AcidGun_Base(Weapon_Projectile_Base):
    "Shared shoot method for AcidProjector and AcidShot"
    def shoot(self, direction, push=True):
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=True)
        try:
            if self.game.board[targetsquare].unit.isMountain():
                raise NullWeaponShot # Mountains can't get acid and don't leave any on the ground after being destroyed
        except AttributeError: # there was no unit
            self.game.board[targetsquare].applyAcid() # give it to the tile instead
        else: # unit needs to be hit with acid
            self.game.board[targetsquare].unit.effects.add(Effects.ACID)  # directly give the unit acid, ice and shield won't prevent you from getting acid unlike when you move to an acid pool.
            if push:
                self.game.board[targetsquare].push(direction) # now push the unit

##################### Actual standalone weapons #####################
class Weapon_TitanFist(Weapon_Charge_Base, Weapon_Punch_Base):
    """Combat mech's default weapon.
    Dashing does not damage the edge tile if it doesn't come in contact with a unit like projectiles do."""
    def __init__(self, power1=False, power2=False):
        super().__init__()
        if not power1: # Weapon_Charge_Base already has self.shoot set to the charge attack
            self.shoot = self.shoot_punch
        if power2: # increase damage by 2
            self.damage = 4
        else: # it's 2 by default
            self.damage = 2

class Weapon_TaurusCannon(Weapon_Projectile_Base, Weapon_hurtAndPushEnemy_Base, Weapon_IncreaseDamageWithPowerInit_Base):
    "Cannon Mech's default weapon."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        super().__init__(power1, power2)
    def shoot(self, direction):
        self._hurtAndPushEnemy(self._getSquareOfUnitInDirection(direction, edgeok=True), direction)

class Weapon_ArtemisArtillery(Weapon_Artillery_Base, Weapon_PushAdjacent_Base):
    "Artillery Mech's default weapon."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self._buildingsimmune = True
        else:
            self._buildingsimmune = False
        if power2:
            self.damage += 2
    def shoot(self, direction, distance):
        "Shoot in direction distance number of tiles. Artillery can never shoot 1 tile away from the wielder."
        if self._buildingsimmune and self.game.board[self.targetsquare].unit.isBuilding():
           pass
        else:
            self.game.board[self.targetsquare].takeDamage(self.damage)
        self._pushAdjacent(self.targetsquare) # now push all the tiles around targetsquare

class Weapon_BurstBeam(Weapon_DirectionalGen_Base):
    """Laser Mech's default weapon.
    If ally immune is powered and you have a friendly on a forest tile, the forest tile does NOT ignite from damage when you shoot.
    If ally immune is powered, it will not hurt *some* objective units like:
        terraformer
        earth mover
        archive tank
        train
        prototype renfield bombs
        normal renfield bombs
        earth mover
        acid launcher
    The following friendly units DO take damage from the beam:
        satellite rocket
        acid vat
        dam"""
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
        try:
            targettile = self.game.board[self.game.board[self.wieldingunit.square].getRelSquare(direction, relsquare)]  # get the target tile, not square
        except KeyError:  # self.game.board[False] means we went off the board
            raise NullWeaponShot
        while True:
            if self.allyimmune and self.isBeamAlly(targettile.unit):
                pass # no damage
            else:
                targettile.takeDamage(currentdamage) # damage the tile
            if self.blocksBeamShot(targettile.unit): # no more pew pew
                break
            if currentdamage != 1:
                currentdamage -= 1
            relsquare += 1
            try:
                targettile = self.game.board[self.game.board[self.wieldingunit.square].getRelSquare(direction, relsquare)] # get the target tile, not square
            except KeyError: # self.game.board[False] means we went off the board
                break # no more pew pew
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
        if super().shoot(direction):
            self.game.board[self.wieldingunit.square].takeDamage(self.selfdamage)

class Weapon_AttractionPulse(Weapon_DirectionalGen_Base, Weapon_getSquareOfUnitInDirection_Base):
    "Defense Mech's first default primary weapon."
    def __init__(self, power1=False, power2=False):
        pass # this weapon has no power upgrades
    def shoot(self, direction):
        try:
            self.game.board[self._getSquareOfUnitInDirection(direction, edgeok=False)].push(Direction.opposite(direction))
        except KeyError: # raised by self.game.board[False]...
            raise NullWeaponShot

class Weapon_ShieldProjector(Weapon_ArtilleryGenLimited_Base, Weapon_getRelSquare_Base): # does not use the artillery base since we need the limited generator
    "The default second weapon for the Defense Mech."
    def __init__(self, power1=False, power2=False, usesremaining=2):
        self.usesremaining = usesremaining
        # power1 adds another use, but we ignore that here because this simulation could be in the middle of a map where usesremaining could be anything.
        # if we increment it by one because they have it powered we could be giving the weapon a use that it doesn't really have.
        # This weapon should always be initialized with usesremaining set to how many uses are actually remaining for the player at the time of the simulation.
        if power2:
            self.bigarea = True
        else:
            self.bigarea = False
    def shoot(self, direction, distance):
        self.usesremaining -= 1
        self.game.board[self.targetsquare].applyShield() # the target tile itself is shielded
        if self.bigarea:
            for d in Direction.gen(): # do all tiles around the target if we have the +3 area upgrade
                try:
                    self.game.board[self.game.board[self.targetsquare].getRelSquare(d, 1)].applyShield()
                except KeyError:
                    pass # tried to shield off the board
        else:
            try:
                self.game.board[self.game.board[self.targetsquare].getRelSquare(direction, 1)].applyShield() # just shield one tile past the target in the same direction
            except KeyError:
                pass # tried to shield off the board

class Weapon_ViceFist(Weapon_getRelSquare_Base, Weapon_DirectionalGen_Base):
    "The default weapon for the Judo mech"
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self.allyimmune = True
        else:
            self.allyimmune = False
        if power2:
            self.damage += 2
    def shoot(self, direction):
        destsquare = self._getRelSquare(Direction.opposite(direction), 1) # where the tossed unit lands
        try:
            if self.game.board[destsquare].unit: # can't toss a unit to an occupied tile
                raise NullWeaponShot
        except AttributeError: # False.unit, square was invalid
            raise NullWeaponShot
        targetsquare = self._getRelSquare(direction, 1) # the tile where the victim is grabbed
        try:
            if Attributes.STABLE in self.game.board[targetsquare].unit.attributes: # if target unit is stable...
                raise NullWeaponShot # we can't toss it
        except (KeyError, AttributeError):  # either the target square was off the board or there was no unit
            raise NullWeaponShot
        # now that we're here, we're sure we have a valid shot
        self.game.board[targetsquare].moveUnit(destsquare) # move the unit from the attack direction to the other side of the wielder
        try:
            if self.allyimmune and self.game.board[destsquare].unit.alliance == Alliance.FRIENDLY:
                pass # no damage to friendlies if allies are immune
            else:
                self.game.board[destsquare].takeDamage(self.damage)
        except AttributeError: # raised from None.alliance. This happens when you throw the unit into a chasm or such and it immediately dies
            pass # unit died, no point in damaging the tile that killed it.

class Weapon_ClusterArtillery(Weapon_Artillery_Base, Weapon_hurtAndPushEnemy_Base):
    "Default weapon for Siege Mech."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self._buildingsimmune = True
        else:
            self._buildingsimmune = False
        if power2:
            self.damage += 1
    def shoot(self, direction, distance):
        for d in Direction.gen(): # self.targetsquare indicates where the shot landed. Nothing actually happens on this tile for this weapon, it's all around it instead.
            currenttargetsquare = self.game.board[self.targetsquare].getRelSquare(d, 1) # set the square we're working on
            try:
                if self._buildingsimmune and self.game.board[currenttargetsquare].unit.isBuilding(): # if buildings are immune and the unit taking damage is a building...
                    pass # don't damage it
                else: # there was a unit and it was not a building or there was a building that's not immune
                    self._hurtAndPushEnemy(currenttargetsquare, d)
            except (KeyError, AttributeError): # KeyError raised from currentsquare being False, self.game.board[False]. AttributeError raised from None.isBuilding()
                pass # this square was off the board

class Weapon_GravWell(Weapon_Artillery_Base):
    "Default first weapon for Gravity Mech"
    def __init__(self, power1=False, power2=False):
        pass # grav well can't be upgraded at all
    def shoot(self, direction, distance):
        self.game.board[self.targetsquare].push(Direction.opposite(direction))

# TODO Weapon_VekHormones()

class Weapon_SpartanShield(Weapon_DirectionalGen_Base, Weapon_getRelSquare_Base):
    "Default weapon of the Aegis Mech"
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        if power1:
            self.gainshield = True
        else:
            self.gainshield = False
        if power2:
            self.damage += 1
    def shoot(self, direction):
        targetsquare = self._getRelSquare(direction, 1)
        try:
            self.game.board[targetsquare].takeDamage(self.damage)
        except KeyError: # board[False]
            raise NullWeaponShot
        try:
            self.game.board[targetsquare].unit.weapon1.flip()
        except AttributeError: # None.weapon1 or weapon1.flip() where flip doesn't exist like a friendly
            pass
        if self.gainshield:
            self.wieldingunit.applyShield()

class Weapon_JanusCannon(Weapon_getSquareOfUnitInDirection_Base, Weapon_hurtAndPushEnemy_Base, Weapon_IncreaseDamageWithPowerInit_Base, Weapon_MirrorGen_Base):
    "Default weapon for Mirror Mech"
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        super().__init__(power1, power2)
    def shoot(self, direction):
        for d in direction, Direction.opposite(direction):
            self._hurtAndPushEnemy(self._getSquareOfUnitInDirection(d, edgeok=True), d)

class Weapon_CryoLauncher(Weapon_Artillery_Base):
    "Default weapon for the Ice mech"
    def __init__(self, power1=False, power2=False):
        pass # cryolauncher doesn't take power
    def shoot(self, direction, distance):
        "Shoot in direction distance number of tiles. Artillery can never shoot 1 tile away from the wielder."
        self.game.board[self.targetsquare].applyIce() # freeze the target
        self.game.board[self.wieldingunit.square].applyIce() # freeze yourself (the square you're on)

class Weapon_AerialBombs(Weapon_getRelSquare_Base, Weapon_RangedGen_Base):
    "Default weapon for the Jet mech."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        self.range = 1 # how many tiles you can jump over and damage. Unit lands on the tile after this distance.
        if power1:
            self.damage += 1
        if power2:
            self.range += 1
    def shoot(self, direction, distance):
        "distance is the number of squares to jump over and damage. The wielder lands on one square past distance."
        destsquare = self._getRelSquare(direction, distance+1)
        try:
            if self.game.board[destsquare].unit:
                raise NullWeaponShot # can't land on an occupied square
        except AttributeError: # landing spot was off the board
            raise NullWeaponShot
        targetsquare = self.wieldingunit.square # start where the unit is
        for r in range(distance):
            targetsquare = self.game.board[targetsquare].getRelSquare(direction, 1)
            self.game.board[targetsquare].takeDamage(self.damage) # damage the target
            self.game.board[targetsquare].applySmoke() # smoke the target
        self.game.board[self.wieldingunit.square].moveUnit(self.game.board[targetsquare].getRelSquare(direction, 1)) # move the unit to its landing position 1 square beyond the last attack

class Weapon_RocketArtillery(Weapon_Artillery_Base, Weapon_IncreaseDamageWithPowerInit_Base, Weapon_hurtAndPushEnemy_Base, Weapon_FartSmoke_Base):
    "Default weapon for the Rocket mech"
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        super().__init__(power1, power2)
    def shoot(self, direction, distance):
        self._hurtAndPushEnemy(self.targetsquare, direction)
        self._fartSmoke(direction)

class Weapon_Repulse(Weapon_NoChoiceGen_Base, Weapon_getRelSquare_Base):
    "Default weapon for Pulse mech"
    def __init__(self, power1=False, power2=False):
        if power1:
            self.shieldself = True
        else:
            self.shieldself = False
        if power2:
            self.shieldally = True
        else:
            self.shieldally = False
    def shoot(self):
        if self.shieldself:
            self.wieldingunit.applyShield()
        for d in Direction.gen():
            targetsquare = self._getRelSquare(d, 1)
            try:
                targetunit = self.game.board[targetsquare].unit
            except KeyError: # self.game.board[False]
                continue # targetsquare was invalid, move on
            else: # targetsquare is a valid square on the board
                if self.shieldally and (targetunit.alliance == Alliance.FRIENDLY or targetunit.isBuilding()): # try to shield allies if needed
                    targetunit.applyShield()
                self.game.board[targetsquare].push(d)

class Weapon_ElectricWhip(Weapon_DirectionalGen_Base):
    """This is the lightning mech's default weapon.
    When building chain is not powered (power1), you cannot hurt buildings or chain through them with this at all.
    It does not go through mountains or supervolcano either. It does go through rocks.
    Cannot attack mines on the ground.
    Reddit said you can attack a building if it's webbed, this is not true. Even if you attack the scorpion webbing the building, the building won't pass the attack through or take damage.
    When you chain through units that are explosive, they explode in the reverse order in which they were shocked. # TODO: this is true and not implemented!
    You can never chain through yourself when you shoot!"""
    def __init__(self, power1=False, power2=False):
        if power1:
            self._buildingchain = True
        else:
            self._buildingchain = False
        if power2:
            self.damage = 3
        else:
            self.damage = 2
    def shoot(self, direction):
        self.hitsquares = [False, self.wieldingunit.square]  # squares that have already been hit so we don't travel back through them in circles.
        # False is included because getRelSquare will return False when you go off the board. We can use this in the branching logic to tell it that anything off the board has been visited.
        # we also include the unit that shot the weapon since you can NEVER chain through yourself!
        self.branchChain(backwards=Direction.opposite(direction), targetsquare=self.game.board[self.wieldingunit.square].getRelSquare(direction, 1))
        if len(self.hitsquares) == 2: # if histsquares never grew, that means that the first shot was invalid
            raise NullWeaponShot
        # done with the recursive method, now skip False and and the wielder's square and make all the units that need to take damage take damage
        for hs in self.hitsquares[2:]:
            if not self.game.board[hs].unit.isBuilding(): # don't damage buildings. If they're here they're already not effected.
                self.game.board[hs].takeDamage(self.damage)
    def unitIsChainable(self, unit):
        "Pass a unit to this method and it will return true if you can chain through it, false if not or if there is no unit."
        try:
            if (self._buildingchain and unit.isBuilding()) or \
                    (self._buildingchain and not unit.isMountain()) or \
                     (not unit.isMountain() and not unit.isBuilding()):
                return True
        except AttributeError:
            pass
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
            nextsquare = self.game.board[targetsquare].getRelSquare(d, 1)
            if nextsquare in self.hitsquares:
                continue
            if self.unitIsChainable(self.game.board[nextsquare].unit):
                self.branchChain(backwards=Direction.opposite(d), targetsquare=nextsquare)

class Weapon_GrapplingHook(Weapon_getSquareOfUnitInDirection_Base, Weapon_DirectionalGen_Base):
    "Default weapon for Hook Mech"
    def __init__(self, power1=False, power2=False):
        if power1:
            self.shieldally = True
        else:
            self.shieldally = False
        # power2 is unused
    def shoot(self, direction):
        try: # first check for a unit right next to us
            if self.game.board[self.game.board[self.wieldingunit.square].getRelSquare(direction, 1)].unit:
                raise NullWeaponShot
        except KeyError: #board[False], this square is off the board which is also a
            raise NullWeaponShot
        try:
            targetunit = self.game.board[self._getSquareOfUnitInDirection(direction, startrel=2)].unit
        except KeyError: # board[False], there was no unit to grapple
            raise NullWeaponShot
        if Attributes.STABLE in targetunit.attributes:
            self.game.board[self.wieldingunit.square].moveUnit( self.game.board[targetunit.square].getRelSquare(Direction.opposite(direction), 1) ) # move the weapon wielder next to the stable unit it just grappled
        else: # unit is not stable
            self.game.board[targetunit.square].moveUnit( self.game.board[self.wieldingunit.square].getRelSquare(direction, 1) ) # move the targetunit next to the wielder
        if self.shieldally and (Alliance.FRIENDLY == targetunit.alliance or targetunit.isBuilding()):
            targetunit.applyShield()

class Weapon_RockLauncher(Weapon_Artillery_Base, Weapon_IncreaseDamageWithPowerInit_Base):
    "Default weapon for Boulder Mech"
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        super().__init__(power1, power2)
    def shoot(self, direction, distance):
        if self.game.board[self.targetsquare].unit: # the tile only takes damage if a unit is present
            self.game.board[self.targetsquare].takeDamage(self.damage) # target takes damage
        else: # otherwise we just place a rock there
            self.game.board[self.targetsquare]._putUnitHere(Unit_Rock(self.game))
        for d in Direction.genPerp(direction):
            try:
                self.game.board[self.game.board[self.targetsquare].getRelSquare(d, 1)].push(d)
            except KeyError:
                pass # tried to push off the board

class Weapon_FlameThrower(Weapon_getRelSquare_Base, Weapon_RangedGen_Base):
    "Default weapon for Flame Mech"
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        self.range = 1
        for p in power1, power2:
            if p:
                self.range += 1
    def shoot(self, direction, distance):
        hotsquares = [] # a list of squares to damage. Build the list first so we can determine if this is an invalid shot
        for r in range(1, distance+1):
            targetsquare = self._getRelSquare(direction, r)
            try:
                if self.game.board[targetsquare].unit.isMountain() and r < self.range: # if the unit on the targetsquare is a mountain (which stops flamethrower from going through it) and there was range remaining...
                    raise NullWeaponShot  # bail since this shot was already taken with less range
            except KeyError: # board[False]
                raise NullWeaponShot
            except AttributeError: # None.isMountain(), there was no unit
                pass
            hotsquares.append(targetsquare)
        # Now we know this is a valid shot.
        for targetsquare in hotsquares:
            try: # unit takes damage if it was already on fire
                if Effects.FIRE in self.game.board[targetsquare].unit.effects:
                    raise FakeException
            except FakeException: # The unit was on fire
                self.game.board[targetsquare].unit.takeDamage(self.damage) # damage the unit only, not the tile!
            except AttributeError: # None.effects, there was no unit
                pass
            self.game.board[targetsquare].applyFire() # light it up
        self.game.board[targetsquare].push(direction) # and finally push the last tile

#class Weapon_FlameShielding(): # passive for later

class Weapon_VulcanArtillery(Weapon_Artillery_Base, Weapon_PushAdjacent_Base, Weapon_getRelSquare_Base):
    "Default Weapon for Meteor Mech"
    def __init__(self, power1=False, power2=False):
        if power1:
            self.backburn = True
        else:
            self.backburn = False
        if power2:
            self.damage = 2
            self.shoot = self.shoot_damage
        else:
            self.shoot = self.shoot_nodamage
    def shoot_damage(self, direction, distance):
        self.shoot_nodamage(direction, distance)
        self.game.board[self.targetsquare].takeDamage(self.damage)
    def shoot_nodamage(self, direction, distance):
        "This shoot method doesn't cause any damage to the tile or unit."
        self.game.board[self.targetsquare].applyFire()
        self._pushAdjacent(self.targetsquare)
        if self.backburn:
            try:
                self.game.board[self._getRelSquare(Direction.opposite(direction), 1)].applyFire()
            except KeyError:  # self.game.board[False].applyFire()
                pass  # totally fine, if your butt is against the wall you just don't fart out any fire

class Weapon_Teleporter(Weapon_RangedGen_Base, Weapon_getRelSquare_Base):
    "Default weapon for Swap Mech"
    def __init__(self, power1=False, power2=False):
        self.range = 1
        if power1:
            self.range += 1
        if power2:
            self.range += 2
    def shoot(self, direction, distance):
        targetsquare = self._getRelSquare(direction, distance)
        try:
            if Attributes.STABLE in self.game.board[targetsquare].unit.attributes: # can't teleport stable units
                raise NullWeaponShot
        except KeyError: # tried to teleport off the board
            raise NullWeaponShot
        except AttributeError: # there was no unit to check for stability
            pass
        self.game.board[self.wieldingunit.square].teleport(targetsquare)

class Weapon_HydraulicLegs(Weapon_Artillery_Base, Weapon_HydraulicLegsUnstableInit_Base, Weapon_hurtPushAdjacent_Base):
    "The default weapon for Leap Mech"
    def genShots(self):
        return super().genShots(minimumdistance=1)
    def shoot(self, direction, distance):
        if self.game.board[self.targetsquare].unit:
            raise NullWeaponShot # the tile you're leaping to must be clear of units
        self.game.board[self.wieldingunit.square].moveUnit(self.targetsquare) # move the wielder first
        self.game.board[self.wieldingunit.square].takeDamage(self.selfdamage) # then the wielder takes damage on the new tile
        self._hurtPushAdjacent(self.targetsquare)

class Weapon_UnstableCannon(Weapon_HydraulicLegsUnstableInit_Base, Weapon_Projectile_Base, Weapon_hurtAndPushEnemy_Base, Weapon_hurtAndPushSelf_Base):
    "Default weapon for the Unstable Mech"
    def __init__(self, power1=False, power2=False):
        super().__init__(power1, power2)
        self.damage += 1 # unstable cannon does 1 more damage by default
    def shoot(self, direction):
        self._hurtAndPushSelf(self.wieldingunit.square, Direction.opposite(direction)) # take self-damage first and push back
        self._hurtAndPushEnemy(self._getSquareOfUnitInDirection(direction, edgeok=True), direction)

class Weapon_AcidProjector(Weapon_AcidGun_Base):
    "Default weapon for the Acid Mech"
    def __init__(self, power1=False, power2=False):
        pass # this weapon can't be upgraded
    def shoot(self, direction):
        super().shoot(direction)

class Weapon_RammingSpeed(Weapon_Charge_Base, Weapon_FartSmoke_Base):
    "Default weapon for the TechnoBeetle"
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self.shoot = self.shoot_smoke
        if power2:
            self.damage += 2
    def shoot_smoke(self, direction):
        super().shoot(direction)
        self._fartSmoke(direction)

class Weapon_NeedleShot(Weapon_RangedAttack_Base):
    "Default weapon for the TechnoHornet"
    def __init__(self, power1=False, power2=False):
        self.range = 1
        self.damage = 1
        for p in power1, power2:
            if p:
                self.range += 1
                self.damage += 1

class Weapon_ExplosiveGoo(Weapon_Artillery_Base, Weapon_PushAdjacent_Base):
    "Default weapon for the TechnoScarab"
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self.shoot = self.shoot_2tiles
        if power2:
            self.damage += 2
    def shoot(self, direction, distance):
        "This is the ExplosiveGoo's shot when it only affects 1 tile, very simple."
        self.game.board[self.targetsquare].takeDamage(self.damage)
        self._pushAdjacent(self.targetsquare)  # now push all the tiles around targetsquare
    def shoot_2tiles(self, direction, distance):
        self.game.board[self.targetsquare].takeDamage(self.damage)
        extrasquare = self.game.board[self.targetsquare].getRelSquare(direction, 1) # set the 2nd square
        try: # try to damage one tile past the target
            self.game.board[extrasquare].takeDamage(self.damage)
        except KeyError: # board[False]; the extra shot was wasted which is fine
            self._pushAdjacent(self.targetsquare)  # just push all the tiles around targetsquare, one of them will be off board
        else: # The tile exists and now we have to push all tiles around BOTH
            for d in list(Direction.genPerp(direction)) + [Direction.opposite(direction)]: # push all BUT ONE of the tiles around targetsquare. The excluded tile is the one in the direction of fire
                try:
                    self.game.board[self.game.board[self.targetsquare].getRelSquare(d, 1)].push(d)
                except KeyError:  # game.board[False]
                    pass
            for d in list(Direction.genPerp(direction)) + [direction]: # push all BUT ONE of the tiles around targetsquare. The excluded tile is the one opposite the direction of fire
                try:
                    self.game.board[self.game.board[extrasquare].getRelSquare(d, 1)].push(d)
                except KeyError:  # game.board[False]
                    pass

################ Non-default weapons
class Weapon_SidewinderFist(Weapon_RangedGen_Base, Weapon_hurtAndPushEnemy_Base, Weapon_getRelSquare_Base, Weapon_IncreaseDamageWithPowerInit_Base):
    "Punch an adjacent tile, damaging and pushing it to the left."
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        self.range = 1
        super().__init__(power1, power2)
        if power1 and power2:
            self.range += 1 # you get an extra range when both damage upgrades are powered?! wtf the description doesn't mention this!
    def shoot(self, direction, distance):
        targetsquare = self._getRelSquare(direction, distance)
        self._hurtAndPushEnemy(targetsquare, Direction.getCounterClockwise(direction)) # raises NullWeaponShot if targetsquare is False
        if distance == 2: # if we used the extra distance, move the wielder to the square next to the target similar to a charge
            self.game.board[self.wieldingunit.square].moveUnit(self._getRelSquare(direction, 1))

class Weapon_RocketFist(Weapon_hurtAndPushEnemy_Base, Weapon_Projectile_Base, Weapon_Punch_Base):
    "Punch an adjacent tile. Upgrades to launch as a projectile"
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        if power1:
            self.shoot = self.shoot_projectile
        else:
            self.shoot = self.shoot_punch
        if power2:
            self.damage += 2
    def shoot_punch(self, direction): # the default shoot method for punching only
        super().shoot_punch(direction)
        self._pushSelfBackwards(direction)
    def shoot_projectile(self, direction):
        self._hurtAndPushEnemy(self._getSquareOfUnitInDirection(direction, edgeok=True), direction)
        self._pushSelfBackwards(direction)
    def _pushSelfBackwards(self, shotdirection):
        "push yourself backwards"
        self.game.board[self.wieldingunit.square].push(Direction.opposite(shotdirection))

class Weapon_ExplosiveVents(Weapon_NoChoiceGen_Base, Weapon_IncreaseDamageWithPowerInit_Base, Weapon_hurtPushAdjacent_Base):
    "Blast all adjacent tiles."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        super().__init__(power1, power2)
    def shoot(self):
        self._hurtPushAdjacent(self.wieldingunit.square)

class Weapon_PrimeSpear(Weapon_RangedAttack_Base):
    "Stab multiple tiles and push the furthest hit tile."
    def __init__(self, power1=False, power2=False):
        self.range = 2
        self.damage = 2
        if power1:
            self.acidtip = True
        else:
            self.acidtip = False
        if power2:
            self.range += 1
    def shoot(self, direction, distance):
        pushedunit, targetsquare = super().shoot(direction, distance)
        if self.acidtip:
            try:
                pushedunit.applyAcid()
            except AttributeError: # None.applyAcid()
                self.game.board[targetsquare].applyAcid() # just the tile gets acid
            else: # the pushed unit got acid
                if pushedunit.hp < 1: # if the unit that just got acid is going to die...
                    self.game.board[targetsquare].applyAcid() # then also give acid to the square it was pushed from. This seems like a bug in the game that if a unit that gets acid dies, the tile it was hit on also gets acid.

class Weapon_VortexFist(Weapon_NoChoiceGen_Base, Weapon_hurtAndPushEnemy_Base):
    "Damage and push all adjacent tiles to the left."
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        self.selfdamage = 2
        if power1:
            self.selfdamage -= 1
        if power2:
            self.damage += 1
    def shoot(self):
        for direction in Direction.gen():
            try:
                self._hurtAndPushEnemy(self.game.board[self.wieldingunit.square].getRelSquare(direction, 1), Direction.getCounterClockwise(direction))
            except NullWeaponShot: # raised from hurtAndPushEnemy going off-board
                pass
        self.game.board[self.wieldingunit.square].takeDamage(self.selfdamage)

class Weapon_TitaniteBlade(Weapon_DirectionalLimitedGen_Base, Weapon_hurtAndPushEnemy_Base, Weapon_getRelSquare_Base):
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.damage = 2
        # power1 adds another use, but we ignore that here because this simulation could be in the middle of a map where usesremaining could be anything.
        if power2:
            self.damage += 2
    def shoot(self, direction):
        targetsquare = self._getRelSquare(direction, 1)
        self._hurtAndPushEnemy(targetsquare, direction) # If this is off board, NullWeaponShot is raised
        self.usesremaining -= 1 # this was a valid shot, so now let's spend the use
        for perpdir in Direction.genPerp(direction):
            try:
                self._hurtAndPushEnemy(self.game.board[targetsquare].getRelSquare(perpdir, 1), direction)
            except NullWeaponShot: # it's ok if the 2 tiles next to the main target tile are off the board, the damage is just wasted
                pass
class Weapon_MercuryFist(Weapon_DirectionalLimitedGen_Base, Weapon_getRelSquare_Base):
    "Smash the ground, dealing huge damage and pushing adjacent tiles."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.damage = 4
        if power2: # power1 gives another use and is ignored here
            self.damage += 1
    def shoot(self, direction):
        targetsquare = self._getRelSquare(direction, 1)
        try:
            self.game.board[targetsquare].takeDamage(self.damage)
        except KeyError: # target is off board and invalid
            raise NullWeaponShot
        self.usesremaining -= 1 # shot is now valid, spend the ammo
        for d in [direction] + list(Direction.genPerp(direction)):
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(d, 1)].push(d)
            except KeyError: # board[False]
                pass # ok that this went off board

class Weapon_PhaseCannon(Weapon_DirectionalGen_Base, Weapon_hurtAndPushEnemy_Base):
    "Shoot a projectile that phases through objects."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self.phaseshield = True
        else:
            self.phaseshield = False
        if power2:
            self.damage += 1
    def shoot(self, direction):
        targetsquare = self.game.board[self.wieldingunit.square].getRelSquare(direction, 1) # start the projectile at square in direction from the unit that used the weapon...
        if not targetsquare:
            raise NullWeaponShot # the first square we tried to get was off the board, this is an invalid shot.
        while True:
            try:
                if not self.game.board[targetsquare].unit.isBuilding():
                    self._hurtAndPushEnemy(targetsquare, direction) # found the unit, hit it's tile
                    return
            except KeyError:  # raised from if game.board[False].unit: targetsquare being false means we never found a unit and went off the board
                self.game.board[oldtargetsquare].takeDamage(self.damage) # edge tile takes damage, no point in trying to push the edge
                return
            except AttributeError: # None.isBuilding()
                pass # there was no unit, keep moving
            else: # there was a building
                if self.phaseshield:
                    self.game.board[targetsquare].applyShield() # shield it if phase shield is powered
            oldtargetsquare = targetsquare
            targetsquare = self.game.board[targetsquare].getRelSquare(direction, 1)  # the next square in the direction the shot

class Weapon_DefShrapnel(Weapon_DirectionalGen_Base, Weapon_NoUpgradesInit_Base, Weapon_getSquareOfUnitInDirection_Base, Weapon_PushProjectile_Base):
    "Fire a non-damaging projectile that pushes tiles around the target."
    def shoot(self, direction):
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=True)
        self._pushProjectile(direction, targetsquare)

class Weapon_RailCannon(Weapon_Projectile_Base, Weapon_hurtAndPushEnemy_Base):
    "Projectile that does more damage to targets that are further away."
    def __init__(self, power1=False, power2=False):
        self.maxdamage = 2
        for p in power1, power2:
            if p:
                self.maxdamage += 1
    def shoot(self, direction):
        self.damage = 0 # this will grow as the shot travels
        targetsquare = self.game.board[self.wieldingunit.square].getRelSquare(direction, 1)  # start the projectile at square in direction from the unit that used the weapon...
        if not targetsquare:
            raise NullWeaponShot # the first square we tried to get was off the board, this is an invalid shot.
        while True:
            try:
                if self.game.board[targetsquare].unit: # found the unit
                    self._hurtAndPushEnemy(targetsquare, direction)
                    return
            except KeyError:  # raised from if game.board[False].unit: targetsquare being false means we never found a unit and went off the board
                self.game.board[lasttargetsquare].takeDamage(self.damage)
                return
            lasttargetsquare = targetsquare
            targetsquare = self.game.board[targetsquare].getRelSquare(direction, 1)  # the next tile in direction of the last square
            if self.damage < self.maxdamage:
                self.damage += 1

class Weapon_ShockCannon(Weapon_Projectile_Base, Weapon_IncreaseDamageWithPowerInit_Base, Weapon_hurtAndPushEnemy_Base):
    "Fire a projectile that hits 2 tiles, pushing them in opposite directions."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        super().__init__(power1, power2)
    def shoot(self, direction):
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=True)
        self._hurtAndPushEnemy(targetsquare, Direction.opposite(direction)) # hurt and push the unit towards the wielder
        try:
            self._hurtAndPushEnemy(self.game.board[targetsquare].getRelSquare(direction, 1), direction)  # hurt and push the unit on the tile past the one we just hit away from the wielder
        except NullWeaponShot: # if you hit the edge, this action is ignored
            pass

class Weapon_HeavyRocket(Weapon_DirectionalLimitedGen_Base, Weapon_getSquareOfUnitInDirection_Base, Weapon_PushProjectile_Base):
    "Fire a projectile that heavily damages a target and pushes adjacent tiles."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.damage = 3
        if power2: # power1 for extra uses is ignored
            self.damage += 2
    def shoot(self, direction):
        self.usesremaining -= 1
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=True)
        self.game.board[targetsquare].takeDamage(self.damage)
        self._pushProjectile(direction, targetsquare)

class Weapon_ShrapnelCannon(Weapon_DirectionalLimitedGen_Base, Weapon_getSquareOfUnitInDirection_Base, Weapon_hurtAndPushEnemy_Base):
    "Shoot a projectile that damages and pushes the targeted tile and the tiles to its left and right."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.damage = 2
        if power2:  # power1 for extra uses is ignored
            self.damage += 1
    def shoot(self, direction):
        self.usesremaining -= 1
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=True)
        self._hurtAndPushEnemy(targetsquare, direction) # hit the target
        for dir in Direction.genPerp(direction): # and then the 2 sides
            try:
                self._hurtAndPushEnemy(self.game.board[targetsquare].getRelSquare(dir, 1), dir)
            except NullWeaponShot:
                pass # peripheral shots went off the board which is OK

class Weapon_AstraBombs(Weapon_ArtilleryGen_Base, Weapon_getRelSquare_Base):
    "Leap over any distance dropping a bomb on each tile you pass."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.damage = 1
        if power2:  # power1 for extra uses is ignored
            self.damage += 2
    def shoot(self, direction, distance):
        "distance is the number of squares to jump over and damage. The wielder lands on one square past distance."
        if self.game.board[self.targetsquare].unit:
            raise NullWeaponShot # can't land on an occupied square
        self.usesremaining -= 1
        currenttargetsquare = self.wieldingunit.square # start where the unit is
        for r in range(distance):
            currenttargetsquare = self.game.board[currenttargetsquare].getRelSquare(direction, 1)
            self.game.board[currenttargetsquare].takeDamage(self.damage) # damage the target
        self.game.board[self.wieldingunit.square].moveUnit(self.targetsquare) # move the unit to its landing position 1 square beyond the last attack

class Weapon_HermesEngines(Weapon_DirectionalGen_Base, Weapon_NoUpgradesInit_Base, Weapon_getRelSquare_Base):
    "Dash in a line, pushing adjacent tiles away."
    def shoot(self, direction):
        targetsquare = self._getRelSquare(direction, 1) # first check the square ahead fo validity
        try:
            if self.game.board[targetsquare].unit: # the first square we tried to target was off the board or has a unit blocking
                raise NullWeaponShot
        except KeyError:
            raise NullWeaponShot
        targetsquare = self.wieldingunit.square # the tile that the mech shoots from is pushed as well
        while True:
            for dir in Direction.genPerp(direction): # do the pushing
                try:
                    self.game.board[self.game.board[targetsquare].getRelSquare(dir, 1)].push(dir)
                except KeyError: # board[False], tried to push off board
                    pass
            oldtargetsquare = targetsquare
            targetsquare = self.game.board[targetsquare].getRelSquare(direction, 1)
            try:
                if self.game.board[targetsquare].unit: # if there's a unit on the next square..
                    break
            except KeyError: # or if we went off the board
                break
        self.game.board[self.wieldingunit.square].moveUnit(oldtargetsquare) # move the wielder to the last good square

class Weapon_MicroArtillery(Weapon_Artillery_Base, Weapon_hurtAndPushEnemy_Base):
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self.extratiles = True
        else:
            self.extratiles = False
        if power2:
            self.damage += 1
    def shoot(self, direction, distance):
        self._hurtAndPushEnemy(self.targetsquare, direction)
        if self.extratiles:
            for dir in Direction.genPerp(direction): # and then the 2 sides
                try:
                    self._hurtAndPushEnemy(self.game.board[self.targetsquare].getRelSquare(dir, 1), direction) # push in same direction as shot
                except NullWeaponShot:
                    pass # peripheral shots went off the board which is OK

class Weapon_AegonMortar(Weapon_Artillery_Base, Weapon_IncreaseDamageWithPowerInit_Base, Weapon_hurtAndPushEnemy_Base):
    "Deals damage to two tiles, pushing one forwards and one backwards."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        super().__init__(power1, power2)
    def shoot(self, direction, distance):
        self._hurtAndPushEnemy(self.targetsquare, Direction.opposite(direction)) # hurt and push the unit towards the wielder
        try:
            self._hurtAndPushEnemy(self.game.board[self.targetsquare].getRelSquare(direction, 1), direction)  # hurt and push the unit on the tile past the one we just hit away from the wielder
        except NullWeaponShot: # if you hit the edge, this action is ignored
            pass

class Weapon_SmokeMortar(Weapon_Artillery_Base, Weapon_NoUpgradesInit_Base):
    "Artillery shot that applies Smoke and pushes two adjacent tiles."
    def shoot(self, direction, distance):
        self.game.board[self.targetsquare].applySmoke()
        for dir in direction, Direction.opposite(direction):
            try:
                self.game.board[self.game.board[self.targetsquare].getRelSquare(dir, 1)].push(dir)
            except KeyError:
                pass # shot went off the board

class Weapon_BurningMortar(Weapon_ArtilleryGen_Base):
    "Artillery attack that sets 5 tiles on Fire."
    def __init__(self, power1=False, power2=False): # power2 is ignored
        if power1:
            self.selfdamage = 0
        else:
            self.selfdamage = 1
    def shoot(self, direction, distance):
        self.game.board[self.targetsquare].applyFire() # first hit the dead center tile
        for dir in Direction.gen():
            try:
                self.game.board[self.game.board[self.targetsquare].getRelSquare(dir, 1)].applyFire()
            except KeyError:
                pass # extra tile was off board
        if self.selfdamage: # take self damage if applicable
            self.game.board[self.wieldingunit.square].takeDamage(self.selfdamage)

class Weapon_RainingDeath(Weapon_ArtilleryGen_Base):
    "A dangerous projectile that damages everything it passes."
    def __init__(self, power1=False, power2=False):
        self.selfdamage = 1
        self.damage = 2 # the damage that the last shot does, all others do 1 less than this
        if power1:
            self._buildingsimmune = True
        else:
            self._buildingsimmune = False
        if power2:
            self.selfdamage += 1
            self.damage += 1
    def shoot(self, direction, distance):
        self.game.board[self.wieldingunit.square].takeDamage(self.selfdamage) # first take self damage
        currentsquare = self.wieldingunit.square # the current square that we are hitting with less damage
        while True:
            currentsquare = self.game.board[currentsquare].getRelSquare(direction, 1) # move to the next square
            if currentsquare == self.targetsquare: # if we're on the last square...
                self.damageSquare(currentsquare, self.damage) # hit it with full power
                return # and we're done
            self.damageSquare(currentsquare, self.damage-1) # hit the square with one less damage
    def damageSquare(self, square, damage):
        "Damage a single square, checking for building immunity."
        if self._buildingsimmune and self.game.board[square].unit.isBuilding():
            pass
        else:
            self.game.board[square].takeDamage(damage)

class Weapon_HeavyArtillery(Weapon_ArtilleryGenLimited_Base):
    "Powerful attack that damages a large area."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.damage = 2
        if power2: # power1 for an extra use is ignored
            self.damage += 1
    def shoot(self, direction, distance):
        self.usesremaining -= 1
        self.game.board[self.targetsquare].takeDamage(self.damage) # first hit the dead center tile
        for dir in Direction.gen():
            try:
                self.game.board[self.game.board[self.targetsquare].getRelSquare(dir, 1)].takeDamage(self.damage)
            except KeyError:
                pass # extra tile was off board

class Weapon_GeminiMissiles(Weapon_ArtilleryGenLimited_Base, Weapon_hurtAndPushEnemy_Base):
    "Launch two missiles, damaging and pushing two targets"
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.damage = 3
        if power2: # power1 for an extra use is also ignored
            self.damage += 1
    def shoot(self, direction, distance):
        self.usesremaining -= 1
        for dir in Direction.genPerp(direction):
            try:
                self._hurtAndPushEnemy(self.game.board[self.targetsquare].getRelSquare(dir, 1), direction)
            except NullWeaponShot: # one of the missiles was off board
                pass # totally fine

class Weapon_ConfuseShot(Weapon_Projectile_Base, Weapon_NoUpgradesInit_Base):
    "Fire a projectile that flips a target's attack direction."
    def shoot(self, direction):
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=False)
        try:
            if not self.game.board[targetsquare].unit.alliance == Alliance.ENEMY: # if we hit a unit that's not an enemy...
                raise NullWeaponShot # it's a wasted shot that did nothing
        except KeyError: #board[False]
            raise NullWeaponShot # didn't find a unit at all
        self.game.board[targetsquare].unit.weapon1.flip() # this should for sure be an enemy at this point

class Weapon_SmokePellets(Weapon_NoChoiceLimitedGen_Base, Weapon_getRelSquare_Base, Weapon_DeploySelfEffectLimitedSmall_Base):
    "Surround yourself with Smoke to defend against nearby enemies."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        if power1: # power2 for extra use ignored
            self.shoot = self.shoot_allyimmune
    def shoot(self):
        super().shoot('applySmoke')
    def shoot_allyimmune(self):
        "a different shoot method for when allyimmune is powered"
        self.usesremaining -= 1
        for dir in Direction.gen():
            try:
                targettile = self.game.board[self._getRelSquare(dir, 1)]
            except KeyError: # board[False]
                continue # targettile is offboard
            try:
                if targettile.unit.alliance == Alliance.FRIENDLY:
                    continue
            except AttributeError: # targettile.None.alliance, no unit there so we smoke it
                pass
            targettile.applySmoke()

class Weapon_FireBeam(Weapon_TemperatureBeam_Base):
    "Fire a beam that applies Fire in a line."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        super().__init__(None, None, usesremaining, 'applyFire')

class Weapon_FrostBeam(Weapon_TemperatureBeam_Base):
    "Fire a beam that Freezes everything in a line."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        super().__init__(None, None, usesremaining, 'applyIce')

class Weapon_ShieldArray(Weapon_NoChoiceLimitedGen_Base, Weapon_getRelSquare_Base, Weapon_DeploySelfEffectLimitedSmall_Base, Weapon_DeploySelfEffectLimitedLarge_Base):
    "Apply a Shield on nearby tiles."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        if power1:
            self.shoot = self.shoot_big # power2 is ignored
    def shoot(self):
        super().shoot('applyShield')
    def shoot_big(self):
        super().shoot_big('applyShield')

class Weapon_PushBeam(Weapon_DirectionalLimitedGen_Base, Weapon_LimitedUnlimitedInit_Base):
    def shoot(self, direction):
        currenttarget = self.game.board[self.wieldingunit.square].getRelSquare(direction, 1)
        if not currenttarget: # first square attacked was offboard and therefor
            raise NullWeaponShot
        self.usesremaining -= 1
        pushsquares = [] # build this into a list of squares we need to push
        while True:
            try:
                if self.game.board[currenttarget].unit.isBuilding() or self.game.board[currenttarget].unit.isMountain():
                    break # buildings and mountains end the shot
            except AttributeError: # None.isBuilding()
                pass # continue on. No point in pushing this since there is no unit anyway
            except KeyError:
                break # we went off the board without ever running into a building or mountain
            else: # there is a unit that possibly needs pushing
                pushsquares.insert(0, currenttarget)
            currenttarget = self.game.board[currenttarget].getRelSquare(direction, 1)
        for sq in pushsquares:
            self.game.board[sq].push(direction)

class Weapon_Boosters(Weapon_ArtilleryGen_Base, Weapon_NoUpgradesInit_Base, Weapon_PushAdjacent_Base):
    "Jump forward and push adjacent tiles away."
    def genShots(self):
        return super().genShots(minimumdistance=1)
    def shoot(self, direction, distance):
        if self.game.board[self.targetsquare].unit:
            raise NullWeaponShot # the tile you're leaping to must be clear of units
        self.game.board[self.wieldingunit.square].moveUnit(self.targetsquare) # move the wielder first
        self._pushAdjacent(self.targetsquare)

class Weapon_SmokeBombs(Weapon_getRelSquare_Base, Weapon_RangedGen_Base):
    "Fly over the targets while dropping Smoke."
    def __init__(self, power1=False, power2=False):
        self.range = 1  # how many tiles you can jump over and damage. Unit lands on the tile after this distance.
        for p in power1, power2:
            if p:
                self.range += 1
    def shoot(self, direction, distance): # this is the same shoot method from AerialBombs with the tile damaging removed. copypasta
        "distance is the number of squares to jump over and damage. The wielder lands on one square past distance."
        destsquare = self._getRelSquare(direction, distance+1)
        try:
            if self.game.board[destsquare].unit:
                raise NullWeaponShot # can't land on an occupied square
        except AttributeError: # landing spot was off the board
            raise NullWeaponShot
        targetsquare = self.wieldingunit.square # start where the unit is
        for r in range(distance):
            targetsquare = self.game.board[targetsquare].getRelSquare(direction, 1)
            self.game.board[targetsquare].applySmoke() # smoke the target
        self.game.board[self.wieldingunit.square].moveUnit(self.game.board[targetsquare].getRelSquare(direction, 1)) # move the unit to its landing position 1 square beyond the last attack

class Weapon_HeatConverter(Weapon_DirectionalLimitedGen_Base, Weapon_getRelSquare_Base):
    "Freeze the tile in front but light the tile behind on Fire in the process."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining # power1 and 2 are ignored
    def shoot(self, direction):
        try:
            self.game.board[self._getRelSquare(direction, 1)].applyIce()
        except KeyError: # board[False]
            raise NullWeaponShot
        try:
            self.game.board[self._getRelSquare(Direction.opposite(direction), 1)].applyFire()
        except KeyError: # board[False]
            pass # this can be offboard

class Weapon_SelfDestruct(Weapon_NoChoiceGen_Base, Weapon_NoUpgradesInit_Base, Weapon_getRelSquare_Base):
    def shoot(self):
        for d in Direction.gen(): # all tiles around wielder must die
            try:
                self.game.board[self._getRelSquare(d, 1)].die()
            except KeyError: # game.board[False]
                pass
        self.game.board[self.wieldingunit.square].die()

class Weapon_TargetedStrike(Weapon_AnyTileGen_Base, Weapon_NoUpgradesLimitedInit_Base, Weapon_PushAdjacent_Base):
    "Call in an air strike on a single tile anywhere on the map."
    def shoot(self, x, y):
        self.usesremaining -= 1
        self.game.board[(x, y)].takeDamage(1) # this weapon can only do one damage so I'm breaking the convention of using self.damage so I can use that init base.
        self._pushAdjacent((x, y))

class Weapon_SmokeDrop(Weapon_AnyTileGen_Base, Weapon_NoUpgradesLimitedInit_Base):
    "Drops Smoke on 5 tiles anywhere on the map."
    def shoot(self, x, y):
        self.usesremaining -= 1
        self.game.board[(x, y)].applySmoke()
        for dir in Direction.gen():
            try:
                self.game.board[self.game.board[(x, y)].getRelSquare(dir, 1)].applySmoke()
            except KeyError: # board[False]
                pass

class Weapon_RepairDrop(Weapon_NoChoiceGen_Base, Weapon_NoUpgradesLimitedInit_Base):
    "Heal all player units (including disabled Mechs)."
    #def shoot(self): # TODO: THIS!
    # repairdrop does remove bad effects from your mech like fire

class Weapon_MissileBarrage(Weapon_NoChoiceLimitedGen_Base):
    "Fires a missile barrage that hits every enemy on the map."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        self.damage = 1
        if power1:
            self.damage += 1 # power2 ignored
    def shoot(self):
        self.usesremaining -= 1
        for e in self.game.enemyunits:
            self.game.board[e.square].takeDamage(self.damage)

class Weapon_WindTorrent(Weapon_DirectionalLimitedGen_Base, Weapon_LimitedUnlimitedInit_Base):
    "Push all units in a single direction."
    def shoot(self, direction):
        # so here's the plan: set xrange and yrange based on the direction chosen.
        # we will omit the entire row or column at the edge of the board that the push direction is in since those tiles can't be pushed off board
        if direction == Direction.UP:
            xrange = (1, 9)
            yrange = (8, 1, -1)
        if direction == Direction.RIGHT:
            xrange = (8, 1, -1)
            yrange = (1, 9)
        if direction == Direction.DOWN:
            xrange = (1, 9)
            yrange = (2, 9)
        if direction == Direction.LEFT:
            xrange = (2, 9)
            yrange = (1, 9)
        for x in range(*xrange):
            for y in range(*yrange):
                #print("pushing (%s, %s) %s" % (x, y, Direction.pprint((direction,))))
                self.game.board[(x, y)].push(direction)

class Weapon_IceGenerator(Weapon_NoChoiceLimitedGen_Base, Weapon_DeploySelfEffectLimitedSmall_Base, Weapon_DeploySelfEffectLimitedLarge_Base, Weapon_getRelSquare_Base):
    "Freeze yourself and nearby tiles."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        self.usesremaining = usesremaining
        size = 1
        for p in power1, power2:
            if p:
                size += 1
        if size == 2:
            self.shoot = self.shoot_big
        elif size == 3:
            self.shoot = self.shoot_huge # we use the default shoot if there was no power
    def shoot(self):
        super().shoot('applyIce')
    def shoot_big(self):
        super().shoot_big('applyIce')
    def shoot_huge(self):
        self.positions = {}
        self.branch(self.wieldingunit.square, n=4)
        for sq in self.positions:
            self.game.board[sq].applyIce()
    def branch(self, coords, n):
        "coords must be a tuple of (x, y)"
        x, y = coords
        if n == 0:
            return
        self.positions[(x, y)] = n
        for mx, my in ((0, 1), (1, 0), (-1, 0), (0, -1)): # these coords represent movement along the x and y axis
            if self.positions.get((x + mx, y + my), 0) < n:
                self.branch((x + mx, y + my), n - 1)

############################# Deployables ##################
class Weapon_LightTank(Weapon_Deployable_Base):
    "Deploy a small tank to help in combat."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        super().__init__(power1, power2, usesremaining)
    def shoot(self, direction, distance):
        super().shoot(Unit_LightTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_StockCannon(power2=self.power2)))

class Weapon_ShieldTank(Weapon_Deployable_Base):
    "Deploy a Shield-Tank that can give Shields to allies."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        super().__init__(power1, power2, usesremaining)
    def shoot(self, direction, distance):
        super().shoot(Unit_ShieldTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_ShieldShot(power2=self.power2)))

class Weapon_AcidTank(Weapon_Deployable_Base):
    "Deploy a Tank that can apply A.C.I.D. to targets."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        super().__init__(power1, power2, usesremaining)
    def shoot(self, direction, distance):
        super().shoot(Unit_AcidTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_AcidShot(power2=self.power2)))

class Weapon_PullTank(Weapon_Deployable_Base):
    "Deploy a Pull-Tank that can pull targets with a projectile."
    def __init__(self, power1=False, power2=False, usesremaining=1):
        super().__init__(power1, power2, usesremaining)
    def shoot(self, direction, distance):
        if self.power2:
            super().shoot(Unit_PullTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_PullShot(), attributes=(Attributes.FLYING,)))
        else:
            super().shoot(Unit_PullTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_PullShot()))
######################### Weapons that deployables shoot ################
# Deployable weapons don't actually take power, but we still use it here because the weapons are modified based on the power of the weapon that actually deployed the tank
class Weapon_StockCannon(Weapon_Projectile_Base, Weapon_hurtAndPushEnemy_Base):
    "This is the weapon for the Light Tank"
    def __init__(self, power1=False, power2=False):
        "This weapon doesn't actually take power itself, power2 should be inherited from Weapon_LightTank to signal that this weapon should do damage."
        if power2:
            self.shoot = self.shoot_damage
            self.damage = 2
    def shoot(self, direction):
        try:
            self.game.board[self._getSquareOfUnitInDirection(direction, edgeok=False)].push(direction)
        except KeyError: # board[False]
            raise NullWeaponShot # pushing a square on the edge of the board in the direction of the void is pointless
    def shoot_damage(self, direction): # copypasta from TaurusCannon
        self._hurtAndPushEnemy(self._getSquareOfUnitInDirection(direction, edgeok=True), direction)

class Weapon_ShieldShot(Weapon_DirectionalGen_Base, Weapon_getSquareOfUnitInDirection_Base):
    "ShieldTank weapon. Shields a single tile."
    def __init__(self, power1=False, power2=False):
        if power2:
            self.shoot = self.shoot_projectile
    def shoot(self, direction):
        try:
            if not self.game.board[self.game.board[self.wieldingunit.square].getRelSquare(direction, 1)].applyShield(): # if a unit didn't get shielded
                raise NullWeaponShot # useless shot
        except KeyError: # board[False]
            raise NullWeaponShot # shot went off the board
    def shoot_projectile(self, direction):
        try:
            self.game.board[self._getSquareOfUnitInDirection(direction, edgeok=False)].applyShield()
        except KeyError: # board[False]
            raise NullWeaponShot

class Weapon_AcidShot(Weapon_AcidGun_Base):
    "AcidTank weapon. Fire a projectile that applies ACID to a single tile."
    def __init__(self, power1=False, power2=False):
        if power2:
            self.shoot = self.shoot_push
    def shoot(self, direction):
        super().shoot(direction, False) # no push
    def shoot_push(self, direction):
        super().shoot(direction, True)  # yes push

Weapon_PullShot = Weapon_AttractionPulse # PullShot is literally the same weapon as AttractionPulse lol
########################### Passives #########################
# TODO :(
########################### Special Mech Weapons (repair) #########################
class Weapon_Repair(Weapon_NoChoiceGen_Base, Weapon_NoUpgradesInit_Base):
    "The default repair action/weapon that every mech starts with."
    def shoot(self):
        self.game.board[self.wieldingunit.square].repair(1)

class Weapon_FrenziedRepair(Weapon_NoChoiceGen_Base, Weapon_NoUpgradesInit_Base, Weapon_PushAdjacent_Base):
    "The repair action/weapon that you get when you have Harold as the pilot."
    def shoot(self):
        self.game.board[self.wieldingunit.square].repair(1)
        self._pushAdjacent(self.wieldingunit.square)

class Weapon_MantisSlash(Weapon_DirectionalGen_Base, Weapon_hurtAndPushEnemy_Base, Weapon_Punch_Base):
    "This is the weapon that replaces repair when Kazaakplethkilik is your pilot. Damage and push an adjacent tile. Escape from Ice."
    def __init__(self, power1=False, power2=False): # power is ignored
        self.damage = 2
    def shoot(self, direction):
        super().shoot_punch(direction)
        self.wieldingunit.removeEffect(Effects.ICE)

################################ Vek Weapons #################################
# All weapons have their ingame description in the docstring followed by the type/name of the enemy that wields this weapon.
# Vek weapons can't have shots generated for them like mech weapons do, so they lack genShots()
# All vek weapons MUST have an attribute self.qshot (queuedshot) which is the shot they will take on their turn.
# All vek weapons MUST have a validate() method to test whether their shot is still valid. This method will be run whenever the vek is moved and when the unit is created.
    # if the shot is invalid, it must set qshot to None and return False. return True otherwise.
    # this method can and should be used to set up a future shot similar to how Weapon_ArtilleryGen_Base set self.targetsquare.
# All shoot() methods take no arguments, they read their own qshot when shooting.
# All vek weapons MUST have a flip() method to flip the direction of attack (spartan shield and confuse shot use this). Some weapons can't be flipped, but they still need a working method that does nothing.
    # flip() must validate the shot afterwards unless the flip was ignored
# Weapons that create webs in the game isn't done here since that's really done during the vek's move/target phase. The user should already have a gameboard with webs laid out.
# Vek weapons will never raise NullWeaponShot

# Vek weapon low-level base objects:
class Weapon_Vek_Base():
    "Base class for all vek weapons."
    def __init__(self, qshot=None):
        self.qshot = qshot

class Weapon_Validate_Base():
    "This is the base validate class for all others."
    def validate(self):
        "The only way this shot can be invalidated is by the shot already being invalidated or the unit being smoked."
        if self.qshot is None:
            return False
        if Effects.SMOKE in self.game.board[self.wieldingunit.square].effects:
            self.qshot = None
            return False
        return True

class Weapon_IgnoreFlip_Base():
    def flip(self):
        "can't be flipped"
        pass

class Weapon_DirectionalValidate_Base(Weapon_Validate_Base):
    "A validate method that works for melee and projectile weapons."
    def validate(self):
        "qshot should be (Direction.XX,). This method checks one square in direction to make sure it's onboard."
        if super().validate(): # if a shot is queued and the unit is not smoked...
            self.targetsquare = self.game.board[self.wieldingunit.square].getRelSquare(*self.qshot, 1)
            if not self.targetsquare: # shot was offboard
                self.qshot = None
            else:
                return True
        return False

class Weapon_DirectionalFlip_Base():
    "A flip method that works for melee, projectile, and charge weapons."
    def flip(self):
        try:
            self.qshot = (Direction.opposite(*self.qshot),)
        except InvalidDirection: # qshot was None
            pass
        self.validate()

# Vek weapon high-level base objects:
class Weapon_SurroundingShoot_Base(Weapon_Vek_Base, Weapon_IgnoreFlip_Base):
    "Base weapon for vek weapons that damage adjacent tiles such as blob and digger weapons."
    def shoot(self):
        "return True if the shot happened, False if it didn't."
        if self.qshot is not None:
            for d in Direction.gen():
                try:
                    self.game.board[self.game.board[self.wieldingunit.square].getRelSquare(d, 1)].takeDamage(self.damage)
                except KeyError: # game.board[False]
                    pass
            return True
        return False

class Weapon_Blob_Base(Weapon_SurroundingShoot_Base):
    "Base weapon for blobs that explode"
    def shoot(self):
        if super().shoot():
            self.wieldingunit.die()

class Weapon_SpinneretFangs_Base(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base):
    "Shared shoot method for melee attacks used by Scorpions and Leapers (units that create webs before their attack)"
    def shoot(self):
        if self.qshot is not None:
            self.wieldingunit._breakAllWebs() # these units remove their webs before they attack
            self.game.board[self.targetsquare].takeDamage(self.damage)
            return True
        return False

class Weapon_Stinger_Base(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base):
    "Shared shoot method for melee attacks used by Hornets."
    def shoot(self):
        if self.qshot is not None:
            self.game.board[self.targetsquare].takeDamage(self.damage)
            return True
        return False

class Weapon_VekProjectileShoot_Base(Weapon_getSquareOfUnitInDirection_Base):
    "A base shoot method shared by vek projectile weapons such as the Firefly and Centipede weapons."
    def shoot(self):
        if self.qshot is not None:
            self.targetsquare = self._getSquareOfUnitInDirection(*self.qshot, edgeok=True)
            self.game.board[self.targetsquare].takeDamage(self.damage)
            return True
        return False

class Weapon_Thorax_Base(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base, Weapon_VekProjectileShoot_Base):
    "Base class for Firefly Thorax weapons"

class Weapon_VekCharge_Base(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base, Weapon_hurtAndPushEnemy_Base):
    "A base for vek charge weapons."
    def shoot(self):
        "Have the unit charge across the board, dying if it comes across a swallow tile."
        if self.qshot is not None:
            prevsquare = self.wieldingunit.square # set the previous tile since if we run into a unit we have to put the unit here
            while True: # self.targetsquare is already set to the first tile from validation
                if self.game.board[self.targetsquare].unit: # if the next square has a unit on it...
                    self._hurtAndPushEnemy(self.targetsquare, *self.qshot) # hurt and push the enemy
                    self.game.board[self.wieldingunit.square].moveUnit(prevsquare) # then move to the square before this one
                    return # and we're done
                elif self.game.board[self.targetsquare].isSwallow()\
                        or Effects.FREEZEMINE in self.game.board[self.targetsquare].effects \
                        or Effects.MINE in self.game.board[self.targetsquare].effects: # if the tile is a swallow tile or has a mine on it
                    self.game.board[self.wieldingunit.square].moveUnit(self.targetsquare) # move the unit here so it can die or trip the mine
                    return
                else: # there was no unit and the tile didn't kill the vek
                    prevsquare = self.targetsquare
                    self.targetsquare = self.game.board[self.targetsquare].getRelSquare(*self.qshot, 1)
                    if not self.targetsquare: # if we went off the board
                        self.game.board[self.wieldingunit.square].moveUnit(prevsquare) # move to that edge tile
                        return

class Weapon_VekArtillery_Base(Weapon_Vek_Base, Weapon_Validate_Base, Weapon_getRelSquare_Base):
    "Base object for vek artillery weapons for Scarabs and Crabs."
    def validate(self):
        "qshot is stored as (Direction, RelDistance)"
        if super().validate():
            self.targetsquare = self._getRelSquare(*self.qshot)
            if not self.targetsquare: # if the shot is now off the board
                self.qshot = None # invalidate the shot
                return
    def flip(self):
        try:
            self.qshot = (Direction.opposite(self.qshot[0]), self.qshot[1]) # only flip the direction, don't touch the distance
        except TypeError: # None[0]
            return # shot was already invalid
        self.validate()
    def shoot(self):
        "Launch the artillery."
        if self.qshot is not None:
            self.game.board[self.targetsquare].takeDamage(self.damage)
            return True

class Weapon_ExplosiveExpulsions_Base(Weapon_VekArtillery_Base):
    "Base class for Crab weapons"
    def shoot(self):
        if super().shoot():
            try:
                self.game.board[self.game.board[self.targetsquare].getRelSquare(self.qshot[0], 1)].takeDamage(self.damage)
            except KeyError:  # board[False]
                pass  # the secondary target can be offboard

class Weapon_Vomit_Base(Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base, Weapon_VekProjectileShoot_Base):
    "Base class for Centipede weapons"
    def shoot(self):
        if super().shoot():
            self.game.board[self.targetsquare].applyAcid() # give acid to the square that was already damaged by the parent obj
            for d in Direction.genPerp(*self.qshot):
                secondarysquare = self.game.board[self.targetsquare].getRelSquare(d, 1)
                try:
                    self.game.board[secondarysquare].takeDamage(self.damage)
                except KeyError: # board[False]
                    continue # secondary square was offboard
                self.game.board[secondarysquare].applyAcid() # give it acid after attacking it

class Weapon_Carapace_Base(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base):
    "Base class for Burrower Carapace weapons"
    def shoot(self):
        if self.qshot is not None:
            self.game.board[self.targetsquare].takeDamage(self.damage) # hit the main target square
            for d in Direction.genPerp(*self.qshot):
                try:
                    self.game.board[self.game.board[self.targetsquare].getRelSquare(d, 1)].takeDamage(self.damage)
                except KeyError: # board[False]
                    continue # secondary square was offboard

############################## Actual vek weapons: #######################################################
class Weapon_UnstableGuts(Weapon_Blob_Base):
    "Explode, killing itself and damaging adjacent tiles for 1 damage. Kill it first to stop it. Blob"
    damage = 1

class Weapon_VolatileGuts(Weapon_Blob_Base):
    "Explode, killing itself and damaging adjacent tiles for 3 damage. Kill it first to stop it. Alpha Blob"
    damage = 3

# TODO: We can't predict the shooting of these 4 weapons, but they need to be counted towards spawning new enemies
class Weapon_UnstableGrowths(Weapon_Vek_Base, Weapon_IgnoreFlip_Base):
    "Throw a sticky blob that will explode. Blobber"
    def shoot(self):
        print("TODO!")

class Weapon_VolatileGrowths(Weapon_Vek_Base, Weapon_IgnoreFlip_Base):
    "Throw a sticky blob that will explode. Blobber"
    def shoot(self):
        print("TODO!")

class Weapon_TinyOffspring(Weapon_Vek_Base, Weapon_IgnoreFlip_Base):
    "Throw a sticky egg that hatches into a Spiderling. Spider"
    def shoot(self):
        print("TODO!")

class Weapon_LargeOffspring(Weapon_Vek_Base, Weapon_IgnoreFlip_Base):
    "Throw a sticky egg that hatches into an Alpha Spiderling. AlphaSpider"
    def shoot(self):
        print("TODO!")

class Weapon_StingingSpinneret(Weapon_SpinneretFangs_Base):
    "Web an adjacent target, preparing to stab it for 1 damage. (We don't actually do any webbing here). Scorpion."
    damage = 1

class Weapon_StingingSpinneretAcid(Weapon_SpinneretFangs_Base):
    "Web an adjacent target, preparing to stab it for 1 damage and apply acid. (We don't actually do any webbing here). AcidScorpion."
    damage = 1
    def shoot(self):
        if super().shoot():
            self.game.board[self.targetsquare].applyAcid()

class Weapon_GoringSpinneret(Weapon_SpinneretFangs_Base):
    "Web an adjacent target, preparing to stab it for 3 damage. (We don't actually do any webbing here). AlphaScorpion."
    damage = 3

class Weapon_AcceleratingThorax(Weapon_Thorax_Base):
    "Launch a volatile mass of goo dealing 1 damage. Firefly"
    damage = 1

class Weapon_AcceleratingThoraxAcid(Weapon_Thorax_Base):
    "Launch a volatile mass of goo dealing 1 damage and applying acid. AcidFirefly"
    damage = 1
    def shoot(self):
        if super().shoot():
            self.game.board[self.targetsquare].applyAcid()

class Weapon_EnhancedThorax(Weapon_Thorax_Base):
    "Launch a volatile mass of goo dealing 3 damage. AlphaFirefly"
    damage = 3

class Weapon_Fangs(Weapon_SpinneretFangs_Base):
    "Web a target, preparing to stab it for 3 damage. Leaper"
    damage = 3

class Weapon_SharpenedFangs(Weapon_SpinneretFangs_Base):
    "Web a target, preparing to stab it for 5 damage. AlphaLeaper"
    damage = 5

class Weapon_Pincers(Weapon_VekCharge_Base):
    "Charge forward to deal 1 damage and push the target. Beetle"
    damage = 1

class Weapon_SharpenedPincers(Weapon_VekCharge_Base):
    "Charge forward to deal 3 damage and push the target. AlphaBeetle"
    damage = 3

class Weapon_SpittingGlands(Weapon_VekArtillery_Base):
    "Lob an artillery shot at a single tile for 1 damage (5 tile range). Scarab"
    damage = 1

class Weapon_AlphaSpittingGlands(Weapon_VekArtillery_Base):
    "Lob an artillery shot at a single tile for 3 damage (5 tile range). AlphaScarab"
    damage = 3

class Weapon_ExplosiveExpulsions(Weapon_ExplosiveExpulsions_Base):
    "Launch artillery attack on 2 tiles for 1 damage (5 tile range). Crab"
    damage = 1

class Weapon_AlphaExplosiveExpulsions(Weapon_ExplosiveExpulsions_Base):
    "Launch artillery attack on 2 tiles for 3 damage (5 tile range). AlphaCrab"
    damage = 3

class Weapon_AcidicVomit(Weapon_Vomit_Base):
    "Launch a volatile mass of goo, dealing 1 damage and applying A.C.I.D. on nearby units. Centipede"
    damage = 1

class Weapon_CorrosiveVomit(Weapon_Vomit_Base):
    "Launch a volatile mass of goo, dealing 2 damage and applying A.C.I.D. on nearby units. Centipede"
    damage = 2

class Weapon_DiggingTusks(Weapon_SurroundingShoot_Base):
    "Create a defensive rock wall before attacking adjacent tiles for 1 damage."
    damage = 1

class Weapon_AlphaDiggingTusks(Weapon_SurroundingShoot_Base):
    "Create a defensive rock wall before attacking adjacent tiles for 2 damage."
    damage = 2

class Weapon_Stinger(Weapon_Stinger_Base):
    "Stab the target for 1 damage. Hornet"
    damage = 1

class Weapon_AcidStinger(Weapon_Stinger_Base):
    "Stab the target for 1 damage and apply A.C.I.D. AcidHornet"
    damage = 1
    def shoot(self):
        if super().shoot():
            self.game.board[self.targetsquare].applyAcid()

class Weapon_LaunchingStinger(Weapon_Stinger_Base):
    "Stab 2 tiles in front of the unit for 2 damage. AlphaHornet"
    damage = 2
    def shoot(self):
        if super().shoot():
            try:
                self.game.board[self.game.board[self.targetsquare].getRelSquare(*self.qshot, 1)].takeDamage(self.damage)
            except KeyError: # board[False], secondary tile was offboard
                pass

class Weapon_SpikedCarapace(Weapon_Carapace_Base):
    "Slam against 3 tiles in a row, hitting each for 1 damage. Burrower"
    damage = 1

class Weapon_BladedCarapace(Weapon_Carapace_Base):
    "Slam against 3 tiles in a row, hitting each for 2 damage. AlphaBurrower"
    damage = 2

class Weapon_FlamingAbdomen(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base, Weapon_hurtAndPushEnemy_Base):
    "Charge, dealing 3 damage, and light every tile in the path on Fire. BeetleLeader"
    # This weapon isn't affected by swallow tiles, just like a mech charge weapon
    damage = 3
    def shoot(self):
        if self.qshot is not None:
            firesquares = set() # a set of squares that will be set on fire after the wielder is moved
            prevsquare = self.wieldingunit.square # set the previous tile since if we run into a unit we have to put the unit here
            while True: # self.targetsquare is already set to the first tile from validation
                if self.game.board[self.targetsquare].unit: # if the next square has a unit on it...
                    self._hurtAndPushEnemy(self.targetsquare, *self.qshot) # hurt and push the enemy
                    self.game.board[self.wieldingunit.square].moveUnit(prevsquare) # then move to the square before this one
                    break
                else: # there was no unit
                    firesquares.add(prevsquare)
                    prevsquare = self.targetsquare
                    self.targetsquare = self.game.board[self.targetsquare].getRelSquare(*self.qshot, 1)
                    if not self.targetsquare: # if we went off the board
                        self.game.board[self.wieldingunit.square].moveUnit(prevsquare) # move to that edge tile
                        break
            for sq in firesquares:
                self.game.board[sq].applyFire()

# class Weapon_GooAttack(Weapon_Stinger_Base):
#     "Attempt to squish the adjacent tile, destroying its contents. LargeGoo, MediumGoo, SmallGoo all use this same exact weapon."
#     damage = 4
#     def shoot(self):
#         """The way this weapon works is that it damages the unit like a regular melee unit would if it's a mech or if the unit doesn't die.
#         However, if the unit dies and is NOT a mech, the goo takes the victim's spot on the board."""
#         if super().shoot():