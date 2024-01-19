import random, json
from datetime import datetime
from char_desc import char_desc
from user_desc import user_desc
import dice

default_template ='''{{#if system}}{{system}}
{{/if}}{{#if wiBefore}}{{wiBefore}}
{{/if}}{{#if description}}{{description}}
{{/if}}{{#if personality}}{{personality}}
{{/if}}{{#if scenario}}{{scenario}}
{{/if}}{{#if wiAfter}}{{wiAfter}}
{{/if}}Then the roleplay chat between {{user}} and {{char}} begins.
{{#if examples}}{{examples}}
{{/if}}<START>
{{history}}'''

class chat:
    def __init__(self, backend):
        self.user = user_desc()
        self.char = char_desc()
        self.backend = backend
        self.history = []
        self.emotion_classifier = None
        self.system = None
        self.lorebooks = []
        self.template = default_template
        self.example_separator = '<START>'
        self._var_handlers = {}

        self.reg_var('time', lambda _=None: datetime.now().strftime(' %I:%M %p').replace(' 0',''))
        self.reg_var('date', lambda _=None: datetime.now().strftime('%B %d, %Y').replace(' 0',' '))
        self.reg_var('weekday', lambda _=None: datetime.now().strftime('%A'))
        self.reg_var('isodate', lambda _=None: datetime.now().date().isoformat())
        self.reg_var('isotime', lambda _=None: datetime.now().strftime('%X')) #%H:%M
        self.reg_var('random', lambda args=['']: random.choice(args))
        self.reg_var('roll', lambda f=['1d20']: str(dice.roll(f[0])))

    def start(self):
        self.history = []
        greeting = 'Hello'
        if self.char.greeting:
            greeting = self.char.greeting
            if not isinstance(greeting, str):
                greeting = random.choice(greeting)
            greeting = self._replace(greeting).replace('\r','')
        self.history.append(self.char.name+': '+greeting)
        return greeting

    def say(self, text, on_stream=None, name='{{user}}', answer_as='{{char}}'):
        if text:
            self.history.append(self._replace(name+': '+text))
        if answer_as:
            self.history.append(self._replace(answer_as) + ': ')
            return self.regenerate(on_stream)

    def regenerate(self, on_stream=None):
        if self.history:
            self.history[-1] = self.history[-1].split(':',1)[0] + ': '
        else:
            self.history = [self.char.name+': ']
        stop = '\n'+self.user.name+':'
        result = self.prompt(self.template, stop, on_stream)
        if not result:
            return result
        result = self._replace(result)
        self.history[-1] += result
        return result

    # prompt without modifying chat history
    def prompt(self, text, stop, on_stream=None, max_length=None):
        if not max_length:
            max_length = self.backend.max_length

        vars = {
            'user':self.user.name,
            'char':self.char.name,
            'system':self.system,
            'description':self.char.description,
            'personality':self.char.personality,
            'scenario':self.char.scenario,
            'template':self.template
        }

        def process_worldinfo(lorebook):
            if not lorebook or not lorebook.entries:
                return

            #ToDo: order, recursive
            history = self.history[-lorebook.scan_depth:]
            used_groups = set()
            for e in lorebook.entries:
                if e.group and e.group in used_groups:
                    continue

                for h in history:
                    if e.match(h):
                        v = e.position.lower()
                        try:
                            vars[v] += '\n'+e.content
                        except:
                            vars[v] = e.content
                        if e.group:
                            used_groups.add(e.group)
                        break

        process_worldinfo(self.char.lorebook)
        for l in self.lorebooks:
            process_worldinfo(l)

        prompt = self._replace(text, vars, ['history','examples'])
        pc = self.backend.tokens_count(prompt)
        def fit_context(lines,replace):
            if not lines:
                return ''
            nonlocal pc
            result = ''
            first = True
            for l in reversed(lines):
                if replace:
                    l = self._replace(l)
                if not first:
                    l = l+'\n'
                else:
                    first = False
                c = self.backend.tokens_count(l)
                if not self.backend.check_length(pc+c+max_length):
                    break
                pc+=c
                result=l+result
            return result

        if '{{history}}' in prompt:
            prompt = self._replace(prompt, {'history': fit_context(self.history, False)},['examples'])
        if '{{examples}}' in prompt:
            examples = fit_context(self.char.examples, True).replace('<START>', self.example_separator)
            prompt = self._replace(prompt, {'examples': examples})
        return self.backend.generate(prompt.replace('\r',''), stop, on_stream).replace('\r','')

    def enable_emotions(self, model = None):
        if model == None:
            model = 'j-hartmann/emotion-english-distilroberta-base'
        from transformers import pipeline
        self.emotion_classifier = pipeline("text-classification",model=model, top_k=None)

    def emotion(self, text = None):
        if self.emotion_classifier == None:
            self.enable_emotions()
        if text == None:
            text = self.history[-1].split(':',1)[-1]
        emotions = self.emotion_classifier(text)
        result = {}
        for e in emotions[0]:
            result[e['label']] = e['score']
        return result

    def reg_var(self, name, handler, template=None):
        if template:
            handler=lambda:handler(self._replace(template))
        self._var_handlers[name.lower()] = handler

    def save(self, path):
        save = {}
        save['char'] = self.char.name
        user = {'name':self.user.name}
        if self.user.description:
            user['description'] = self.user.description
        save['user'] = user
        if self.system:
            save['system'] = self.system
        save['history'] = self.history
        with open(path, "w") as f:
            json.dump(save, f)

    def load(self, path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                char = data['char']
                if char != self.char.name:
                    if char in self.char.list():
                        self.char.load(char)
                user = data.get('user')
                if user:
                    self.user.name = user['name']
                    self.user.description = user.get('description')
                self.system = data.get('system')
                self.history = data['history']
        except FileNotFoundError:
            return False
        return True

    def _replace(self, text, vars = None, ignore = None):
        if vars is None:
            vars = { 'user':self.user.name, 'char':self.char.name }
        s = 0
        while True:
            v = None
            r = None
            try:
                s = text.index('{{',s)
                e = text.index('}}',s+2)
                v = text[s+2:e].strip()
            except ValueError:
                break
            try:
                r = vars[v.lower()]
                if r is None:
                    r = ''
            except KeyError:
                if v.startswith('#if'):
                    v = v[3:].strip()
                    vl = v.lower()
                    r = vars.get(vl)
                    try:
                        close='{{/if}}'
                        if ignore and vl in ignore:
                            cs = text.index(close,s)
                            s = cs+len(close)
                            continue
                        text = text[:s]+text[e+2:]
                        cs = text.index(close,s)
                        if r:
                            text = text[:cs]+text[cs+len(close):]
                        else:
                            text=text[:s]+text[cs+len(close):]
                    except ValueError:
                        if not r:
                            text = text[:s]
                        break
                    continue
                a = None
                try:
                    s2 = v.index('(')
                    a = v[s2+1:v.index(')',s2)]
                    v = v[:s2]
                except ValueError:
                    try:
                        s2 = v.index(':')
                        a = v[s2+1:]
                        v = v[:s2]
                    except ValueError:
                        pass
                handler = self._var_handlers.get(v.lower())
                if handler:
                    if a != None:
                        r = handler(a.split(','))
                    else:
                        r = handler()
                else:
                    if not ignore or not v.lower() in ignore:
                        print('unrecognized var:',v)
                    s = e+2
                    continue
            text=text[:s]+r+text[e+2:]
        return text
