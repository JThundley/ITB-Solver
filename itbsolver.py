#!/usr/bin/env python3
# This script brute forces the best possible single turn in Into The Breach
############ IMPORTS ######################
from itertools import permutations
from copy import deepcopy
############### GLOBALS ###################
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
    'ICE', # sometimes does nothing to tile
    'ACID',
    # These effects can only be applied to tiles:
    'SMOKE',
    'TIMEPOD',
    'MINE',
    'FREEZEMINE',
    'SUBMERGED', # I'm twisting the rules here. In the game, submerged is an effect on the unit. Rather than apply and remove it as units move in and out of water, we'll just apply this to water tiles and check for it there.
    # These effects can only be applied to units:
    'SHIELD',
    'EXPLOSIVE',
     ))

# These are attributes that are applied to units.
# Attributes typically don't change, the only exception being ARMORED which can be removed from a psion dying.
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

Passives = Constant(thegen, ( # This isn't all passives, just ones that need to be checked for presence only at certain times.
    'REPAIRFIELD', # mech passives (from weapons)
    'AUTOSHIELDS',
    'STABILIZERS',
    'KICKOFFBOOSTERS',
    'FORCEAMP',
    ))

Actions = Constant(thegen, ( # These are the actions that a player can take with a unit they control.
    'MOVE',
    'SHOOT',
    'MOVE2', # secondary move
    'SHOOT2', # secondary shoot
    ))

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
    def __init__(self, dir):
        super().__init__()
        self.message = "Invalid Direction: {0}".format(dir)
    def __str__(self):
        return self.message

class CantHappenInGame(Exception):
    """This is raised when something happens that's not permitted in game.
    For example, if the Terraformer's shot goes off the board. The in-game Terraformer will never be placed to allow this."""

class FakeException(Exception):
    "This is raised to do some more efficient try/except if/else statements"

class GameOver(Exception):
    "This is raised when your powergrid health is depleted, causing the end of the current simulation."

class DontGiveUnitAcid(Exception):
    "This is raised when a tile tries to give acid to a building that can't take it. This signals that the tile should take the acid instead as if the unit isn't there."

class SimulationFinished(Exception):
    "This is raised when an OrderSimulator runs out of actions to simulate"

class OutOfAmmo(Exception):
    "This is raised when a weapon tries to fire a shot but doesn't have ammo."

# Onto the rest
class Powergrid():
    "This represents your powergrid hp. When this hits 0, it's game over!"
    def __init__(self, game, hp=7):
        self.hp = hp
        self.game = game
    def takeDamage(self, damage):
        self.hp -= damage
        if self.hp < 1:
            raise GameOver
        self.game.score.submit(-50, 'powergrid_hurt', damage)

class Powergrid_CriticalShields(Powergrid):
    "This is your powergrid hp when you have the CriticalShields passive in play."
    def __init__(self, game, hp=7):
        super().__init__(game, hp)
        self.qdamage = 0 # damaged queued to take place when flushHurt tells us to
        self._findBuildings()
    def takeDamage(self, damage):
        self.qdamage += damage
    def _findBuildings(self):
        "This is run when the CriticalShields passive is in play. It goes through the board and builds a set of every building."
        self.buildings = set()
        for sq in self.game.board:
            try:
                if self.game.board[sq].unit.isBuilding():
                    self.buildings.add(sq)
            except AttributeError: # None.isbuilding()
                pass
    def _shieldBuildings(self):
        "Shield all your buildings, return nothing."
        for sq in self.buildings:
            try:
                if self.game.board[sq].unit.isBuilding(): # we have to check again because it's possible a building was destroyed and now another unit is standing in it's place.
                    self.game.board[sq].unit.applyShield()
            except AttributeError:
                continue
    def flushHurt(self):
        """Call this to signal that buildings are done taking damage.
        If we don't do this it'll be possible in the sim to shoot something that hits 2 buildings, and damaging the first one
        causes the 2nd one to shield before it takes damage, which isn't what happens in the game.
        However, if you have 2 powergrid hp and a 1 hp explosive vek next to a building and then you push the vek into the building, you take 1 damage from the bump
        and then the critical shields fire, protecting the building from the explosion damage."""
        if self.qdamage:
            super().takeDamage(self.qdamage)
            if self.hp == 1:
                self._shieldBuildings()
            self.qdamage = 0


############# THE MAIN GAME BOARD!
class Game():
    "This represents the a single instance of a game. This is the highest level of the game."
    def __init__(self, board=None, powergrid_hp=7, environeffect=None, vekemerge=None):
        """board is a dict of tiles to use. If it's left blank, a default board full of empty ground tiles is generated.
        powergrid_hp is the amount of power (hp) you as a player have. When this reaches 0, the entire game ends.
        environeffect is an environmental effect object that should be run during a turn.
        vekemerge is the special VekEmerge environmental effect. If left blank, an empty one is created.
        """
        if board:
            self.board = board
        else: # create a blank board of normal ground tiles
            self.board = {} # a dictionary of all 64 squares on the board. Each key is a tuple of x,y coordinates and each value is the tile object: {(1, 1): Tile, ...}
                # Each square is called a square. Each square must have a tile assigned to it, an optionally a unit on top of the square. The unit is part of the tile.
            for letter in range(1, 9):
                for num in range(1, 9):
                    self.board[(letter, num)] = Tile_Ground(self, square=(letter, num))
        self.powergrid = Powergrid(self, powergrid_hp)
        try:
            environeffect.game = self
        except AttributeError:
            self.environeffect = None # no environmental effect being used
        else:
            self.environeffect = environeffect
        if vekemerge:
            self.vekemerge = vekemerge
        else:
            self.vekemerge = Environ_VekEmerge()
        self.vekemerge.game = self
        # playerunits and nonplayerunits are used for passives that need to be applied to all vek and/or all mechs.
        # nonplayerunits is also a list of units that take a turn doing an action, such as vek and NPC friendlies.
        # units without weapons that don't take turns such as the rock also need to be here so they can take fire damage.
        # There are some units that do not add their new "replacement unit" to these lists. This is because it's not necessary.
            # These replacement units don't have a weapon and don't take a turn and can't take fire damage.
        self.playerunits = set() # All the units that the player has direct control over, including dead mech corpses
        self.nonplayerunits = [] # all the units that the player can't control. This includes enemies and friendly NPCs such as the train.
        self.hurtplayerunits = [] # a list of the player's units hurt by a single action. All units here must be checked for death after they all take damage and then this is reset.
        self.hurtpsion = None # This is set to a single psion that was damaged since there can never be more than 1 psion on the board at at time
        self.hurtenemies = [] # a list of all enemy units that were hurt during a single action. This includes robots
        self.postattackmoves = set() # a set of tuples of squares. This is for Goo units that need to move to their victim's squares "after" the attack.
                                #  If we don't do this, a goo will replace the unit it killed on the board, and then that unit will erase the goo when it's deaths replaces the square with None.
        self.psionPassiveTurn = None # This will be replaced by a method provided by the Regeneration and Hive Targeting (tentacle) psion effects that take a turn to do their effect.
        self.stormGeneratorTurn = None # This will be replaced by a method provided by the StormGenerator passive weapon
        self.visceraheal = 0 # The amount to heal a mech that killed a vek. Each vek that is killed grants this amount of hp healing
        self.otherpassives = set() # misc passives that only need to be checked for presence and nothing else.
        self.score = ScoreKeeper()
        self.actionlog = [] # a log of each action the player has taken in this particular game
        self.idcount = 0 # this is used to count unique numbers assigned to player-controlled units.
                        # this is needed so we can later find the corresponding unit in different game instances, after it has moved
    def flushHurt(self):
        "resolve the effects of hurt units, returns the number of enemies killed (for use with viscera nanobots). Tiles are damaged first, then Psions are killed, then your mechs can explode, then vek/bots can die"
        # print("hurtenemies:", self.hurtenemies)
        # print("hurtplayerunits:", self.hurtplayerunits)
        # print("hurtpsion:", self.hurtpsion)
        killedenemies = 0
        postattackmoves = self.postattackmoves
        self.postattackmoves = set()
        while True:
            # First, copy our collections of hurt units, as these units dying could explode and then hurt more, hence the while loop.
            hurtplayerunits = self.hurtplayerunits
            hurtenemies = self.hurtenemies
            self.hurtplayerunits = []
            self.hurtenemies = []
            try:  # signal to the powergrid to damage multiple buildings at once if we're using Powergrid_CriticalShields
                self.powergrid.flushHurt()
            except AttributeError:
                pass
            try:
                if self.hurtpsion._allowDeath():
                    killedenemies += 1
                self.hurtpsion = None
            except AttributeError:
                pass
            for hpu in hurtplayerunits:
                hpu.explode()
            for he in hurtenemies:
                if he._allowDeath():
                    killedenemies += 1
            for srcsquare, destsquare in postattackmoves:
                self.board[srcsquare].moveUnit(destsquare)
            if not (self.hurtenemies or self.hurtplayerunits or self.hurtpsion):
                return killedenemies
    def start(self):
        "Initialize the simulation. Run this after all units have been placed on the board."
        psionicreceiver = False
        for unit in self.playerunits:
            for weap in 'weapon1', 'weapon2':
                try:
                    getattr(unit, weap).enable()
                except AttributeError: # unit.None.enable(), or enable() doesn't exist
                    pass
                except FakeException: # This is raised by the psionic receiver
                    psionicreceiver = True
        for unit in self.nonplayerunits:
            if psionicreceiver:
                try:
                    unit.weapon1._enableMechs()
                except AttributeError:
                    continue
            try:
                unit.weapon1.enable()
            except AttributeError:
                pass
            try: # validate all enemy qshots
                unit.weapon1.validate()
            except AttributeError:
                pass
            try: # set companion tiles for multi-tile units
                unit._setCompanion()
            except AttributeError: # not a multi-tile unit
                pass
    def endPlayerTurn(self):
        """Simulate the outcome of this single turn, as if the player clicked the 'end turn' button in the game. Let the vek take their turn now.
        Order of turn operations:
           Fire
           Storm Smoke
           Regeneration / Psion Tentacle (Psion passive turn)
           Environment
           Enemy Actions
           NPC actions
           Enemies emerge
        """
        # Do the fire turn:
        for unit in self.playerunits: # copypasta instead of converting playerunits to a list
            if Effects.FIRE in unit.effects:
                unit.takeDamage(1, ignorearmor=True, ignoreacid=True)
        for unit in self.nonplayerunits: # fire damage seems to happen to vek in the order of their turn
            if Effects.FIRE in unit.effects:
                unit.takeDamage(1, ignorearmor=True, ignoreacid=True)
        self.flushHurt()
        try: # Do the storm generator turn:
            self.stormGeneratorTurn()
        except TypeError: # self.None()
            pass
        try: # Do the psion healing / regeneration turn
            self.psionPassiveTurn()
        except TypeError: # self.None()
            pass
        try: # run the environmental turn
            self.environeffect.run()
        except AttributeError: # self.None.run()
            pass
        # Now run the enemy's turn:
        for unit in self.nonplayerunits:
            if unit.alliance == Alliance.ENEMY:
                try:
                    unit.weapon1.shoot()
                except AttributeError: # unit.None.shoot()
                    pass
        # Now do NPC actions:
        for unit in self.nonplayerunits:
            if unit.alliance != Alliance.ENEMY:
                try:
                    unit.weapon1.shoot()
                except AttributeError: # unit.None.shoot()
                    pass
        self.vekemerge.run()
    def killMech(self, unit):
        """Run this to process a mech dying.
        unit is the mech unit in self.playerunits
        returns nothing, raises GameOver if the last mech dies."""
        self.playerunits.discard(unit)
        for u in self.playerunits:
            if u.isMech(): # if there is a live mech still in play, the game goes on
                return
        raise GameOver # if not, the game ends
    def getNextUnitID(self):
        "Increment self.idcount and return the next id to use"
        self.idcount += 1
        return self.idcount
    def getCopy(self):
        "return a copy of this game object and copies of all the objects it contains."
        try:
            environeffect = type(self.environeffect)(list(self.environeffect.squares)) # make a new environeffect object
        except (TypeError, AttributeError): # AttributeError: 'NoneType' object has no attribute 'squares'
            environeffect = None # set it to be none when passed in
        # create the new game object.
        newgame = Game({}, self.powergrid.hp, environeffect, Environ_VekEmerge(list(self.vekemerge.squares)))
        # Now go through each square and copy the properties of each to the new game object
        for letter in range(1, 9):
            for num in range(1, 9):
                newgame.board[(letter, num)] = self.board[(letter, num)].getCopy(newgame)
                try:
                    newgame.board[(letter, num)].createUnitHere(self.board[(letter, num)].unit.getCopy(newgame))
                except AttributeError: # None._addUnitToGame()
                    pass # there was no unit on this tile
        newgame.start()
        return newgame

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
    def isMoveBlocker(self):
        "return True if the unit blocks mech movement, False if it doesn't. Chasm tiles block movement, as well as all enemies and some other units."
        try:
            return self._blocksmove
        except AttributeError:
            return False

class Tile_Base(TileUnit_Base):
    """The base class for all Tiles, all other tiles are based on this. Mountains and buildings are considered units since they have HP and block movement on a tile, thus they go on top of the tile."""
    def __init__(self, game, square=None, type=None, effects=None, unit=None): # TODO: this unit argument is unreachable
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
        self._removeSmokeStormGen()
        for e in Effects.SMOKE, Effects.ACID:
            self.effects.discard(e) # Fire removes smoke and acid
        try:
            self.unit.applyFire()
        except AttributeError:
            return
    def applySmoke(self):
        "make a smoke cloud on the current tile"
        self.effects.discard(Effects.FIRE) # smoke removes fire
        self.effects.add(Effects.SMOKE)
        self._addSmokeStormGen(self.square)
        try:
            self.unit.effects.discard(Effects.FIRE) # a unit moving into smoke removes fire.
        except AttributeError: # self.None.effects.discard
            pass # no unit which is fine
        else:
            if Attributes.IMMUNESMOKE not in self.unit.attributes:
                try: # invalidate qshots of enemies that get smoked
                    self.unit.weapon1.qshot = None
                except AttributeError: # either there was no unit or the unit had no weapon
                    pass
                else:
                    if self.unit.alliance == Alliance.ENEMY: # if this was an enemy that was smoked, let's also break all its webs:
                        self.unit._breakAllWebs()
    def applyIce(self):
        "apply ice to the tile and unit."
        if not self.hasShieldedUnit():
            self.effects.discard(Effects.FIRE) # remove fire from the tile
            try:
                self.unit.applyIce() # give the unit ice
            except AttributeError: # None.applyIce()
                pass
    def applyAcid(self):
        try:
            self.unit.applyAcid()
        except (AttributeError, DontGiveUnitAcid): # the tile doesn't get acid if a unit is present to take it instead
            self.effects.add(Effects.ACID)
            self.effects.discard(Effects.FIRE)
    def applyShield(self):
        "Try to give a shield to a unit present. return True if a unit was shielded, False if there was no unit."
        try: # Tiles can't be shielded, only units
            self.unit.applyShield()
            return True
        except AttributeError:
            return False
    def repair(self, hp):
        "Repair this tile and any mech on it. hp is the amount of hp to repair on the present unit. This method should only be used for mechs and not vek as they can be healed but they never repair the tile."
        self.effects.discard(Effects.FIRE)
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
                self.effects.discard(Effects.ACID)
    def _tileTakeDamage(self):
        "Process the effects of the tile taking damage. returns nothing."
        pass
    def _putUnitHere(self, unit):
        """Run this method whenever a unit lands on this tile whether from the player moving or a unit getting pushed. unit can be None to get rid of a unit.
        If there's a unit already on the tile, it's overwritten but not properly deleted. returns nothing."""
        self.unit = unit
        try:
            self.unit.square = self.square
        except AttributeError: # raised by None.square
            return  # bail, the unit has been replaced by nothing which is ok.
        self._spreadEffects()
        try:
            self.unit.weapon1.validate()
        except AttributeError: # None.weapon1, _spreadEffects killed the unit or unit.None.validate(), unit didn't have a weapon1
            pass
    def createUnitHere(self, unit):
        "Run this method when putting a unit on the board for the first time. This ensures that the unit is sorted into the proper set in the game."
        unit._addUnitToGame()
        self._putUnitHere(unit)
    def replaceTile(self, newtile, keepeffects=True):
        """replace this tile with newtile. If keepeffects is True, add them to newtile without calling their apply methods.
        Warning: effects are given to the new tile even if it can't support them! For example, this will happily give a chasm fire or acid.
        Avoid this by manually removing these effects after the tile is replaced or setting keepeffects False and then manually keep only the effects you want."""
        unit = self.unit
        if keepeffects:
            newtile.effects.update(self.effects)
        newtile.square = self.square
        self.game.board[self.square] = newtile
        self.game.board[self.square]._putUnitHere(unit)
    def moveUnit(self, destsquare):
        "Move a unit from this square to destsquare, keeping the effects. This overwrites whatever is on destsquare! returns nothing."
        # assert Attributes.STABLE not in self.unit.attributes # the train is a stable unit that moves
        if destsquare == self.square:
            return # tried to move a unit to the same square it's already one. This had the unintended consequence of leaving the square blank!
        #print("moveUnit from", self.square, destsquare) # DEBUG
        self.unit._breakAllWebs()
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
            return False # There was no unit to push
        else: # push the unit
            destinationsquare = self.getRelSquare(direction, 1)
            try:
                self.game.board[destinationsquare].unit.takeBumpDamage() # try to have the destination unit take bump damage
            except AttributeError: # raised from None.takeBumpDamage, there is no unit there to bump into
                self.moveUnit(destinationsquare) # move the unit from this tile to destination square
            except KeyError:
                #raise # DEBUG
                return False # raised by self.board[None], attempted to push unit off the board, no action is taken
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
            raise InvalidDirection(direction)
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
        raise InvalidDirection(direction)
    def isSwallow(self):
        "return True if this tile kills non-massive non-flying units like water and chasm"
        try:
            return self._swallow
        except AttributeError:
            return False
    def isGrassland(self):
        try:
            return self._grassland
        except AttributeError:
            return False
    def _addSmokeStormGen(self, square):
        "This method is replaced by Weapon_StormGenerator when it is in play."
        pass
    def _removeSmokeStormGen(self):
        "This method is replaced by Weapon_StormGenerator when it is in play."
        pass
    def _pass(self, fakearg=None):
        "This is only here to replace the above 2 stormgem methods when destructing it."
        pass
    def getCopy(self, newgame):
        """return a copy of this tile for inclusion in a new copy of a game object
        newgame is the newgame object to be set.
        """
        return type(self)(newgame, self.square, effects=set(self.effects))
    def __str__(self):
        return "%s at %s. Effects: %s Unit: %s" % (self.type, self.square, set(Effects.pprint(self.effects)), self.unit)

class Tile_Ground(Tile_Base):
    "This is a normal ground tile."
    def __init__(self, game, square=None, type='ground', effects=None):
        super().__init__(game, square, type, effects=effects)
    def applyAcid(self):
        super().applyAcid()
        if not self.unit:
            self._tileTakeDamage()
    def applyFire(self):
        self._tileTakeDamage() # fire removes timepods and mines just like damage does
        super().applyFire()
    def _spreadEffects(self):
        "Ground tiles can have mines on them, but many other tile types can't."
        super()._spreadEffects()
        if Effects.MINE in self.effects:
            self.unit.die()
            self.effects.discard(Effects.MINE)
            self.game.score.submit(-3, 'mine_die')
        elif Effects.FREEZEMINE in self.effects:
            self.effects.discard(Effects.FREEZEMINE)
            self.unit.applyIce()
            self.game.score.submit(-3, 'freezemine_die')
        elif Effects.TIMEPOD in self.effects:
            if self.unit.alliance == Alliance.FRIENDLY:
                self.game.score.submit(2, 'timepod_pickup')
            else:
                self.game.score.submit(-30, 'timepod_die')
    def _tileTakeDamage(self):
        for (effect, event) in (Effects.TIMEPOD, 'timepod'), (Effects.MINE, 'mine'), (Effects.FREEZEMINE, 'freezemine'):
            try:
                self.effects.remove(effect)
            except KeyError:  # there was no effect on the tile
                pass
            else:
                getattr(self, '_{0}DieScore'.format(event))()

