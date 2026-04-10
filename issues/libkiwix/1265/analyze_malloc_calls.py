#!/usr/bin/env python3


import sys

memoryAllocationMap = {}
nBytesUsed = 0

def parse_malloc(line):
    _, m, _, addr = line.split()
    n = int(m[7:-1])
    return addr, n

def parse_free(line):
    _, f = line.split()
    addr = f[5:-1]
    return addr

for line in sys.stdin:
    nBytes = 0
    if 'malloc' in line:
        addr, nBytes = parse_malloc(line)
        memoryAllocationMap[addr] = nBytes
        nBytesUsed += nBytes
    elif 'free' in line:
        addr = parse_free(line)
        if addr in memoryAllocationMap:
            nBytes = memoryAllocationMap[addr]
            del memoryAllocationMap[addr]
            nBytesUsed -= nBytes
        else:
            print('!!!')
    print(f'{line.strip()} | {nBytesUsed}', )


print("\n\n\n-------------------------------\n")
print("Allocated memory blocks:")
for addr, nBytes in memoryAllocationMap.items():
    print(f' - {addr}: {nBytes}')
