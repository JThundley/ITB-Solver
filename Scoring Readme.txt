############################# SCORING ##################################
Scoring is done on a scale of -100 to 100, but arbitrary numbers are allowed. Negative numbers are for when bad things happen, positive numbers are good things.
When a unit dies, any damage and effects to it are un-scored. This is to avoid damaging a unit to death being more valuable than just instakilling the unit by pushing it into water.
We also want to avoid a unit catching on fire and then dying being more valuable than just killing the unit.

Here is the general strategy for scoring:
Units getting effects added to them are the lowest scores, below 10. The rationale being that enemies being set on fire and getting acid is good, but id doesn't matter much
if you don't kill that unit during this turn. The enemy can still damage you and your buildings. The damage that the fire causes is scored separately as normal damage done to the unit.
The same goes for acid: it'll help you do more damage to the unit and that damage is what really matters. If the unit dies, the scoring for acid/fire/ice/shield is undone. The effect makes no difference
after the unit is dead.
Damage is the next highest score, typically in the low 10's. Remember that damage means damage that the unit took and *survived*.
Death is the highest score, in the higher 10s. Death points typically scale with how much total HP the unit has as the unit is a decent measure of how dangerous the unit is.

MISC:
The powergrid taking damage is -50
A building taking damage is 0 (we only count the powergrid damage)
An objective building taking damage is -20 in addition to the powergrid damage that goes with it.
A building being frozen or shielded is 9
A freezemine/mine being destroyed is -3
A timepod being destroyed is -30
A timepod being picked up is 2 (Don't score this too high since leaving it on the field is nearly as good as picking it up)
An objective unit dying is -30 (Doesn't apply to units you're supposed to kill such as Dam and Acid Vat)
Objective units you're supposed to kill are 10 per damage
Objective units you're supposed to kill are 10 * total hp when killed
A new vek emerging into fire or acid is 7

ENEMIES:
An enemy taking damage is is -10
An enemy dying is 11 * total hp, e.g. killing a 1hp leaper = 11, killing a 4hp boss = 44
A boss dying is 12 * total hp
An enemy gaining fire/acid/ice is 6
An enemy losing fire/acid/ice is -6
An enemy being shielded is -6
An enemy losing shield is 6
An enemy with 1 hp gaining acid is 0
An enemy repairing is 10 per hp

FRIENDLIES:
A mech taking damage is -15
A mech dying is -15 * total hp
A pilot being lost to mech death is -20
A friendly repairing hp is 15 per hp
A deployable tank taking damage is -10
A deployable tank dying is -11 * total hp
A friendly gaining fire/acid/ice is -6
A friendly losing fire/acid/ice is 6
A friendly being shielded is 6
A friendly losing shield is -6