# TicTacTobot

TicTacToe on an Opentrons Liquid Handling Robot, using a video game controller.

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

## Notes

- This code is written in "Hackathon style".

- Uses custom a branch of the Opentrons API, to make everything run smoothly. Available [here](https://github.com/rickwierenga/opentrons/tree/tictactobot).

---

_This project was developed for the Sculpting Evolution Group, to present at the Media Lab's Members Meeting, Fall 2022_
