#!/usr/bin/env python3

from os import write
from re import S
import xml.etree.ElementTree as ET
import glob
import math
import hashlib

class Maze:

    def __init__(self):
        self.rooms = []
        self.items = []
        self.revisions = []

        self.name = 'room*.maze'
        self.dir = './../maze/'
        self.entry_pattern = 'maze'
        self.entry_room_num = 5
        self.out_aiml = 'generated.aiml'
        self.item_name = 'thing*.item'
        
        self.hide_words = True

        m = hashlib.sha256()
        m.update(b"XYZABCCONFUSEME")
        self.confuse_text = m.hexdigest()[:15].upper() 

        self.local_moves_simple_out = []
        self.local_moves_combined = []

        self.raw_moves = [
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

    def hide_word_list(self):

        if self.hide_words:
            self.moves = [ x for x in self.raw_moves]
            l = []
            for x in self.moves:
                m = hashlib.sha256()
                m.update(x.encode('utf8'))
                y = m.hexdigest()
                l.append(y)
            
            self.moves = l
            #print(self.moves)
        else:
            self.moves = [x for x in self.raw_moves]

    def add_raw_moves(self, moves):
        if type(moves) is str:
            moves = moves.strip().lower()
            if moves not in self.raw_moves and moves != 'noop':
                self.raw_moves.append(moves)
        if type(moves) is list:
            for i in moves:
                ii = i[1].strip().lower()
                if ii not in self.raw_moves and ii != 'noop':
                    self.raw_moves.append(ii)
        if type(moves) is dict:
            for key in moves:
                ii = key.strip().lower()
                if ii not in self.raw_moves and ii != 'noop':
                    self.raw_moves.append(ii)
        #print(self.raw_moves)
            

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
        
        for i in range(0, len(g)):
            room_txt = g[i]
            if room_txt == self.dir + 'room00.maze':
                room_txt = ''
            x, y = self.room_factory(room=room_txt)
            self.rooms.append(x)
            #if i != g[0]:
            self.revisions.append(y)
        
        g = glob.glob(self.dir + self.item_name)
        g.sort()
        for i in g:
            self.items.append(self.item_factory(item_file=i))
        #print(self.items)
        #print(self.revisions)
        pass

    def write_xml(self):
        w = open(self.dir + self.out_aiml, 'w')
        w.write('<aiml version="1.0.1" encoding="UTF-8">\n')
        self.entry_category(w)
        #self.entry_moves(w)
        self.direction_statements(w)
        self.internal_reject(w)
        self.simple_look(w)

        self.make_global_list()

        self.revision_list(w)
        self.item_statements(w)
        self.item_list(w)
        self.reject_list(w)
        w.write('</aiml>\n')
        pass
    
    def room_factory(self, room=''):
        flag_skip_output = False
        if len(room) == 0: 
            flag_skip_output = True
            zz = ''
        else:
            z = open(room, 'r')
            zz = z.readlines()
            zz = [x for x in zz if not x.startswith('#')]
            zz = self.strip_comments(zz)
            zz = ''.join( zz)
            z.close()
            if len(zz.strip()) == 0:
                flag_skip_output = True
                zz = ''

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
        revision = '0'
        moves = []
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
            elif num > 4 + zzz and i == "*":
                remember = num
                state = "revision"
            elif num > 4 + zzz and i == "@":
                remember = num
                state = "phrase"
            elif num > 4 + zzz and i == ";":
                state = "number"
            elif num > 4 + zzz and i not in "@;*":
                if remember != num: continue
                if state == "phrase":
                    phrase += str(i)
                if state == "number" and i != ' ':
                    destination += str(i)
                if state == "revision" and i != ' ':
                    revision += str(i) ## this is the room num location for the revision
                if i == '\n':
                    if revision.strip() == '0'  and len(phrase.strip()) > 0:
                        phrases[str(phrase).strip().lower()] = int(destination.strip())
                        phrase = ''
                        destination = '0'
                    elif revision.strip() != '0' and len(phrase.strip()) > 0:
                        moves.append( [int(revision), str(phrase).strip().lower(), int(destination.strip())])
                        #print(revision, phrase, destination,'<<', sep='-')

                        revision = '0'
                        phrase = ''
                        destination = '0'
                        pass
                pass  
            if i == '\n':
                num += 1
        
        #print(moves)
        
        if flag_skip_output: # len(zz) == 0:
            x = {
                'number': 0, #int(number.strip()),
                'title': '',
                'description': '',
                'destination': '',
                'phrases': {}
            }

            
            y = {
                'number': 0, # int(number.strip()),
                'moves': [],
                'active':  False 
            }
            return x, y

        destination = 0
        number = number.split()
        if len(number) > 1:
            destination = int(number[1])
            number = str(number[0])
        else:
            number = str(number[0])
            destination = str(number[0])

        x = {
            'number': int(number.strip()),
            'title': title,
            'description': description,
            'destination': destination,
            'phrases': phrases
        }
        
        if revision.strip() != '' :
            y = {
                'number': int(number.strip()),
                'moves': moves,
                'active': True if len(moves) > 0 else False 
            }
        else:
            y = {}

        self.add_raw_moves(moves)
        self.add_raw_moves(phrases)
        return x, y

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
        for i in self.raw_moves:
            file.write('<category>\n<pattern>' + i.upper() + '</pattern>\n')
            file.write('<template>\n')
            
            for ii in self.rooms:
                num = '000' + str(ii['number'])
                num = num[-2:]
                file.write('<condition name="topic" value="ROOM'+ num +'">\n')
                if i in ii['phrases'].keys() :
                    z = ii['phrases'][i]
                    #print(i,z, '<<')
                    numx = '000' + str(z)
                    numx = numx[-2:]
                    file.write('''<think><set name="move">TRUE</set></think>\n''')
                    file.write('''<srai> ''' + self.confuse_text + ''' INTERNALLOOK ROOM''' + numx + '''</srai>
                                <think><set name="move">FALSE</set></think>\n ''')
                    pass
                else:
                    file.write('''<think><set name="move">TRUE</set></think>
                        <srai>INTERNALREJECT ''' + self.confuse_text + '''</srai>''')

                    
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

    def internal_reject(self, file):
        file.write('''<category>
            <pattern>
            INTERNALREJECT ''' + self.confuse_text + '''
            </pattern>
            <template>
                <!-- condition name="move" value="TRUE" -->
                You cannot do that here.
                <think><set name="move">FALSE</set></think>
                <!-- /condition -->
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
        for i in range( len(self.rooms)):
            self.reused_seen(file, self.rooms[i]['number'])
            self.reused_revision(file, self.revisions[i]['number'], 'FALSE' if i != 0 else 'TRUE')

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

    def reused_revision(self, file, num, val='FALSE'):
        #num = '000' + str(num)
        #num = num[-2:]
        num = str(num)
        file.write('''
            <think><set name="revision''' + num + '''">''' + val + '''</set></think>\n''')
        pass

    def direction_statements(self, file):
        for i in range(len(self.rooms)):
            num = self.rooms[i]['number']
            numx = '000' + str(num)
            numx = numx[-2:]
            file.write('<!-- ROOM' + str(numx) + ' -->\n')
            
            self.internal_look(file, num)
        pass

    def internal_look(self, file, num): ### keep this 
        numx = '000' + str(num)
        numx = numx[-2:]
        long = self.rooms[num]['description']
        short = self.rooms[num]['title']
        dest = self.rooms[num]['destination']
        numy = '000' + str(dest)
        numy = numy[-2:]
        file.write('''        <category>
        <pattern>''' + self.confuse_text + ''' INTERNALLOOK ROOM''' + numx + '''</pattern>
            <template>
                <!-- ''' + short + ''' -->
                
                <condition name="seen''' + numx + '''" value="UNSEEN">
                    ''' + long + '''
                </condition>

                <condition name="seen''' + numx + '''" value="SEEN">
                    ''' + short + '''
                </condition >
                <srai> INTERNALLISTROOM''' + numx + '''</srai>

                <think><set name="seen''' + numx + '''">SEEN</set></think>
                <think><set name="topic">ROOM''' + numy + '''</set></think>
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

    def make_global_list(self):
        local_moves_simple = []
        local_moves_revisions = []
        local_moves_combined = []

        for y in range(len(self.rooms)):
            for k, v in self.rooms[y]['phrases'].items():
                if True: 
                    
                    g = int(self.rooms[int(v)]['destination'])
                    yy = int(self.rooms[int(y)]['number'])
                    z = 0
                    #print(g, 'g',v)
                    if len(self.revisions[y]['moves']) > 0 : 
                        r = self.rooms[y]['destination']
                    else:
                        r = y

                    if g != v:
                        z = y
                        pass
                    if [yy,k,v,z, r,0] not in local_moves_simple:
                        local_moves_simple.append([yy,k,v,z, r,0])
                    #print(local_moves_simple[-1], 'simple\n')
        
        inner_num = 1
        for zzz in self.revisions:
            
            for move in zzz['moves']:
                #inner = inner_num 
                r = int(self.rooms[inner_num -1 ]['destination']) 
                g = int(self.rooms[inner_num -1 ]['number'])
                inner = g

                if r == g:
                    if [move[0] ,move[1], move[2], inner, r,0] not in local_moves_revisions:
                        local_moves_revisions.append([move[0], move[1], move[2], inner, r, 0])
                    #print(local_moves_revisions[-1], 'last\n')

                if r != g:
                    a = move[0]
                    b = move[1]
                    c = move[2]
                    d = r
                    e = g
                    f = r
                    if [a, b, c, d, e, f] not in local_moves_revisions:
                        local_moves_revisions.append([a, b, c, d, e, f])
                        #print(local_moves_revisions[-1], 'last x\n')
                pass
            inner_num += 1

        ## move and rename lists ##
        local_moves_combined = []
        local_moves_simple_out = []
        local_moves_revisions_out = []
        
        local_moves_simple_out = local_moves_simple
        
        local_moves_combined += local_moves_simple_out 
        
        local_moves_revisions_out += local_moves_revisions 
        
        local_moves_combined += local_moves_revisions_out

        #print(local_moves_combined, 'combined')
        self.local_moves_combined = local_moves_combined
        self.local_moves_simple_out = local_moves_simple_out
        #################################
        pass

    def reject_list(self, file):
        nn = 0
        for ix in range(len(self.moves)): # self.moves:
            i = self.raw_moves[ix]
            ii = self.moves[ix]
            #print(ix, i, '<<')
            for j in self.rooms:
                
                num = '000' + str(j['number'])
                num = num[-2:]

                match = [
                    local for local in self.local_moves_combined 
                    if int(local[0]) == int(j['number']) and 
                    (local[1].upper().strip() == i.upper().strip())  
                ]

                if len(match) == 0 : #and False:

                    file.write('<category>\n<pattern>' + self.confuse_text + ''' INTERNALLOOK REVISION ROOM''' + num + ' ' + ii.upper() + '</pattern>\n')
                    file.write('<template>\n<think><set name="move">TRUE</set></think>\n<srai>\n')

                    file.write( 'INTERNALREJECT ' + self.confuse_text )
                    file.write('''<think><set name="move">FALSE</set></think>''')

                    file.write('</srai>\n</template></category>\n')
                    nn += 1
        pass

    def revision_list(self, file):
        nn = 0
        for ix in range(len(self.moves)): # self.moves:
            i = self.raw_moves[ix]
            ii = self.moves[ix]
            file.write('<category>\n<pattern>' + i.upper() + '</pattern>\n')
            file.write('<template>\n<!-- think><set name="move">TRUE</set></think -->\n<srai>\n')

            file.write( self.confuse_text + ''' INTERNALLOOK REVISION <get name="topic" /> ''' + ii.upper()+ ' ' )
            file.write('''<think><set name="move">FALSE</set></think>''')

            file.write('</srai>\n</template></category>\n')
            nn += 1
        #print(nn, "nn num")
        
        #################################
        xx = (len(self.revisions) -1 ) * (len(self.revisions) -1) -1
        b = len(format(xx,'b')) 
        b_old = len(self.revisions) 
        #print(b, xx, b_old)

        #################################
        
        n = 0             
        
        for local in self.local_moves_combined: 
            
            revision = str(local[3]) 
            flag_revision = False

            if local[3] != 0 and (local[4] == local[0] and local[3] == local[4]): 
                revision = str(local[3])
                #print(local, end=' -- ')
                #local[0] = local[3]
                #local[2] = local[3]
                #print(local)
                flag_revision = True

            numx = '000' + str(local[2] ) 
            numx = numx[-2:]
            numy = '000' + str(local[2] )
            numy = numy[-2:]
            numz = '000' + str(local[0] % b_old )
            numz = numz[-2:]

            numn = '000' + str(local[3] % b_old )
            numn = numn[-2:]

            z_input = self.confuse_text + ' INTERNALLOOK REVISION ROOM' + str(numz) + ' ' + self.convert_to_hash( local[1].upper().strip()) ## numz

            file.write('<category>\n<pattern>' + z_input + '</pattern>\n')
            file.write('<template>')
            
            if flag_revision:
                
                file.write('<think><set name="revision'+ revision +'">TRUE</set></think>\n')
                #file.write('revision' + revision + ' ')

            file.write('<srai>' + self.confuse_text + ' ' + self.convert_to_hash( local[1].upper().strip()) +  ' INTERNALHOP ROOM' + numx + '</srai>\n')
            
            file.write('</template>\n')
            file.write('</category>\n')

            ##########################

            file.write('<category>\n<pattern>' + self.confuse_text + ' ' + self.convert_to_hash( local[1].upper().strip()) +  ' INTERNALHOP ROOM' + numx + '</pattern>\n')
            file.write('<template>')

            file.write('<condition name="revision' + str(local[3]) + '" value="TRUE" >')
            file.write('<think><set name="topic">ROOM'  + numx + '</set></think>\n')

            file.write('<srai>' + self.confuse_text + ' INTERNALLOOK ROOM' + numx + '</srai>\n')    

            file.write('</condition>')
            
            file.write('</template>\n')
            file.write('</category>\n')

            ##########################

            n += 1
                        
                            
        print(n, 'n')

    def string_from_int(self, input, largest, starting_str='', const_for_slice=-1, reverse=False, set_symbol=1, mult_input=1):
        zz = ''
        xx = largest
        
        for i in range(0, len(format(xx, 'b'))):
            zz = zz + '0'
        
        i = int(input * mult_input)
        l = format(i, 'b')
        l = zz + l
        l = l[-len(zz):]
        if const_for_slice > -1:
            l = l[:const_for_slice] + str(set_symbol) + l[const_for_slice:]

        if reverse == True:
            #print(l, end=' ')
            l = l[::-1]
            #print(l)

        if l in ['00001','00100', '10000']: 
            #print(l)
            pass
            #exit()

        z = starting_str 
        
        for x in range(len(l)):
            j = l[x]
            if j == '0':
                z += ' ' + 'FALSE'
            if j == '1':
                z += ' ' + 'TRUE'
        return z, l
        
    def convert_to_hash(self, direction):
        for i in range(len(self.raw_moves)): # self.raw_moves:
            if direction.upper().strip() == self.raw_moves[i].upper().strip():
                return self.moves[i].strip().upper()
        return ''

    def test_condition(self, file):
        z = self.entry_pattern.upper()
        file.write('\n\n')
        file.write('<category>\n<pattern>' + z + '</pattern>\n')
        file.write('<template>\n')
        file.write('<think><set name="test">1</set></think>\n')

        file.write('<condition name="test" value="1"> here1 </condition>\n')
        file.write('<condition name="test" value="1"> here2 </condition>\n')
        
        file.write('</template>\n')
        file.write('</category>\n')


if __name__ == '__main__':
    m = Maze()
    m.read_files()
    #print(m.rooms)
    m.hide_word_list()
    m.write_xml()
    #print(str(m.revisions[0]))
    
    