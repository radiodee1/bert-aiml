#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import glob

class Maze:

    def __init__(self):
        self.rooms = []
        self.name = 'room*.maze'
        self.dir = './../maze/'

    def read_files(self):
        g = glob.glob(self.dir + self.name)
        print(g)
        for i in g:
            self.rooms.append(self.room_factory(room=i))
        pass

    def write_xml(self):
        pass
    
    def room_factory(self, room=''):
        z = open(room, 'r')
        zz = z.readlines()
        zz = [x for x in zz if not x.startswith('#')]
        zz = ''.join( zz)
        z.close()
        number = ''
        title = ''
        description = ''
        phrases = {}

        #print(zz)
        num = 0
        remember = 0
        zzz = 0
        state = ''
        phrase = ''
        destination = '0'
        for i in zz:
            
            if num == 0 + zzz and i != '\n':
                number += str(i)
                #print(number)
            elif num == 2 + zzz and i != '\n':
                title += str(i)
                #print(title)
            elif num == 4 + zzz and i != '\n':
                description += str(i)
                #print(description)
            elif num > 4 + zzz and i == "@":
                remember = num
                state = "phrase"
            elif num > 4 + zzz and i == ";":
                state = "number"
            elif num > 4 + zzz and i not in "@;":
                if remember != num: continue
                if state == "phrase":
                    phrase += str(i)
                if state == "number" and i != ' ':
                    destination += str(i)
                if i == '\n':
                    phrases[str(phrase).strip().lower()] = int(destination.strip())
                    phrase = ''
                    destination = '0'
                pass  
            if i == '\n':
                num += 1
        
        pass
        #z.close()
        x = {
            'number': int(number.strip()),
            'title': title,
            'description': description,
            'phrases': phrases
        }
        #print(x)
        return x
    

if __name__ == '__main__':
    m = Maze()
    m.read_files()
    print(m.rooms)
