This was v1, where we just run a server on the Opentrons. That was quite slow and "stuttering".

## Protocol

TCP/IP sockets. Server uses port 65432. All commands are 13 bytes.

```
M:xxx,yyy,zzz     move to location

# below only the first character matters.
PPPPPPPPPPPPP     pick up next tip
EEEEEEEEEEEEE     eject tip to next free location

A:xxx,yyy,zzz     aspirate at location, 100ul
D:xxx,yyy,zzz     dispense at location, 100ul
```
