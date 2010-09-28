==================
 strace_wire_dump
==================

strace can capture the data read from and written to file descriptors.
Unfortunately, it displays them as a hex dump. This tool converts
the strace log to a numbered series of files containing the hexdumped
content as binary.

The files are named NNNN_W_F.txt, where NNNN is the sequence number, W
says whether the bytes were written ('w') or read ('r') and F is the
file descriptor. Multiple writes or writevs to the same FD are
coalesced into one file, as long as no non-write happens between them.

Usage example
=============

Let's assume you're debugging a problem with git-svn which complains
about a "400 Bad Request". You want to see what goes over the TCP connection,
and you cannot use Wireshark because you're not root enough. You have observed
in strace that the TCP connection to the server gets to be fd 5. So you execute
the following strace command line::
 |  strace -o STRACE.txt -e read=5 -e write=5 -f git svn clone SOME_URL

This will produce a log file STRACE.txt with lines like::
 |  epoll_wait(4, {{EPOLLIN, {u32=163117760, u64=163117760}}}, 16, 2000000) = 1
 |  read(5, "HTTP/1.1 400 Bad Request\r\nDate: T"..., 8000) = 373
 |   | 00000  48 54 54 50 2f 31 2e 31  20 34 30 30 20 42 61 64  HTTP/1.1  400 Bad |
 |   | 00010  20 52 65 71 75 65 73 74  0d 0a 44 61 74 65 3a 20   Request ..Date:  |

Then you run strace_wire_dump on the logfile::
 |  strace_wire_dump.py STRACE.txt

and end up with::
 | $ ls
 | 0000_5_r.txt  0014_5_r.txt  0028_5_r.txt  0042_5_r.txt	0056_5_r.txt  0070_5_w.txt
 | 0001_5_r.txt  0015_5_r.txt  0029_5_r.txt  0043_5_r.txt	0057_5_r.txt  0071_5_r.txt
 | ...
 | 0013_5_r.txt  0027_5_r.txt  0041_5_r.txt  0055_5_r.txt	0069_5_r.txt  0083_5_r.txt

From the numbered text files, you can then reconstruct what went over
the wire when.



Bugs
====

1. This tool does not yet recognize when file descriptors are reused.
   
2. Userfriendlyness is minimal.


