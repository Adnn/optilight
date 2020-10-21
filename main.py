#!/usr/bin/env python3

import argparse
from functools import reduce, cmp_to_key
import itertools
import operator
import json


class Stats:
    def __init__(self, array):
        self.array = array
        self.total = reduce(operator.add, self.array)

    def __str__(self):
        return "Mob: {} | Res: {} | Rec: {} | Dis: {} | Int: {} | Str: {}".format(*self.array)

    def thresholds(self):
        return list(map(lambda a : a//10, self.array))

    def summedthresholds(self):
        return reduce(operator.add, self.thresholds())

    def clamped(self):
        """ The normalized stats, i.e. the thresholds times 10 """
        return Stats(list(map(lambda a : a*10, self.thresholds())))

    def waste(self):
        """ Return another Stats instance representing the waste in each entry """
        """ Waste == the unit digit """
        return difference(self, self.clamped())


def accumulate(left, right):
    return Stats(list(map(operator.add, left.array, right.array)))

def difference(left, right):
    return Stats(list(map(operator.sub, left.array, right.array)))

def compare(left, right):
    return left.summedthresholds() - right.summedthresholds()



class Equipment:
    def __init__(self, json, implicit_masterwork=False):
        self.name = json["name"]
        self.power = json["power"]
        self.masterworked = json["mw"]
        self.stats = Stats(json["stats"])

        # Sanity check:
        if self.stats.total != json["total"]:
            raise Exception("Error in stats vs. total for {} (power: {})".format(self.name, self.power))

        if implicit_masterwork:
            self.masterwork()

    def masterwork(self):
        if not self.masterworked:
            self.stats = accumulate(self.stats, Stats([2, 2, 2, 2, 2, 2]))
            self.masterworked = True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "{}:{} ({})".format(self.name, self.power, self.stats.total)


def combinationStats(combination):
    return reduce(accumulate, [equipment.stats for equipment in combination])


def combinationRank(combination):
    return combinationStats(combination).summedthresholds()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize Destiny2 equipment stats thresholds")
    parser.add_argument("equipment",
                        help="Path to a Json file containing the available equipment")
    parser.add_argument("--masterwork", action="store_true",
                        help="Masterwork equipment, if it is not already")
    args = parser.parse_args()

    with open(args.equipment) as f:
        equipment = json.load(f)

    result = {category: [Equipment(entry, args.masterwork) for entry in inventory]
              for category, inventory in equipment.items()}

    combinations = itertools.product(*result.values())
    for loadout in sorted(combinations, key=combinationRank):
        stats = combinationStats(loadout)
        print ("Rank {} ({}), waste: {} ({})\n\t{}"\
                .format(combinationRank(loadout),
                        Stats(stats.thresholds()),
                        stats.waste().total,
                        stats.waste(),
                        loadout))
