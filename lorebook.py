from os import listdir
import json

class lorebook_entry:
    def __init__(self):
        self.keys = []
        self.secondary_keys = None
        self.content = None
        self.selective_logic = 0
        self.case_sensitive = False
        self.constant = False
        self.order = 100  # if two entries inserted, entry with lower order inserted higher
        self.group = None
        self.position = 'wiBefore'

    def match(self, text):
        if self.constant:
            return True

        if not self.case_sensitive:
            text = text.lower()

        found = False
        for k in self.keys:
            if k in text:
                found = True
                break
        if not found:
            return False

        if not self.secondary_keys:
            return True

        if self.selective_logic == 1:   # NOT ALL
            found = False
            for k in self.secondary_keys:
                if not k in text:
                    found = True
            if not found:
                return False
        elif self.selective_logic == 2: # NOT ANY
            for k in self.secondary_keys:
                if k in text:
                    return False
        else:                           # AND ANY
            found = False
            for k in self.secondary_keys:
                if k in text:
                    found = True
                    break
            if not found:
                return False

        return True

class lorebook:
    def __init__(self, filename = None):
        self.name = None
        self.scan_depth = 50 # chat history depth
        self.recursive = False
        self.entries = []
        self.dir = 'lorebooks/'
        if filename:
            self.load(filename)

    def load(self, name):
        if not name.endswith('.json'):
            name += '.json'
        name.replace('\\','/')
        if not '/' in name and self.dir:
            name = self.dir+name
        try:
            with open(name, 'r') as f:
                return self.load_json(json.load(f))
        except Exception as e: 
            print('lorebook:',e)
            return False

    def list(self):
        lst = []
        try:
            lst = listdir(self.dir)
        except:
            pass
        for i in range(len(lst)):
            lst[i] = lst[i].rstrip('.json')
        return lst

    def load_json(self, text):
        data = json.loads(text) if isinstance(text, str) else text
        if 'data' in data:
            data = data['data']
        self.id = data.get('id')
        self.name = data.get('name')
        self.scan_depth = data.get('scan_depth')
        self.recursive = data.get('recursive_scanning')
        self.entries = []
        entries = data.get('entries')
        if isinstance(entries, dict):
            entries = entries.values()
        for e in entries:
            if e.get('enabled') == False or e.get('disable') == True:
                continue

            entry = lorebook_entry()
            entry.content = e.get('content')
            if not entry.content:
                continue

            entry.order = e.get('insertion_order')
            if entry.order is None:
                entry.order = e.get('order')
            entry.group = e.get('group')

            position = e.get('position')
            if isinstance(position, str) and position == 'after_char':
                entry.position = 'wiAfter'
            if isinstance(position, int) and position > 0: # ToDo
                entry.position = 'wiAfter'

            entry.constant = e.get('constant')
            if entry.constant:
                self.entries.append(entry)
                continue

            entry.keys = e.get('keys')
            if entry.keys is None:
                entry.keys = e.get('key')
            if not entry.keys:
                continue

            if e.get('selective') == True:
                entry.secondary_keys = e.get('secondary_keys')
                if entry.secondary_keys is None:
                    entry.secondary_keys = e.get('keysecondary')
            selectiveLogic = e.get('selectiveLogic')
            if selectiveLogic:
                entry.selective_logic = selectiveLogic

            entry.case_sensitive = e.get('case_sensitive')
            if entry.case_sensitive != True:
                entry.keys = list(map(str.lower, entry.keys))
                if entry.secondary_keys:
                    entry.secondary_keys = list(map(str.lower, entry.secondary_keys))

            self.entries.append(entry)
        return True
