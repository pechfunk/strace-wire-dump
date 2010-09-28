#!/usr/bin/env python2.5

"""
Dumping tool for strace

strace can capture the data read from and written to file descriptors.
Unfortunately, it displays them as a hex dump. This tool converts
the strace log to a numbered series of files containing the hexdumped
content as binary.

The files are named NNNN_W_F.txt, where NNNN is the sequence number, W
says whether the bytes were written ('w') or read ('r') and F is the
file descriptor. Multiple writes or writevs to the same FD are
coalesced into one file, as long as no non-write happens between them.

This tool does not yet recognize when file descriptors are reused.

Userfriendlyness is minimal.
"""

import re, sys

readRe = re.compile(r"^read\((\d+),")
writevRe = re.compile(r"^writev?\((\d+),")
writevHeaderRe = re.compile(r"^ \* (\d+) bytes in buffer (\d+)")
writevBodyRe = re.compile(r"^ \| ([a-z0-9]+)\s+((([a-z0-9]{2} )+) ((([a-z0-9]{2} )+)?)) ")

def test_regexes() :
    m = readRe.match('read(5, "# This file was created by config"..., 4096) = 2551\n')
    assert m.groups() == ('5',)

    m=writevBodyRe.match(''' | 00240  65 3e 0a 3c 2f 44 3a 6d  75 6c 74 69 73 74 61 74  e>.</D:m ultistat |
''')
    gs= m.groups()
    assert gs[1]=='65 3e 0a 3c 2f 44 3a 6d  75 6c 74 69 73 74 61 74 '
    m=writevBodyRe.match(''' | 00250  75 73 3e 0a                                       us>.              |
''')
    gs=m.groups()
    assert m.groups()[1]=='75 73 3e 0a  '
    m = writevHeaderRe.match(""" * 157 bytes in buffer 7
""")
    assert m

def hexes_to_bytes(s):
    return ''.join([chr(int(x,16)) for x in s.split()])

def test_hexes_to_bytes():
    assert hexes_to_bytes("") == ""
    assert hexes_to_bytes("41 42 ") == "AB"
    assert hexes_to_bytes(" 47 41 42 43 44  45 46") == "GABCDEF"

def events_from_file(f):
    "yield (fdstr, isWrite, bytes) for every IO in the log"
    fragments = []
    isWrite = False
    fdStr = "Invalid"
    valid = False
    for inpLine in f:
        #print "LINE", inpLine[:20]
        m = readRe.match(inpLine)
        if m:
            #print "READ!"
            if valid:
                newFdStr = m.group(1)
                if isWrite or newFdStr != fdStr:
                    # new chapter
                    yield (fdStr, isWrite, "".join(fragments))
                    fragments = []
                    fdStr = newFdStr
                    isWrite = False
            fdStr = m.group(1)
            isWrite = False
            fragments = []
            valid = True
        else:
            m = writevRe.match(inpLine)
            if m:
                #print "WRITE!"
                if valid:
                    newFdStr = m.group(1)
                    if (not isWrite) or newFdStr != fdStr:
                        # new chapter
                        if fragments:
                            yield (fdStr, isWrite, "".join(fragments))
                        fragments = []
                        fdStr = newFdStr
                        isWrite = True                    
                else:
                    # not valid. Start writing
                    valid = True
                    fdStr = m.group(1)
                    isWrite = True
                    fragments = []
            else:
                m = writevHeaderRe.match(inpLine)
                if m:
                    #print "HEADER!"
                    pass #ignore that line, keep reading
                else:
                    m= writevBodyRe.match(inpLine)
                    if m:
                        #print "BODY!", m.group(2)
                        fragments.append(hexes_to_bytes(m.group(2)))
                    else:
                        if valid and fragments:
                            yield (fdStr, isWrite, "".join(fragments))
                        fragments = []
                        valid = False
                        isWrite = False
                        fdStr = "Invalid"
    if valid and fragments:
        yield (fdStr, isWrite, "".join(fragments))
    
    
def log_to_fragments(f):
    "create a lot of files in the local dir from events in logfile f"
    serial = 0    
    for (fdStr, isWrite, bs) in events_from_file(f):
        
        fn = "%0.4d_%s_%s.txt" %(serial, fdStr, ["r","w"][int(not not isWrite)])
        #print fn
        file(fn, "w").write(bs)
        serial += 1

if __name__=="__main__":
    test_regexes()
    test_hexes_to_bytes()
    if len(sys.argv) < 2:
        print "Syntax: strace_wire_dump.py STRACELOGFILE"
        sys.exit(10)
    log_to_fragments(file(sys.argv[1]))
    
