#!/usr/bin/env python3

#import aiml as aiml_std
from transformers import BertTokenizer, BertForNextSentencePrediction
import torch
import xml.etree.ElementTree as ET
import re
import os
import string
import random
from dotenv import load_dotenv
import math
import argparse


load_dotenv()

try:
    AIML_DIR=os.environ['AIML_DIR'] 
except:
    AIML_DIR=''

try:
    BATCH_SIZE=int(os.environ['BATCH_SIZE']) 
except:
    BATCH_SIZE = 32

try:
    WORD_FACTOR=int(os.environ['WORD_FACTOR']) 
except:
    WORD_FACTOR = -1

try:
    DOUBLE_COMPARE=int(os.environ['DOUBLE_COMPARE']) 
except:
    DOUBLE_COMPARE = 0

try:
    MAX_LENGTH=int(os.environ['MAX_LENGTH']) 
except:
    MAX_LENGTH = 16

try:
    CUDA=int(os.environ['CUDA']) 
except:
    CUDA = 0

try:
    BERT_MODEL=int(os.environ['BERT_MODEL'])
except:
    BERT_MODEL = 0

try:
    WEIGHT_TEMPLATE=float(os.environ['WEIGHT_TEMPLATE'])
except:
    WEIGHT_TEMPLATE= 1.0

try:
    WEIGHT_PATTERN=float(os.environ['WEIGHT_PATTERN'])
except:
    WEIGHT_PATTERN= 1.0

try:
    AIML_FILE=str(os.environ['AIML_FILE'])
except:
    AIML_FILE = ''

try:
    SRAI_LITERAL=int(os.environ['SRAI_LITERAL'])
except:
    SRAI_LITERAL = 1

