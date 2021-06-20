#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import glob

class Maze:

    def __init__(self):
        self.rooms = []
        self.name = 'room*.maze'
        self.dir = './../maze/'
        self.entry_pattern = 'try maze'
        self.entry_room_num = 0
        self.out_aiml = 'generated.aiml'
        self.moves = [
            'go north',
            'go south',
            'go west',
            'go east',
            'go up',
            'go down',
            'go northeast',
            'go southeast',
            'go northwest',
            'go southwest'
        ]

    def read_files(self):
        g = glob.glob(self.dir + self.name)
        g.sort()
        print(g)
        for i in g:
            self.rooms.append(self.room_factory(room=i))
        
        pass

    def write_xml(self):
        w = open(self.dir + self.out_aiml, 'w')
        w.write('<aiml version="1.0.1" encoding="UTF-8">\n')
        self.entry_category(w)
        self.entry_moves(w)
        self.direction_statements(w)
        self.simple_look(w)
        w.write('</aiml>\n')
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

    def entry_moves(self, file):
        for i in self.moves:
            file.write('<category>\n<pattern>' + i.upper() + '</pattern>\n')
            file.write('<template>')
            for ii in self.rooms:
                num = '000' + str(ii['number'])
                num = num[-2:]
                file.write('<condition name="topic" value="ROOM'+ num +'">\n')
                if i in ii['phrases'].keys():
                    z = ii['phrases'][i]
                    numx = '000' + str(z)
                    numx = numx[-2:]
                    file.write('    <srai>INTERNAL ROOM' + numx + ' ' + i.upper() +'</srai>\n')
                    pass
                else:
                    file.write('    You cannot do that here.\n')
                    pass
                file.write('</condition>\n')
            file.write('</template>\n')
            file.write('</category>\n\n')
        pass
    
    def entry_category(self, file):
        file.write('''
            <category>
            <pattern>''')
        file.write(self.entry_pattern.upper() )
        file.write('''</pattern>
            <template>
            <!-- starting room -->\n''')
        # insert think here
        num = str(self.entry_room_num)
        num = '000' + num
        num = num[-2:]
        file.write('''
            <think><set name="topic">ROOM''' + num + '''</set></think>\n''')
        for i in range(len(self.rooms)):
            self.reused_seen(file, self.rooms[i]['number'])

        file.write('''
            <srai> INTERNALLOOK <get name="topic" /></srai>
            </template>
            </category>\n''')
        pass

    def reused_seen(self, file, num, val='unseen'):
        num = '000' + str(num)
        num = num[-2:]
        file.write('''
            <think><set name="seen''' + num + '''">''' + val + '''</set></think>\n''')
        pass

    def direction_statements(self, file):
        for i in range(len(self.rooms)):
            num = self.rooms[i]['number']
            file.write('<!-- ROOM' + str(num) + ' -->\n')
            numx = '000' + str(num)
            numx = numx[-2:]

            for ii in self.rooms[i]['phrases'].keys():
                print(ii, self.rooms[i]['phrases'][ii])
                
                numx = '000' + str(self.rooms[i]['phrases'][ii])
                numx = numx[-2:]
                file.write('''
                <category>
                <pattern>
                INTERNAL ROOM'''+ numx + ''' ''' + ii.upper() + '''
                </pattern>
                <template>
                    <think><set name="topic">ROOM''' + numx + '''</set></think>
                    <srai> INTERNALLOOK <get name="topic" /></srai>
                </template>
                </category>\n''')
            
            self.internal_look(file, num)
        pass

    def internal_look(self, file, num):
        numx = '000' + str(num)
        numx = numx[-2:]
        long = self.rooms[num]['description']
        short = self.rooms[num]['title']
        file.write('''        <category>
        <pattern>INTERNALLOOK ROOM''' + numx + '''</pattern>
            <template>
                <condition name="seen''' + numx + '''" value="unseen">
                    ''' + long + '''
                </condition>

                <condition name="seen''' + numx + '''" value="seen">
                    ''' + short + '''
                </condition>

                <think><set name="seen''' + numx + '''">seen</set></think>
            </template>

        </category>\n''')
        pass

    def simple_look(self, file):
        file.write('''<!-- simple look command -->\n''')
        file.write('''        <category>
        <pattern>
            LOOK
        </pattern>
        <template>
            <!-- one condition block for every room -->\n''')

        for i in range(len(self.rooms)):
            num = self.rooms[i]['number']
            numx = '000' + str(num)
            numx = numx[-2:]
            file.write('''            <condition name="topic" value="ROOM''' + numx + '''">
                <think><set name="seen''' + numx + '''">unseen</set></think>
            </condition>\n''')
        file.write('''            <srai> INTERNALLOOK <get name="topic" /></srai>
            </template>
            </category>\n''')
        pass

if __name__ == '__main__':
    m = Maze()
    m.read_files()
    print(m.rooms)
    m.write_xml()
