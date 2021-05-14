#!/usr/bin/env python3

import aiml as aiml_std
from transformers import BertTokenizer, BertForNextSentencePrediction
import torch
import xml.etree.ElementTree as ET
import re
import os

class Kernel:

    def __init__(self):
        self.filename = 'name'
        self.verbose_response = True
        self.output = ""
        self.kernel = aiml_std.Kernel()
        self.tree = None
        self.root = None
        self.l = []
        self.score = []
        self.memory = {}
        self.index = -1
        self.incomplete = False
        self.depth_limit = 5
        self.depth = 0
        self.files = []

        name = [ 'bert-base-uncased', 'bert-large-uncased' ]
        index = 0
        self.tokenizer = BertTokenizer.from_pretrained(name[index])
        self.model = BertForNextSentencePrediction.from_pretrained(name[index])
        print(self.model.config)

    def verbose(self, isverbose):
        #print(isverbose)
        self.verbose_response = isverbose
        self.kernel.verbose(isverbose)

    def learn(self, file):
        self.filename = file
        if self.filename in self.files:
            return
        self.files.append(file)

        self.kernel.learn(file)
        self.l = []
        self.score = []
        self.tree = ET.parse(file)
        self.root = self.tree.getroot()
        num = 0
        for child in self.root.iter('category'):
            #pat = None
            #tem = None
            pat_dict = self.pattern_factory(child)
            pat_dict['index'] = num
            
            #print(pat_dict)

            self.l.append([None, None, pat_dict])

            num += 1
            pass
        if self.verbose_response:
            print(self.l)
            print(len(self.l), num)

    def respond(self, input):
        self.score = []
        self.index = -1
        self.incomplete = False

        tempout = '' #self.kernel.respond(input)
        ## checkout input and response ##
        self.output = tempout

        if len(tempout) > 0:
            return self.output
        ## compare all aiml input patttern ##
        num = 0
        for i in self.l:
            i[2]['star'] = None
            input_02 = self.mod_input(i[2], input)
            ii = i[2]['pattern']
            s = self.bert_compare(ii, input_02)
            print(s)
            self.score.append(s)
            if self.verbose_response: print(num, s)
            num += 1
        print('----')
        ## find highest entry ##
        high = 0
        #pat = ''
        num = 0
        index = -1
        for i in self.score:
            if i > high:
                high = i
                #pat = self.l[num][0]
                index = num
            num += 1
        ## update dictionary ##
        
        d = self.mod_respond_dict(self.l[index][2], input)
        self.l[index][2] = d
        z = self.mod_template_out(self.l[index][2], input)
        
        self.index = index
        self.output = z
        
        if self.incomplete == True:
            self.output = ''
        
        if len(self.output) > 0: self.depth = 0

        return self.output

    def bert_score(self):
        if self.index == -1:
            return 0
        return self.score[self.index]

    def bert_compare(self, prompt1, prompt2):
        if not isinstance(prompt1, str): prompt1 = str(prompt1)
        if not isinstance(prompt2, str): prompt2 = str(prompt2)
        encoding = self.tokenizer(prompt1, prompt2, return_tensors='pt')
        outputs = self.model(**encoding, next_sentence_label=torch.LongTensor([1]))
        logits = outputs.logits
        s = logits[0][0] #.item()
        return s

    def pattern_factory(self, category):
        pat = None
        tem = None
        set = None
        get = None
        z = None
        srai = None
        learn = None
        star_list = []
        start = ""
        end = ""
        tem_02 = ""
        pat_02 = ""
        original = ""
        for i in category:
            original = i.text

            if i.tag == 'pattern':
                pat = i.text
                original = ET.tostring(i)

                if '*' in pat:
                    x = pat.strip().split(' ')
                    for ii in range(len(x)):
                        y = x[ii]
                        if y == "*":
                            star_list.append(ii )
                #print(star_list,'<====')

                #pat = i.text 
                #print(pat, '<-- pat')
                set = i
                get = i
                start = pat.split(" ")[0]
                end = pat.split(" ")[-1]
                pat_02 = pat.strip()

            if i.tag == 'template':
                tem = i #.text
                tem_02 = i.text 
                    
                set = i.find('./set')
                get = i.find('./get')
                srai = i.find('./srai')
                learn = i.find('./learn')
                
                start = pat.split(" ")[0]
                end = pat.split(" ")[-1]
                print(learn, "<-- ")

        
        wo_start = False
        wo_end = False

        if (pat_02.startswith('_') or pat_02.startswith('*')) and ( pat_02.endswith('*')):
            wo_start_end = True # pat_txt
            pass
        else:
            wo_start_end = False # pat_txt

        if  pat_02.endswith('*'):
            wo_end = True
        else:
            wo_end = False

        if pat_02.startswith('_') or pat_02.startswith('*'):
            wo_start = True
        else:
            wo_start = False
        
        d = {
            'start': start,
            'end': end,
            'wo_start': wo_start,
            'wo_end': wo_end,
            'wo_start_end': wo_start_end,
            'pattern': pat, 
            'template': tem.text.strip(),
            'initial_template': tem, 
            'initial_srai' : srai,
            'initial_learn' : learn,
            'index': None,
            'set_exp': set,
            'get_exp': get,
            'tem_wo_start': wo_start, 
            'tem_wo_end': wo_end, 
            'star': None,
            'star_list': star_list,
            'original': original
        }

        return d


    def mod_input(self, d_list, input):
        d = d_list
        l = input.split(' ')
        z = d['star_list']
        if len(z) is 1:
            if d['wo_start']:
                d['start'] = l[0]
                l = l[1:]
            if d['wo_end']:
                d['end'] = l[-1]
                l = l[:-1]
        else:
            if d['wo_start']:
                d['start'] = l[0]
                l = l[z[-1]:] # l[1:]
            if d['wo_end']:
                d['end'] = l[-1]
                l = l[:z[0]] # l[:-1]
            
        print(l)
        input = ' '.join(l)
        return input

    def mod_template_out(self, d_list, input):
        d = d_list
        #if input is None: input = d['template']
        l = input.split(' ')
        
        print(d, 'd')
        if d['initial_srai'] is not None:
            print(d['initial_srai'])
            self.depth += 1
            if self.depth < self.depth_limit:
                self.index = 0
                self.output = ''
                self.incomplete = False
                x = self.respond(d['initial_srai'].text)
                return x
            pass
        if d['initial_learn'] is not None:
            x = d['initial_learn'].text.strip()
            if not x.startswith('/'):
                cwd = os.getcwd() + '/'
                x = cwd + x
                if not os.path.isfile(x):
                    print('bad file specification')
                    return ''
            #print(x, '<<')
            self.learn(x)            
            return ''
            pass
        if d['wo_start']:
            d['start'] = l[0]
            d['star'] = l[0]
            return d['star'] + ' ' + d['template']
        if d['wo_end']:
            d['end'] = l[-1]
            d['star'] = l[-1]
            return d['template'] + ' ' + d['star']
        return d['template']
        
    def mod_set(self, d):
        set = d['set_exp']
        get = d['get_exp']
        tem = d['initial_template']
        sta = d['star']
        if set is not None and set.attrib['name']:
            if d['wo_end']:
                self.memory[set.attrib['name']] = d['end']
                
            if d['wo_start']:
                self.memory[set.attrib['name']] = d['start']
                
    def mod_respond_dict(self, d, input):
        set = d['set_exp']
        get = d['get_exp']
        tem = d['initial_template']
        sta = d['star']
        self.mod_set(d)
        
        tem_x = str(ET.tostring(tem)).replace('<template>', '', -1).replace('</template>', '', -1)
        tem_x = tem_x.replace("b'", '').replace("'","")
        
        tem_x = tem_x.replace('\\n', '')

        tem_x = str(re.sub(' +', ' ', tem_x).strip())
        tem_x = str(' '.join(tem_x.split()))
        tem_x = re.sub('^\s+', 'z', tem_x)
        tem_x = re.sub('\s+$', 'z', tem_x)
        
        #print(tem_x, '= x')

        d['tem_wo_start'] = tem_x.startswith("<") or tem_x.startswith('_') or tem_x.startswith('*')
        d['tem_wo_end'] = tem_x.endswith("*") or tem_x.endswith(">")
        #print(z, self.memory)
        if get is not None:
            #d['tem_wo_end'] = True
            t = ''
            if get.attrib['name'] in self.memory:
                t = self.memory[get.attrib['name']]
                if t is  None or t == '':
                    self.incomplete = True
                    
                    d['template'] = ''
                    return d #['template']
            #print(t,'===', ET.tostring(get))
            star = tem.find('get') ## <---
            tt = ''
            if star is not None:
                #tem.remove(star)
                pass
            if d['tem_wo_end']:
                tt = tem.text.strip() + ' ' + t
            elif d['tem_wo_start']:
                tt = t + ' ' + tem.text.strip()
            
            d['template'] = tt #tem
            #print(d, 'd')
            return d #['template']

        return d

    ## NOT USED ##
    def mod_respond_star(self, d):
        set = d['set_exp']
        get = d['get_exp']
        tem = d['initial_template']
        star_list = d['star_list']
        print(star_list,'----')
        if star_list is not None and len(star_list) > 0:
            t = star_list[0]
            x = tem.text.strip().split(' ')
            if t <= len(x):
                x = x[t]
            t = x[0]
            print(t,'===') 
            
            tt = ''
            
            if d['tem_wo_end']:
                tt = tem.text.strip() + ' ' + t
            if d['tem_wo_start']:
                tt = t + ' ' + tem.text.strip()
            if t == '':
                tt = ''
            
            d['template'] = tt 

        return d 


if __name__ == '__main__':

    k = Kernel()
    k.verbose(False)
    k.learn('../aiml/startup.xml')
    while True:
        y = input("> ")
        #k.respond(y)
        x = k.kernel.respond(y)
        x = ''
        if len(x.strip()) == 0 and not k.verbose_response: 
            r = k.respond(y) 
            print(r)
        else:
            print(x)