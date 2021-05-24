#!/usr/bin/env python3

import aiml as aiml_std
from transformers import BertTokenizer, BertForNextSentencePrediction
import torch
import xml.etree.ElementTree as ET
import re
import os
import string
import random
from dotenv import load_dotenv

load_dotenv()

print(os.environ['AIML_DIR'])

AIML_DIR=os.environ['AIML_DIR']
BATCH_SIZE=int(os.environ['BATCH_SIZE'])

class Kernel:

    def __init__(self):
        self.filename = 'name'
        self.verbose_response = True
        self.output = ""
        self.kernel = aiml_std.Kernel()
        self.tree = None
        self.root = None
        self.l = []
        self.z = []
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
        #print(self.model.config)

    def verbose(self, isverbose):
        #print(isverbose)
        self.verbose_response = isverbose
        self.kernel.verbose(isverbose)

    def learn(self, file):
        self.filename = file
        if self.filename in self.files:
            return
        self.files.append(file)

        #self.kernel.learn(file)
        #self.l = []
        #self.score = []
        self.tree = ET.parse(file)
        self.root = self.tree.getroot()

        self.pattern_factory_topic(self.root)

    def respond(self, input):
        self.score = []
        self.index = -1
        self.incomplete = False
        self.input = str(re.sub(' +', ' ', input).upper().strip())
        self.input = self.input.translate(str.maketrans('','', string.punctuation))

        self.l = []
        word_factor = 2
        i_length = len(input.strip().split(' '))
        #print(len(self.l), 'list')
        for j in range(len(self.z)):
            p = self.z[j]['pattern']
            p_len = len(p.strip().split(' '))
            if i_length >= p_len + word_factor:
                continue
            if i_length <= p_len - word_factor:
                continue
            self.l.append(self.z[j])
            pass

        print(len(self.z), len(self.l))

        batch_pattern = []
        batch_input = []
        self.target = []

        ## input pattern batch ##
        batch_size = BATCH_SIZE
        num = 0
        for ii in range(0, len(self.l) , batch_size):
            #print(ii, ii+batch_size)
            
            if ii + batch_size > len(self.l):
                batch_size = len(self.l) - ii
            #print(batch_size, '< bs')
            batch_pattern = []
            batch_input = []
            self.target = []
            for j in range(ii, ii+batch_size):
                #print(j, end=',')

                i = self.l[j]
                i['star'] = None
                input_02, d = self.mod_input(i, input)
                #self.l[num] = d ## <-- ???
                ip = i['pattern']
                #s = self.bert_compare(ii, input_02)
                #print(ii, num)
                if i['initial_that'] is not None and len(i['initial_that']) > 0:
                    ip += ' ' + i['initial_that']
                #print(ii, num)
                ## batches start
                batch_pattern.append(ip)
                batch_input.append(input_02)
                self.target.append(1)
                ## batches end
                num += 1
            s = self.bert_batch_compare(batch_pattern, batch_input)
            
            num = 0
            j = 0
            #print()
            batch_size = BATCH_SIZE
            if ii + batch_size > len(self.l):
                batch_size = len(self.l) - ii
            for j in range(ii, ii + batch_size):
                #print(j, num, end=',')

                self.score.append(s[num])
                num += 1
            #print('< score')
            
        
        ## find highest entry ##
        high = 0
        num = 0
        index = -1
        for i in self.score:
            i = i[0] - i[1]
            i = self.mod_that(self.l[num], input, i)
            print(i, self.l[num]['initial_template'].text.strip(), len(self.score))
            if i > high:
                high = i
                index = num
            num += 1
        ## update dictionary ##
        
        d = self.mod_respond_dict(self.l[index], input)
        #self.l[index] = d
        z = self.mod_template_out(self.l[index], input) ## includes srai output
        
        self.index = index
        
        r = self.choose_output(self.l[index]) ## random
        if r == '' and z != '':
            self.output = z
        else:
            self.output = r

        
        if len(self.output) > 0: self.depth = 0

        self.output = str(re.sub(' +', ' ', self.output).upper().strip())
        self.output = self.output.translate(str.maketrans('','', string.punctuation))

        if self.output not in self.answers:
            self.answers.append(self.output.upper().strip())

        self.answers = self.answers[- self.answers_length:] ## last few
        #print(self.answers)

        return self.output

    def choose_output(self, d):
        if len(d['random_list']) > 0:
            return random.choice(d['random_list'])
        #elif True:
        #return d['template_modified'].strip()
        return ''

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
    
    def pattern_factory_topic(self, root):
        num = 0
        for child in root:
            if child.tag == "topic":
                #print(child.attrib['name'])
                topic = ''
                if child.attrib['name'] is not None and len(child.attrib['name'].strip()) > 0:
                    topic = child.attrib['name'].upper().strip()
                #print('change topic', topic)
                
                for ch2 in child:
                    pat_dict = self.pattern_factory(ch2, topic)
                    pat_dict['index'] = num
                    
                    #self.l.append( pat_dict)
                    self.z.append(pat_dict)

                    num += 1
                    pass

            if child.tag == "category":
                #print('do category')
                pat_dict = self.pattern_factory(child)
                pat_dict['index'] = num
            
                #self.l.append(pat_dict)
                self.z.append(pat_dict)

                num += 1
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
        for i in category:
            original = i.text

            if i.tag == 'pattern':
                pat = i.text
                if pat is None: pat = ''
                pat = ' '.join(pat.split(' ')).strip()
                original = ET.tostring(i)

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
            if i.tag == "that":
                that = i.text
        
        wo_start = False
        wo_end = False

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
            'that_star_list': that_star_list,
            'original': original,
            'topic': topic,
            'random': random,
            'random_list': random_list,
            'condition': condition
        }

        if random is not None:
            self.mod_pattern_factory_random_tag(d['random'], d)

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
        #print(l)
        z = d['star_list']
        if len(z) is 1:
            if d['wo_start']:
                d['start'] = l[0]
                l = l[1:]
            elif d['wo_end']:
                d['end'] = l[-1]
                l = l[:-1]
        elif len(z) > 1:
            if d['wo_start']:
                d['start'] = l[0]
                l = l[z[-1]:] # l[1:]
            elif d['wo_end']:
                d['end'] = l[-1]
                l = l[:z[0]] # l[:-1]
            
        #print(l)
        input = ' '.join(l)
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
        #print('template :', element.text, element.tag, element.attrib)
        if element.text is not None:
            t = element.text.strip()
            d['template_modified'] += t
        
        for x in element:
            
            if x.tag == "srai" :
                d['template_modified'] = ''
                z = self.consume_srai(x, d)
                if z is not None and len(z) > 0:
                    d['template_modified'] = z ## replace, not concatenate!
                    #print(self.depth, "< depth")
                    self.depth += 1
                    if self.depth < self.depth_limit:
                        self.index = 0
                        self.output = ''
                        self.incomplete = False
                        x = self.respond(d['template_modified'])
                        return x 

            if x.tag == "learn" : 
                self.consume_learn(x, d)
                return ''
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
            if x.tag == "think":
                self.consume_think(x, d)
            if x.tag == "condition":
                z = self.consume_condition(x, d)
                if z is not None and len(z) > 0:
                    d['template_modified'] = z

        if len(element) > 0 and element[0].tail is not None:
            #print(element[0].tail, '<< tail')
            t = element[0].tail
            t = t.strip()
            d['template_modified'] += ' ' + t

        return d['template_modified']

    def consume_srai(self, element, d):
        #print('srai :', element.text, element.tag, element.attrib)
        d['template_modified'] = ''
        if element.text is not None:
            d['template_modified'] += ' ' + element.text
        
        for x in element:
            
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
        
        #print('srai internal :', d['template_modified'])

        if len(element) > 0 and element[0].tail is not None:
            #print(element[0].tail, '<< tail')
            d['template_modified'] += ' ' + element[0].tail

        return d['template_modified']

    def consume_set(self, element, d):
        #print('set :', element.text, element.tag, element.attrib)
        
        z = element.text

        for x in element:
            
            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)

        if 'name' in element.attrib:
            self.memory[element.attrib['name']] = z.upper().strip()

        return z

    def consume_learn(self, element, d):
        #print('set :', element.text, element.tag, element.attrib)
        if element.text is not None:
            d['template_modified'] += element.text
        
        #x = element.text

        #d['initial_learn'] = x.strip()
        x = d['initial_learn'].text.strip()
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
        if element.text is not None:
            d['template_modified'] += element.text
        for xx in element.attrib:
            #print(xx)
            pass

        if 'name' in element.attrib.keys() and element.attrib['name'] in self.memory.keys():
            #print(self.memory, '<< memory get')
            y = self.memory[element.attrib['name']]
            #print(y)
            return y

        z = ''
        for x in element:
            
            if x.tag == "star" : 
                z = self.consume_star_tag(x, d)
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
        #print('think :', element.text, element.tag, element.attrib)
        
        for x in element:
            
            if x.tag == "set" : 
                self.consume_set(x, d)
                
        return '' 

    def consume_condition(self, element, d):
        #print(element.attrib)
        name = ''
        value = ''
        z = ''
        match = False
        fallback = ''
        if element.attrib is not None:
            if 'name' in element.attrib.keys():
                name = element.attrib['name'].lower().strip()
                d['condition'] = name
            if 'value' in element.attrib.keys():
                value = element.attrib['value'].upper().strip()            

        for x in element:
            
            if x.tag == "li":
                z, match = self.consume_li_tag(x, d)
                if z is not None:
                    if match is False: 
                        fallback = z
                    d['template_modified'] = z
                    if match is True:
                        break

        if len(z) > 0:
            if match is False and len(fallback) > 0:
                return fallback
            elif match is True and len(d['template_modified']) > 0:
                return d['template_modified']

        if name in self.memory.keys() and len(z) == 0:
            if value.upper() != self.memory[name].upper():
                return ''
            elif len(z) is 0:
                return element.text
            else:
                return z
        return d['template_modified'].strip()

    def consume_li_tag(self, element, d):
        name = d['condition']
        value = ''
        exact_match = False
        print(element.attrib,name)

        if element.attrib is not None and len(element.attrib) > 0:
            
            if 'value' in element.attrib.keys():
                value = element.attrib['value'].upper().strip()  

            if name is not None and name in self.memory.keys() :
                if value.upper() != self.memory[name].upper():
                    return '', exact_match
                else:
                    exact_match = True
                    return element.text, exact_match
            else:
                
                return '', exact_match
        else:
            return element.text, exact_match

        pass
        
    
if __name__ == '__main__':

    k = Kernel()
    k.verbose(False)
    k.learn('../aiml/startup.xml')
    while True:
        y = input("> ")
        #k.respond(y)
        #x = k.kernel.respond(y)
        x = ''
        if len(x.strip()) == 0 and not k.verbose_response: 
            r = k.respond(y) 
            print(r)
        else:
            print(x)