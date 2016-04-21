#!/usr/bin/env python
#
# script i'm using to validate output, a bit
#

import json
from collections import OrderedDict

def main():
    # read in output files
    output_file = open("../output/part-00000", "r")
    counter_map = {}
    sources = []
    for line in output_file:
        parts = line.split(None, 1)
        if len(parts) > 1:
            data = json.loads(parts[1])
        sources.append(data['source'])
        for key in data:
            if data[key] == None:
                if key in counter_map:
                    counter_map[key] += 1
                else:
                    counter_map[key] = 1
    od = OrderedDict(sorted(counter_map.items(), key=lambda t: t[1]))        
    print (counter_map, set(sources))
    print (od)

if __name__ == "__main__":
    main()
