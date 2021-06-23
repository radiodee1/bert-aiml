#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import glob

class Maze:

    def __init__(self):
        self.rooms = []
        self.items = []

        self.name = 'room*.maze'
        self.dir = './../maze/'
        self.entry_pattern = 'try maze'
        self.entry_room_num = 0
        self.out_aiml = 'generated.aiml'
        self.item_name = 'thing*.item'
        
        self.confuse_text = "XYZABCCONFUSEME"

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

    def strip_comments(self, list_of_strings):
        z = []
        for i in list_of_strings:
            end = False
            l = ''
            for ii in i:
                if ii == '#':
                    end = True
                    l += '\n'
                if end == False:
                    l += ii
                pass
            z.append(l)
            
        return z

    def read_files(self):
        g = glob.glob(self.dir + self.name)
        g.sort()
        print(g)
        for i in g:
            self.rooms.append(self.room_factory(room=i))
        
        g = glob.glob(self.dir + self.item_name)
        g.sort()
        for i in g:
            self.items.append(self.item_factory(item_file=i))
        print(self.items)
        pass

    def write_xml(self):
        w = open(self.dir + self.out_aiml, 'w')
        w.write('<aiml version="1.0.1" encoding="UTF-8">\n')
        self.entry_category(w)
        self.entry_moves(w)
        self.direction_statements(w)
        self.simple_look(w)
        self.item_statements(w)
        self.item_list(w)
        w.write('</aiml>\n')
        pass
    
    def room_factory(self, room=''):
        z = open(room, 'r')
        zz = z.readlines()
        zz = [x for x in zz if not x.startswith('#')]
        zz = self.strip_comments(zz)
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
        destination = 0
        number = number.split()
        if len(number) > 1:
            destination = int(number[1])
            number = str(number[0])
        else:
            number = str(number[0])
        x = {
            'number': int(number.strip()),
            'title': title,
            'description': description,
            'destination': destination,
            'phrases': phrases
        }
        #print(x)
        return x

    def item_factory(self, item_file=''):
        z = open(item_file, 'r')
        zz = z.readlines()
        zz = [x for x in zz if not x.startswith('#')]
        zz = self.strip_comments(zz)
        z.close()
        pass

        name = ''
        num = 0
        phrases = {}

        index = 0
        for i in zz:
            if index == 0:
                num = int(i.strip())
            if index == 2:
                name = str(i.strip())

            if index >=3 and i.startswith('@'):
                i = i[1:]
                p = i.split(';')
                if len(p) > 1:
                    v = int(p[1].strip())
                p = p[0].strip()
                phrases[p] = v
                
            index += 1
            pass

        x = {
            'item': name,
            'location': num,
            'phrases': phrases
        }
        return x

    def entry_moves(self, file):
        for i in self.moves:
            file.write('<category>\n<pattern>' + i.upper() + '</pattern>\n')
            file.write('<template>\n')
            
            for ii in self.rooms:
                num = '000' + str(ii['number'])
                num = num[-2:]
                file.write('<condition name="topic" value="ROOM'+ num +'">\n')
                if i in ii['phrases'].keys():
                    z = ii['phrases'][i]
                    numx = '000' + str(z)
                    numx = numx[-2:]
                    file.write('''<think><set name="move">TRUE</set></think>\n''')
                    file.write('''<srai> ''' + self.confuse_text + ''' INTERNALLOOK ROOM''' + numx + '''</srai>
                                <think><set name="move">FALSE</set></think>\n ''')
                    pass
                else:
                    file.write('''<think><set name="move">TRUE</set></think>
                        <srai>INTERNALREJECT</srai>''')

                    
                file.write('</condition>\n')

            for ii in self.rooms:
                num = '000' + str(ii['number'])
                num = num[-2:]
                file.write('<condition name="topic" value="ROOM'+ num +'">\n')
                if i in ii['phrases'].keys():
                    z = ii['phrases'][i]
                    numx = '000' + str(z)
                    numx = numx[-2:]
                    file.write('''<think><set name="topic">ROOM''' + numx + '''</set></think>\n''')
                    
                    
                file.write('</condition>\n')
            file.write('</template>\n')
            file.write('</category>\n\n')

        file.write('''<category>
            <pattern>
            INTERNALREJECT
            </pattern>
            <template>
                <condition name="move" value="TRUE">
                You cannot do that here.
                <think><set name="move">FALSE</set></think>
                </condition>
            </template>
            </category>\n\n''')
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

        for j in self.items:
            location = '000' + str(j['location'])
            location = location[-2:]
            file.write('''
            <think><set name="''' + j['item'].upper() + '''">ROOM''' + location + '''</set></think>\n''')

        file.write('''
            <srai>''' + self.confuse_text + ''' INTERNALLOOK <get name="topic" /></srai>
            </template>
            </category>\n''')
        pass

    def reused_seen(self, file, num, val='UNSEEN'):
        num = '000' + str(num)
        num = num[-2:]
        file.write('''
            <think><set name="seen''' + num + '''">''' + val + '''</set></think>\n''')
        pass

    def direction_statements(self, file):
        for i in range(len(self.rooms)):
            num = self.rooms[i]['number']
            numx = '000' + str(num)
            numx = numx[-2:]
            file.write('<!-- ROOM' + str(numx) + ' -->\n')
            
            self.internal_look(file, num)
        pass

    def internal_look(self, file, num):
        numx = '000' + str(num)
        numx = numx[-2:]
        long = self.rooms[num]['description']
        short = self.rooms[num]['title']
        file.write('''        <category>
        <pattern>''' + self.confuse_text + ''' INTERNALLOOK ROOM''' + numx + '''</pattern>
            <template>
                <condition name="seen''' + numx + '''" value="UNSEEN">
                    ''' + long + '''
                </condition>

                <condition name="seen''' + numx + '''" value="SEEN">
                    ''' + short + '''
                </condition>
                <srai> INTERNALLISTROOM''' + numx + '''</srai>

                <think><set name="seen''' + numx + '''">SEEN</set></think>
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
                <think><set name="seen''' + numx + '''">UNSEEN</set></think>
            </condition>\n''')
        file.write('''            <srai>''' + self.confuse_text + ''' INTERNALLOOK <get name="topic" /></srai>
            </template>
            </category>\n''')
        pass

    def item_statements(self, file):
        ## get
        file.write('\n<!-- get and drop -->\n\n')

        for i in self.items:
            file.write('<category><pattern>\n')
            file.write('GET ' + i['item'].upper() +'\n')
            file.write('</pattern>\n')
            file.write('<template>\n')
            file.write('GET ' + i['item'].upper() +'\n')
            file.write('<srai>' +self.confuse_text + ' INTERNALGET' + i['item'].upper() + ' <get name="topic" /></srai>\n')
            file.write('</template>\n')
            file.write('</category>\n\n')

            for j in self.rooms:
                numj = j['number']
                numj = '00' + str(numj)
                numj = numj[-2:]
                file.write('<category><pattern>\n')
                file.write(self.confuse_text + ' INTERNALGET' + i['item'].upper() + ' ROOM' + numj + '\n')
                file.write('</pattern>\n')
                file.write('<template>\n')
                file.write('<condition name="'+ i['item'].upper() +'" value="ROOM' + numj + '" >')
                file.write('<think><set name="' + i['item'].upper() + '">ROOM-1</set></think></condition>\n')
                file.write('</template>\n')
                file.write('</category>\n\n')
                pass

        ## drop
        for i in self.items:
            file.write('\n<category><pattern>\n')
            file.write('DROP ' + i['item'].upper() +'\n')
            file.write('</pattern>\n')
            file.write('<template>\n')
            file.write('DROP ' + i['item'].upper() +'\n')
            file.write('<condition name="'+ i['item'].upper() +'" value="ROOM-1" >')
            file.write('<think><set name="' + i['item'].upper() + '"><get name="topic" /></set></think></condition>\n')
            file.write('</template>\n')
            file.write('</category>\n')

        pass

    def item_list(self, file):
        file.write('\n<!-- list items in room -->\n\n')

        for ii in self.rooms:
            numi = '00' + str(ii['number'])
            numi = numi[-2:]
            file.write('\n<category><pattern>\n')
            file.write('INTERNALLISTROOM' + numi)
            file.write('</pattern>\n')
            file.write('<template>\n')
            for i in self.items:
                file.write('<condition name="'+ i['item'].upper() +'" value="ROOM' + numi + '" >')
                file.write(i['item'].upper() + '</condition>\n')
            file.write('</template>\n')
            file.write('</category>\n')
            pass

if __name__ == '__main__':
    m = Maze()
    m.read_files()
    print(m.rooms)
    m.write_xml()
