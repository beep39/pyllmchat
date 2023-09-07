import random
from datetime import datetime
from char_desc import char_desc
from user_desc import user_desc

default_template ='''{{#if system}}{{system}}
{{/if}}{{#if description}}{{description}}
{{/if}}{{#if personality}}{{personality}}
{{/if}}{{#if scenario}}{{scenario}}
{{/if}}Then the roleplay chat between {{user}} and {{char}} begins.
{{#if examples}}{{examples}}
{{/if}}<START>
{{history}}'''

class chat:
    def __init__(self, backend):
        self.user = user_desc()
        self.char = char_desc()
        self.backend = backend
        self.emotion_classifier = None
        self.system = None
        self.template = default_template
        self._var_handlers = {}

        self.reg_var('time', lambda args=None: datetime.now().strftime(' %I:%M %p').replace(' 0',''))
        self.reg_var('date', lambda args=None: datetime.now().strftime('%B %d, %Y').replace(' 0',' '))
        self.reg_var('random', lambda args=['']: random.choice(args))

    def start(self):
        self.lines = []
        greeting = None
        if self.char.greeting:
            greeting = self.char.greeting
            if not isinstance(greeting, str):
                greeting = random.choice(greeting)
            greeting = self._replace(greeting)
            self.lines.append(self.char.name+': '+greeting)
        return greeting

    def say(self, text, on_stream=None, name='{{user}}', answer_as='{{char}}'):
        self.lines.append(self._replace(name+': '+text))
        if answer_as:
            self.lines.append(self._replace(answer_as) + ': ')
            return self.regenerate(on_stream)

    def regenerate(self, on_stream=None):
        self.lines[-1] = self.lines[-1].split(':',1)[0] + ': '
        stop = '\n'+self.user.name+':'
        result = self.prompt(self.template, stop, on_stream)
        if not result:
            return result
        result = self._replace(result)
        self.lines[-1] += result
        return result

    # prompt without modifying chat history
    def prompt(self, text, stop, on_stream=None, max_length=None):
        if not max_length:
            max_length = self.backend.max_length
        prompt = self._replace(text)
        pc = self.backend.tokens_count(prompt)
        def fit_context(lines):
            if not lines:
                return ''
            nonlocal pc
            result = ''
            first = True
            for l in reversed(lines):
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
            prompt = prompt.replace('{{history}}', fit_context(self.lines))
        if '{{examples}}' in prompt:
            examples = list(map(self._replace, self.char.examples))
            prompt = prompt.replace('{{examples}}', fit_context(examples))
        return self.backend.generate(prompt, stop, on_stream)

    def enable_emotions(self, model = None):
        if model == None:
            model = 'j-hartmann/emotion-english-distilroberta-base'
        from transformers import pipeline
        self.emotion_classifier = pipeline("text-classification",model=model, top_k=None)

    def emotion(self, text = None):
        if self.emotion_classifier == None:
            self.enable_emotions()
        if text == None:
            text = self.lines[-1].split(':',1)[-1]
        emotions = self.emotion_classifier(text)
        result = {}
        for e in emotions[0]:
            result[e['label']] = e['score']
        return result
 
    def reg_var(self, name, handler, template=None):
        if template:
            handler=lambda:handler(self._replace(template))
        self._var_handlers[name] = handler

    def _replace(self, text):
        vars = {
            'user':self.user.name,
            'char':self.char.name,
            'system':self.system,
            'description':self.char.description,
            'personality':self.char.personality,
            'scenario':self.char.scenario,
            'template':self.template
        }
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
                r = vars[v]
                if r is None:
                    r = ''
            except KeyError:
                if v.startswith('#if'):
                    text = text[:s]+text[e+2:]
                    v = v[3:].strip()
                    r = vars.get(v)
                    try:
                        close='{{/if}}'
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
                    pass
                handler = self._var_handlers.get(v)
                if handler:
                    if a != None:
                        r = handler(a.split(','))
                    else:
                        r = handler()
                else:
                    if v != 'history' and v != 'examples': #filled last
                        print('unrecognized var:',v)
                    s = e+2
                    continue
            text=text[:s]+r+text[e+2:]
        return text