class Tile_Forest_Sand_Base(Tile_Base):
    "This is the base class for both Forest and Sand Tiles since they both share the same applyAcid mechanics."
    def __init__(self, game, square=None, type=None, effects=None):
        super().__init__(game, square, type, effects=effects)
    def applyAcid(self):
        try:
            self.unit.applyAcid() # give the unit acid if present
        except (AttributeError, DontGiveUnitAcid): # no unit present, so the tile gets acid
            self.effects.discard(Effects.FIRE) # fire is put out by acid.
            self.replaceTile(Tile_Ground(self.game, effects=(Effects.ACID,)), keepeffects=True) # Acid removes the forest/sand and makes it no longer flammable/smokable
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
        self.replaceTile(Tile_Ground(self.game, effects=(Effects.FIRE,)), keepeffects=True)  # Acid removes the forest/sand and makes it no longer flammable/smokable
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
            self.effects.discard(Effects.SUBMERGED)  # Remove the submerged effect from the newly spawned ice tile in case we just froze water.
            self.replaceTile(Tile_Ice(self.game))
        try:
            self.unit.applyIce()
        except AttributeError:
            return
    def applyFire(self):
        "Fire always removes smoke except over water and it removes acid from frozen acid tiles"
        for e in Effects.SMOKE, Effects.ACID:
            self.effects.discard(e)
        self._removeSmokeStormGen()
        try: # it's important that we set the unit on fire first. Otherwise the tile will be changed to water, then the unit will be set on fire in water. whoops.
            self.unit.applyFire()
        except AttributeError:
            pass
        self.replaceTile(Tile_Water(self.game))
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
        except (AttributeError, DontGiveUnitAcid):
            pass
        self.effects.add(Effects.ACID) # water gets acid regardless of a unit being there or not
    def _spreadEffects(self):
        if (Attributes.MASSIVE not in self.unit.attributes) and (Attributes.FLYING not in self.unit.attributes): # kill non-massive non-flying units that went into the water.
            self.unit.die()
        else: # the unit lived
            if Attributes.FLYING not in self.unit.attributes:
                self.unit.effects.discard(Effects.FIRE) # water puts out the fire, but if you're flying you remain on fire
                if Effects.ACID in self.effects: # spread acid from tile to unit but don't remove it from the tile
                    self.unit.applyAcid()
                if Effects.ACID in self.unit.effects: # if the unit has acid and is massive but not flying, spread acid from unit to tile
                    self.effects.add(Effects.ACID) # don't call self.applyAcid() here or it'll give it to the unit and not the tile.
                try: # if this was a massive vek boss that fell in the water...
                    self.unit.weapon1.qshot = None # invalidate his shot
                except AttributeError: # this has the side effect of giving mechs a qshot, but that shouldn't effect anything
                    pass
            self.unit.effects.discard(Effects.ICE) # water breaks you out of the ice no matter what

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
        self.replaceTile(Tile_Ice_Damaged(self.game))

class Tile_Ice_Damaged(Tile_Water_Ice_Damaged_Base):
    def __init__(self, game, square=None, type='ice_damaged', effects=None):
        super().__init__(game, square, type, effects=effects)
    def _tileTakeDamage(self):
        self.replaceTile(Tile_Water(self.game))

class Tile_Chasm(Tile_Base):
    "Non-flying units die when pushed into a chasm. Chasm tiles cannot have acid or fire, but can have smoke."
    _blocksmove = True
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
        except AttributeError: # there is no unit that can't take acid here
            return
    def _spreadEffects(self):
        if (Attributes.FLYING in self.unit.attributes) and (Effects.ICE not in self.unit.effects): # if the unit can fly and is not frozen...
            pass # congratulations, you live!
        else:
            self.unit.die()
            try:
                self.unit._realDeath() # try permanently killing a mech corpse
            except AttributeError:
                pass
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
        self._addSmokeStormGen(self.square)
    def _spreadEffects(self):
        if (Attributes.MASSIVE not in self.unit.attributes) and (Attributes.FLYING not in self.unit.attributes): # kill non-massive non-flying units that went into the water.
            self.unit.die()
        else: # the unit lived
            if Attributes.FLYING not in self.unit.attributes:
                self.unit.applyFire() # lava is always on fire, now you are too!
            self.unit.effects.discard(Effects.ICE) # water and lava breaks you out of the ice no matter what

class Tile_Grassland(Tile_Base):
    "Your bonus objective is to terraform Grassland tiles into Sand. This is mostly just a regular ground tile."
    def __init__(self, game, square=None, type='grassland', effects=None):
        super().__init__(game, square, type, effects=effects)
        self._grassland = True

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
        self.gotfire = self.gotacid = self.gotice = self.gotshield = False # These flags are set to true when this unit gets fire, acid, or ice applied to it.
        # This is done so we can avoid scoring a unit catching on fire and then dying from damage being more valuable than just killing the unit.
        self.lostfire = self.lostacid = self.lostice = self.lostshield = False # these flags are set to true when this unit loses fire, acid, or ice.
        self._initScore()
    def _applyEffectUnshielded(self, effect):
        "A helper method to check for the presence of a shield before applying an effect. return True if the effect was added, False if not."
        if Effects.SHIELD not in self.effects:
            self.effects.add(effect)
            return True
        return False
    def applyFire(self):
        if Effects.FIRE not in self.effects: # if we don't already have fire
            self._removeIce()
            if not Attributes.IMMUNEFIRE in self.attributes:
                if self._applyEffectUnshielded(Effects.FIRE): # no need to try to remove a timepod from a unit (from super())
                    self.gotfire = True
                    self.game.score.submit(self.score['fire_on'], '{0}_fire_on'.format(self.type))
    def applyIce(self):
        if Effects.ICE not in self.effects:
            if self._applyEffectUnshielded(Effects.ICE): # If a unit has a shield and someone tries to freeze it, NOTHING HAPPENS!
                self._removeFire()
                try:
                    self.weapon1.qshot = None # invalidate the unit's queued shot
                except AttributeError:  # self.None.qshot
                    pass
                self.gotice = True
                self.game.score.submit(self.score['ice_on'], '{0}_ice_on'.format(self.type))
                self.game.board[self.square]._spreadEffects() # spread effects after freezing because flying units frozen over chasms need to die
    def applyAcid(self, ignoreprotection=False):
        "give the unit acid. If ignoreprotection is True, don't check if the unit is protected by a shield or ice first (this is used by acid weapons). returns nothing."
        if Effects.ACID not in self.effects:
            if ignoreprotection:
                self.effects.add(Effects.ACID)
                self._applyAcidScore()
            elif self._applyEffectUnshielded(Effects.ACID): # you only get acid if you don't have a shield.
                self._applyAcidScore()
    def _applyAcidScore(self):
        "A helper method to score the unit getting acid."
        self.gotacid = True
        self.game.score.submit(self.score['acid_on'], '{0}_acid_on'.format(self.type))
    def applyWeb(self):
        self.effects.add(Effects.WEB)
    def applyShield(self):
        if Effects.SHIELD not in self.effects:
            self.effects.add(Effects.SHIELD)
            self.gotshield = True
            self.game.score.submit(self.score['shield_on'], '{0}_shield_on'.format(self.type))
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        """Process this unit taking damage. All effects are considered unless the ignore* flags are set in the arguments.
        Units will not die after reaching 0 hp here, run _allowDeath() to allow them to die. This is needed for vek units that can be killed and then pushed to do bump damage or spread effects.
        return False if ice or a shield blocked the damage, True otherwise."""
        if self._takeDamageProtected():
            if Attributes.ARMORED in self.attributes and Effects.ACID in self.effects: # if you have both armor and acid...
                pass # acid cancels out armored
            elif not ignorearmor and Attributes.ARMORED in self.attributes: # if we aren't ignoring armor and you're armored...
                damage -= 1 # damage reduced by 1
            elif not ignoreacid and Effects.ACID in self.effects: # if we're not ignoring acid and the unit has acid
                damage *= 2
            self.hp -= damage # the unit takes the damage
            self.damage_taken += damage
            self.game.score.submit(self.score['hurt'], '{0}_hurt'.format(self.type), damage)
            return True
    def _takeDamageProtected(self):
        "Check if there is a shield or ice on the unit before it takes damage. return True if there was no shield or ice, False if the damage was blocked by one of them."
        for effect, effname in (Effects.SHIELD, 'shield'), (Effects.ICE, 'ice'): # let the shield and then ice take the damage instead if present. Frozen units can have a shield over the ice, but not the other way around.
            try:
                self.effects.remove(effect)
            except KeyError:
                pass
            else:
                self.game.score.submit(self.score['{0}_off'.format(effname)], '{0}_{1}_off'.format(self.type, effname)) # score the shield or ice being lost
                self.game.board[self.square]._spreadEffects() # spread effects now that they lost a shield or ice
                return False # and then stop processing things, the shield or ice took the damage.
        return True
    def takeBumpDamage(self):
        "take damage from bumping. This is when you're pushed into something or a vek tries to emerge beneath you."
        self.takeDamage(1, ignorearmor=True, ignoreacid=True)
    def takeEmergeDamage(self):
        """Take damage from vek emerging below. Most of the time this is just normal bump damage, but mechs override this to take no damage with a certain passive."""
        self.takeBumpDamage()
    def _allowDeath(self):
        "Check if this unit was killed but had it's death suppressed. Kill it now if it has 0 or less hp."
        if self.hp <= 0:  # if the unit has no more HP and is allowed to die
            self.damage_taken += self.hp  # hp is now negative or 0. Adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead.
            self.die()
            return True
    def die(self):
        "Make the unit die. This method is not ok for mechs to use as they never leave acid where they die. They leave corpses which are also units."
        self.game.board[self.square].unit = None # it's dead, replace it with nothing
        self._removeUnitFromGame()
        if Effects.ACID in self.effects: # units that have acid leave acid on the tile when they die:
            self.game.board[self.square].applyAcid()
        self._breakAllWebs()
        self.explode()
        self._dieScore()
    def explode(self):
        "Make the unit explode only if it is explosive (to be used after death). Explosion damage ignores acid and armor."
        if Effects.EXPLOSIVE in self.effects:
            self.game.board[self.square].takeDamage(1, ignorearmor=True, ignoreacid=True) # take an additional damage on the square of the unit
            for d in Direction.gen(): # as well as around it
                try:
                    self.game.board[self.game.board[self.square].getRelSquare(d, 1)].takeDamage(1, ignorearmor=True, ignoreacid=True)
                except KeyError: # board[False]
                    pass
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
    def isMech(self):
        "return True if unit is a mech, False if it's not."
        return hasattr(self, 'repweapon') # only mechs have a repweapon slot
    def isNormalVek(self):
        "Return True if the unit is a vek THAT RECEIVES PSION BONUSES, false if it doesn't get buffs from a psion."
        try:
            return self._getspsionbonus
        except AttributeError:
            return False
    def isPsion(self):
        "return True if the unit is a psion, False if it isn't."
        try:
            return self._psion
        except AttributeError:
            return False
    def isRenfieldBomb(self):
        "return True if the unit is a renfield bomb (not prototype), False if it isn't."
        try:
            return self._renfieldbomb
        except AttributeError:
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
        "same as breakWeb except we remove all webs that this unit has. This method doesn't use arguments and propagates by default"
        for sq in self.web:
            self.game.board[sq].unit._breakWeb(self.square, prop=False)
        self.web = set()
    def _dieScore(self):
        "submit the score event for this unit dying and undo scoring of damage and effects to the unit. returns nothing"
        if self.damage_taken:
            self.game.score.undo(self.score['hurt'], '{0}_hurt'.format(self.type), self.damage_taken) # undo the damage that this unit took.
        # we want to avoid the situation of damaging something for 5 hp to kill it is more valuable than just pushing it into water.
        for onoff in ('got', 'on'), ('lost', 'off'):
            for effectname in 'fire', 'acid', 'ice', 'shield':
                if getattr(self, '{0}{1}'.format(onoff[0], effectname)):
                    event = '{0}_{1}'.format(effectname, onoff[1])
                    self.game.score.undo(self.score[event], '{0}_{1}'.format(self.type, event))
        self.game.score.submit(self.score['die'], '{0}_die'.format(self.type)) # score the actual death now.
    def _removeFire(self):
        "Remove fire from the unit and do scoring based on it."
        try:
            self.effects.remove(Effects.FIRE)
        except KeyError:
            pass
        else:
            self.game.score.submit(self.score['fire_off'], '{0}_fire_off'.format(self.type))
            self.lostfire = True
    def _removeIce(self):
        "Remove ice from the unit and do scoring based on it"
        try:
            self.effects.remove(Effects.ICE)
        except KeyError:
            pass
        else:
            self.game.score.submit(self.score['ice_off'], '{0}_ice_off'.format(self.type))
            self.lostice = True
    def _removeAcid(self):
        "Remove acid from the unit and do scoring."
        try:
            self.effects.remove(Effects.ACID)
        except KeyError:
            pass
        else:
            self.game.score.submit(self.score['acid_off'], '{0}_acid_off'.format(self.type))
            self.lostacid = True
    def _removeShield(self):
        "Remove the shield and do scoring."
        try:
            self.effects.remove(Effects.Shield)
        except KeyError:
            pass
        else:
            self.game.score.submit(self.score['shield_off'], '{0}_shield_off'.format(self.type))
            self.lostshield = True
    def getCopy(self, newgame):
        "return a copy of this unit object. newgame is the new game instance to assign to this newly created unit."
        newunit = type(self)(newgame, hp=self.hp, maxhp=self.maxhp, effects=set(self.effects), attributes=set(self.attributes))
        try:
            newunit.web = set(self.web)
        except NameError: # unit has no web because webs don't matter for this type of unit
            pass
        return newunit
    def _initScore(self):
        "This method is overridden by children to set up their score dicts. This one is a dummy."
        print("DEBUG: No _initScore() for unit {0}".format(self.type))
        self.score = {'fire_on': 0,
                      'fire_off': 0,
                      'ice_on': 0,
                      'ice_off': 0,
                      'acid_on': 0,
                      'acid_off': 0,
                      'shield_on': 0,
                      'shield_off': 0,
                      'hurt': 0,
                      'die': 0,
                      'heal': 0}
    def __str__(self):
        return "%s %s/%s HP. Effects: %s, Attributes: %s Webs: %s" % (self.type, self.hp, self.maxhp, set(Effects.pprint(self.effects)), set(Attributes.pprint(self.attributes)), self.web)

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
    def repairHP(self, amount=1):
        "Repair hp amount of hp. Does not take you higher than the max. Does not remove any effects."
        self.hp += amount
        if self.hp > self.maxhp:
            amount -= self.hp - self.maxhp
            self.hp = self.maxhp
        self.game.score.submit(self.score['heal'], '{0}_heal', amount)

class Unit_Unwebbable_Base():
    """A base class that provide blank web methods for units that aren't effected by webs.
    (NPC units and stable units)
    """
    def applyWeb(self):
        pass
    def _breakAllWebs(self):
        pass
    def _breakWeb(self, compsquare, prop=True):
        pass
    def _makeWeb(self, compsquare, prop=True):
        pass

class Unit_NoDelayedDeath_Base(Unit_Base, Unit_Unwebbable_Base):
    "A base class for units that get to bypass the hurt queues such as buildings and other neutral units."
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        res = super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
        super()._allowDeath()
        return res

class Unit_PlayerControlled_Base():
    "A base class that provides methods to add and remove units that the player controls to the game objects set. This is done on creation and death. Also allows movement."
    def _addUnitToGame(self):
        self.game.playerunits.add(self)
        self.id = self.game.getNextUnitID()
    def _removeUnitFromGame(self):
        self.game.playerunits.remove(self)
    def getMoves(self, moves):
        """Find out where this unit can move to in the current state of the gameboard and return it as a set of coordinate tuples.
        moves is the number of moves this unit has (int).
        returns a set-like dict_keys of squares of where this unit can travel to.
        It's important to note that that this list includes squares that are occupied by other units that you can pass through!
        Another part of the code must check if the square is occupied before actually moving you there.
        The square where the unit starts is not included.
        This method will return an empty set if you are unable to move due to web or ice

        Things that DO block movement:
        Enemies
          Blob
          Bots
          Volatile Vek
        Buildings
        Mountains
        Chasm Tiles
        Boulder/Rock
        AcidVat

        Things that DONT block movement:
        Mechs
          Frozen Mechs
          Mech Corpses
        Objective units
          Satellite Rocket (and corpse)
          Archive Tank
          Old Artillery
          Terraformer
          Earth Mover
          Train
          Acid Launcher
          Prototype Renfield Bomb
        Light Tank (deployable)
        Mine Bot (Technically an enemy)
        
        Flying lets you pass through anything."""
        if self.web or Effects.ICE in self.effects: # if you're webbed or frozen...
            return set() # you can't move
        self.positions = {}
        self._getMovesBranch(self.square, moves+1)
        del self.positions[self.square] # Don't include the starting position
        answer = self.positions.keys()
        del self.positions # positions is no longer needed, delete it to keep the size of the game obj down since it will be deepcopied many times.
        return answer
    def _getMovesBranch(self, position, moves):
        "recursive method used by getMoves() to build self.positions. returns nothing."
        if moves == 0:
            return
        self.positions[position] = moves
        for direction in Direction.gen():
            newsquare = self.game.board[position].getRelSquare(direction, 1)
            if not newsquare: # if the new square is off the board, move on
                continue
            if not self._isMoveObstruction(newsquare) and self.positions.get(newsquare, 0) < moves:
                self._getMovesBranch(newsquare, moves-1)
    def _isMoveObstruction(self, square):
        "pass in a square tuple and return True if the tile/unit obstructs movement, False if it doesn't."
        if Attributes.FLYING in self.attributes: # flying units can pass through any unit and tile
            return False
        try:
            if self.game.board[square].unit.isMoveBlocker(): # if the unit blocks movement:
                if self.getKwanMove() and self.game.board[square].unit.alliance == Alliance.ENEMY: # if the Kwan pilot is allowing this unit to move through enemies...
                    pass
                else:
                    return True # the unit blocks movement
        except AttributeError: # no unit on tile
            pass
        return self.game.board[square].isMoveBlocker() # if the tile blocks movement

class Unit_NonPlayerControlled_Base():
    "A base class that provides methods to add and remove units that the player doesn't control to the game objects set. This is done on creation and death."
    def _addUnitToGame(self):
        self.game.nonplayerunits.append(self)
    def _removeUnitFromGame(self):
        try:
            self.game.nonplayerunits.remove(self) # try to remove this dead unit
        except ValueError: # It's possible for an enemy to "die twice" in some circumstances, e.g. when you punch a vek and push him onto a mine.
            return  # the killing damage is dealt by the weapon, but the vek isn't killed by flushHurt() yet. It lands on the mine tile first where the mine detonates and kills it,
                    # removing it from game.nonplayerunits. If this is the case we can stop processing its death here.

class Unit_NonPlayerControlledIgnore_Base():
    "A base class that provides methods to skip the adding and removal of units that the player doesn't control. These units skip the lists and don't take turns and can't take fire damage."
    def _addUnitToGame(self):
        pass
    def _removeUnitFromGame(self):
        pass

