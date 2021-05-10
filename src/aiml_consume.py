#!/usr/bin/env python3

import aiml as aiml_std
from transformers import BertTokenizer, BertForNextSentencePrediction
import torch
import xml.etree.ElementTree as ET
import re

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
        ## find highest entry ##
        high = 0
        pat = ''
        num = 0
        index = -1
        for i in self.score:
            if i > high:
                high = i
                pat = self.l[num][0]
                index = num
            num += 1
        ## update dictionary ##
        #print(self.l[index][2])
        z = self.mod_dict_out(self.l[index][2], input)
        
        print(z, '<<')

        #print(self.score[index].item(), index)
        #print(self.memory,'<<')
        self.index = index

        if z is  None  and len(self.output) is 0 and index is not -1 and self.score[index].item() > 5.0:
            if self.verbose_response: print(input,'--' ,index, '-- print template --', self.l[index][2]['template'])
            self.output = self.l[index][2]['template']
            #print (ET.tostring(self.output), "???")
            self.output = self.output.strip()
        elif z is not None :
            self.output = z

        if self.incomplete == True:
            self.output = ''
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
                    
                    pat = i.text 
                    #print(pat, '<-- pat')
                    set = i
                    get = i
                    start = pat.split(" ")[0]
                    end = pat.split(" ")[-1]
                    pat_02 = pat

            if i.tag == 'template':
                tem = i.text
                tem_02 = i.text 
                    
                set = i.find('./set')
                get = i.find('./get')
                #z = True
                #print(set, get)
                pass
                #print(tem_02, "<-- tem")

            
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

        #pat_02 = ET.XML(pat).text
        if pat_02 is not None:
            pat_02 = pat_02.strip()

        d = {
            'start': start,
            'end': end,
            'wo_start': wo_start,
            'wo_end': wo_end,
            'wo_start_end': wo_start_end,
            'pattern': pat, 
            'template': tem.strip(),
            'initial_template': tem.strip(),
            'index': None,
            'set_exp': set,
            'get_exp': get,
            'tem_wo_start':tem_02.startswith('<') or tem_02.startswith('*') or tem_02.startswith("_") ,
            'tem_wo_end':tem_02.endswith('>') or tem_02.endswith("*") ,
            'star': None,
            'original': original
        }

        if i.tag == "template": self.mod_get_set(d)
        return d


    def mod_input(self, d_list, input):
        d = d_list
        l = input.split(' ')
        if d['wo_start']:
            l = l[1:]

        if d['wo_end']:
            l = l[:-1]
            #print (l)
            #exit()

        input = ' '.join(l)
        return input

    def mod_dict_out(self, d_list, input):
        d = d_list
        l = input.split(' ')
        if d['wo_start']:
            d['start'] = l[0]
            d['star'] = l[0]
            return d['star'] + ' ' + d['template']
        if d['wo_end']:
            d['end'] = l[-1]
            d['star'] = l[-1]
            return d['template'] + ' ' + d['star']
        #self.mod_get_set(d)
        

    def mod_get_set(self, d):
        set = d['set_exp']
        get = d['get_exp']
        tem = d['initial_template']
        sta = d['star']
        if set is not None and set.attrib['name']:
            if d['wo_end']:
                self.memory[set.attrib['name']] = d['end']
                
            if d['wo_start']:
                self.memory[set.attrib['name']] = d['start']
                
        elif get is not None:
            t = ''
            if get.attrib['name'] in self.memory:
                t = self.memory[get.attrib['name']]
                if t is  None or t == '':
                    self.incomplete = True
                    n = ET.Element('template')
                    n.text = ''
                    d['template'] = '' #n #ET.Element('template')
                    return
            #print(t,'===', ET.tostring(get))
            star = tem.find('get') ## <---
            tt = ''
            if star is not None:
                #tem.remove(star)
                pass
            if d['tem_wo_end']:
                tt = tem.text.strip() + ' ' + t
            if d['tem_wo_start']:
                tt = t + ' ' + tem.text.strip()
            #d['template'] = tem.text
            n = ET.Element('template')
            n.text = tt
            tem = n
            #print('>>',ET.tostring(tem), t, self.memory)
            d['template'] = tt #tem
            #exit()
        if sta is not None:
            t = sta
            #print(t,'===') #, ET.tostring(get))
            #exit()
            star = tem.find('star')
            tt = ''
            if star is not None:
                tem.remove(star)
            if d['tem_wo_end']:
                tt = tem.text.strip() + ' ' + t
                #print(tt, 'end')
            if d['tem_wo_start']:
                tt = t + ' ' + tem.text.strip()
                #print(tt, 'start')
            #d['template'] = tem.text
            if t == '':
                tt = ''
            n = ET.Element('template')
            n.text = tt
            #tem = n
            #print('>>',ET.tostring(tem), t, self.memory)
            d['template'] = n


if __name__ == '__main__':

    k = Kernel()
    k.verbose(False)
    k.learn('../aiml/startup.xml')
    while True:
        y = input("> ")
        x = k.kernel.respond(y)
        x = ''
        if len(x.strip()) == 0 and not k.verbose_response: 
            r = k.respond(y) 
            print(r)
        else:
            print(x)