class Kernel:

    def __init__(self):
        self.filename = 'name'
        self.verbose_response = True
        self.output = ""
        self.srai_list = []
        self.num = 0
        self.srai_completion = False
        #self.kernel = aiml_std.Kernel()
        self.tree = None
        self.root = None
        self.l = []
        self.z = []
        self.score = []
        self.memory = {}
        self.index = -1
        self.incomplete = False
        self.depth_limit = 10
        self.depth = 0
        self.files = []
        self.files_size = 0
        self.input = None
        self.used = []
        self.used_num = 0
        self.answers = []
        self.answers_length = 5
        self.time1 = None
        self.time2 = None
        self.args = None

        parser = argparse.ArgumentParser(description="Bert Aiml", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--raw-pattern', action='store_true', help='output all raw patterns.')
        parser.add_argument('--count', action='store_true', help='count number of responses.')
        self.args = parser.parse_args()

        name = [ 'bert-base-uncased', 'bert-large-uncased' ]
        index = BERT_MODEL
        self.tokenizer = BertTokenizer.from_pretrained(name[index])
        self.model = BertForNextSentencePrediction.from_pretrained(name[index])
        if CUDA == 1:
            self.model = self.model.to('cuda')
        #print(self.model.config)

    def verbose(self, isverbose):
        #print(isverbose)
        self.verbose_response = isverbose
        #self.kernel.verbose(isverbose)

    def learn(self, file):
        self.filename = file
        if self.filename in self.files:
            return
        self.files.append(file)

        #self.kernel.learn(file)
        #self.l = []
        #self.score = []
        tree = ET.parse(file)
        root = tree.getroot()
        self.files_size =  len(root)

        self.pattern_factory_topic(root)

    def respond(self, input):
        x = self.respond_bert(input)

        if x not in self.srai_list:
            self.srai_list.append(x)

        if len(self.srai_list) > 0:
            self.srai_list.reverse()
            x = ' '.join(self.srai_list)
            #print(self.srai_list,'x')
            
        if len(self.srai_list) == 1:
            self.srai_list = []
        self.output = x
        return self.output
        

    def respond_srai(self, input):
        self.l = []
        num = 0
        input = str(re.sub(' +', ' ', input).upper().strip())
        input = input.translate(str.maketrans('','', string.punctuation))

        for j in range(len(self.z)):
            self.l.append(self.z[j])
            i = self.z[j]
            ii = str(re.sub(' +', ' ', i['pattern']).upper().strip())
            ii = ii.translate(str.maketrans('','', string.punctuation))
            #print(ii)
            if input.strip().upper() == ii.strip().upper():
                num = j
                #print(i['template'],'found')
                #return i['template']

        return self.update_dictionary(num, input)

    def respond_bert(self, input):
        self.score = []
        self.index = -1
        self.incomplete = False
        self.input = str(re.sub(' +', ' ', input).upper().strip())
        self.input = self.input.translate(str.maketrans('','', string.punctuation))

        self.l = []
        word_factor = WORD_FACTOR
        i_length = len(input.strip().split(' '))
        #print(len(self.l), 'list')
        for j in range(len(self.z)):
            p = self.z[j]['pattern']
            p_len = len(p.strip().split(' '))
            if i_length >= p_len + word_factor and word_factor != -1:
                continue
            if i_length <= p_len - word_factor and word_factor != -1:
                continue
            self.l.append(self.z[j])
            pass

        #print(len(self.z), len(self.l), 'len')

        batch_pattern = []
        batch_input = []
        batch_template = []
        #self.target = []

        ## input pattern batch ##
        batch_size = BATCH_SIZE
        num = 0
        replacements = 0
        for ii in range(0, len(self.l) , batch_size):
            #print(ii, ii+batch_size)
            
            if ii + batch_size > len(self.l):
                batch_size = len(self.l) - ii
            #print(batch_size, '< bs')
            batch_pattern = []
            batch_template = []
            batch_input = []
            #self.target = []
            for j in range(ii, ii+batch_size):
                #print(j, end=',')

                i = self.l[j]
                i['star'] = None
                input_02, d = self.mod_input(i, input)
                #self.l[num] = d ## <-- ???
                ip = i['pattern']
                ip = str(re.sub('\*', '', ip).upper().strip())
                
                it = i['template']

                if DOUBLE_COMPARE >= 1:
                    if len(it.strip()) == 0 and i['initial_template'] is not None:
                        it = i['initial_template'].text 
                    if len(it.strip()) == 0 and i['initial_srai'] is not None:
                        it = i['initial_srai'].text 
                    if len(it.strip()) == 0 :
                        it = i['pattern']
                        replacements += 1
                        #print('empty input template', it, j)

                #print(it, num, 'it')
                if i['initial_that'] is not None and len(i['initial_that']) > 0:
                    ip += ' ' + i['initial_that']
                #print(ii, num)
                
                ## batches start
                if DOUBLE_COMPARE <  2: batch_pattern.append(ip)
                if DOUBLE_COMPARE >= 1: batch_template.append(it)
                batch_input.append(input_02)

                num += 1

            
            if DOUBLE_COMPARE < 2:
                s = self.bert_batch_compare(batch_pattern, batch_input)
                batch_pattern = None #[]
            if DOUBLE_COMPARE >= 1:
                si = self.bert_batch_compare(batch_input, batch_template)
                batch_template = None #[]
            batch_input = None #[]

            num_s = 0
            j = 0
            #print()
            batch_size = BATCH_SIZE
            if ii + batch_size > len(self.l):
                batch_size = len(self.l) - ii
            for j in range(ii, ii + batch_size):
                #print(j, num, end=',')
                score = []
                if DOUBLE_COMPARE < 2:
                    score.extend(s[num_s])
                    pass
                if DOUBLE_COMPARE >= 1:
                    score.extend(si[num_s])
                self.score.append( score ) # ((*s[num_s], *si[num_s]))
                #print(self.score[num_s], num_s, 'score')
                num_s += 1
            #print('< score')
        
        print(len(self.l) // BATCH_SIZE, 'batches') 
        if replacements > 0: print(replacements, 'replacements', len(self.l), 'total')   
        
        ## find highest entry ##
        high = 0
        num = 0
        index = -1
        for _ in self.score:
            i = self.score[num]
            #i = (i[0] - i[1])   
            if DOUBLE_COMPARE == 1:
                i = abs ((i[0] - i[1]) * WEIGHT_PATTERN + (i[2] - i[3]) * WEIGHT_TEMPLATE)
            else:
                i = abs (i[0] - i[1])
            i = self.mod_that(self.l[num], input, i)

            if i > high:
                high = i
                index = num
            num += 1
        return self.update_dictionary(index, input)
        
    def update_dictionary(self, index, input):
        ## update dictionary ##
        
        d = self.mod_respond_dict(self.l[index], input)
        
        z = self.mod_template_out(self.l[index], input) ## includes srai output
        
        self.index = index
        
        r = self.choose_output(self.l[index]) ## random
        if r == '' and z != '':
            self.output = z
        else:
            self.output = r

        pre_output = self.output.strip()
        
        if len(self.output) > 0: self.depth = 0

        self.output = str(re.sub(' +', ' ', self.output).upper().strip())
        self.output = self.output.translate(str.maketrans('','', string.punctuation))

        if self.output not in self.answers:
            self.answers.append(self.output.upper().strip())

        self.answers = self.answers[- self.answers_length:] ## last few
        #print(self.answers, '???')
        
        if self.args.count: self.count_output(self.output)

        self.output = pre_output
        
        m = [[self.l[x]['pattern'], self.score[x][0] - self.score[x][1]] for x in range(len(self.l))]
        #print(m[:15])
        def spec(x):
            return x[1]
        m.sort(reverse=True,key=spec)
        print(m[:15])

        return self.output

    def choose_output(self, d):
        if len(d['random_list']) > 0:
            return random.choice(d['random_list'])
        #elif True:
        #return d['template_modified'].strip()
        return ''

    def bert_batch_compare(self, prompt1, prompt2):
        encoding = self.tokenizer(prompt1, prompt2, return_tensors='pt', padding=True, truncation=True, add_special_tokens=True, max_length=MAX_LENGTH)
        #target = torch.LongTensor(self.target)
        target = torch.ones((1,len(prompt1)), dtype=torch.long)
        if CUDA == 1:
            encoding = encoding.to('cuda')
            target = target.to('cuda')

        outputs = self.model(**encoding, next_sentence_label=target)
        logits = outputs.logits.detach()
        #print(outputs, '< logits')
        return logits

    def pattern_factory_topic(self, root):
        num = 0
        for child in root:
            if child.tag == "topic":
                topic = ''
                if child.attrib['name'] is not None and len(child.attrib['name'].strip()) > 0:
                    topic = child.attrib['name'].upper().strip()
                
                for ch2 in child:
                    pat_dict = self.pattern_factory(ch2, topic)
                    pat_dict['index'] = num
                    
                    self.z.append(pat_dict)

                    num += 1
                    pass

            if child.tag == "category":
                pat_dict = self.pattern_factory(child)
                pat_dict['index'] = num
            
                self.z.append(pat_dict)

                num += 1
        pass
    
    def raw_pattern(self):
        print('raw patterns')
        t = open('output.txt', 'w')
        for i in self.z:
            if self.verbose_response: print(i['pattern'])
            t.write(i['pattern'] + '\n')
        t.close()
        pass

    def count_output(self, output):
        self.used_num += 1
        if output not in self.used:
            self.used.append(output)
        pass

    def pattern_factory(self, category, topic=None):
        pat = None
        tem = None
        set = None
        get = None
        z = None
        srai = None
        learn = None
        that = ''
        random = None
        condition = None
        random_list = []
        star_list = []
        that_star_list = []
        that_wo_start = None
        that_wo_end = None
        start = ""
        end = ""
        tem_02 = ""
        pat_02 = ""
        original = ""

        star_list_start = []
        star_list_end = []
        star_list_mem = {}

        for i in category:
            #original = i.text

            if i.tag == 'pattern':
                pat = i.text
                if pat is None: pat = ''
                pat = ' '.join(pat.split(' ')).strip()
                #original = ET.tostring(i)

                if '*' in pat:
                    x = pat.strip().split(' ')
                    for ii in range(len(x)):
                        y = x[ii]
                        if y == "*":
                            star_list.append(ii + 1 )
                
                set = i
                get = i
                start = pat.split(" ")[0]
                end = pat.split(" ")[-1]
                pat_02 = pat.strip()

            if i.tag == 'template':
                tem = i 
                if tem.text is None: tem.text = ''
                tem_02 = i.text 
                    
                set = i.find('./set')
                get = i.find('./get')
                srai = i.find('./srai')
                learn = i.find('./learn')
                random = i.find('./random')
                #that = i.find('./that')
                
                start = pat.split(" ")[0]
                end = pat.split(" ")[-1]
                #print(learn, "<-- ")

                if learn is not None: tem.text += learn.text

            if i.tag == "that":
                that = i.text
        
        wo_start = False
        wo_end = False
        ###################
        max_list_len = 2
        if pat_02.strip().endswith('*'):
            max_list_len = 1

        if "*" in pat_02:
            xx = pat_02.split(' ')
            #tem_02 = tem_02.split(' ')
            star_list_start = [ None for _ in range(min( len(xx) // 2 , max_list_len))]
            star_list_end = [ None for _ in range(min(len(xx) // 2, max_list_len))]

            for ii in range(len(star_list_start)):
                if xx[ii] == "*" : 
                    star_list_start[ii] = '*' 

            start_of_xx = len(xx) - len(star_list_end) 
            for ii in range(len(star_list_end)):
                if xx[start_of_xx + ii] == "*" : 
                    star_list_end[ ii] = '*' 
            
        ###################
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
        ###################
        if  that.endswith('*'):
            that_wo_end = True
        else:
            that_wo_end = False

        if that.startswith('_') or that.startswith('*'):
            that_wo_start = True
        else:
            that_wo_start = False
        ###################
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
            'that_wo_start': that_wo_start,
            'that_wo_end': that_wo_end,
            'star': None,
            'star_list': star_list,
            'star_list_start': star_list_start,
            'star_list_end': star_list_end,
            'star_list_mem': star_list_mem,
            'that_star_list': that_star_list,
            #'original': original,
            'topic': topic,
            'random': random,
            'random_list': random_list,
            'condition': condition,
            'encounter_think': False
        }

        if random is not None:
            self.mod_pattern_factory_random_tag(d['random'], d)
            #print(d)

        return d

    def mod_pattern_factory_random_tag(self, element, d_dict):
        d = d_dict
        d['random_list'] = []
        
        for x in element:
            if x.tag == "li" : 
                d['random_list'].append(x.text)
                
        return ''

    def mod_that(self, d_list, input, score):
        d = d_list
        d['that_star_list'] = []
        #print(d['that_star_list'],'< star list:', input)
        if d['initial_that'] is not None and len(d['initial_that']) > 0:
            out = d['initial_that']
            out = str(re.sub(' +', ' ', out).strip())

            if d['that_wo_end'] and len(out.split(' ')) > 0:
                d['that_star_list'].append(len(out.split(' ')) - 1)
                d['initial_that'] = d['initial_that'][:-1]
            if d['that_wo_start'] and len(out.split(' ')) > 0:
                d['that_star_list'].append(0)
                d['initial_that'] = d['initial_that'][1:]

            out = out.translate(str.maketrans('','', string.punctuation))
            if out.upper().strip() not in self.answers:
                score = 0
        if d['topic'] is not None and 'topic' in self.memory:
            if self.memory['topic'] != d['topic']:
                score = 0
        if d['topic'] is not None and len(d['topic']) > 0 and 'topic' not in self.memory:
            score = 0

        return score

    def mod_input(self, d_list, input):
        d = d_list
        l = str(re.sub(' +', ' ', input).strip())
        l = l.split(' ')
        d['star_list_mem'] = {}
        #print(l)
        ll = str(re.sub(' +', ' ',input).strip())
        ll = ll.split(' ')
        

        num = 0
        if len(d['star_list_start']) > 0 or len(d['star_list_end']) > 0 and len(d['star_list_start']) >= len(ll):
            

            for ii in range(len(d['star_list_start'])):
                if d['star_list_start'][ii] is not None and ii < len(ll):
                    d['star_list_mem'][num] = ll[ii]
                    ll.pop(ii)
                    num += 1
                    pass

            start_of_xx = len(ll) - len(d['star_list_end'])
            start_of_xx = max(start_of_xx, 0)
            for ii in range(len(d['star_list_end'])):
                if d['star_list_end'][ii] is not None and ii < len(ll):
                    d['star_list_mem'][num] = ll[start_of_xx + ii]
                    ll.pop(start_of_xx + ii)
                    num += 1
                pass
            
        input = ' '.join(ll)

        return input, d

    def mod_template_out(self, d_list, input):
        d = d_list
        #if input is None: input = d['template']
        l = input.split(' ')
        
        #print(d, 'd')
        if not self.srai_completion:
            d['template_modified'] = ''
            pass
        else:
            self.srai_list = []

        if d['initial_template'] is not None or True:
            d['template_modified'] = ''
            #print(d['initial_template'], 'nothing?')
            xx = self.consume_template(d['initial_template'], d)
            xx = ' '.join(xx.split(' '))
            xx = str(re.sub(' +', ' ', xx).strip())
            d['template'] = xx
            #print(xx, ': d-template')
            #d['srai_completion'] = False
            return xx

        #d['srai_completion'] = False
        return ''

    def mod_set(self, d):
        set = d['set_exp']
        

        if set is None: return
        t = ''
        for x in set:
            if x.tag == "star":
                if 'index' in x.attrib.keys() and int(x.attrib['index']) > 0:
                    t = d['star_list_mem'][int(x.attrib['index'])]
                else:
                    t = d['star_list_mem'][0]
                pass
            else:
                t = set.text.strip()

        self.memory[set.attrib['name'].upper()] = t


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
        t = ''
        if get is not None:
            
            #t = ''
            if get.attrib['name'].upper() in self.memory.keys(): 
                t = self.memory[get.attrib['name'].upper()]
                if t is  None or t == '':
                    self.incomplete = True
                    
                    d['template'] = ''
                    return d #['template']
        #### 
        if t is not None and t != '':
            tt = ''

            if d['tem_wo_end']:
                tt = tem.text.strip() + ' ' + t
            elif d['tem_wo_start']:
                tt = t + ' ' + tem.text.strip()
            
            d['template'] = tt #tem
            #print(d, 'd')
            return d 

        return d

    ## Start consume functions ##

    def consume_template(self, element, d):
        #print('template :', element.text, element.tag, element.attrib)
        r = ''
        l = []
        local_text = ''
        z = ''
        if element.text is not None:
            t = element.text.strip()
            #d['template_modified'] += t
            local_text += t
            #l.append(t)
        

        for x in element:
            
            if x.tag == "srai" :
                #d['template_modified'] = ''
                #d['srai_completion'] = True
                self.srai_completion = True
                #print('srai')
                z = self.consume_srai(x, d)
                if z is not None and len(z) > 0:
                    #d['template_modified'] =  z ## replace, not concatenate!
                    #print(z,'z')
                    self.depth += 1
                    if self.depth < self.depth_limit:
                        self.index = 0
                        self.output = ''
                        self.incomplete = False
                        #d['srai_completion'] = True
                        if SRAI_LITERAL == 1:
                            r = self.respond_srai(z) 
                            self.srai_list.append(r)
                            #d['template_modified'] = r
                        else:
                            r = self.respond_bert(z) 
                            self.srai_list.append(r)
                        #l.append(r)
                        #print(r, '<<<r')

            if x.tag == "learn" : 
                self.consume_learn(x, d)
                return ''
            if x.tag == "get" : 
                z = self.consume_get(x, d)
                #d['template_modified'] += " " + z
                local_text += ' ' + z
            if x.tag == "set" : 
                z = self.consume_set(x, d)
                if z is not None:
                    #d['template_modified'] += " " + z
                    local_text += ' ' + z

            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)
                if z is not None:
                    #d['template_modified'] += " " + z
                    local_text += ' ' + z

            if x.tag == "think":
                self.consume_think(x, d)
            if x.tag == "condition":
                z = self.consume_condition(x, d)
                if z is not None and len(z.strip()) > 0:
                    l.append(z)
                    #d['template_modified'] =z #+= ' ' + z
                    local_text += ' ' + z.strip() 
                    pass
            if x.tail is not None and len(x.tail) > 0: local_text += ' ' + x.tail.strip()
        
            print(x.tag, 'tag', local_text)
        
        if len(r) > 0:
            local_text += ' ' + r
        
        return local_text 

    def consume_srai(self, element, d):
        #print('srai :', element.text, element.tag, element.attrib, d['template_modified'])
        
        local_text = ''
        if element.text is not None and len(element.text.strip()) > 0:
            #print(element.text)
            #return element.text
            local_text  += ' ' + element.text
        
        for x in element:
            
            if x.tag == "get" : 
                z = self.consume_get(x, d)
                d['template_modified'] += " " + z
                local_text += ' ' + z
                #print(local_text)
            if x.tag == "set" : 
                z = self.consume_set(x, d)
                if z is not None:
                    d['template_modified'] += " " + z
                    local_text += ' ' + z

            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)
                if z is not None:
                    d['template_modified'] += " " + z
                    local_text += ' ' + z
            if x.tag == "think":
                self.consume_think(x, d)

            if x.tail is not None and len(x.tail) > 0: local_text += ' ' + x.tail.strip()

        

        #if len(element) > 0 and element[0].tail is not None:
        #    #print(element[0].tail, '<< tail')
        #    local_text += ' ' + element[0].tail
        
        print('srai internal :', local_text)

        return local_text # d['template_modified']

    def consume_set(self, element, d):
        #print('set :', element.text, element.tag, element.attrib)
        z = ''
        if element.text is not None:
            z = element.text.strip()

        for x in element:
            if x.tag == "set" : 
                z = self.consume_set(x, d)
                #if z is not None and not d['encounter_think']:
                #    d['template_modified']  += ' ' + z
            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)

            if x.tag == "get" : 
                z = self.consume_get(x, d)
                #d['template_modified'] += " " + z
                #local_text += ' ' + z
                #print(local_text)

            #if x.tail is not None and len(x.tail) > 0: z += ' ' + x.tail.strip()


        if 'name' in element.attrib:
            #print(element.attrib,'attrib', self.memory)
            self.memory[element.attrib['name'].upper()] = z.upper().strip()
            print('---', z.upper().strip(), '---')

        return z.upper().strip()

    def consume_learn(self, element, d):
        #print('set :', element.text, element.tag, element.attrib)
        if element.text is not None:
            d['template_modified'] += element.text
        
        #x = element.text

        #d['initial_learn'] = x.strip()
        x = ''
        if d['initial_learn'] is not None:
            x = d['initial_learn'].text.strip()
            d['initial_learn'].text = ''
        if not x.startswith('/'):
            cwd = os.getcwd() + '/'
            x = cwd + AIML_DIR + x
            if not os.path.isfile(x):
                print(x, ': bad file specification')
                return ''
        print(x, '<<')
        self.learn(x)            
        return ''

    def consume_get(self, element, d):
        #print('get :', element.text, element.tag, element.attrib)
        z = ''
        if element.text is not None:
            d['template_modified'] += ' ' + element.text
            z += ' ' + element.text
        for xx in element.attrib:
            #print(xx)
            pass

        if 'name' in element.attrib.keys() and element.attrib['name'].upper() in self.memory.keys():
            #print(self.memory, '<< memory get')
            y = self.memory[element.attrib['name'].upper()]
            #print(y)
            return y

        
        for x in element:
            
            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)

            if x.tail is not None and len(x.tail) > 0: z += ' ' + x.tail.strip()

        return z

    def consume_star_tag(self, element, d):
        #print('star :', element.text, element.tag, element.attrib)
        
        s = d['star_list']
        z = element.attrib
        p = self.input.strip()
        p = ' '.join(p.split(' '))
        r = ''
        #print(z,'< before')
        if 'index' in z:
            x = int(z['index']) - 1
        else: x = 0
        #print(x, '< x')
        if len(s) > 0:
            if x <= len(s) : x = int(s[x]) -1
            z = p.split(' ')
            if x < len(z): 
                r = z[x]
        #print(s, r,'< after ')
        #print('---')
        
        return r
    
    def consume_think(self, element, d):

        d['encounter_think'] = True

        for x in element:
            
            if x.tag == "set" : 
                self.consume_set(x, d)
                
        d['encounter_think'] = False
        return '' # d['template_modified']

    def consume_condition(self, element, d):
        #print(element.attrib)
        r = ''
        name = ''
        value = ''
        z = ''
        match = False
        fallback = ''
        local_text = ''
        if element.attrib is not None:
            if 'name' in element.attrib.keys():
                name = element.attrib['name'].upper().strip()
                d['condition'] = name
            if 'value' in element.attrib.keys():
                value = element.attrib['value'].upper().strip()            

        present = ((name.upper() in self.memory.keys() or name in self.memory.keys()) and 
            (value.upper() == self.memory[name.upper()].upper() or value.upper() == self.memory[name].upper()
            or value == self.memory[name]))

        if present and element.text is not None and len(element.text) > 0:
            local_text += ' ' + element.text
            d['template_modified'] += ' '+ element.text

        #if True:
        for x in element:
            if x.tag == "think" and present: 
                self.consume_think(x, d)
                #d['template_modified'] = ''

            if x.tag == "srai" and present:
                #d['template_modified'] = ''
                z = self.consume_srai(x, d)
                if z is not None and len(z) > 0:
                    d['template_modified'] = z ## replace, not concatenate!
                    #print(self.depth, "< depth")
                    local_text += ' ' + z
                    self.depth += 1
                    if self.depth < self.depth_limit:
                        self.index = 0
                        self.output = ''
                        self.incomplete = False
                        print('z:', z)
                        if SRAI_LITERAL == 1 :
                            r = self.respond_srai(z) 
                            self.srai_list.append(r)
                        else:
                            r = self.respond_bert(z)   
                            self.srai_list.append(r)   

            if present and x.tail is not None and len(x.tail) > 0: local_text += ' ' + x.tail.strip()

        if present and r is not None and len(r.strip()) > 0: 
            pass
            local_text += ' ' + r
            #return r
        print('=', local_text, '=')

        return local_text 

    
    
if __name__ == '__main__':

    k = Kernel()
    k.verbose(False)
    k.learn('../aiml/startup.xml')
    if len(AIML_FILE) > 0:
        if AIML_FILE.startswith('/'):
            k.learn(AIML_FILE)
        else:
            x = os.getcwd() + '/' + AIML_DIR + AIML_FILE
            if os.path.isfile(x):
                k.learn(x)
                print(x,'<<')
            else:
                print('bad file specification')
                exit()
    print(k.args)
    if k.args.raw_pattern:
        k.raw_pattern()
        exit()
    while True:
        try:
            y = input("> ")
        except EOFError:
            if not k.args.count: exit()
            name = ''
            if DOUBLE_COMPARE == 0: name = '.pat'
            if DOUBLE_COMPARE == 1: name = '.pat.tem'
            if DOUBLE_COMPARE == 2: name = '.tem'
            print(len(k.z), len(k.used), 'used', k.used_num, 'attempts')
            z = open('ratio' + name + '.txt', 'w')
            z.write(str(len(k.z)) + ' total categories\n' )
            z.write(str(len(k.used)) + ' total used\n')
            z.write(str(k.used_num) + ' total number of attempts\n')
            z.close()
            exit()    
        x = ''
        if len(x.strip()) == 0 : 
            r = k.respond(y) 
            print(r)
        else:
            print(x)