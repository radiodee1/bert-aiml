#!/usr/bin/env python3

import aiml as aiml_std
from transformers import BertTokenizer, BertForNextSentencePrediction
import torch
import xml.etree.ElementTree as ET
import re
import os
import string

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
        self.input = None
        self.target = []
        self.answers = []
        self.answers_length = 5

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
            
            self.l.append( pat_dict)

            num += 1
            pass
        if self.verbose_response:
            print(self.l)
            print(len(self.l), num)

    def respond(self, input):
        self.score = []
        self.index = -1
        self.incomplete = False
        self.input = input

        batch_pattern = []
        batch_input = []
        self.target = []

        tempout = '' 
        ## checkout input and response ##
        self.output = tempout

        if len(tempout) > 0:
            return self.output
        ## compare all aiml input patttern ##
        num = 0
        for i in self.l:
            i['star'] = None
            input_02, d = self.mod_input(i, input)
            self.l[num] = d
            ii = i['pattern']
            #s = self.bert_compare(ii, input_02)
            #print(ii, num)
            if i['initial_that'] is not None and len(i['initial_that']) > 0:
                ii += ' ' + i['initial_that']
            print(ii, num)
            ## batches start
            batch_pattern.append(ii)
            batch_input.append(input_02)
            self.target.append(1)
            ## batches end
            num += 1

        s = self.bert_batch_compare(batch_pattern, batch_input)
        self.score = s

        ## find highest entry ##
        high = 0
        num = 0
        index = -1
        for i in self.score:
            i = i[0] - i[1]
            i = self.mod_that(self.l[num], input, i)
            print(i)
            if i > high:
                high = i
                index = num
            num += 1
        ## update dictionary ##
        
        d = self.mod_respond_dict(self.l[index], input)
        self.l[index] = d
        z = self.mod_template_out(self.l[index], input)
        
        self.index = index
        self.output = z
        
        if self.incomplete == True:
            self.output = ''
        
        if len(self.output) > 0: self.depth = 0

        if self.output not in self.answers:
            out = self.output
            out = out.translate(str.maketrans('','', string.punctuation))
            self.answers.append(out.upper().strip())

        self.answers = self.answers[- self.answers_length:] ## last few
        print(self.answers)

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
        print(logits)
        s = logits[0][0] - logits[0][1] #.item()
        return s

    
    def bert_batch_compare(self, prompt1, prompt2):
        
        encoding = self.tokenizer(prompt1, prompt2, return_tensors='pt', padding=True, truncation=True, add_special_tokens=True)
        #print(encoding)
        target = torch.LongTensor(self.target)
        
        #print(target)
        outputs = self.model(**encoding, next_sentence_label=target)
        logits = outputs.logits
        #print(logits, '< logits')
        s = logits 
        return s
    

    def pattern_factory(self, category):
        pat = None
        tem = None
        set = None
        get = None
        z = None
        srai = None
        learn = None
        that = None
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
                pat = ' '.join(pat.split(' ')).strip()
                original = ET.tostring(i)

                if '*' in pat:
                    x = pat.strip().split(' ')
                    for ii in range(len(x)):
                        y = x[ii]
                        if y == "*":
                            star_list.append(ii + 1 )
                #print(star_list,'<====')

                #pat = i.text 
                #print(pat, '<-- pat')
                set = i
                get = i
                start = pat.split(" ")[0]
                end = pat.split(" ")[-1]
                pat_02 = pat.strip()

            if i.tag == 'template':
                tem = i 
                tem_02 = i.text 
                    
                set = i.find('./set')
                get = i.find('./get')
                srai = i.find('./srai')
                learn = i.find('./learn')
                #that = i.find('./that')
                
                start = pat.split(" ")[0]
                end = pat.split(" ")[-1]
                #print(learn, "<-- ")
            if i.tag == "that":
                that = i.text
        
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
            'template_modified': '',
            'initial_template': tem, 
            'initial_srai' : srai,
            'initial_learn' : learn,
            'initial_that': that,
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

    def mod_that(self, d_list, input, score):
        d = d_list
        
        if d['initial_that'] is not None and len(d['initial_that']) > 0:
            out = d['initial_that']
            out = out.translate(str.maketrans('','', string.punctuation))
            if out.upper().strip() not in self.answers:
                score = 0
        z = score
        #print(d, z, 'd,z')
        return z

    def mod_input(self, d_list, input):
        d = d_list
        l = str(re.sub(' +', ' ', input).strip())
        #l = l.strip().split(' ')
        #l = ' '.join(l)
        l = l.split(' ')
        #print(l)
        z = d['star_list']
        if len(z) is 1:
            if d['wo_start']:
                d['start'] = l[0]
                l = l[1:]
            if d['wo_end']:
                d['end'] = l[-1]
                l = l[:-1]
        elif len(z) > 1:
            if d['wo_start']:
                d['start'] = l[0]
                l = l[z[-1]:] # l[1:]
            if d['wo_end']:
                d['end'] = l[-1]
                l = l[:z[0]] # l[:-1]
            
        #print(l)
        input = ' '.join(l)
        #print(input)
        return input, d

    def mod_template_out(self, d_list, input):
        d = d_list
        #if input is None: input = d['template']
        l = input.split(' ')
        
        #print(d, 'd')
        if d['initial_template'] is not None:
            d['template_modified'] = ''
            xx = self.consume_template(d['initial_template'], d)
            xx = ' '.join(xx.split(' '))
            xx = str(re.sub(' +', ' ', xx).strip())
            d['template'] = xx
            #print(xx, ': d-template')
            return xx
        
        return ''

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
        tem_x = str(' '.join(tem_x.split(' ')))
        tem_x = re.sub('^\s+', 'z', tem_x)
        tem_x = re.sub('\s+$', 'z', tem_x)
        
        #print(tem_x, '= x')

        d['tem_wo_start'] = tem_x.startswith("<") or tem_x.startswith('_') or tem_x.startswith('*')
        d['tem_wo_end'] = tem_x.endswith("*") or tem_x.endswith(">")
        #print(z, self.memory)
        if get is not None:
            #d['tem_wo_end'] = True
            t = ''
            if get.attrib['name'] in self.memory.keys(): # and self.memory.has_key(get.attrib['name']):
                t = self.memory[get.attrib['name']]
                if t is  None or t == '':
                    self.incomplete = True
                    
                    d['template'] = ''
                    return d #['template']
            #### 
            tt = ''
            
            if d['tem_wo_end']:
                tt = tem.text.strip() + ' ' + t
            elif d['tem_wo_start']:
                tt = t + ' ' + tem.text.strip()
            
            d['template'] = tt #tem
            #print(d, 'd')
            return d #['template']

        return d

    ## Start consume functions ##

    def consume_template(self, element, d):
        print('template :', element.text, element.tag, element.attrib)
        if element.text is not None:
            t = element.text.strip()
            d['template_modified'] += t
        
        for x in element:
            print(x.attrib)
            print(x.tag)
            print(x.text)
            print('---')
            if x.tag == "srai" :
                d['template_modified'] = ''
                z = self.consume_srai(x, d)
                if z is not None and len(z) > 0:
                    d['template_modified'] = z ## replace, not concatenate!
                    print(self.depth, "< depth")
                    self.depth += 1
                    if self.depth < self.depth_limit:
                        self.index = 0
                        self.output = ''
                        self.incomplete = False
                        x = self.respond(d['template_modified'])
                        return x 

            if x.tag == "learn" : self.consume_learn(x, d)
            if x.tag == "get" : 
                z = self.consume_get(x, d)
                d['template_modified'] += " " + z
            if x.tag == "set" : 
                z = self.consume_set(x, d)
                if z is not None:
                    d['template_modified'] += " " + z
            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)
                if z is not None:
                    d['template_modified'] += " " + z

        if len(element) > 0 and element[0].tail is not None:
            print(element[0].tail, '<< tail')
            t = element[0].tail
            t = t.strip()
            d['template_modified'] += ' ' + t

        return d['template_modified']

    def consume_srai(self, element, d):
        print('srai :', element.text, element.tag, element.attrib)
        d['template_modified'] = ''
        if element.text is not None:
            d['template_modified'] += ' ' + element.text
        
        for x in element:
            print(x.attrib)
            print(x.tag)
            print(x.text)
            print('---')

            if x.tag == "get" : 
                z = self.consume_get(x, d)
                d['template_modified'] += " " + z
            if x.tag == "set" : 
                z = self.consume_set(x, d)
                if z is not None:
                    d['template_modified'] += " " + z
            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)
                if z is not None:
                    d['template_modified'] += " " + z
        
        print('srai internal :', d['template_modified'])

        if element[0].tail is not None:
            print(element[0].tail, '<< tail')
            d['template_modified'] += ' ' + element[0].tail

        return d['template_modified']

    def consume_set(self, element, d):
        print('set :', element.text, element.tag, element.attrib)
        if element.text is not None:
            d['template_modified'] += element.text
        
        z = element.text

        for x in element:
            
            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)

        if 'name' in element.attrib:
            self.memory[element.attrib['name']] = z

        print(self.memory, "<<< memory set")
        return z

    def consume_learn(self, element, d):
        print('set :', element.text, element.tag, element.attrib)
        if element.text is not None:
            d['template_modified'] += element.text
        
        #x = element.text

        #d['initial_learn'] = x.strip()
        x = d['initial_learn'].text.strip()
        if not x.startswith('/'):
            cwd = os.getcwd() + '/'
            x = cwd + x
            if not os.path.isfile(x):
                print(x, ': bad file specification')
                return ''
        #print(x, '<<')
        self.learn(x)            
        return ''

    def consume_get(self, element, d):
        print('get :', element.text, element.tag, element.attrib)
        if element.text is not None:
            d['template_modified'] += element.text
        for xx in element.attrib:
            print(xx)

        if 'name' in element.attrib.keys() and element.attrib['name'] in self.memory.keys():
            print(self.memory, '<< memory get')
            y = self.memory[element.attrib['name']]
            print(y)
            return y

        z = ''
        for x in element:
            print(x.attrib)
            print(x.tag)
            print(x.text)
            print('---')
            
            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)
        return z

    def consume_star_tag(self, element, d):
        print('star :', element.text, element.tag, element.attrib)
        #if element.text is not None:
            #d['template_modified'] += ' ' + element.text
            #pass
        s = d['star_list']
        z = element.attrib
        p = self.input.strip()
        p = ' '.join(p.split(' '))
        r = ''
        print(z,'< before')
        if 'index' in z:
            x = int(z['index']) - 1
        else: x = 0
        print(x, '< x')
        if len(s) > 0:
            if x <= len(s) : x = int(s[x]) -1
            z = p.split(' ')
            if x < len(z): 
                r = z[x]
        print(s, r,'< after ')
        print('---')
        
        return r

    
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