##############################################################################
################################### MISC UNITS ###############################
##############################################################################
class Unit_Mountain_Building_Base(Unit_NoDelayedDeath_Base, Unit_NonPlayerControlledIgnore_Base):
    "The base class for mountains and buildings. They have special properties when it comes to fire and acid."
    blocksbeamshot = True  # this unit blocks beam shots that penetrate almost all other units.
    _blocksmove = True # Buildings and mountains block movement
    def __init__(self, game, type, hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.update((Attributes.STABLE, Attributes.IMMUNEFIRE))
    def applyFire(self):
        "mountains and buildingscan't be set on fire, but the tile they're on can!"
        pass
    def applyAcid(self, ignoreprotection=False):
        raise DontGiveUnitAcid # buildings and mountains can't gain acid, but the tile they're on can!. Raise this so the tile that tried to give acid to the present unit gets it instead.

class Unit_Mountain(Unit_Mountain_Building_Base):
    def __init__(self, game, type='mountain', attributes=None, effects=None):
        super().__init__(game, type=type, hp=1, maxhp=1, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self._mountain = True
    def _initScore(self):
        self.score = {#'fire_on': 0,
                      #'fire_off': 0,
                      'ice_on': 0,
                      'ice_off': 0,
                      #'acid_on': 0,
                      #'acid_off': 0,
                      'shield_on': 0,
                      'shield_off': 0,
                      'hurt': 0,
                      'die': 0,
                      #'heal': 0
                    }
    def applyAcid(self, ignoreprotection=False):
        pass
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "This takeDamage ignores the amount of damage dealt to the mountain and flattens it to 1."
        if self._takeDamageProtected():
            self.damage_taken += 1
            self.game.score.submit(self.score['hurt'], '{0}_hurt'.format(self.type), damage)
            self.game.board[self.square]._putUnitHere(Unit_Mountain_Damaged(self.game))

class Unit_Mountain_Damaged(Unit_Mountain):
    def __init__(self, game, type='mountaindamaged', effects=None):
        super().__init__(game, type=type, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "any damage to the mountain will kill it in it's damaged state."
        if self._takeDamageProtected():
            self.hp = 0 # required for PrimeSpear to detect a unit that died
            self._dieScore()
            self.game.board[self.square]._putUnitHere(None)

class Unit_Volcano(Unit_Mountain):
    "Indestructible volcano that blocks movement and projectiles."
    def __init__(self, game, type='volcano', effects=None):
        super().__init__(game, type=type, effects=effects)
        self.alliance = Alliance.NEUTRAL
    def _initScore(self):
        "we can get away with not scoring anything to do with volcanos since you can't really interact with them"
        return
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        return # what part of indestructible do you not understand?!
    def die(self):
        return # indestructible!
    def applyIce(self):
        "while volcanos can be frozen, it makes no difference in the game."
        return
    def applyShield(self):
        return
    def applyAcid(self, ignoreprotection=False):
        return

class Unit_Building(Unit_Mountain_Building_Base):
    def __init__(self, game, type='building', hp=1, maxhp=1, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.alliance = Alliance.NEUTRAL
        self._building = True # a flag to indicate this is a building rather than do string comparisons
    def _initScore(self):
        self.score = {#'fire_on': 0,
                      #'fire_off': 0,
                      'ice_on': 9,
                      'ice_off': -9,
                      #'acid_on': 0,
                      #'acid_off': 0,
                      'shield_on': 9,
                      'shield_off': -9,
                      'hurt': 0,
                      'die': 0,
                      #'heal': 0
                    }
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        orighp = self.hp
        if Passives.AUTOSHIELDS in self.game.otherpassives:
            super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
            # The only situation that should actually hit this is 0 < 1 < 2, meaning that the building had 2 hp and took 1 damage surviving the attack.
            if 0 < self.hp < orighp:
                self.applyShield() # the passive gives it a shield
        else:
            if super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid): # just run the parent's takeDamage
                if damage > orighp:
                    damage = orighp # flatten damage down to the hp of the building that died, otherwise hitting a 2hp building for 5 damage does 5 damage to powergrid :(
                self.game.powergrid.takeDamage(damage)

class Unit_Building_Objective(Unit_Building):
    alliance = Alliance.NEUTRAL
    _building = True
    def __init__(self, game, type='buildingobjective', hp=1, maxhp=1, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, effects=effects)
    def _initScore(self):
        self.score = {#'fire_on': 0,
                      #'fire_off': 0,
                      'ice_on': 0,
                      'ice_off': 0,
                      #'acid_on': 0,
                      #'acid_off': 0,
                      'shield_on': 0,
                      'shield_off': 0,
                      'hurt': -20,
                      'die': -20,
                      #'heal': 0
                    }

class Unit_Acid_Vat(Unit_NoDelayedDeath_Base, Unit_Unwebbable_Base, Unit_NonPlayerControlled_Base):
    alliance = Alliance.NEUTRAL
    _blocksmove = True
    def __init__(self, game, type='acidvat', hp=2, maxhp=2, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, effects=effects)
    def _initScore(self):
        self.score = {'fire_on': 6,
                      'fire_off': -6,
                      'ice_on': -6,
                      'ice_off': 6,
                      'acid_on': 2,
                      #'acid_off': 0,
                      'shield_on': -6,
                      'shield_off': 6,
                      'hurt': 10,
                      'die': 20,
                      #'heal': 0
                    }
    def die(self):
        "Acid vats turn into acid water when destroyed."
        self.game.board[self.square]._putUnitHere(None) # remove the unit before replacing the tile otherwise we get caught in an infinite loop of the vat starting to die,
                                                        # changing the ground to water, then dying again because it drowns in water.
        self._removeUnitFromGame()
        self.game.board[self.square].replaceTile(Tile_Water(self.game, effects=(Effects.ACID,)), keepeffects=True) # replace the tile with a water tile that has an acid effect and keep the old effects
        self.game.vekemerge.remove(self.square) # don't let vek emerge from this newly created acid water tile
        self.game.board[self.square].effects.discard(Effects.FIRE) # don't keep fire, this tile can't be on fire.

class Unit_Rock(Unit_NoDelayedDeath_Base, Unit_NonPlayerControlled_Base):
    alliance = Alliance.NEUTRAL
    _blocksmove = True
    def __init__(self, game, type='rock', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=1, maxhp=1, attributes=attributes, effects=effects)
    def _initScore(self):
        self.score = {'fire_on': 0,
                      'fire_off': 0,
                      'ice_on': 0,
                      'ice_off': 0,
                      'acid_on': 0,
                      'acid_off': 0,
                      'shield_on': 0,
                      'shield_off': 0,
                      'hurt': 0,
                      'die': 0,
                      #'heal': 0
                    }

############################################################################################################################
################################################### FRIENDLY Sub-Units #####################################################
############################################################################################################################
class Sub_Unit_Base(Unit_Fighting_Base, Unit_PlayerControlled_Base):
    "The base unit for smaller sub-units that the player controls as well as objective units that the player controls.."
    _repairdrop = True # indicates that this unit is healed by repairdrop
    def __init__(self, game, type, hp, maxhp, moves, weapon1=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.moves = moves
        self.alliance = Alliance.FRIENDLY
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        self.game.hurtplayerunits.append(self)
        return super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
    def die(self):
        super().die()

class Deployable_Tank_Base(Sub_Unit_Base):
    "A base unit for deployable tanks that only provides scoring."
    def _initScore(self):
        self.score = {'fire_on': -6,
                      'fire_off': 6,
                      'ice_on': -5,
                      'ice_off': 5,
                      'acid_on': -2,
                      'acid_off': 2,
                      'shield_on': 6,
                      'shield_off': -6,
                      'hurt': 10,
                      'die': -30,
                      'heal': 10
                      }

class Unit_AcidTank(Deployable_Tank_Base):
    def __init__(self, game, type='acidtank', hp=1, maxhp=1, weapon1=None, moves=3, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_FreezeTank(Deployable_Tank_Base):
    def __init__(self, game, type='freezetank', hp=1, maxhp=1, weapon1=None, moves=4, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_ArchiveTank(Deployable_Tank_Base):
    def __init__(self, game, type='archivetank', hp=1, maxhp=1, weapon1=None, moves=4, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_OldArtillery(Deployable_Tank_Base):
    def __init__(self, game, type='oldartillery', hp=2, maxhp=2, moves=1, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_OldEarthArtillery(), moves=moves, effects=effects, attributes=attributes)

class Unit_ShieldTank(Deployable_Tank_Base):
    def __init__(self, game, type='shieldtank', hp=1, maxhp=1, weapon1=None, moves=3, effects=None, attributes=None): # shield tanks can optionally have 3 hp with a power upgrade
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_LightTank(Deployable_Tank_Base):
    def __init__(self, game, type='lighttank', hp=1, maxhp=1, weapon1=None, moves=3, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

class Unit_PullTank(Deployable_Tank_Base):
    def __init__(self, game, type='pulltank', hp=1, maxhp=1, weapon1=None, moves=3, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, moves=moves, effects=effects, attributes=attributes)

##############################################################################
################################# OBJECTIVE UNITS ############################
##############################################################################
class Unit_MultiTile_Base(Unit_Base, Unit_Unwebbable_Base, Unit_NonPlayerControlled_Base):
    "This is the base class for multi-tile units such as the Dam and Train. Effects and damage to one unit also happens to the other."
    alliance = Alliance.NEUTRAL
    def __init__(self, game, type, hp, maxhp, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.update((Attributes.STABLE, Attributes.IMMUNEFIRE, Attributes.IMMUNESMOKE)) # these attributes are shared by the dam and train
        self.replicate = True # When this is true, we replicate actions to the other companion unit and we don't when False to avoid an infinite loop.
        self.deadfromdamage = False # Set this true when the unit has died from damage. If we don't, takeDamage() can happen to both tiles, triggering die() which would then replicate to the other causing it to die twice.
    def _replicate(self, meth, **kwargs):
        "Replicate an action from this unit to the other. meth is a string of the method to run. Returns nothing."
        if self.replicate:
            comptile = self.game.board[self.companion]
            comptile.unit.replicate = False
            try: # try running the companion's method as takeDamage() with keyword arguments
                getattr(comptile.unit, meth)(damage=kwargs['damage'], ignorearmor=kwargs['ignorearmor'], ignoreacid=kwargs['ignoreacid'])
            except KeyError: # else it's an applySomething() method with no args
                getattr(comptile, meth)()
            comptile.unit.replicate = True
    def applyIce(self):
        super().applyIce()
        self._replicate('applyIce')
    def applyAcid(self, ignoreprotection=False):
        super().applyAcid()
        self._replicate('applyAcid')
    def applyShield(self):
        super().applyShield()
        self._replicate('applyShield')
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "Process this unit taking damage. All effects are considered unless set to True in the arguments. Yes this is copypasta from the base, but we don't need to check for armored here."
        if self._takeDamageProtected():
            if not ignoreacid and Effects.ACID in self.effects: # if we're not ignoring acid and the unit has acid
                damage *= 2
            self.hp -= damage # the unit takes the damage
            self.damage_taken += damage
            self.game.score.submit(self.score['hurt'], '{0}_hurt'.format(self.type), damage)
            if self.hp <= 0:  # if the unit has no more HP
                self.damage_taken += self.hp  # hp is now negative or 0. Adjust damage_taken to ignore overkill. If the unit had 4 hp and it took 7 damage, we consider the unit as only taking 4 damage because overkill is useless. Dead is dead.
                self.deadfromdamage = True
                self.die()
            self._replicate('takeDamage', damage=damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
            return True
    # def _dieScore(self): # fuck it, let's just make the score for multi-tile units half of what they should be so when they count twice they add up to a whole unit :D
    #     "only count the death of this unit once, not once per tile"
    #     if self.replicate:
    #         super()._dieScore()

class Unit_Dam(Unit_MultiTile_Base):
    "When the Dam dies, it floods the middle of the map. Dam is not effected by RepairDrop."
    def __init__(self, game, type='dam', hp=2, maxhp=2, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.add(Attributes.MASSIVE)
    def _initScore(self):
        "These score events are done twice, once per each tile"
        self.score = {#'fire_on': -6,
                      #'fire_off': 6,
                      'ice_on': -2.5,
                      'ice_off': 2.5,
                      'acid_on': -1,
                      'acid_off': 1,
                      'shield_on': -2.5,
                      'shield_off': 2.5,
                      'hurt': 5,
                      'die': 10,
                      #'heal': 10
                      }
    def _setCompanion(self):
        "Set self.companion to the square of this unit's companion."
        if self.square[1] == 4:  # set the companion tile without user intervention since the dam is always on the same 2 tiles.
            self.companion = (8, 3)
        elif self.square[1] == 3:
            self.companion = (8, 4)
        else:
            raise CantHappenInGame
    def die(self):
        "Make the unit die."
        self._removeUnitFromGame()
        self.game.board[self.square]._putUnitHere(Unit_Volcano(self.game)) # it's dead, replace it with a volcano since there is an unmovable invincible unit there.
        # we also don't care about spreading acid back to the tile, nothing can ever spread them from these tiles.
        for x in range(7, 0, -1): # spread water from the tile closest to the dam away from it
            self.game.board[(x, self.square[1])].replaceTile(Tile_Water(self.game))
            self.game.vekemerge.remove((x, self.square[1])) # don't let vek emerge from these newly created water tiles
        if not self.deadfromdamage: # only replicate death if dam died from an instadeath call to die(). If damage killed this dam, let the damage replicate and kill the other companion.
            self._replicate('die')

class Unit_Train_Base(Unit_MultiTile_Base):
    "Base class for the undamaged train"
    _beamally = True
    def __init__(self, game, type=None, hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.update({Attributes.IMMUNEFIRE, Attributes.IMMUNESMOKE, Attributes.STABLE})
    def _initScore(self):
        "These score events are done twice, once per each tile"
        self.score = {#'fire_on': -6,
                      #'fire_off': 6,
                      'ice_on': 3,
                      'ice_off': -3,
                      'acid_on': 0,
                      'acid_off': 0,
                      'shield_on': 2.5,
                      'shield_off': -2.5,
                      'hurt': -5,
                      'die': -5,
                      #'heal': 10
                      }
    def die(self):
        "Make the unit die."
        # we also don't care about spreading acid back to the tile, nothing can ever spread them from these tiles.
        self._deathAction()
        if not self.deadfromdamage: # only replicate death if dam died from an instadeath call to die(). If damage killed this dam, let the damage replicate and kill the other companion.
            self._replicate('die')
    def applyAcid(self, ignoreprotection=False):
        "The train having acid has no consequence in the game. The train always has 1hp and leaves a corpse so it can't transfer acid anywhere"
        pass

class Unit_Train(Unit_Train_Base):
    def __init__(self, game, type='train', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.weapon1 = Weapon_ChooChoo()
        # close to copypasta from Unit_Fighting_Base
        self.weapon1.wieldingunit = self
        self.weapon1.game = self.game
        if Effects.ICE in self.effects: # Make qshot active if unit isn't frozen, nothing else will stop it from moving.
            self.weapon1.qshot = None
        else:
            self.weapon1.qshot = ()
    def _setCompanion(self):
        "Set the train's companion tile. This has to be run each time it moves forward."
        self.companion = (self.square[0]-1, self.square[1])
    def _deathAction(self):
        self._removeUnitFromGame()
        self.game.board[self.square]._putUnitHere(Unit_TrainDamaged(self.game))
        self.game.board[self.square].unit._setCompanion()

class Unit_TrainCaboose(Unit_Train_Base):
    def __init__(self, game, type='traincaboose', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
    def _setCompanion(self):
        "Set the train's companion tile. This has to be run each time it moves forward."
        self.companion = (self.square[0]+1, self.square[1])
    def _deathAction(self):
        self.game.board[self.square]._putUnitHere(Unit_TrainDamagedCaboose(self.game))
        self.game.board[self.square].unit._setCompanion()

class Unit_TrainDamaged_Base(Unit_Train):
    def __init__(self, game, type=None, hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
    def _deathAction(self):
        self.game.board[self.square]._putUnitHere(Unit_TrainCorpse(self.game))

class Unit_TrainDamaged(Unit_TrainDamaged_Base):
    def __init__(self, game, type='traindamaged', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)

class Unit_TrainDamagedCaboose(Unit_TrainDamaged_Base):
    def __init__(self, game, type='traindamagedcaboose', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)

class Unit_TrainCorpse(Unit_TrainCaboose):
    def __init__(self, game, type='traincorpse', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        return # invincible
    def die(self):
        return # invincible

class Unit_Terraformer(Sub_Unit_Base, Unit_Unwebbable_Base):
    def __init__(self, game, type='terraformer', hp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, weapon1=Weapon_Terraformer(), attributes=attributes, effects=effects)
        self.attributes.add(Attributes.STABLE)
    def _initScore(self):
        self.score = {'fire_on': -8,
                      'fire_off': 8,
                      'ice_on': -7,
                      'ice_off': 7,
                      'acid_on': -4,
                      'acid_off': 4,
                      'shield_on': 7,
                      'shield_off': -7,
                      'hurt': -15,
                      'die': -30,
                      'heal': 15
                    }

class Unit_AcidLauncher(Sub_Unit_Base, Unit_Unwebbable_Base):
    def __init__(self, game, type='acidlauncher', hp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, weapon1=Weapon_Disintegrator(), attributes=attributes, effects=effects)
        self.attributes.add(Attributes.STABLE)
    def _initScore(self):
        self.score = {'fire_on': -8,
                      'fire_off': 8,
                      'ice_on': -7,
                      'ice_off': 7,
                      'acid_on': -4,
                      'acid_off': 4,
                      'shield_on': 7,
                      'shield_off': -7,
                      'hurt': -15,
                      'die': -30,
                      'heal': 15
                    }

class Unit_SatelliteRocket(Unit_Fighting_Base, Unit_NoDelayedDeath_Base, Unit_NonPlayerControlled_Base):
    alliance = Alliance.NEUTRAL
    # is not a beamally
    def __init__(self, game, type='satelliterocket', hp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SatelliteLaunch(), attributes=attributes, effects=effects)
        self.moves = moves
        self.attributes.add(Attributes.STABLE)
    def _initScore(self):
        self.score = {'fire_on': -8,
                      'fire_off': 8,
                      'ice_on': -7,
                      'ice_off': 7,
                      'acid_on': -4,
                      'acid_off': 4,
                      'shield_on': 7,
                      'shield_off': -7,
                      'hurt': -15,
                      'die': -30,
                      'heal': 15
                    }
    def die(self):
        super().die()
        self.game.board[self.square]._putUnitHere(Unit_SatelliteRocketCorpse(self.game))

class Unit_SatelliteRocketCorpse(Unit_Fighting_Base, Unit_Unwebbable_Base):
    alliance = Alliance.NEUTRAL
    def __init__(self, game, type='satelliterocketcorpse', hp=1, maxhp=1, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.add(Attributes.STABLE)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        return # invincible
    def die(self):
        return # invincible
    def _initScore(self):
        self.score = {'fire_on': 0,
                      'fire_off': 0,
                      'ice_on': 0,
                      'ice_off': 0,
                      'acid_on': 0,
                      'acid_off': 0,
                      'shield_on': 0,
                      'shield_off': 0,
                      'hurt': 0,
                      'die': 0,
                      'heal': 0
                    }

class Unit_EarthMover(Sub_Unit_Base, Unit_Unwebbable_Base):
    "This unit doesn't get a weapon because its effect doesn't matter for a single turn."
    _beamally = True
    alliance = Alliance.NEUTRAL
    def __init__(self, game, type='earthmover', hp=2, maxhp=2, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, moves=moves, attributes=attributes, effects=effects)
        self.attributes.add(Attributes.STABLE)
    def _initScore(self):
        self.score = {'fire_on': -8,
                      'fire_off': 8,
                      'ice_on': 7,
                      'ice_off': -7,
                      'acid_on': -4,
                      'acid_off': 4,
                      'shield_on': 7,
                      'shield_off': -7,
                      'hurt': -15,
                      'die': -30,
                      'heal': 15
                    }
    def die(self):
        super().die()
        self.game.board[self.square]._putUnitHere(Unit_EarthMoveCorpse(self.game))

class Unit_EarthMoveCorpse(Unit_SatelliteRocketCorpse):
    def __init__(self, game, type='earthmovercorpse', hp=1, maxhp=1, moves=0, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)

class Unit_PrototypeRenfieldBomb(Unit_Base, Unit_Unwebbable_Base, Unit_NonPlayerControlledIgnore_Base):
    alliance = Alliance.NEUTRAL
    _beamally = True
    def __init__(self, game, type='prototypebomb', hp=1, maxhp=1, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.effects.add(Effects.EXPLOSIVE)
        self.attributes.add(Attributes.IMMUNEFIRE)
    def _initScore(self):
        self.score = {#'fire_on': -8, immune to fire
                      #'fire_off': 8,
                      'ice_on': 7,
                      'ice_off': -7,
                      'acid_on': 0, # 1 hp, acid, damage, and healing doesn't matter
                      'acid_off': 0,
                      'shield_on': 7,
                      'shield_off': -7,
                      'hurt': 0,
                      'die': -30,
                      'heal': 0
                    }

class Unit_RenfieldBomb(Unit_Base, Unit_Unwebbable_Base, Unit_NonPlayerControlledIgnore_Base):
    alliance = Alliance.NEUTRAL
    _beamally = True
    _renfieldbomb = True
    def __init__(self, game, type='renfieldbomb', hp=4, maxhp=4, attributes=None, effects=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, attributes=attributes, effects=effects)
        self.attributes.add(Attributes.IMMUNEFIRE)
    def _initScore(self):
        self.score = {'fire_on': -8,
                      'fire_off': 8,
                      'ice_on': 7,
                      'ice_off': -7,
                      'acid_on': -4,
                      'acid_off': 4,
                      'shield_on': 7,
                      'shield_off': -7,
                      'hurt': -15,
                      'die': -30,
                      'heal': 15
                    }

############################################################################################################################
###################################################### ENEMY UNITS #########################################################
############################################################################################################################
class Unit_Enemy_Base(Unit_Repairable_Base, Unit_Unwebbable_Base, Unit_NonPlayerControlled_Base):
    "A base class for almost all enemies."
    alliance = Alliance.ENEMY
    _blocksmove = True
    def __init__(self, game, type, hp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
    def _initScore(self):
        self.score = {'fire_on': 6,
                      'fire_off': -6,
                      'ice_on': 6,
                      'ice_off': -6,
                      'acid_on': 6,
                      'acid_off': -6,
                      'shield_on': -6,
                      'shield_off': 6,
                      'hurt': 10,
                      'die': 11 * self.maxhp,
                      'heal': 10
                    }

class Unit_Vek_Base():
    "A base class for all vek, including psions but excluding bots and minions."
    def takeBumpDamage(self):
        "Veks take extra bump damage when ForceAmp is in play."
        if Passives.FORCEAMP in self.game.otherpassives:
            self.takeDamage(2, ignorearmor=True, ignoreacid=True)
        else:
            self.takeDamage(1, ignorearmor=True, ignoreacid=True)

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
        if self.hp > 0: # Only add hurt enemies to the list if they're still alive. Before doing this, a vek could be killed, explode, take more damage and explode again.
            self.game.hurtenemies.append(self)  # add it to the queue of units to be killed at the same time
        return super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)

class Unit_NormalVek_Base(Unit_Vek_Base, Unit_EnemyNonPsion_Base):
    "A base class for all vek who benefit from psions. Not bots, psions, bosses, or minions."
    _getspsionbonus = True

class Unit_NormalVekFlying_Base(Unit_EnemyNonPsion_Base):
    "A simple base unit for flying vek."
    def __init__(self, game, type, hp, maxhp, weapon1=None, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_Psion_Base(Unit_Vek_Base, Unit_EnemyNonPsion_Base):
    "Base unit for vek psions. When psions are hurt, their deaths are resolved first before your mechs or other vek/bots."
    _psion = True
    def __init__(self, game, type, hp, maxhp, weapon1=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        "Psions die before units so they go to a special place when damaged."
        self.game.hurtpsion = self
        return Unit_Enemy_Base.takeDamage(self, damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
        # we need to skip Unit_EnemyNonPsion_Base's takeDamage() because it adds hurt units to hurtenemies
    def die(self):
        self.weapon1.disable()
        super().die()

class Unit_EnemyBurrower_Base(Unit_NormalVek_Base):
    "A simple base class for the only 2 burrowers in the game."
    def __init__(self, game, type, hp, maxhp, weapon1=None, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.update((Attributes.BURROWER, Attributes.STABLE))
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
        if self.hp > 0: # if burrower didn't die...
            self._burrow()
    def _burrow(self):
        "Burrow the unit underground, removing fire if present."
        self.game.board[self.square].unit = None # The unit is gone from the board, but still present otherwise.
        self.weapon1.qshot = None # cancel the unit's attack.
        self._removeFire()

class Unit_EnemyLeader_Base(Unit_NormalVek_Base):
    "A simple base class for Massive bosses."
    def __init__(self, game, type, hp, maxhp, weapon1=None, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.MASSIVE)
        self.score['die'] = 12 * self.maxhp

class Unit_Blobber(Unit_NormalVek_Base):
    "The Blobber doesn't have a direct attack."
    def __init__(self, game, type='blobber', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_UnstableGrowths(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaBlobber(Unit_NormalVek_Base):
    "Also has no direct attack."
    def __init__(self, game, type='alphablobber', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_UnstableGuts(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Scorpion(Unit_NormalVek_Base):
    def __init__(self, game, type='scorpion', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_StingingSpinneret(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_VolatileVek(Unit_NormalVek_Base):
    def __init__(self, game, type='volatilevek', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_StingingSpinneret(), qshot=qshot, effects=effects, attributes=attributes)
        self.effects.add(Effects.EXPLOSIVE)

class Unit_AlphaScorpion(Unit_NormalVek_Base):
    def __init__(self, game, type='alphascorpion', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_GoringSpinneret(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Firefly(Unit_NormalVek_Base):
    def __init__(self, game, type='firefly', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AcceleratingThorax(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaFirefly(Unit_NormalVek_Base):
    def __init__(self, game, type='alphascorpion', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_EnhancedThorax(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Leaper(Unit_NormalVek_Base):
    def __init__(self, game, type='leaper', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Fangs(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaLeaper(Unit_NormalVek_Base):
    def __init__(self, game, type='alphaleaper', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SharpenedFangs(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Beetle(Unit_NormalVek_Base):
    def __init__(self, game, type='beetle', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Pincers(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaBeetle(Unit_NormalVek_Base):
    def __init__(self, game, type='alphabeetle', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SharpenedPincers(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Scarab(Unit_NormalVek_Base):
    def __init__(self, game, type='scarab', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SpittingGlands(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaScarab(Unit_NormalVek_Base):
    def __init__(self, game, type='alphascarab', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AlphaSpittingGlands(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Crab(Unit_NormalVek_Base):
    def __init__(self, game, type='crab', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_ExplosiveExpulsions(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaCrab(Unit_NormalVek_Base):
    def __init__(self, game, type='alphacrab', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AlphaExplosiveExpulsions(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Centipede(Unit_NormalVek_Base):
    def __init__(self, game, type='centipede', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AcidicVomit(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaCentipede(Unit_NormalVek_Base):
    def __init__(self, game, type='alphacentipede', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_CorrosiveVomit(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Digger(Unit_NormalVek_Base):
    def __init__(self, game, type='digger', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_DiggingTusks(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaDigger(Unit_NormalVek_Base):
    def __init__(self, game, type='alphadigger', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_AlphaDiggingTusks(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Hornet(Unit_NormalVekFlying_Base):
    def __init__(self, game, type='hornet', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Stinger(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaHornet(Unit_NormalVekFlying_Base):
    def __init__(self, game, type='alphahornet', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_LaunchingStinger(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_SoldierPsion(Unit_Psion_Base):
    def __init__(self, game, type='soldierpsion', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_InvigoratingSpores(), effects=effects, attributes=attributes)

class Unit_ShellPsion(Unit_Psion_Base):
    def __init__(self, game, type='shellpsion', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_HardenedCarapace(), effects=effects, attributes=attributes)

class Unit_BloodPsion(Unit_Psion_Base):
    def __init__(self, game, type='bloodpsion', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Regeneration(), effects=effects, attributes=attributes)

class Unit_BlastPsion(Unit_Psion_Base):
    def __init__(self, game, type='blastpsion', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_ExplosiveDecay(), effects=effects, attributes=attributes)

class Unit_PsionTyrant(Unit_Psion_Base):
    def __init__(self, game, type='psiontyrant', hp=2, maxhp=2, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_HiveTargeting(), effects=effects, attributes=attributes)

class Unit_Spider(Unit_NormalVek_Base):
    def __init__(self, game, type='spider', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_TinyOffspring(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaSpider(Unit_NormalVek_Base):
    def __init__(self, game, type='alphaspider', hp=4, maxhp=4, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_LargeOffspring(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Burrower(Unit_EnemyBurrower_Base):
    def __init__(self, game, type='burrower', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SpikedCarapace(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaBurrower(Unit_EnemyBurrower_Base):
    def __init__(self, game, type='alphaburrower', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_BladedCarapace(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_BeetleLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='beetleleader', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_FlamingAbdomen(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_LargeGoo(Unit_EnemyLeader_Base):
    def __init__(self, game, type='largegoo', hp=3, maxhp=3, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_GooAttack(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_MediumGoo(Unit_EnemyLeader_Base):
    def __init__(self, game, type='mediumgoo', hp=2, maxhp=2, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_GooAttack(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_SmallGoo(Unit_EnemyLeader_Base):
    def __init__(self, game, type='smallgoo', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_GooAttack(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_HornetLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='hornetleader', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SuperStinger(), qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.FLYING)

class Unit_PsionAbomination(Unit_Psion_Base):
    def __init__(self, game, type='psionabomination', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Overpowered(), effects=effects, attributes=attributes)
        self.attributes.add(Attributes.MASSIVE)

class Unit_ScorpionLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='scorpionleader', hp=7, maxhp=7, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_MassiveSpinneret(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_FireflyLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='fireflyleader', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_BurningThorax(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_SpiderLeader(Unit_EnemyLeader_Base):
    def __init__(self, game, type='spiderleader', hp=6, maxhp=6, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_PlentifulOffspring(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaBlob(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='alphablob', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_VolatileGuts(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Blob(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type='blob', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_UnstableGuts(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_SpiderlingEgg(Unit_EnemyNonPsion_Base):
    "Spiderling eggs are not considered normal vek, they don't get effects from psions"
    def __init__(self, game, type='spiderlingegg', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SpiderlingEgg(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_Spiderling(Unit_NormalVek_Base):
    "Spiderlings themselves do get psion passives however."
    def __init__(self, game, type='spiderling', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_TinyMandibles(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_AlphaSpiderling(Unit_NormalVek_Base):
    def __init__(self, game, type='alphaspiderling', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_TinyMandiblesAlpha(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_EnemyBot_Base(Unit_EnemyNonPsion_Base):
    def __init__(self, game, type, hp=1, maxhp=1, weapon1=None, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, qshot=qshot, effects=effects, attributes=attributes)

class Unit_CannonBot(Unit_EnemyBot_Base):
    def __init__(self, game, type='cannonbot', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Cannon8RMarkI(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_CannonMech(Unit_EnemyBot_Base):
    def __init__(self, game, type='cannonmech', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Cannon8RMarkII(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_ArtilleryBot(Unit_EnemyBot_Base):
    def __init__(self, game, type='artillerybot', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Vk8RocketsMarkI(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_ArtilleryMech(Unit_EnemyBot_Base):
    def __init__(self, game, type='artillerymech', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Vk8RocketsMarkII(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_LaserBot(Unit_EnemyBot_Base):
    def __init__(self, game, type='laserbot', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_BKRBeamMarkI(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_LaserMech(Unit_EnemyBot_Base):
    def __init__(self, game, type='lasermech', hp=1, maxhp=1, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_BKRBeamMarkII(), qshot=qshot, effects=effects, attributes=attributes)

class Unit_MineBot(Unit_EnemyBot_Base):
    _blocksmove = False # the minebot actually does not block movement even though it's an enemy. I guess because it's an enemy you need to protect.
    def __init__(self, game, type='minebot', hp=1, maxhp=1, qshot=None, effects=None, attributes=None): # this unit doesn't get a weapon.
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=None, qshot=qshot, effects=effects, attributes=attributes)
    def _initScore(self):
        self.score = {'fire_on': -6,
                      'fire_off': 6,
                      'ice_on': 6,
                      'ice_off': -6,
                      'acid_on': 0,
                      'acid_off': 0,
                      'shield_on': 6,
                      'shield_off': -6,
                      'hurt': 10,
                      'die': -20,
                      'heal': 10
                    }

class Unit_BotLeader_Attacking(Unit_EnemyBot_Base):
    def __init__(self, game, type='botleaderattacking', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_Vk8RocketsMarkIII(), qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.MASSIVE)
        self.score['die'] = 12 * self.maxhp

class Unit_BotLeader_Healing(Unit_EnemyBot_Base):
    def __init__(self, game, type='botleaderhealing', hp=5, maxhp=5, qshot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=Weapon_SelfRepair(), qshot=qshot, effects=effects, attributes=attributes)
        self.attributes.add(Attributes.MASSIVE)
        self.score['die'] = 12 * self.maxhp

############################################################################################################################
##################################################### FRIENDLY MECHS #######################################################
############################################################################################################################
class Unit_Mech_Base(Unit_Repairable_Base, Unit_PlayerControlled_Base):
    "This is the base unit of Mechs."
    alliance = Alliance.FRIENDLY  # and friendly, duh
    def __init__(self, game, type, hp, maxhp, moves, repweapon=None, weapon1=None, weapon2=None, pilot=None, effects=None, attributes=None):
        super().__init__(game, type=type, hp=hp, maxhp=maxhp, weapon1=weapon1, effects=effects, attributes=attributes)
        self.moves = moves # how many moves the mech has
        self.attributes.add(Attributes.MASSIVE) # all mechs are massive

        try: # see if there's a pilot that provides something
            pilot.mech = self
        except AttributeError:
            pass # there isn't, that's fine
        else: # there was a pilot
            pilot.enable()

        # repweapon is the weapon that is fired when a mech repairs itself. Every mech must have some type of repair weapon
        try: # see if the pilot provided a repweapon
            self.repweapon.game = self.game
        except AttributeError: # it didn't
            try: # check if there was a repweapon passed in
                repweapon.game = self.game
            except AttributeError: # there wasn't so just set a default
                self.repweapon = Weapon_Repair()
                self.repweapon.game = self.game
            else:
                self.repweapon = repweapon
        self.repweapon.wieldingunit = self

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
            if Effects.EXPLOSIVE in self.effects: # if the mech that died was explosive, the corpse needs to be explosive and explode
                self.game.board[self.square].unit.effects.add(Effects.EXPLOSIVE)
        self.game.killMech(self)
        self._dieScore()
    def repair(self, hp, ignorerepairfield=False):
        "Repair the unit healing hp and removing bad effects. ignorerepairfield is set to True by _repairField() to make sure we don't get stuck in a loop."
        if ignorerepairfield or not self._repairField():
            self.repairHP(hp)
            for effect, effectname in (Effects.FIRE, 'fire'), (Effects.ACID, 'acid'), (Effects.ICE, 'ice'):
                try: # try removing bad effects
                    self.effects.remove(effect)
                except KeyError:
                    pass
                else:
                    if getattr(self, 'got{0}'.format(effectname)): # if we got the effect during this turn, undo getting it
                        event = '{0}_on'.format(effectname)
                        self.game.score.undo(self.score[event], '{0}_{1}'.format(self.type, event))
                    self.game.score.submit(self.score['{0}_off'.format(effectname)], '{0}_{1}_off'.format(self.type, effectname)) # score getting rid of the bad effect
    def _repairField(self):
        "Repair all your mechs if the repairfield passive is in play. Returns True if it was and the healing was done, False if the passive wasn't active."
        if Passives.REPAIRFIELD in self.game.otherpassives:
            for u in self.game.playerunits.copy():
                try:
                    u.repair(1, ignorerepairfield=True)
                except AttributeError:
                    pass # subunits don't have a repair method, so just try to repair every player controlled unit
            return True
        return False
    def takeDamage(self, damage, ignorearmor=False, ignoreacid=False):
        res = super().takeDamage(damage, ignorearmor=ignorearmor, ignoreacid=ignoreacid)
        self._allowDeath()  # mechs die right away, but explosions are delayed so the corpse actually explodes
        return res
    def takeEmergeDamage(self):
        "A special method that only mechs have for taking damage from emerging vek. This is done so we can take the passive Stabilizers into effect."
        if Passives.STABILIZERS in self.game.otherpassives:
            return
        self.takeBumpDamage()
    def _initScore(self):
        self.score = {'fire_on': -6,
                      'fire_off': 6,
                      'ice_on': -6,
                      'ice_off': 6,
                      'acid_on': -6,
                      'acid_off': 6,
                      'shield_on': 6,
                      'shield_off': -6,
                      'hurt': -15,
                      'die': -15 * self.maxhp,
                      'heal': 15
                    } # TODO: score pilot deaths?
    def canDoubleShot(self):
        "return True if this unit can shoot twice due to Silica's doubleshot, False if not."
        try:
            return self.doubleshot
        except AttributeError:
            return False
    def getSecondaryMoves(self):
        ":return These are moves that you make after shooting, only pilots can enable this"
        try:
            return self.secondarymoves
        except AttributeError:
            return 0
    def getKwanMove(self):
        ":return This is set to True when HenryKwan allows the mech to move through enemy units"
        try:
            return self.kwanmove
        except AttributeError:
            return False

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
    def repair(self, hp, ignorerepairfield=True):
        "repair the mech corpse back to unit it was. ignorerepairfield is ironically ignored itself."
        self.oldunit.repairHP(hp)
        self._revive()
    def _revive(self):
        "Revive the corpse into a mech. returns nothing"
        try:
            self.oldunit.effects.remove(Effects.FIRE)  # fire is removed revived mechs. They get fire again if they're revived on a fire tile.
        except KeyError:
            pass
        else:
            self.game.score.submit(self.score['fire_off'], '{0}_fire_off'.format(self.type)) # score getting rid of fire
        self.game.board[self.square].createUnitHere(self.oldunit)
    def _realDeath(self):
        "This method removes the mech corpse from the game. This kind of death can only be achieved by pushing a mech corpse into a chasm tile (or a flying mech dying over a chasm). returns nothing"
        super()._removeUnitFromGame()
    def isMech(self):
        "A mech corpse is NOT considered a mech even though it has the repweapon attribute."
        return False

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
                self.game.board[square].effects.discard(e)

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
            tile = self.game.board[square]
            try:
                tile.unit.takeEmergeDamage()
            except AttributeError: # there was no unit
                if (Effects.FIRE in tile.effects) or (Effects.ACID in tile.effects):
                    self.game.score.submit(7, 'vek_emerge_fire_or_acid')
                else:
                    self.game.score.submit(-2, 'vek_emerge')
            else:
                self.game.flushHurt() # let the unit that took this bump damage die
    def remove(self, square):
        "remove square from self.squares, ignoring if it wasn't there in the first place. returns nothing."
        try:
            self.squares.remove(square)
        except ValueError:
            pass
        else:
            self.game.score.submit(12, 'vek_emerge_removed')

##############################################################################
################################## WEAPONS ###################################
##############################################################################
# all weapons must accept power1 and power2 arguments even if the weapon doesn't actually support upgrades.
# All weapons must have a shoot() method to shoot the weapon.
# All weapons must have a genShots() method to generate all possible shots the wieldingunit in its current position with this weapon can take. It must yield tuples which are arguments to the weapon's shoot() method.
    # genShots() should generate a shot to take, but not test the entire state of the board to ensure it is valid. It makes more sense to have shoot() invalidate the shot when it discovers that it's invalid.
    # That way if it is valid, we may have temporary variables ready to go for the shot and we avoided checking to see if it's valid twice.
    # The weapon should raise NullWeaponShot when it detects an invalid shot. The board MUST NOT be changed before NullWeaponShot is raised (because we'll try the next shot then and there without generating an entire new board).
# Any weapons that deal damage must store the amount of damage as self.damage
# Any weapons that deal self damage must store the amount of damage as self.selfdamage
# Any weapons that have limited range must store their range as self.range
# Weapons with limited uses must accept the argument ammo=int() in __init__(). Set the number of uses left as self.ammo
# self.game will be set by the unit that owns the weapon.
# self.wieldingunit is the unit that owns the weapon. It will be set by the unit that owns the weapon.
# All mech weapons are assumed to be enabled whether they require power or not. If your mech has an unpowered weapon, it's totally useless to us here.
# All weapons must have a getCopy() method that returns a copy of the object.

#class Weapon_Base(): XXX TODO
#    "Weapon base object"
#    def getCopy(self):
#        "By default, return a new obj of the same type WITHOUT copying any of the weapon's attributes"
#        return type(self)

# Generator base classes:
class Weapon_DirectionalGen_Base():
    "The base class for weapons that only need a direction to be shot, like projectiles."
    def genShots(self):
        for d in Direction.gen():
            yield (d,)

class Weapon_ArtilleryGen_Base():
    "The generator for artillery weapons."
    def genShots(self, minimumdistance=2):
        """Generate every possible shot that the weapon wielder can take from their position with an artillery weapon.
        Yields a tuple of ((x, y), direction). x, y are the coordinates where the weapon should strike and direction is the direction the weapon is being fired.
        minimumdistance is how near the wielder the weapon can shoot. Artillery weapons typically can't shoot the square next to them, but Hydraulic Legs can.
        genShots() methods usually don't take arguments, only child objects should use this argument.
        This genShots can only return valid shots by nature, no need to validate them in weapons that use this."""
        for direction in Direction.gen():
            relativedistance = minimumdistance  # artillery weapons can't shoot the tile next to them, they start at one tile past that.
            while True:
                targetsquare = self.game.board[self.wieldingunit.square].getRelSquare(direction, relativedistance)
                if targetsquare:
                    yield (targetsquare, direction)
                    relativedistance += 1
                else:  # square was false, we went off the board
                    break  # move onto the next direction

class Weapon_NoChoiceGen_Base():
    "A generator for weapons that give you no options of how you can fire it, e.g. Repulse, Self-destruct"
    def genShots(self):
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
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo

class Weapon_PushProjectile_Base():
    def _pushProjectile(self, direction, targetsquare):
        "Push targetsquare all directions except for the one the shot came from."
        for d in list(Direction.genPerp(direction)) + [direction]:  # push all BUT ONE of the tiles around targetsquare. The excluded tile is the one opposite the direction of fire
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(d, 1)].push(d)
            except KeyError:  # game.board[False]
                pass

class Weapon_LimitedUnlimitedInit_Base():
    def __init__(self, power1=False, power2=False, ammo=1):
        "an init where power1 provides infinite uses and power2 does nothing."
        if power1:
            self.ammo = -1 # easier than making it actually unlimited.
        else:
            self.ammo = ammo

class Weapon_SpendAmmo_Base():
    "Provides a method to spend limited ammo."
    def _spendAmmo(self):
        "Spend ammo if we have it, raise OutOfAmmo if we don't."
        if self.ammo == 0:
            raise OutOfAmmo
        self.ammo -= 1

class Weapon_DeploySelfEffectLimitedSmall_Base(Weapon_SpendAmmo_Base):
    def shoot(self, methname):
        "A shared shoot method for weapons that deploy an effect on themselves and to tiles around the weapon wielder. methname is a string of the effect method to call like 'applySmoke'"
        self._spendAmmo()
        getattr(self.game.board[self.wieldingunit.square], methname)() # do the effect on yourself
        for dir in Direction.gen():
            try:
                getattr(self.game.board[self._getRelSquare(dir, 1)], methname)()
            except KeyError: # board[False]
                pass

class Weapon_DeploySelfEffectLimitedLarge_Base(Weapon_SpendAmmo_Base):
    def shoot_big(self, methname):
        "A shared shoot method for weapons that deploy an effect on themselves and to a larger area of tiles around the weapon wielder. methname is a string of the effect method to call like 'applySmoke'"
        self._spendAmmo()
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

class Weapon_BlocksBeamShot_Base():
    "Provides a method shared by BurstBeam and BKRBeam used by bots"
    def blocksBeamShot(self, unit):
        "Return True if unit will block a beam shot that usually penetrates, False if we can penetrate through it."
        try:
            return unit.blocksbeamshot
        except AttributeError:  # units that allow penetration don't have this attribute set at all
            return False

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

class Weapon_TemperatureBeam_Base(Weapon_DirectionalGen_Base, Weapon_SpendAmmo_Base):
    "A base class for both the FireBeam and FrostBeam."
    def __init__(self, power1=False, power2=False, ammo=1, effectmeth=None):
        "effectmeth must be a string of either applyFire or applyIce"
        self.ammo = ammo # power1 and 2 ignored for this weapon
        self.effectmeth = effectmeth
    def shoot(self, direction):
        currenttarget = self.game.board[self.wieldingunit.square].getRelSquare(direction, 1)
        if not currenttarget: # first square attacked was offboard and therefor
            raise NullWeaponShot
        self._spendAmmo()
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

class Weapon_Deployable_Base(Weapon_ArtilleryGen_Base, Weapon_SpendAmmo_Base):
    "methods shared by weapons that deploy small tanks"
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.hp = 1 # the deployed tank's HP
        if power1:
            self.hp += 2
        self.power2 = power2 # this is passed onto the deployed tank's weapon
    def genShots(self):
        "A genshots for limited deployable tanks that doesn't allow you to shoot into swallowing tiles and immediately kill your deployable."
        for i in super().genShots():
            if not self.game.board[i[0]].isSwallow():
                yield i
    def shoot(self, targetsquare, unit): # this should only ever be called by child objects so the non-standard arg should be fine
        if self.game.board[targetsquare].unit:
            raise NullWeaponShot # can't deploy a tank to an occupied square
        self._spendAmmo()
        self.game.board[targetsquare].createUnitHere(unit)

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
            try:
                self.game.board[targetsquare].unit.applyAcid(True) # directly give the unit acid, ice and shield won't prevent you from getting acid from the gun unlike when you move to an acid pool.
            except DontGiveUnitAcid:
                self.game.board[targetsquare].applyAcid() # give it to the tile instead
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

class Weapon_ArtemisArtillery(Weapon_ArtilleryGen_Base, Weapon_PushAdjacent_Base):
    "Artillery Mech's default weapon."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self._buildingsimmune = True
        else:
            self._buildingsimmune = False
        if power2:
            self.damage += 2
    def shoot(self, targetsquare, direction):
        "Shoot in direction distance number of tiles. Artillery can never shoot 1 tile away from the wielder."
        try:
            if self._buildingsimmune and self.game.board[targetsquare].unit.isBuilding(): # if buildings are immune and the target is a building..
                pass # don't damage the target
            else:
                raise AttributeError
        except AttributeError: # None.isBuilding(), there was no unit there or manually raised because buildings aren't immune or the unit there isn't a building
            self.game.board[targetsquare].takeDamage(self.damage)
        self._pushAdjacent(targetsquare) # now push all the tiles around targetsquare regardless

class Weapon_BurstBeam(Weapon_DirectionalGen_Base, Weapon_BlocksBeamShot_Base):
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
        currentdamage = self.damage # damage being dealt as the beam travels. This decreases the further we go until we reach 1
        try:
            targettile = self.game.board[self.game.board[self.wieldingunit.square].getRelSquare(direction, 1)]  # get the target tile, not square
        except KeyError:  # self.game.board[False] means we went off the board
            raise NullWeaponShot
        while True:
            if self.allyimmune and self.is_beamally(targettile.unit):
                pass # no damage
            else:
                targettile.takeDamage(currentdamage) # damage the tile
            if self.blocksBeamShot(targettile.unit): # no more pew pew
                break
            if currentdamage != 1:
                currentdamage -= 1
            try:
                targettile = self.game.board[self.game.board[targettile.square].getRelSquare(direction, 1)] # get the target tile, not square
            except KeyError: # self.game.board[False] means we went off the board
                break # no more pew pew
    def is_beamally(self, unit):
        "return True if unit is considered an ally to the beam weapon when it has the first upgrade powered."
        try:
            return unit.alliance == Alliance.FRIENDLY or unit._beamally
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

class Weapon_ShieldProjector(Weapon_ArtilleryGen_Base, Weapon_getRelSquare_Base, Weapon_SpendAmmo_Base): # does not use the artillery base since we need the limited generator
    "The default second weapon for the Defense Mech."
    def __init__(self, power1=False, power2=False, ammo=2):
        self.ammo = ammo
        # power1 adds another use, but we ignore that here because this simulation could be in the middle of a map where ammo could be anything.
        # if we increment it by one because they have it powered we could be giving the weapon a use that it doesn't really have.
        # This weapon should always be initialized with ammo set to how many uses are actually remaining for the player at the time of the simulation.
        if power2:
            self.bigarea = True
        else:
            self.bigarea = False
    def shoot(self, targetsquare, direction):
        self._spendAmmo()
        self.game.board[targetsquare].applyShield() # the target tile itself is shielded
        if self.bigarea:
            for d in Direction.gen(): # do all tiles around the target if we have the +3 area upgrade
                try:
                    self.game.board[self.game.board[targetsquare].getRelSquare(d, 1)].applyShield()
                except KeyError:
                    pass # tried to shield off the board
        else:
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(direction, 1)].applyShield() # just shield one tile past the target in the same direction
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

class Weapon_ClusterArtillery(Weapon_ArtilleryGen_Base, Weapon_hurtAndPushEnemy_Base):
    "Default weapon for Siege Mech."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self._buildingsimmune = True
        else:
            self._buildingsimmune = False
        if power2:
            self.damage += 1
    def shoot(self, targetsquare, direction):
        for d in Direction.gen(): # targetsquare indicates where the shot landed. Nothing actually happens on this tile for this weapon, it's all around it instead.
            currenttargetsquare = self.game.board[targetsquare].getRelSquare(d, 1) # set the square we're working on
            try:
                if self._buildingsimmune and self.game.board[currenttargetsquare].unit.isBuilding(): # if buildings are immune and the unit taking damage is a building...
                    pass # don't damage it
                else: # there was a unit and it was not a building or there was a building that's not immune
                    self._hurtAndPushEnemy(currenttargetsquare, d)
            except (KeyError, AttributeError): # KeyError raised from currentsquare being False, self.game.board[False]. AttributeError raised from None.isBuilding()
                pass # this square was off the board

class Weapon_GravWell(Weapon_ArtilleryGen_Base):
    "Default first weapon for Gravity Mech"
    def __init__(self, power1=False, power2=False):
        pass # grav well can't be upgraded at all
    def shoot(self, targetsquare, direction):
        self.game.board[targetsquare].push(Direction.opposite(direction))

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

class Weapon_CryoLauncher(Weapon_ArtilleryGen_Base):
    "Default weapon for the Ice mech"
    def __init__(self, power1=False, power2=False):
        pass # cryolauncher doesn't take power
    def shoot(self, targetsquare, direction):
        "Shoot in direction distance number of tiles. Artillery can never shoot 1 tile away from the wielder."
        self.game.board[targetsquare].applyIce() # freeze the target
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
        except KeyError: # landing spot was off the board
            raise NullWeaponShot
        targetsquare = self.wieldingunit.square # start where the unit is
        for r in range(distance):
            targetsquare = self.game.board[targetsquare].getRelSquare(direction, 1)
            self.game.board[targetsquare].takeDamage(self.damage) # damage the target
            self.game.board[targetsquare].applySmoke() # smoke the target
        self.game.board[self.wieldingunit.square].moveUnit(self.game.board[targetsquare].getRelSquare(direction, 1)) # move the unit to its landing position 1 square beyond the last attack

class Weapon_RocketArtillery(Weapon_ArtilleryGen_Base, Weapon_IncreaseDamageWithPowerInit_Base, Weapon_hurtAndPushEnemy_Base, Weapon_FartSmoke_Base):
    "Default weapon for the Rocket mech"
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        super().__init__(power1, power2)
    def shoot(self, targetsquare, direction):
        self._hurtAndPushEnemy(targetsquare, direction)
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
                try:
                    if self.shieldally and (targetunit.alliance == Alliance.FRIENDLY or targetunit.isBuilding()): # try to shield allies if needed
                        raise FakeException
                except AttributeError: # None.alliance, no unit
                    continue
                except FakeException:
                    targetunit.applyShield() # shield first and push 2nd. The game shows that you'll lose hp from bumping, but instead you get a shield and then immediately lose it to the bump and take no direct damage
                self.game.board[targetsquare].push(d)

class Weapon_ElectricWhip(Weapon_DirectionalGen_Base):
    """This is the lightning mech's default weapon.
    When building chain is not powered (power1), you cannot hurt buildings or chain through them with this at all.
    It does not go through mountains or supervolcano either. It does go through rocks.
    Cannot attack mines on the ground.
    Reddit said you can attack a building if it's webbed, this is not true. Even if you attack the scorpion webbing the building, the building won't pass the attack through or take damage.
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

class Weapon_RockLauncher(Weapon_ArtilleryGen_Base, Weapon_IncreaseDamageWithPowerInit_Base):
    "Default weapon for Boulder Mech"
    def __init__(self, power1=False, power2=False):
        self.damage = 2
        super().__init__(power1, power2)
    def shoot(self, targetsquare, direction):
        if self.game.board[targetsquare].unit: # the tile only takes damage if a unit is present
            self.game.board[targetsquare].takeDamage(self.damage) # target takes damage
        else: # otherwise we just place a rock there
            self.game.board[targetsquare]._putUnitHere(Unit_Rock(self.game))
        for d in Direction.genPerp(direction):
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(d, 1)].push(d)
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

#class Weapon_FlameShielding() is in the passives section

class Weapon_VulcanArtillery(Weapon_ArtilleryGen_Base, Weapon_PushAdjacent_Base, Weapon_getRelSquare_Base):
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
    def shoot_damage(self, targetsquare, direction):
        self.shoot_nodamage(targetsquare, direction)
        self.game.board[targetsquare].takeDamage(self.damage)
    def shoot_nodamage(self, targetsquare, direction):
        "This shoot method doesn't cause any damage to the tile or unit."
        self.game.board[targetsquare].applyFire()
        self._pushAdjacent(targetsquare)
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

class Weapon_HydraulicLegs(Weapon_ArtilleryGen_Base, Weapon_HydraulicLegsUnstableInit_Base, Weapon_hurtPushAdjacent_Base):
    "The default weapon for Leap Mech"
    def genShots(self):
        return super().genShots(minimumdistance=1)
    def shoot(self, targetsquare, direction):
        if self.game.board[targetsquare].unit:
            raise NullWeaponShot # the tile you're leaping to must be clear of units
        self.game.board[self.wieldingunit.square].moveUnit(targetsquare) # move the wielder first
        self.game.board[self.wieldingunit.square].takeDamage(self.selfdamage) # then the wielder takes damage on the new tile
        self._hurtPushAdjacent(targetsquare)

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

class Weapon_ExplosiveGoo(Weapon_ArtilleryGen_Base, Weapon_PushAdjacent_Base):
    "Default weapon for the TechnoScarab"
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self.shoot = self.shoot_2tiles
        if power2:
            self.damage += 2
    def shoot(self, targetsquare, direction):
        "This is the ExplosiveGoo's shot when it only affects 1 tile, very simple."
        self.game.board[targetsquare].takeDamage(self.damage)
        self._pushAdjacent(targetsquare)  # now push all the tiles around targetsquare
    def shoot_2tiles(self, targetsquare, direction):
        self.game.board[targetsquare].takeDamage(self.damage)
        extrasquare = self.game.board[targetsquare].getRelSquare(direction, 1) # set the 2nd square
        try: # try to damage one tile past the target
            self.game.board[extrasquare].takeDamage(self.damage)
        except KeyError: # board[False]; the extra shot was wasted which is fine
            self._pushAdjacent(targetsquare)  # just push all the tiles around targetsquare, one of them will be off board
        else: # The tile exists and now we have to push all tiles around BOTH
            for d in list(Direction.genPerp(direction)) + [Direction.opposite(direction)]: # push all BUT ONE of the tiles around targetsquare. The excluded tile is the one in the direction of fire
                try:
                    self.game.board[self.game.board[targetsquare].getRelSquare(d, 1)].push(d)
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

class Weapon_TitaniteBlade(Weapon_DirectionalGen_Base, Weapon_hurtAndPushEnemy_Base, Weapon_getRelSquare_Base, Weapon_SpendAmmo_Base):
    "Swing a massive sword to damage and push 3 tiles."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.damage = 2
        # power1 adds another use, but we ignore that here because this simulation could be in the middle of a map where ammo could be anything.
        if power2:
            self.damage += 2
    def shoot(self, direction):
        targetsquare = self._getRelSquare(direction, 1)
        if not targetsquare:
            raise NullWeaponShot
        self._spendAmmo()  # this is a valid shot, so now let's spend the use
        self._hurtAndPushEnemy(targetsquare, direction)
        for perpdir in Direction.genPerp(direction):
            try:
                self._hurtAndPushEnemy(self.game.board[targetsquare].getRelSquare(perpdir, 1), direction)
            except NullWeaponShot: # it's ok if the 2 tiles next to the main target tile are off the board, the damage is just wasted
                pass

class Weapon_MercuryFist(Weapon_DirectionalGen_Base, Weapon_getRelSquare_Base, Weapon_SpendAmmo_Base):
    "Smash the ground, dealing huge damage and pushing adjacent tiles."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.damage = 4
        if power2: # power1 gives another use and is ignored here
            self.damage += 1
    def shoot(self, direction):
        targetsquare = self._getRelSquare(direction, 1)
        if not targetsquare: # target is off board and invalid
            raise NullWeaponShot
        self._spendAmmo()
        self.game.board[targetsquare].takeDamage(self.damage)
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

class Weapon_HeavyRocket(Weapon_DirectionalGen_Base, Weapon_getSquareOfUnitInDirection_Base, Weapon_PushProjectile_Base, Weapon_SpendAmmo_Base):
    "Fire a projectile that heavily damages a target and pushes adjacent tiles."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.damage = 3
        if power2: # power1 for extra uses is ignored
            self.damage += 2
    def shoot(self, direction):
        self._spendAmmo()
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=True)
        self.game.board[targetsquare].takeDamage(self.damage)
        self._pushProjectile(direction, targetsquare)

class Weapon_ShrapnelCannon(Weapon_DirectionalGen_Base, Weapon_getSquareOfUnitInDirection_Base, Weapon_hurtAndPushEnemy_Base, Weapon_SpendAmmo_Base):
    "Shoot a projectile that damages and pushes the targeted tile and the tiles to its left and right."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.damage = 2
        if power2:  # power1 for extra uses is ignored
            self.damage += 1
    def shoot(self, direction):
        self._spendAmmo()
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=True)
        self._hurtAndPushEnemy(targetsquare, direction) # hit the target
        for dir in Direction.genPerp(direction): # and then the 2 sides
            try:
                self._hurtAndPushEnemy(self.game.board[targetsquare].getRelSquare(dir, 1), dir)
            except NullWeaponShot:
                pass # peripheral shots went off the board which is OK

class Weapon_AstraBombs(Weapon_ArtilleryGen_Base, Weapon_getRelSquare_Base, Weapon_SpendAmmo_Base):
    "Leap over any distance dropping a bomb on each tile you pass."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.damage = 1
        if power2:  # power1 for extra uses is ignored
            self.damage += 2
    def shoot(self, targetsquare, direction):
        "distance is the number of squares to jump over and damage. The wielder lands on one square past distance."
        if self.game.board[targetsquare].unit:
            raise NullWeaponShot # can't land on an occupied square
        self._spendAmmo()
        currenttargetsquare = self.game.board[self.wieldingunit.square].getRelSquare(direction, 1) # start one square in front of the unit
        while currenttargetsquare != targetsquare:
            self.game.board[currenttargetsquare].takeDamage(self.damage) # damage the target
            currenttargetsquare = self.game.board[currenttargetsquare].getRelSquare(direction, 1) # move one square in direction
        self.game.board[self.wieldingunit.square].moveUnit(targetsquare) # move the unit to its landing position 1 square beyond the last attack

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

class Weapon_MicroArtillery(Weapon_ArtilleryGen_Base, Weapon_hurtAndPushEnemy_Base):
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        if power1:
            self.extratiles = True
        else:
            self.extratiles = False
        if power2:
            self.damage += 1
    def shoot(self, targetsquare, direction):
        self._hurtAndPushEnemy(targetsquare, direction)
        if self.extratiles:
            for dir in Direction.genPerp(direction): # and then the 2 sides
                try:
                    self._hurtAndPushEnemy(self.game.board[targetsquare].getRelSquare(dir, 1), direction) # push in same direction as shot
                except NullWeaponShot:
                    pass # peripheral shots went off the board which is OK

class Weapon_AegonMortar(Weapon_ArtilleryGen_Base, Weapon_IncreaseDamageWithPowerInit_Base, Weapon_hurtAndPushEnemy_Base):
    "Deals damage to two tiles, pushing one forwards and one backwards."
    def __init__(self, power1=False, power2=False):
        self.damage = 1
        super().__init__(power1, power2)
    def shoot(self, targetsquare, direction):
        self._hurtAndPushEnemy(targetsquare, Direction.opposite(direction)) # hurt and push the unit towards the wielder
        try:
            self._hurtAndPushEnemy(self.game.board[targetsquare].getRelSquare(direction, 1), direction) # hurt and push the unit on the tile past the one we just hit away from the wielder
        except NullWeaponShot: # if you hit the edge, this action is ignored
            pass

class Weapon_SmokeMortar(Weapon_ArtilleryGen_Base, Weapon_NoUpgradesInit_Base):
    "Artillery shot that applies Smoke and pushes two adjacent tiles."
    def shoot(self, targetsquare, direction):
        self.game.board[targetsquare].applySmoke()
        for dir in direction, Direction.opposite(direction):
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(dir, 1)].push(dir)
            except KeyError:
                pass # shot went off the board

class Weapon_BurningMortar(Weapon_ArtilleryGen_Base):
    "Artillery attack that sets 5 tiles on Fire."
    def __init__(self, power1=False, power2=False): # power2 is ignored
        if power1:
            self.selfdamage = 0
        else:
            self.selfdamage = 1
    def shoot(self, targetsquare, direction):
        self.game.board[targetsquare].applyFire() # first hit the dead center tile
        for dir in Direction.gen():
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(dir, 1)].applyFire()
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
    def shoot(self, targetsquare, direction):
        self.game.board[self.wieldingunit.square].takeDamage(self.selfdamage) # first take self damage
        currentsquare = self.wieldingunit.square # the current square that we are hitting with less damage
        while True:
            currentsquare = self.game.board[currentsquare].getRelSquare(direction, 1) # move to the next square
            if currentsquare == targetsquare: # if we're on the last square...
                self.damageSquare(currentsquare, self.damage) # hit it with full power
                return # and we're done
            self.damageSquare(currentsquare, self.damage-1) # hit the square with one less damage
    def damageSquare(self, square, damage):
        "Damage a single square, checking for building immunity."
        if self._buildingsimmune and self.game.board[square].unit.isBuilding():
            pass
        else:
            self.game.board[square].takeDamage(damage)

class Weapon_HeavyArtillery(Weapon_ArtilleryGen_Base, Weapon_SpendAmmo_Base):
    "Powerful attack that damages a large area."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.damage = 2
        if power2: # power1 for an extra use is ignored
            self.damage += 1
    def shoot(self, targetsquare, direction):
        self._spendAmmo()
        self.game.board[targetsquare].takeDamage(self.damage) # first hit the dead center tile
        for dir in Direction.gen():
            try:
                self.game.board[self.game.board[targetsquare].getRelSquare(dir, 1)].takeDamage(self.damage)
            except KeyError:
                pass # extra tile was off board

class Weapon_GeminiMissiles(Weapon_ArtilleryGen_Base, Weapon_hurtAndPushEnemy_Base, Weapon_SpendAmmo_Base):
    "Launch two missiles, damaging and pushing two targets"
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.damage = 3
        if power2: # power1 for an extra use is also ignored
            self.damage += 1
    def shoot(self, targetsquare, direction):
        self._spendAmmo()
        for dir in Direction.genPerp(direction):
            try:
                self._hurtAndPushEnemy(self.game.board[targetsquare].getRelSquare(dir, 1), direction)
            except NullWeaponShot: # one of the missiles was off board
                pass # totally fine

class Weapon_ConfuseShot(Weapon_Projectile_Base, Weapon_NoUpgradesInit_Base):
    "Fire a projectile that flips a target's attack direction."
    def shoot(self, direction):
        targetsquare = self._getSquareOfUnitInDirection(direction, edgeok=False)
        try:
            self.game.board[targetsquare].unit.weapon1.flip()
        except (KeyError, AttributeError): # KeyError: board[False]; AttributeError: unit.None, weapon doesn't have flip() method
            raise NullWeaponShot # didn't find a unit at all or attacked unit can't be flipped. Waste of a shot.

class Weapon_SmokePellets(Weapon_NoChoiceGen_Base, Weapon_getRelSquare_Base, Weapon_DeploySelfEffectLimitedSmall_Base):
    "Surround yourself with Smoke to defend against nearby enemies."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        if power1: # power2 for extra use ignored
            self.shoot = self.shoot_allyimmune
    def shoot(self):
        super().shoot('applySmoke')
    def shoot_allyimmune(self):
        "a different shoot method for when allyimmune is powered"
        self._spendAmmo()
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
    def __init__(self, power1=False, power2=False, ammo=1):
        super().__init__(None, None, ammo, 'applyFire')

class Weapon_FrostBeam(Weapon_TemperatureBeam_Base):
    "Fire a beam that Freezes everything in a line."
    def __init__(self, power1=False, power2=False, ammo=1):
        super().__init__(None, None, ammo, 'applyIce')

class Weapon_ShieldArray(Weapon_NoChoiceGen_Base, Weapon_getRelSquare_Base, Weapon_DeploySelfEffectLimitedSmall_Base, Weapon_DeploySelfEffectLimitedLarge_Base):
    "Apply a Shield on nearby tiles."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        if power1:
            self.shoot = self.shoot_big # power2 is ignored
    def shoot(self):
        super().shoot('applyShield')
    def shoot_big(self):
        super().shoot_big('applyShield')

class Weapon_PushBeam(Weapon_DirectionalGen_Base, Weapon_LimitedUnlimitedInit_Base, Weapon_SpendAmmo_Base):
    def shoot(self, direction):
        currenttarget = self.game.board[self.wieldingunit.square].getRelSquare(direction, 1)
        if not currenttarget: # first square attacked was offboard and therefor
            raise NullWeaponShot
        self._spendAmmo()
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
    def shoot(self, targetsquare, direction):
        if self.game.board[targetsquare].unit:
            raise NullWeaponShot # the tile you're leaping to must be clear of units
        self.game.board[self.wieldingunit.square].moveUnit(targetsquare) # move the wielder first
        self._pushAdjacent(targetsquare)

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

class Weapon_HeatConverter(Weapon_DirectionalGen_Base, Weapon_getRelSquare_Base, Weapon_SpendAmmo_Base):
    "Freeze the tile in front but light the tile behind on Fire in the process."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo # power1 and 2 are ignored
    def shoot(self, direction):
        targetsquare = self._getRelSquare(direction, 1)
        if not targetsquare:
            raise NullWeaponShot
        self._spendAmmo()
        self.game.board[targetsquare].applyIce()
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

class Weapon_TargetedStrike(Weapon_AnyTileGen_Base, Weapon_NoUpgradesLimitedInit_Base, Weapon_PushAdjacent_Base, Weapon_SpendAmmo_Base):
    "Call in an air strike on a single tile anywhere on the map."
    def shoot(self, x, y):
        self._spendAmmo()
        self.game.board[(x, y)].takeDamage(1) # this weapon can only do one damage so I'm breaking the convention of using self.damage so I can use that init base.
        self._pushAdjacent((x, y))

class Weapon_SmokeDrop(Weapon_AnyTileGen_Base, Weapon_NoUpgradesLimitedInit_Base, Weapon_SpendAmmo_Base):
    "Drops Smoke on 5 tiles anywhere on the map."
    def shoot(self, x, y):
        self._spendAmmo()
        self.game.board[(x, y)].applySmoke()
        for dir in Direction.gen():
            try:
                self.game.board[self.game.board[(x, y)].getRelSquare(dir, 1)].applySmoke()
            except KeyError: # board[False]
                pass

class Weapon_RepairDrop(Weapon_NoChoiceGen_Base, Weapon_NoUpgradesLimitedInit_Base, Weapon_SpendAmmo_Base):
    "Heal all player units (including disabled Mechs)."
    # it repairs the train, but it has no effect since the 2 different stages only have 1 hp. Any of the 3 stages being repaired is inconsequential.
    # it repairs the earth mover which does matter because it has 2 hp! Same with acid launcher. And Satellite Rocket. And Terraformer.
        # These can all be repaired, but not from death.
    # it removes fire from your mech and subunits, but does not repair the tile. If you're on a fire tile and you repairdrop, you're instantly on fire again.
    # it breaks you out of ice
    # Sub units are repaired and fire is removed from them.
    # acid is NOT removed from units. If a mech has acid, dies and becomes a corpse, the corpse still has acid and the revived mech has acid.
        # You can't give acid to a mech corpse however. If you hit a mech corpse with acid, it doesn't get it. Then you revive it and it still doesn't have it.
    def shoot(self):
        self._spendAmmo()
        for unit in self.game.playerunits.copy():
            self._healunit(unit)
        for unit in self.game.nonplayerunits:
            if self.isHealNPC(unit):
                self._healunit(unit)
    def _healunit(self, unit):
        try:
            unit._revive()
        except AttributeError:
            pass # unit was not a corpse
        else: # unit was revived, we need to now change unit to the revived unit
            unit = self.game.board[unit.square].unit
        unit.hp = unit.maxhp # restore all health
        unit._removeFire() # put out fire on the unit
        unit._removeIce() # break the unit out of ice
        self.game.board[unit.square]._spreadEffects() # possibly spread fire back to the unit
    def isHealNPC(self, unit):
        "Returns true if this NPC is healed by RepairDrop, False if it's not."
        try:
            return unit._repairdrop
        except AttributeError:
            return False

class Weapon_MissileBarrage(Weapon_NoChoiceGen_Base, Weapon_SpendAmmo_Base):
    "Fires a missile barrage that hits every enemy on the map."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
        self.damage = 1
        if power1:
            self.damage += 1 # power2 ignored
    def shoot(self):
        self._spendAmmo()
        for e in self.game.nonplayerunits:
            if e.alliance == Alliance.ENEMY:
                self.game.board[e.square].takeDamage(self.damage)

class Weapon_WindTorrent(Weapon_DirectionalGen_Base, Weapon_LimitedUnlimitedInit_Base):
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

class Weapon_IceGenerator(Weapon_NoChoiceGen_Base, Weapon_DeploySelfEffectLimitedSmall_Base, Weapon_DeploySelfEffectLimitedLarge_Base, Weapon_getRelSquare_Base):
    "Freeze yourself and nearby tiles."
    def __init__(self, power1=False, power2=False, ammo=1):
        self.ammo = ammo
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
    def __init__(self, power1=False, power2=False, ammo=1):
        super().__init__(power1, power2, ammo)
    def shoot(self, targetsquare, direction):
        super().shoot(targetsquare, Unit_LightTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_StockCannon(power2=self.power2)))

class Weapon_ShieldTank(Weapon_Deployable_Base):
    "Deploy a Shield-Tank that can give Shields to allies."
    def __init__(self, power1=False, power2=False, ammo=1):
        super().__init__(power1, power2, ammo)
    def shoot(self, targetsquare, direction):
        super().shoot(targetsquare, Unit_ShieldTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_ShieldShot(power2=self.power2)))

class Weapon_AcidTank(Weapon_Deployable_Base):
    "Deploy a Tank that can apply A.C.I.D. to targets."
    def __init__(self, power1=False, power2=False, ammo=1):
        super().__init__(power1, power2, ammo)
    def shoot(self, targetsquare, direction):
        super().shoot(targetsquare, Unit_AcidTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_AcidShot(power2=self.power2)))

class Weapon_PullTank(Weapon_Deployable_Base):
    "Deploy a Pull-Tank that can pull targets with a projectile."
    def __init__(self, power1=False, power2=False, ammo=1):
        super().__init__(power1, power2, ammo)
    def shoot(self, targetsquare, direction):
        if self.power2:
            super().shoot(targetsquare, Unit_PullTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_PullShot(), attributes=(Attributes.FLYING,)))
        else:
            super().shoot(targetsquare, Unit_PullTank(self.game, hp=self.hp, maxhp=self.hp, weapon1=Weapon_PullShot()))

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

class Weapon_OldEarthArtillery(Weapon_ArtilleryGen_Base, Weapon_NoUpgradesInit_Base):
    "Underpowered compared to modern artillery, but still useful. OldArtillery"
    damage = 2
    def shoot(self, targetsquare, direction):
        self.game.board[targetsquare].takeDamage(self.damage) # copypasta from Weapon_ExplosiveGoo
        extrasquare = self.game.board[targetsquare].getRelSquare(direction, 1) # set the 2nd square
        try: # try to damage one tile past the target
            self.game.board[extrasquare].takeDamage(self.damage)
        except KeyError: # board[False]; the extra shot was wasted which is fine
            pass

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
        self.wieldingunit._removeIce() # yes this breaks you out of ice and does the attack

################################ Vek Weapons #################################
# All weapons have their ingame description in the docstring followed by the type/name of the enemy that wields this weapon.
# Vek weapons can't have shots generated for them like mech weapons do, so they lack genShots()
# All vek weapons MUST have an attribute self.qshot (queuedshot) which is the shot they will take on their turn.
# All vek weapons MUST have a validate() method to test whether their shot is still valid. This method will be run whenever the vek is moved and when the unit is created.
    # if the shot is invalid, it must set qshot to None and return False. return True otherwise.
    # this method can and should be used to set up a future shot similar to how Weapon_ArtilleryGen_Base set self.targetsquare.
# All shoot() methods take no arguments, they read their own qshot when shooting.
# Any vek weapons that can have their shot direction flipped MUST have a flip() method to flip the direction of attack (spartan shield and confuse shot use this).
    # If a weapon can't be flipped, it doesn't need a flip() method.
# Weapons that create webs in the game isn't done here since that's really done during the vek's move/target phase. The user should already have a gameboard with webs laid out.
# Vek weapons will never raise NullWeaponShot

# Vek weapon low-level base objects:
class Weapon_NPC_Base():
    "Base class for all nonplayer weapons."
    def __init__(self, qshot=None):
        self.qshot = qshot

class Weapon_Vek_Base(Weapon_NPC_Base):
    "Base class for all vek weapons."
    def __init__(self, qshot=None):
        super().__init__(qshot)
        self.dealDamage = self._dealDamageDefault
    def _dealDamageDefault(self, square):
        """A helper method for vek to use when dealing damage with their weapon. The amount of damage dealt is self.damage.
        This was implemented because VekHormones needs to deal extra damage when a vek hurts another.
        This method does NOT take VekHormones into account. This is the default that vek weapons use.
        square is a tuple of the square to damage.
        returns nothing."""
        self.game.board[square].takeDamage(self.damage)
    def _dealDamageVekHormones(self, square):
        """A helper method for vek to use when dealing damage with their weapon. The amount of damage dealt is self.damage.
        This was implemented because VekHormones needs to deal extra damage when a vek hurts another.
        This method actually takes vek hormones into account.
        square is a tuple of the square to damage.
        damage is the amount of damage to deal.
        returns nothing."""
        self.game.board[square].takeDamage(self.damage)
        try:
            if self.game.board[square].unit.alliance == Alliance.ENEMY:
                raise FakeException
        except AttributeError:
            return
        except FakeException:
            self.game.board[square].takeDamage(self.game.vekhormones)

class Weapon_Validate_Base():
    "This is the base validate class for all others."
    def validate(self):
        "The only way this shot can be invalidated is by the shot already being invalidated or the unit being smoked."
        if self.qshot is None:
            return False
        for eff in Effects.SMOKE, Effects.SUBMERGED:
            if eff in self.game.board[self.wieldingunit.square].effects:
                self.qshot = None
                return False
            return True

class Weapon_DirectionalValidate_Base(Weapon_Validate_Base):
    "A validate method that works for melee and projectile weapons."
    def validate(self):
        "qshot should be (Direction.XX,). This method checks one square in direction to make sure it's onboard."
        if super().validate(): # if a shot is queued and the unit is not smoked or submerged...
            self.targetsquare = self.game.board[self.wieldingunit.square].getRelSquare(*self.qshot, 1)
            if not self.targetsquare: # shot was offboard
                self.qshot = None
            else:
                return True
        return False

class Weapon_DirectionalFlip_Base():
    "A flip method that works for melee, projectile, and charge weapons. Doesn't work for artillery"
    def flip(self):
        try:
            self.qshot = (Direction.opposite(*self.qshot),)
        except InvalidDirection: # qshot was None
            pass
        self.validate()

# Vek weapon high-level base objects:
class Weapon_SurroundingShoot_Base(Weapon_Vek_Base):
    "Base weapon for vek weapons that damage adjacent tiles such as blob and digger weapons."
    def shoot(self):
        "return True if the shot happened, False if it didn't."
        if self.qshot is not None:
            for d in Direction.gen():
                try:
                    self._dealDamage(self.game.board[self.wieldingunit.square].getRelSquare(d, 1))
                except KeyError: # game.board[False]
                    pass
            return True
        return False

class Weapon_Blob_Base(Weapon_SurroundingShoot_Base):
    "Base weapon for blobs that explode"
    def shoot(self):
        if super().shoot():
            self.wieldingunit.die()

class Weapon_VekMelee_Base(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base):
    "Shared shoot method for melee attacks used by Scorpions, Leapers, and hornets."
    def shoot(self):
        if self.qshot is not None:
            self._dealDamage(self.targetsquare)
            return True
        return False

class Weapon_VekProjectileShoot_Base(Weapon_getSquareOfUnitInDirection_Base):
    "A base shoot method shared by vek projectile weapons such as the Firefly and Centipede weapons."
    def shoot(self):
        if self.qshot is not None:
            self.targetsquare = self._getSquareOfUnitInDirection(*self.qshot, edgeok=True)
            self._dealDamage(self.targetsquare)
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
                elif self.game.board[self.targetsquare].isSwallow():
                    self.game.board[self.wieldingunit.square].moveUnit(self.targetsquare) # move the unit here so it can die or trip the mine
                    return
                else: # there was no unit and the tile didn't kill the vek
                    prevsquare = self.targetsquare
                    self.targetsquare = self.game.board[self.targetsquare].getRelSquare(*self.qshot, 1)
                    if not self.targetsquare: # if we went off the board
                        self.game.board[self.wieldingunit.square].moveUnit(prevsquare) # move to that edge tile
                        return

class Weapon_NPCArtillery_Base(Weapon_NPC_Base, Weapon_Validate_Base, Weapon_getRelSquare_Base):
    "Base object for vek artillery weapons for Scarabs and Crabs and the bots."
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
            self._dealDamage(self.targetsquare)
            return True

class Weapon_VekArtillery_Base(Weapon_Vek_Base, Weapon_NPCArtillery_Base):
    "Base object for vek artillery weapons for Scarabs and Crabs and the bots."

class Weapon_ExplosiveExpulsions_Base(Weapon_VekArtillery_Base):
    "Base class for Crab weapons"
    def shoot(self):
        if super().shoot():
            try:
                self._dealDamage(self.game.board[self.targetsquare].getRelSquare(self.qshot[0], 1))
            except KeyError:  # board[False]
                pass  # the secondary target can be offboard

class Weapon_Vomit_Base(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base, Weapon_VekProjectileShoot_Base):
    "Base class for Centipede weapons"
    def shoot(self):
        if super().shoot():
            self.game.board[self.targetsquare].applyAcid() # give acid to the square that was already damaged by the parent obj
            for d in Direction.genPerp(*self.qshot):
                secondarysquare = self.game.board[self.targetsquare].getRelSquare(d, 1)
                try:
                    self._dealDamage(secondarysquare)
                except KeyError: # board[False]
                    continue # secondary square was offboard
                self.game.board[secondarysquare].applyAcid() # give it acid after attacking it

class Weapon_Carapace_Base(Weapon_Vek_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base):
    "Base class for Burrower Carapace weapons"
    def shoot(self):
        if self.qshot is not None:
            self._dealDamage(self.targetsquare)# hit the main target square
            for d in Direction.genPerp(*self.qshot):
                try:
                    self._dealDamage(self.game.board[self.targetsquare].getRelSquare(d, 1))
                except KeyError: # board[False]
                    continue # secondary square was offboard

class Weapon_GreaterHornet_Base(Weapon_VekMelee_Base):
    "A base class for AlphaHornet and HornetLeader that stab multiple tiles. self.range must be set by the child object"
    damage = 2 # both units do 2 damage
    def shoot(self):
        if super().shoot(): # hit the first tile
            for r in range(self.extrarange):
                self.targetsquare = self.game.board[self.targetsquare].getRelSquare(*self.qshot, 1)
                try:
                    self._dealDamage(self.targetsquare)
                except KeyError: # board[False], secondary tile was offboard
                    return # don't process further shots

class Weapon_Cannon8R_Base(Weapon_NPC_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base, Weapon_getSquareOfUnitInDirection_Base):
    "Base class for the weapons used by Cannon-Bot and Cannon-Mech."
    def shoot(self):
        if self.qshot is not None: # copypasta from Weapon_VekArtillery_Base.
            self.targetsquare = self._getSquareOfUnitInDirection(*self.qshot, edgeok=True)
            self.game.board[self.targetsquare].takeDamage(self.damage)
            self.game.board[self.targetsquare].applyFire()

class Weapon_Vk8Rockets_Base(Weapon_VekArtillery_Base):
    "Base class for the weapons used by ArtilleryBot and ArtilleryMech"
    def shoot(self):
        if super().shoot(): # this hits the targeted square
            for d in Direction.genPerp(self.qshot[0]): # now hit the 2 squares beside it
                try:
                    self.game.board[self.game.board[self.targetsquare].getRelSquare(d, 1)].takeDamage(self.damage)
                except KeyError: # board[False]
                    pass # secondary hit was off the board

class Weapon_BKRBeam_Base(Weapon_NPC_Base, Weapon_DirectionalValidate_Base, Weapon_DirectionalFlip_Base, Weapon_BlocksBeamShot_Base):
    "Base class for laser bot/mech weapons"
    def shoot(self):
        if self.qshot is not None:
            currentdamage = self.damage # damage being dealt as the beam travels. This decreases the further we go until we reach 1
            targettile = self.game.board[self.game.board[self.wieldingunit.square].getRelSquare(self.qshot[0], 1)]  # get the target tile, not square
            while True:
                targettile.takeDamage(currentdamage) # damage the tile
                if self.blocksBeamShot(targettile.unit): # no more pew pew
                    return
                if currentdamage != 1:
                    currentdamage -= 1
                try:
                    targettile = self.game.board[self.game.board[targettile.square].getRelSquare(self.qshot[0], 1)] # get the target tile, not square
                except KeyError: # self.game.board[False] means we went off the board
                    return # no more pew pew

############################## Actual vek weapons: #######################################################
class Weapon_UnstableGuts(Weapon_Blob_Base):
    "Explode, killing itself and damaging adjacent tiles for 1 damage. Kill it first to stop it. Blob"
    damage = 1

class Weapon_VolatileGuts(Weapon_Blob_Base):
    "Explode, killing itself and damaging adjacent tiles for 3 damage. Kill it first to stop it. Alpha Blob"
    damage = 3

class Weapon_UnstableGrowths(Weapon_Vek_Base):
    "Throw a sticky blob that will explode. Blobber"
    def shoot(self):
        self.game.score.submit(-5, 'blob_spawned')

class Weapon_VolatileGrowths(Weapon_Vek_Base):
    "Throw a massive blob that will explode. Blobber"
    def shoot(self):
        self.game.score.submit(-6, 'alpha_blob_spawned')

class Weapon_TinyOffspring(Weapon_Vek_Base):
    "Throw a sticky egg that hatches into a Spiderling. Spider"
    def shoot(self):
        self.game.score.submit(-2, 'spideregg_spawned')

class Weapon_LargeOffspring(Weapon_Vek_Base):
    "Throw a sticky egg that hatches into an Alpha Spiderling. AlphaSpider"
    def shoot(self):
        self.game.score.submit(-3, 'alphaspideregg_spawned')

class Weapon_StingingSpinneret(Weapon_VekMelee_Base):
    "Web an adjacent target, preparing to stab it for 1 damage. (We don't actually do any webbing here). Scorpion."
    damage = 1

class Weapon_GoringSpinneret(Weapon_VekMelee_Base):
    "Web an adjacent target, preparing to stab it for 3 damage. (We don't actually do any webbing here). AlphaScorpion."
    damage = 3

class Weapon_AcceleratingThorax(Weapon_Thorax_Base):
    "Launch a volatile mass of goo dealing 1 damage. Firefly"
    damage = 1

class Weapon_EnhancedThorax(Weapon_Thorax_Base):
    "Launch a volatile mass of goo dealing 3 damage. AlphaFirefly"
    damage = 3

class Weapon_Fangs(Weapon_VekMelee_Base):
    "Web a target, preparing to stab it for 3 damage. Leaper"
    damage = 3

class Weapon_SharpenedFangs(Weapon_VekMelee_Base):
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

class Weapon_Stinger(Weapon_VekMelee_Base):
    "Stab the target for 1 damage. Hornet"
    damage = 1

# class Weapon_AcidStinger(Weapon_VekMelee_Base): # acid units aren't really implemented in the game
#     "Stab the target for 1 damage and apply A.C.I.D. AcidHornet"
#     damage = 1
#     def shoot(self):
#         if super().shoot():
#             self.game.board[self.targetsquare].applyAcid()

class Weapon_LaunchingStinger(Weapon_GreaterHornet_Base):
    "Stab 2 tiles in front of the unit for 2 damage. AlphaHornet"
    extrarange = 1

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

class Weapon_GooAttack(Weapon_VekMelee_Base):
    "Attempt to squish the adjacent tile, destroying its contents. LargeGoo, MediumGoo, SmallGoo all use this same exact weapon."
    damage = 4
    def shoot(self):
        """The way this weapon works is that it damages the unit like a regular melee unit would if it's a mech or if the unit doesn't die.
        However, if the unit dies and is NOT a mech, the goo takes the victim's spot on the board. If it attacks a mountain, it kills it in a single shot without creating a damagedmountain first."""
        if super().shoot():
            targetunit = self.game.board[self.targetsquare].unit
            try:
                if (targetunit.hp > 0 or (targetunit.alliance == Alliance.FRIENDLY and Attributes.MASSIVE in targetunit.attributes)) and not targetunit.isMountain():
                    # if the unit the goo attacked survived or if it was a mech that was killed and the unit wasn't a mountain
                    return # Do nothing, the goo should NOT take the place of its victim
                else: # the unit was a mountain or it died and it wasn't a mech
                    raise AttributeError # so the goo takes the place of the unit
            except AttributeError: # None.isMountain(), there was no unit
                self.game.postattackmoves.add((self.wieldingunit.square, self.targetsquare)) # have the goo take the place of the unit it just killed

class Weapon_SuperStinger(Weapon_GreaterHornet_Base):
    "Stab three tiles in a row for 2 damage each. HornetLeader"
    extrarange = 2

class Weapon_MassiveSpinneret(Weapon_Vek_Base, Weapon_hurtAndPushEnemy_Base, Weapon_Validate_Base):
    "Web all targets, preparing to deal 2 damage to adjacent tiles (This attack also pushes targets). ScorpionLeader"
    damage = 2
    def shoot(self):
        if self.qshot is not None:
            for d in Direction.gen():
                try:
                    self._hurtAndPushEnemy(self.game.board[self.wieldingunit.square].getRelSquare(d, 1), d)
                except NullWeaponShot: # game.board[False]
                    pass

class Weapon_BurningThorax(Weapon_Vek_Base, Weapon_Validate_Base, Weapon_getSquareOfUnitInDirection_Base):
    "Launch goo projectiles in two directions, dealing 4 damage with each. FireflyLeader."
    # The shot validation for this unit is very wonky. The way Vek targeting works as far as I can tell is that any vek that attacks in a specific direction
    # targets 1 square in the direction of their attack. This means that units like the AlphaHornet can't choose to use less range, they can only choose direction.
    # When the vek is moved to the edge of the board so that their target square goes off the board, their attack is cancelled. This is all good and fine and makes sense.
    # The problem with this FireflyLeader is that he attacks the same way except it isn't apparent which direction he's targeting since he shoots out of both directions at once.
    # Through testing, I've seen this unit have his shot cancelled for seemingly no reason. For example, I had a mech above the firefly in the same y axis and he targeted me.
    # Its upward shot would hit me, while his bottom shot would just hit an empty tile. I then teleported the firefly down to the edge of the board and his shot was canceled!
    # This means that his AI targeted the square below it and away from my mech, and then deduced that this was a good shot to take since the butt-shot would have hit my mech.
    # Why would it target that way instead of toward me? No idea. I did further testing of this in the map editor where I put mountains on every tile except 2, one for a swap mech
    # and one for the FireflyLeader. What I found was inconsistency. The firefly would always target me, but after I teleported it against the wall it would sometimes have
    # its attack canceled, sometimes it wouldn't. The UI gives no indication of which way the firefly was actually targeting and it doesn't even choose which direction to target
    # consistently. This leads me to the conclusion that it's random and the player can never tell which way the firefly targeted. That means moving it to the edge of the map is
    # a total gamble. I think the only sensible thing for me to do in this program is to treat this weapon as impossible to positionally invalidate.
    damage = 4
    def shoot(self):
        if self.qshot is not None:
            for d in self.qshot[0], Direction.opposite(*self.qshot):
                try:
                    self._dealDamage(self._getSquareOfUnitInDirection(d, edgeok=True))
                except NullWeaponShot: # caused by the wielder being up against the wall, the other shot is so valid so we ignore this
                    pass

class Weapon_PlentifulOffspring(Weapon_Vek_Base, Weapon_Validate_Base):
    "Throw out 2-3 Spider eggs. SpiderLeader"
    def shoot(self):
        if self.qshot is not None:
            self.game.score.submit(-5, 'many_spidereggs_spawned')
            # This weapon, just like the blobber, creates new units in unpredictable locations. The creation of these new units needs to be counted against your score.

class Weapon_SpiderlingEgg(Weapon_Vek_Base):
    "Hatch into Spiderling. SpiderlingEgg. The unit name and weapon name are the same."
    def validate(self):
        pass
    def shoot(self): # A spiderling egg will always hatch unless it is killed first, so we ignore qshot.
        self.game.score.submit(-3, 'spider_spawned')

class Weapon_TinyMandibles(Weapon_VekMelee_Base):
    "Weak 1 damage attack against a single adjacent target. Spiderling"
    damage = 1

class Weapon_TinyMandiblesAlpha(Weapon_VekMelee_Base):
    "Weak 2 damage attack against a single adjacent target. AlphaSpiderling"
    damage = 2

class Weapon_Cannon8RMarkI(Weapon_Cannon8R_Base):
    "Projectile that causes target to burn. CannonBot"
    damage = 1

class Weapon_Cannon8RMarkII(Weapon_Cannon8R_Base):
    "Stronger projectile that causes target to burn. CannonMech"
    damage = 3

class Weapon_Vk8RocketsMarkI(Weapon_Vk8Rockets_Base):
    "Launch Rockets at 3 tiles (dealing 1 damage). ArtilleryBot"
    damage = 1

class Weapon_Vk8RocketsMarkII(Weapon_Vk8Rockets_Base):
    "Launch Rockets at 3 tiles (dealing 3 damage). ArtilleryMech"
    damage = 3

class Weapon_BKRBeamMarkI(Weapon_BKRBeam_Base):
    "Piercing beam, damage reduced by range (2 damage). LaserBot"
    damage = 2

class Weapon_BKRBeamMarkII(Weapon_BKRBeam_Base):
    "Piercing beam, damage reduced by range (4 damage). LaserMech"
    damage = 4

# MineBot weapon not implemented because it's actually something done during the enemy move/target phase.
# It moves and leaves a mine in its place AFTER the player has taken his turn.

class Weapon_Vk8RocketsMarkIII(Weapon_Vk8Rockets_Base):
    "Launch Rockets at 3 tiles dealing 2 damage to each. BotLeader_Attacking"
    damage = 2

class Weapon_SelfRepair(Weapon_Vek_Base, Weapon_Validate_Base):
    """This is the BotLeader's self-Repair weapon that it uses after taking damage. BotLeader_Healing
    The Bot Leader gets a shield on the start of his target phase, so this weapon here won't actually give the shield."""
    # this does remove fire and presumably acid
    def shoot(self):
        if self.qshot is not None:
            self.wieldingunit.hp = self.wieldingunit.maxhp
            if Effects.FIRE not in self.game.board[self.wieldingunit.square].effects: # these repairs do not remove bad effects from the tile. If you trap him on a fire tile and he repairs there, he keeps fire.
                self.wieldingunit.effects.discard(Effects.FIRE) # repair doesn't remove acid from the unit, but it does remove fire.
            # Ice cancels the attack like a regular weapon, he can't repair out of ice.

############################## Objective Weapons ###########################################
# Objective weapons that the player controls (terraformer, acidlauncher) have the same requirements as player weapons, except don't have power arguments.
# Objective weapons that the player does NOT control (train, satellite rockets) have the same requirements as enemy weapons.
    # They require a qshot to indicate whether it is attacking this turn or not.

class Weapon_ChooChoo(Weapon_Vek_Base):
    "Move forward 2 spaces, but will be destroyed if blocked. Train"
    def validate(self):
        "The only way this shot can be invalidated is by the shot already being invalidated. Freezing it will cancel the shot, but that isn't checked here. The train is immune to smoke and it will never go in water."
        pass
    def shoot(self):
        if self.qshot is not None:
            targetsquare = self.wieldingunit.square
            for r in 1, 2:
                targetsquare = self.game.board[targetsquare].getRelSquare(Direction.RIGHT, 1)
                try: # try to kill the units in the way of the train
                    self.game.board[targetsquare].unit.die()
                except AttributeError: # None.die()
                    pass
                except KeyError: # board[False]
                    raise CantHappenInGame("Train's Choo Choo weapon tried to attack off the board.")
                else: # there was a unit in the way that died.
                    self.game.board[self.wieldingunit.square].unit.takeDamage(1) # only damage the train itself
                    return
    # These are the old train methods that I first wrote. These ones make the train move like it does in game.
    # I realized later that this is inconsequential to a single turn, so I ripped out the movement functionality.
    # def shoot(self):
    #     if self.qshot is not None:
    #         try:
    #             self.oldcaboosesquare = self.wieldingunit.companion
    #         except AttributeError: # companion isn't set yet
    #             self.wieldingunit._setCompanion()
    #             self.oldcaboosesquare = self.wieldingunit.companion
    #         prevsquare = self.wieldingunit.square
    #         for r in 1, 2:
    #             targetsquare = self.game.board[prevsquare].getRelSquare(Direction.RIGHT, 1)
    #             try: # try to kill the units in the way of the train
    #                 self.game.board[targetsquare].unit.die()
    #             except AttributeError: # None.die()
    #                 prevsquare = targetsquare # no unit, the train moves right one square.
    #             except KeyError: # board[False]
    #                 raise Exception("Train's Choo Choo weapon tried to move it off the board.")
    #             else: # there was a unit in the way that died.
    #                 if prevsquare != targetsquare: # if the train needs to be moved
    #                     self.game.board[self.wieldingunit.square].moveUnit(prevsquare) # move the front of the train
    #                     self._moveCaboose()
    #                 self.game.board[self.wieldingunit.square].takeDamage(1)
    #                 return
    #         # If we made it here, that means there was no unit in the way. Move the train right 2 squares:
    #         self.game.board[self.wieldingunit.square].moveUnit(targetsquare)  # move the front of the train
    #         self._moveCaboose()
    # def _moveCaboose(self): # consider not actually moving the train at all. The train's NPC action is the last thing to happen in a turn besides vek spawning which can never be affected by the train's position.
    #     "Move the caboose of the train and update the campion of the already moved front of the train"
    #     self.wieldingunit._setCompanion()
    #     self.game.board[self.oldcaboosesquare].moveUnit(self.wieldingunit.companion)
    #     self.game.board[self.wieldingunit.companion].unit._setCompanion()

class Weapon_SatelliteLaunch(Weapon_Vek_Base, Weapon_getRelSquare_Base):
    "Launch a satellite into space, destroying surrounding area. SatelliteRocket"
    def validate(self):
        pass
    def shoot(self):
        if self.qshot is not None:
            for d in Direction.gen():  # all tiles around wielder must die # copypasta from Weapon_SelfDestruct
                try:
                    self.game.board[self._getRelSquare(d, 1)].die()
                except KeyError:  # game.board[False]
                    pass
            # no need to actually remove the rocket from the board as it makes no difference at the end of a turn.

class Weapon_Disintegrator(Weapon_AnyTileGen_Base):
    "Dissolve all target tiles with acid. acidlauncher"
    def shoot(self, x, y):
        self.action((x, y))
        for d in Direction.gen(): # do all tiles around the target
            try:
                self.action(self.game.board[(x, y)].getRelSquare(d, 1))
            except KeyError:
                pass # tried to target off the board
    def action(self, square):
        "Kill the unit and put acid on the tile of square."
        try:
            self.game.board[square].unit.die()
        except AttributeError: # board[square].None.die()
            pass
        self.game.board[square].applyAcid()

class Weapon_Terraformer(Weapon_DirectionalGen_Base):
    "Eradicate all life in front of the Terraformer. Terraformer. Yes, the unit is called Terraformer and the weapon is also called Terraformer"
    def shoot(self, dir):
        targetsquare = self.wieldingunit.square
        for distance in 1, 2:
            targetsquare = self.game.board[targetsquare].getRelSquare(dir, 1)
            self._convertGrassland(targetsquare)
            for perpsq in Direction.genPerp(dir):
                self._convertGrassland(self.game.board[targetsquare].getRelSquare(perpsq, 1))
    def _convertGrassland(self, sq):
        "kill the unit on square and convert the tile to sand if it was a grassland tile, ground if it wasn't."
        try:
            tile = self.game.board[sq]
        except KeyError:
            raise CantHappenInGame("The Terraformer was placed in a way that it's weapon shoots off the board. This can't happen in the game.")
        # if we're killing a mountain, don't replace the tile. Mountains should always only have ground tiles under them.
        # This is the correct behavior from the game, if you terraform a mountain it leaves a ground tile and not a sand tile
        try:
            if tile.unit.isMountain():
                pass
            else:
                raise AttributeError
        except AttributeError: # tile.None.isMountain()
            tile.replaceTile(Tile_Sand(self.game))
            # TODO: score count the score for the objective goal here.
            # Maybe this should only be counted once per shot. We shouldn't create a scenario where terraforming more grassland tiles is more valuable than killing more vek.
        tile.die()

###############################################################################
############################### Passive Weapons ###############################
###############################################################################
# All passive weapons must have an enable() method to apply the effect. enable() must only be run after all units have been placed on the board.
# All vek passive weapons must have a disable() method to remove the effect when the psion dies.
    # Mech passives don't have disable() because even if they die and the corpse is removed via a chasm, the passive remains in play.
# All vek passives must also support giving the passive to mechs which is what the Psionic Receiver mech passive does.

class Weapon_PsionPassive_Base():
    "A base class for passive Psion weapons that don't need a turn. Child classes must provide _applyEffect(unit) and _removeEffect(unit)."
    _mechs = False # Psionic receiver will set this to True via self._enableMechs() if we are to also have mechs benefit from psion passives
    def enable(self):
        """Enable the passive effect. This should only be run after all units have been placed on the board.
        If self.mechs is True, this will also give the effect to all the mechs as well as all the Vek because of the Psionic Receiver passive.
        returns nothing."""
        for unit in self.game.nonplayerunits:
            if unit.isNormalVek():
                self._applyEffect(unit)
        if self._mechs:
            for unit in self.game.playerunits:
                if unit.isMech():
                    self._applyEffect(unit)
    def disable(self):
        """Disable the passive effect. This is done when the psion dies.
        If self.mechs is True, this will also remove the effect to all the mechs as well as all the Vek because of the Psionic Receiver passive.
        returns nothing."""
        for unit in list(self.game.nonplayerunits):
            if unit.isNormalVek():
                self._removeEffect(unit)
        if self._mechs:
            for unit in self.game.playerunits:
                if unit.isMech():
                    self._removeEffect(unit)
    def _enableMechs(self):
        "Tell this psion weapon to also effect mechs because of Psionic Receiver"
        self._mechs = True

class Weapon_InvigoratingSpores(Weapon_PsionPassive_Base):
    "All other Vek receive +1 HP as long as the Psion is living. Soldier Psion"
    def _applyEffect(self, unit):
        "Don't give units more hp here, since they were already added to the board in their current state of hp. This is a dummy method."
        #unit.maxhp += 1
        #unit.hp += 1
        pass
    def _removeEffect(self, unit):
        "A helper method to properly remove all the effects or attributes to unit. returns nothing."
        if unit.hp == 1: # if this passive going away is going to kill the unit...
            unit.die() # then just have it die. Since we're not really doing damage here, this is the way to do it.
            return # We can't call takeDamage() because then a shield or ice would prevent the unit from dying which isn't what happens ingame.
        else:
            unit.maxhp -= 1
            unit.hp -= 1

class Weapon_HardenedCarapace(Weapon_PsionPassive_Base):
    "All other Vek have incoming weapon damage reduced by 1 (By giving them armor). Shell Psion"
    def __init__(self):
        self.skipmechs = set() # a set of mechs that were already armored. This is built when we enable and this is checked when removing armored so we can avoid removing armor from units that already had it before the psion.
    def _applyEffect(self, unit):
        if Attributes.ARMORED in unit.attributes:
            self.skipmechs.add(unit) # unit might be a vek, but there are no naturally armored vek
        else:
            unit.attributes.add(Attributes.ARMORED)
    def _removeEffect(self, unit):
        try:
            if unit in self.skipmechs:
                return
        except AttributeError: # self.skipmechs doesn't exist
            pass
        unit.attributes.remove(Attributes.ARMORED)

class Weapon_ExplosiveDecay(Weapon_PsionPassive_Base):
    "All other Vek will explode on death, dealing 1 damage to adjacent tiles. Blast Psion"
    def _applyEffect(self, unit):
        unit.effects.add(Effects.EXPLOSIVE)
    def _removeEffect(self, unit):
        unit.effects.remove(Effects.EXPLOSIVE)

class Weapon_PsionSemiPassive_Base(Weapon_PsionPassive_Base):
    "A base class for passive Psion weapons that DO need a turn to apply their effect. Childs of this one don't need _applyEffect or _removeEffect, but they do need _turnAction()."
    def enable(self):
        self.game.psionPassiveTurn = self._turnAction
    def disable(self):
        self.game.psionPassiveTurn = None

class Weapon_Regeneration(Weapon_PsionSemiPassive_Base): # Regenerate happens after fire damage, but before enemy actions.
    "All other Vek heal 1 at the start of their turn. Blood Psion"
    def _turnAction(self):
        "This is the action to run when it's actually time to regenerate health."
        for unit in self.game.nonplayerunits:
            if unit.isNormalVek():
                unit.repairHP(1)
        if self._mechs:
            for unit in self.game.playerunits:
                if unit.isMech():
                    unit.repairHP(1)

class Weapon_HiveTargeting(Weapon_PsionSemiPassive_Base):
    "All player units take 1 damage at the end of every turn. Psion Tyrant."
    def _turnAction(self):
        "This is the action to run when it's time to actually slip 'em the tentacle."
        for unit in self.game.playerunits: # No need to check if it's a mech here, psion tentacle hurts your subunits too
            self._unitTakeDamage(unit)
        for unit in self.game.nonplayerunits: # we also need to make the renfield bomb take damage
            if unit.isRenfieldBomb():
                self._unitTakeDamage(unit)
                break
        if self._mechs:
            for unit in self.game.nonplayerunits: # No need to check if it's a normal vek here, Hive Targetting hurts all vek, even the psion itself!
                if unit.alliance == Alliance.ENEMY: # but don't let the renfield bomb take 2 damage and don't kill rocks
                    self._unitTakeDamage(unit)
        self.game.flushHurt()
    def _unitTakeDamage(self, unit):
        "helper method to have the unit take damage."
        unit.takeDamage(1) # It's just a regular attack, I've seen armor block it.

class Weapon_Overpowered(Weapon_PsionSemiPassive_Base):
    "All other Vek gain +1 HP, Regeneration, and explode on death. Psion Abomination"
    def enable(self):
        "a hybrid enable that does both of the full passive and semi passive type of enabling."
        Weapon_PsionPassive_Base.enable(self)
        Weapon_PsionSemiPassive_Base.enable(self)
    def disable(self):
        "a hybrid disable that does both of the full passive and semi passive type of disabling."
        Weapon_PsionPassive_Base.disable(self)
        Weapon_PsionSemiPassive_Base.disable(self)
    def _applyEffect(self, unit):
        Weapon_ExplosiveDecay._applyEffect(self, unit)
        Weapon_InvigoratingSpores._applyEffect(self, unit)
    def _removeEffect(self, unit):
        Weapon_ExplosiveDecay._removeEffect(self, unit)
        Weapon_InvigoratingSpores._removeEffect(self, unit) # do this last since it can kill the unit
    def _turnAction(self):
        Weapon_Regeneration._turnAction(self)

################################# Mech Passive Weapons #############################
# All mech passives must support power1 and 2 like regular mech weapons.
# Mech weapons must have an enable() method, but do not need a disable() as the passives are never disabled.

class Weapon_FlameShielding(Weapon_NoUpgradesInit_Base):
    "All Mechs are immune to Fire."
    def enable(self):
        for unit in self.game.playerunits:
            if unit.isMech():
                unit.attributes.add(Attributes.IMMUNEFIRE)

class Weapon_StormGenerator():
    "All Smoke deals damage to enemy units every turn."
    damage = 1
    def __init__(self, power1=False, power2=False):
        if power1:
            self.damage += 1
    def enable(self):
        self.game.stormtiles = set()
        # replace the game instance's stormGeneratorTurn with a real method
        self.game.stormGeneratorTurn = self._turnAction
        # Build a set of all tiles on the board that have smoke.
        for t in self.game.board.values():  # for now, iterate through all 64 tiles looking for smoke TODO: optimize?
            if Effects.SMOKE in t.effects:
                self.game.stormtiles.add(t.square)
        # replace the dummy stormgen methods on the Tile object:
        Tile_Base._addSmokeStormGen = self._addSmokeStormGen
        Tile_Base._removeSmokeStormGen = self._removeSmokeStormGen
    def _turnAction(self):
        "Damage all enemy units in a tile with smoke."
        for sq in self.game.stormtiles:
            t = self.game.board[sq]
            try:
                if t.unit.alliance == Alliance.ENEMY:
                    pass
                else:
                    continue
            except AttributeError: # t.None.alliance, no unit
                continue
            if Effects.SMOKE in t.effects:
                t.unit.takeDamage(self.damage, ignoreacid=True, ignorearmor=True) # the tile doesn't take damage
        self.game.flushHurt()
    def _addSmokeStormGen(self, square):
        self.game.stormtiles.add(square)
    def _removeSmokeStormGen(self):
        self.game.stormtiles.discard(self.square)
    def disable(self):
        "Undo the big mess we made. This is only to make tests pass ;)"
        # put the dummy stormgen methods back onto the Tile object:
        Tile_Base._addSmokeStormGen = Tile_Base._pass
        Tile_Base._removeSmokeStormGen = Tile_Base._pass

class Weapon_VisceraNanobots():
    "Mechs heal 1 damage when they deal a killing blow."
    heal = 1
    def __init__(self, power1=False, power2=False):
        "power2 is ignored."
        if power1:
            self.heal += 1
    def enable(self): # TODO: finish implementing this into the player's attack turn
        self.game.visceraheal = self.heal

# class Weapon_NetworkedArmor(): # This weapon scrapped because it doesn't make a difference for a single turn. Just tell the sim how much hp your mech has.
#     "All Mechs gain +1 HP."

class Weapon_RepairField(Weapon_NoUpgradesInit_Base):
    "Repairing one Mech will affect all Mechs."
    def enable(self):
        self.game.otherpassives.add(Passives.REPAIRFIELD)

class Weapon_AutoShields(Weapon_NoUpgradesInit_Base):
    "Buildings gain a Shield after taking damage."
    def enable(self):
        self.game.otherpassives.add(Passives.AUTOSHIELDS)

class Weapon_Stabilizers(Weapon_NoUpgradesInit_Base):
    "Mechs no longer take damage when blocking emerging Vek."
    def enable(self):
        self.game.otherpassives.add(Passives.STABILIZERS)

class Weapon_PsionicReceiver(Weapon_NoUpgradesInit_Base):
    "Mechs use bonuses from Vek Psion."
    def enable(self):
        raise FakeException

# Not doing this one, just tell the game how many moves your mechs currently have.
# class Weapon_KickoffBoosters():
#     "Mechs gain +1 move if they start their turn adjacent to each other."
#     move = 1
#     def __init__(self, power1=False, power2=False):
#         if power1:
#             self.move += 1 # mechs get 2 total moves
#     def enable(self):
#         for pu in self.game.playerunits:
#             if pu.isMech():
#                 for d in Direction.gen():
#                     try:
#
#         self.game.otherpassives.add(Passives.KICKOFFBOOSTERS) # Only effects mechs, not subunits. Both units get the buff even after you move one away.

# class Weapon_MedicalSupplies(Weapon_NoUpgradesInit_Base): # Not implementing this one either.

class Weapon_VekHormones(Weapon_IncreaseDamageWithPowerInit_Base):
    "Enemies do +1 Damage against other enemies."
    damage = 1
    def enable(self):
        self.game.vekhormones = self.damage
        Weapon_Vek_Base._dealDamage = Weapon_Vek_Base._dealDamageVekHormones
    def disable(self):
        "A destructor class to fix my tests. This was enabling vek hormones across all tests"
        Weapon_Vek_Base._dealDamage = Weapon_Vek_Base._dealDamageDefault

class Weapon_ForceAmp(Weapon_NoUpgradesInit_Base):
    "All Vek take +1 damage from Bumps and blocking emerging Vek."
    def enable(self):
        self.game.otherpassives.add(Passives.FORCEAMP)

# class Weapon_AmmoGenerator(): # not implementing this one. Just tell the sim how much ammo you have.

class Weapon_CriticalShields(Weapon_NoUpgradesInit_Base):
    "If Power Grid is reduced to 1, all buildings gain a Shield."
    def enable(self):
        "Replace your old and busted powergrid object with the special powergrid for dealing with critical shields."
        self.game.powergrid = Powergrid_CriticalShields(self.game, self.game.powergrid.hp)

########################## PILOTS #########################
# Few pilots are implemented because only a few actually have unique behavior that is needed.
# All pilots must have an enable() method to start their functionality
# All pilots must have a mech attribute which is set by the mech itself when initialized
# If you pilot isn't powered, then don't even tell the sim about it.
class Pilot_AddAttr_Base():
    "A base class for pilots that add an attribute to the mech."
    def __init__(self, attr):
        self.attr = attr
    def enable(self):
        self.mech.attributes.add(self.attr)

class Pilot_SecondaryMove_Base():
    "A base class for pilots that enable moving again after shooting."
    def enable(self):
        self.mech.secondarymoves = self.moves

class Pilot_ReplaceRepairWep_Base():
    def __init__(self, weapon):
        "weapon is the weapon object to replace the mech's repair."
        self.weapon = weapon
    def enable(self):
        self.mech.repweapon = self.weapon

class Pilot_AbeIsamu(Pilot_AddAttr_Base):
    "Armored: Mech gains Armored"
    def __init__(self):
        super().__init__(Attributes.ARMORED)

class Pilot_Prospero(Pilot_AddAttr_Base):
    "Flying: Mech gains Flying (1 power required)"
    def __init__(self):
        super().__init__(Attributes.FLYING)

class Pilot_Ariadne(Pilot_AddAttr_Base):
    "Rockman: +3 Health and immune to Fire."
    def __init__(self):
        super().__init__(Attributes.IMMUNEFIRE)

class Pilot_CamilaVera(Pilot_AddAttr_Base):
    "Evasion: Mech unaffected by Webbing and Smoke. (being immune to webbing is ignored, you'll just show up in the sim as not webbed)."
    def __init__(self):
        super().__init__(Attributes.IMMUNESMOKE)

class Pilot_ChenRong(Pilot_SecondaryMove_Base):
    "Sidestep: After attacking, gain 1 free tile movement."
    moves = 1

class Pilot_Archimedes(Pilot_SecondaryMove_Base):
    "Fire-and-Forget: Move again after shooting. (1 power required)"
    def enable(self):
        self.moves = self.mech.moves
        super().enable()

class Pilot_HenryKwan():
    "Maneuverable: Mech can move through enemy units."
    def enable(self):
        self.mech.kwanmove = True

class Pilot_Silica():
    "Double Shot: Mech can act twice if it does not move. (2 power required)"
    def enable(self):
        self.mech.doubleshot = True

class Pilot_Mafan():
    "Zoltan: +1 Reactor Core. Reduce Mech HP to 1. Gain Shield every turn. The only thing this pilot does is remove the score penalty for losing your shield since it always comes back."
    def enable(self):
        self.mech.score['shield_off'] = 0

class Pilot_HaroldSchmidt(Pilot_ReplaceRepairWep_Base):
    "Frenzied Repair: Push adjacent tiles when repairing."
    def __init__(self):
        super().__init__(Weapon_FrenziedRepair())

class Pilot_Kazaaakpleth(Pilot_ReplaceRepairWep_Base):
    "Mantis: 2 damage melee attack replaces Repair."
    def __init__(self):
        super().__init__(Weapon_MantisSlash())

############################# SCORING #######################
class ScoreKeeper():
    "This object keeps track of the score of a single game simulation with certain criteria. The MasterScoreKeeper feeds it."
    score = 0
    def __init__(self):
        self.log = [] # a tally of which events this scorekeeper saw. The amount is prepended to the log event
        # When a score is undone, a - is prepended to the log event.
    def submit(self, score, event, amount=1):
        """Submit a single event to be scored.
        score is an int of the points that it's worth.
        event is a string of a score event name.
        amount is the number of times to score it.
        returns nothing."""
        self.log.append('{0}{1}'.format(amount, event))
        self.score += score * amount
    def undo(self, score, event, amount=1):
        "Undo a single event in the score. event is a score constant. amount is the number of times to score it. returns nothing."
        self.log.append('-{0}{1}'.format(amount, event))
        self.score -= score * amount
    def __lt__(self, other):
        if self.score < other.score:
            return True
        return False
    def __gt__(self, other):
        if self.score > other.score:
            return True
        return False
    def __str__(self):
        try:
            return "Score: {0}, Events: {1}, ActionLog: {2}".format(self.score, self.log, self.actionlog)
        except AttributeError: # self.actionlog wasn't set
            return "Score: {0}, Events: {1}, ActionLog: None".format(self.score, self.log)

################################ SIMULATING ############################
class BinaryCounter():
    """Count a number in binary to be used for deciding which elements to include and exclude and also to advance
    unit move and shoot action generators."""
    def __init__(self, iterobj):
        self.binary = [False] * len(iterobj)
    def __iter__(self):
        return self
    def __next__(self):
        "advance the binary counter by 1, returning the index of the highest changed index."
        n = 0  # index of allactions item to check
        while True:
            try:
                if self.binary[n]: # if it's true, change it to False and go to the next until we find a False
                    self.binary[n] = False
                    n += 1
                else:  # we found a False
                    self.binary[n] = True
                    return n
            except IndexError:  # we tried to go beyond the end, this means we offered a set with all actions
                raise StopIteration
    def getInclusion(self, iterobj):
        "return a new list of items from iterobj when corresponding indexes of the binary number are True"
        newobj = []
        for i in range(len(iterobj)):
            if self.binary[i]:
                newobj.append(iterobj[i])
        return newobj

class OrderGenerator(): # TODO: we aren't generating orders for tank sub-units spawned by those weapons!
    "This object takes a Game object that's been set up and it generates instructions for worker threads to carry out and simulate."
    def __init__(self, game):
        self.game = game
        self.game.start()
    def __iter__(self):
        self.gen = self._gen()
        return self
    def __next__(self):
        return next(self.gen)
    def _gen(self):
        "Do the actual generating tuples of tuples: ((unit, Action.xyz), ...)"
        for playeractions in self._genActions():
            for order in permutations(playeractions):
                if self._validate(order):
                    #print("Valid:", tuple([(unit.type, Actions.pprint((action,))[0]) for unit, action in order])) # DEBUG
                    yield order
    def _getAllActions(self):
        """return a list of all possible actions the player can take on their turn.
        This includes exclusive moves, for example if a unit can shoot twice this will also show that they can move,
        even though they can't do both on a single turn.
        It's a list of tuples: [(unit, action), ...]"""
        allactions = []
        for pcu in self.game.playerunits:
            allactions.append((pcu, Actions.SHOOT)) # all units can shoot
            if pcu.moves: # if the unit can move
                allactions.append((pcu, Actions.MOVE)) # give it a move turn
            try:
                if pcu.secondarymoves: # if the unit has a secondary move
                    raise FakeException
            except AttributeError: # unit didn't have secondarymoves at all, it wasn't a mech
                pass
            except FakeException:
                allactions.append((pcu, Actions.MOVE2))  # give it a 2nd move turn
            try:
                if pcu.canDoubleShot(): # if the unit is allowed a 2nd shot
                    raise FakeException
            except AttributeError:
                pass
            except FakeException:
                allactions.append((pcu, Actions.SHOOT2))
        return allactions
    def _validate(self, actionorder):
        """Verify that this attempt is valid and not trying to simulate something not allowed in the game.
        actionorder must be an iter of (unit, action) tuples.
        Some examples of invalid attempts are:
            Letting a unit shoot and then use it's initial (or only) move.
            Letting a unit shoot, move, then shoot again. (You can only shoot twice if you don't move)
            Letting a unit move twice and then shoot. (You can only move a 2nd time after taking a shot)
        return True if it's a valid attempt, False if it's not."""
        # make a dict of player units to the actions that they can no longer use
        bannedactions = {p: set() for p in self.game.playerunits}
        # as we step through the attempt, we'll add actions that are no longer available and find illegal attempts
        for unit, action in actionorder:
            if action in bannedactions[unit]: # make sure the current action isn't already banned
                return False
            else: # if not, it is now
                bannedactions[unit].add(action)

            if action == Actions.SHOOT: # shooting means you can no longer move
                bannedactions[unit].add(Actions.MOVE)
            elif action == Actions.MOVE2: # You can't move, shoot, or shoot2 or after doing your 2nd move
                if Actions.SHOOT not in bannedactions[unit]: # if you haven't shot yet...
                    return False # you can't do a 2nd move. 2nd moves are only allowed after shooting a weapon
                bannedactions[unit].update({Actions.MOVE, Actions.SHOOT, Actions.SHOOT2})
            elif action == Actions.SHOOT2: # you can't move or take your first shot after your 2nd shot.
                bannedactions[unit].update({Actions.MOVE, Actions.SHOOT})
        return True
    def _genActions(self):
        "This generates unique combinations from _getAllActions. yields a set of {(unit, action), ...} tuples."
        # The way this works is that the bool at the beginning indicates whether it should be included or not.
        # when we start and get allactions, everything is off, set to False. We'll go through this and flip each bool,
        # essentially counting in binary.
        allactions = self._getAllActions()
        bc = BinaryCounter(allactions)
        while True:
            yield bc.getInclusion(allactions)
            try:
                next(bc)
            except StopIteration:
                return

class OrderSimulator():
    """This object takes a Game object that's been set up and a game order tuple.
    It simulates all possible unit moves/shots and returns the best possible score.
    This can be thought of as a worker thread."""
    sims = 0 # a count of the unique simulations attempted.
    def __init__(self, game, order):
        if not order:
            print("Empty Order Simulation skipped") # TODO: do game ending score counting for the null set order where the player does nothing
            return
        else:
            pass
            #print("\nOrder is: ", order)
        self.game = game  # set the final game instance to be persistent so run can use it.
        self.order = order
        self.player_action_iters = [None] * len(order)
        # build out self.player_action_iters based on order
        self._increment_player_action_iters(len(self.player_action_iters)-1, game, order)
        #print("self.pai is", self.player_action_iters)
        self.highscore = ScoreKeeper() # initialize with a blank scorekeeper
    def run(self):
        """Start brute forcing all possible player actions for this particular order.
        returns a tuple of how many simulations were run and the best high score object."""
        try:
            game = self.game
        except AttributeError: # self.game was never set because we're working on the null set of orders
            return # TODO: end the game for the null set
        del self.game # don't keep the cruft
        finalaction = len(self.player_action_iters) - 1
        while True:
            self.sims += 1
            try:
                game.endPlayerTurn()
            except GameOver:
                pass # continue on to the next simulation
            else:
                if game.score > self.highscore:
                    self.highscore = game.score
                    self.highscore.actionlog = game.actionlog
            try:
                game = self._increment_player_action_iters(finalaction)
            except SimulationFinished:
                print('{0} sims finished for order {1}'.format(self.sims, [(x[0].type, Actions.pprint((x[1],))) for x in self.order]))
                return self.sims, self.highscore
    def _increment_player_action_iters(self, index, startingstate=None, startingorder=None):
        """increment self.player_action_iters.
        index is an int of the index of self.player_action_iters to operate on.
        startingstate is the initial gamestate to use when bootstrapping
        startingorder is the order to to use when bootstrapping
        returns the next game object.
        :raise SimulationFinished when we run out of unit actions to iterate through."""
        assert index > -1
        try:
            return next(self.player_action_iters[index])
        except StopIteration: # this one ran out, so increment the previous one and get a new gamestate from it
            if index == 0: # don't wrap around to -1
                raise SimulationFinished
            self._replace_pai(self._increment_player_action_iters(index - 1), index)
            return self._increment_player_action_iters(index) # and now try to get the next game from this newly replaced pai
        except TypeError: # raised when trying to next(None) on initial startup
            if not startingstate:
                #print("No startingstate! Caught TypeError when trying to next(self.player_action_iters[{0}]). That Iter was: {1}".format(index, self.player_action_iters[index]))
                raise
            #print("replacing pai at index", index)
            #print("startingstate is ", startingstate)
            #print("startingorder is", startingorder)
            if index == 0:
                self._replace_pai(startingstate, 0, startingorder)
            else:
                self._replace_pai(self._increment_player_action_iters(index - 1, startingstate, startingorder), index, startingorder)
            # Now that a pai has been put in place, call this same method recursively to get the next one and return a game
            return self._increment_player_action_iters(index, startingstate, startingorder)
    def _replace_pai(self, game, index, orders=None):
        """Replace a player_action_iter with a new one with game as it's starting state.
        game is the game state with which to start this new iterator.
        index is an int of the index of this player_action_iter.
        orders is the order if we are initializing a None
        returns nothing."""
        #print("game is", game)
        assert game
        try:
            self.player_action_iters[index] = type(self.player_action_iters[index])(game, *self.player_action_iters[index].getArgs())
        except AttributeError: # type(None)(...)
            if not orders:
                raise Exception("No orders given!") # TODO: Debug
            if orders[index][1] in (Actions.SHOOT, Actions.SHOOT2):  # if this action is to shoot...
                self.player_action_iters[index] = Player_Action_Iter_Shoot(game, orders[index][0])  # add a shoot iterator (orders[index][0] is the unit in orders)
            elif orders[index][1] == Actions.MOVE:  # if the action is to move
                self.player_action_iters[index] = Player_Action_Iter_Move(game, orders[index][0], orders[index][0].moves)  # add a MOVE iterator
            else:  # it must be a MOVE2 action
                self.player_action_iters[index] = Player_Action_Iter_Move(game, orders[index][0], orders[index][0].secondarymoves)  # add a MOVE2 iterator

class Player_Action_Iter_Base():
    """The base object for Player Action iters.
    Player Action Iters are used by Order Simulator for a single unit to take every possible action.
    Actions consist of moves or shots.
    __next__ methods return a new deepcopy of a game object with this unit's next move already made."""
    def __init__(self, prevgame, unit):
        """prevgame is the game object and state before this unit makes it's moves.
        prevgame should not be a deepcopy.
        unit is the unit object that this iter is iterating through.
        returns nothing."""
        assert prevgame
        #self.prevgame = deepcopy(prevgame) # the starting state for each action that this object generates. This should never change.
        self.prevgame = prevgame # the starting state for each action that this object generates. This should never change.
        self.origunitid = unit.id # this won't change and is used to find the corresponding unit in new copies of prevgame.
        for u in self.prevgame.playerunits:
            try:
                if unit.id == u.id:
                    self.unit = u
                    break
            except AttributeError: # Unit_Mech_Corpse' object has no attribute 'id'
                continue
        self.unit = unit # if unit wasn't set from the previous game, set it to what was passed in so this can keep being passed to new iterators
        # until we find a game object with this unit in it
    def __iter__(self):
        return self
    def _copygame(self):
        "Return a deepcopy of the previous game and also set self.unit to the proper unit in the new deepcopy."
        assert self.prevgame
        newgame = deepcopy(self.prevgame)
        #print("prevgame units is: ", self.prevgame.playerunits)
        #print("newgame units is: ", newgame.playerunits)
        #print("playerunits is", [x.square for x in newgame.playerunits])
        for u in newgame.playerunits:
            try:
                if self.origunitid == u.id:
                    self.unit = u
                    return newgame
            except AttributeError: # Unit_Mech_Corpse' object has no attribute 'id'
                continue
        #print("originunitsquare is", self.origunitsquare)
        #raise Exception("No unit with square {0} found in prevgame. playerunits are: {1}".format(self.origunitsquare, [x.square for x in newgame.playerunits]))
        raise StopIteration # If self.unit didn't get set, raise StopIteration as that unit is not available to make an action.
    def __iter__(self):
        return self

class Player_Action_Iter_Shoot(Player_Action_Iter_Base):
    """This object iterates through Action.SHOOT actions."""
    def __init__(self, prevgame, unit):
        super().__init__(prevgame, unit)
        self.gen = self._genNextShot()
    def __next__(self):
        while True:
            shot = next(self.gen) # will raise StopIteration and stop this from advancing.
            newgame = self._copygame()
            try:
                getattr(self.unit, shot[0]).shoot(*shot[1])
            except (NullWeaponShot, GameOver) as exc:
                #print("Disqualified: ", exc)
                continue # this wasn't a valid solution if the shot did nothing or ended the game
            try:
                newgame.flushHurt()
            except GameOver:
                continue
            newgame.actionlog.append('{0} on {1} shoots {2} {3}'.format(self.unit.type, self.unit.square, *shot))  # record this action to the game's action log
            return newgame
    def _genNextShot(self):
        "generate tuples of (weapon, (shot,)) for __next__ to use."
        try:
            if Effects.SMOKE in self.unit.game.board[self.unit.square].effects: # if this unit is in smoke
                if Attributes.IMMUNESMOKE not in self.unit.attributes: # and it's not smoke immune...
                    return # it can't shoot
        except AttributeError: # self.unit was never initially set
            return
        if Effects.ICE in self.unit.effects: # if this unit is frozen...
            weapons = ('repweapon',) # the only weapon you can fire is your repair
        else:
            weapons = ('repweapon', 'weapon1', 'weapon2')
        for weapon in weapons:
            try:
                gs = getattr(getattr(self.unit, weapon), 'genShots') # see if this weapon exists and can be shot
            except AttributeError: # this unit didn't have this weapon attribute at all or it's a passive weapon that can't be fired.
                continue # onto the next weapon
            for shot in gs():
                yield (weapon, shot)
    def getArgs(self):
        """return a tuple of the (unit,) argument that was used to construct this object.
        note that the prevgame argument is omitted, because this is what changes in the replacement object.
        This is used to initialize a replacement object after this one has run it's course."""
        return (self.unit,)

class Player_Action_Iter_Move(Player_Action_Iter_Base):
    """This object iterates through Action.MOVE actions."""
    def __init__(self, prevgame, unit, moves):
        """Moves is the number of squares this unit can move.
        This is provided because this object is used for both regular moves and secondary moves."""
        super().__init__(prevgame, unit)
        self.moves = moves
        self.gen = self._genNextMove()
        self.originsquare = self.unit.square
    def __next__(self):
        while True:
            sq = next(self.gen) # will raise StopIteration and stop this from advancing
            newgame = self._copygame()
            newgame.board[self.unit.square].moveUnit(sq)
            try: # you can move onto a mine and die so we need flushHurt after moving
                newgame.flushHurt()
            except GameOver:
                continue
            #newgame.actionlog.append((self.unit, Actions.MOVE, sq)) # record this action to the game's action log
            newgame.actionlog.append('{0} on {1} moves to {2}'.format(self.unit.type, self.originsquare, self.unit.square)) # record this action to the game's action log
            return newgame
    def _genNextMove(self):
        "generate tuples of squares (x, y) for __next__ to use."
        for square in self.unit.getMoves(self.moves):
            if not self.unit.game.board[square].unit: # if there's not a unit present on the square
                yield square
    def getArgs(self):
        """return a tuple of the (unit, moves) arguments that were used to construct this object.
        note that the prevgame argument is omitted, because this is what changes in the replacement object.
        This is used to initialize a replacement object after this one has run it's course."""
        return (self.unit, self.moves)
