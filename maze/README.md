# Definitions

Lines that begin with `#` are ignored. Characters on a line after a `#` are ignored. Blank lines separate components in these definition files, except for the descriptions of the commands that would allow you to navigate to another room. These start with an `@` sign and are completed with a number after an `;` sign.

# maze files: `room00.maze`

```
0 

Room 0 - Start room

Go east, west, or south. This is the longer text that fills the screen when the room is visited for the first time. It may contain several sentences.
@ Go east;1
@ Go west;2
@ go south; 3


# hash is for comments. blank lines are important!
```

# item files: `thing00.item`

```
0 # item can be found at this room number when the maze loads

lamp # this is the name of the item

@ light the lamp ; 99 # this is currently not used
```