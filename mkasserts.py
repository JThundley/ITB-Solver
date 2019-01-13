#!/usr/bin/env python3
x = input("x: ")
y = input("y: ")
print("\n    assert g.board[(%s, %s)].effects == set() # no tile effects" % (x, y))
print("    assert g.board[(%s, %s)].unit == None # no unit here" % (x, y))
print("    assert g.board[(%s, %s)].unit.effects == set()" % (x, y))
print("    assert g.board[(%s, %s)].unit.hp == 5" % (x, y))
