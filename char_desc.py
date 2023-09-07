from os import listdir
import struct, json
from base64 import b64decode

class char_desc:
    def __init__(self):
        self.name = 'Character'
        self.description = None
        self.personality = None
        self.greeting = None
        self.examples = None
        self.creator_notes = None
        self.scenario = None
        self.dir = 'characters/'

    def load(self, name):
        if not name.endswith('.png'):
            name += '.png'
        name.replace('\\','/')
        if not '/' in name:
            name = self.dir+name
        with open(name, 'rb') as f:
            data = None
            try:
                if f.read(8) != b'\x89PNG\r\n\x1a\n':
                    return False
                while(True):
                    l = struct.unpack(">I",f.read(4))[0]
                    if f.read(4) != b'tEXt':
                        f.seek(l+4,1)
                        continue
                    if f.read(6) != b'chara\x00':
                        f.seek(l+4-6,1)
                        continue
                    text = b64decode(f.read(l-6)).decode('UTF-8')
                    data = json.loads(text)
                    break
            except:
                return False
            return self.load_data(data)

    def load_data(self, data):
        self.name = data.get('name')
        self.description = data.get('description')
        self.scenario = data.get('scenario')
        self.personality = data.get('personality')
        self.greeting = data.get('first_mes')
        alt_greetings = data.get('alternate_greetings')
        if alt_greetings and not isinstance(alt_greetings, str):
            if self.greeting:
                alt_greetings.insert(0, self.greeting)
            self.greeting = alt_greetings
        mes_example = data.get('mes_example')
        if mes_example:
            split = '<START>'
            mes_example = mes_example.split(split)
            self.examples = []
            for m in mes_example:
                m = m.strip()
                if not m:
                    continue
                self.examples.append(split+'\n'+m)
        else:
            self.examples = None
        self.creator_notes = data.get('creator_notes')
        #for k in data:
        #    print('@'+k+':', data[k])
        return True

    def list(self):
        lst = listdir(self.dir)
        for i in range(len(lst)):
            lst[i] = lst[i].rstrip('.png')
        return lst
