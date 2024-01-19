import random

def roll(formula):
    split = formula.split('d')
    count = 1
    if len(split)>1 and split[0].isdecimal():
        count = int(split[0])
    split = split[-1].split('+')
    add = 0
    if len(split)>1 and split[1].isdecimal():
        add = int(split[1])
    range = int(split[0]) if split[0].isdecimal() else 1
    return random.randint(count, count*range) + add
