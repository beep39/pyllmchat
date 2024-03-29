from backend import backend
import requests
import json

class backend_kobold(backend):
    def __init__(self, api_url, max_context_length=None):
        super().__init__()
        if not api_url.endswith('/'):
            api_url += '/'

        if max_context_length:
            self.max_context_length = max_context_length
        else:
            try:
                r = requests.get(api_url+'extra/true_max_context_length')
                self.max_context_length = r.json()['value']
            except:
                print('unable to get max context, using default')

        self.api_url = api_url + 'extra/'
        self.sampler_order = [6,0,1,3,4,2,5]

    def tokens_count(self, text):
        r = requests.post(self.api_url+'tokencount', json={'prompt':text })
        return r.json()['value']

    def generate(self, prompt, stop, on_stream=None):
        data = {'prompt':prompt,
                'stop_sequence': [stop],

                'max_context_length': self.max_context_length,
                'max_length': self.max_length,
                'temperature': self.temperature,

                'rep_pen': self.rep_pen,
                'rep_pen_range': 600,
                'rep_pen_slope': 0,
                'tfs': 1,
                'top_a': 0,
                'top_k': self.top_k,
                'top_p': self.top_p,
                'min_p': self.min_p,
                'typical': self.typical,

                'sampler_order': self.sampler_order,
                'use_story': False,
                'use_memory': False,
                'use_authors_note': False,
                'use_world_info': False,
                'singleline': False
            }

        result = ''
        try:
            r = requests.post(self.api_url+'generate/stream/', json=data, stream=True)
            if r.status_code != 200:
                print('model_kobold', r.status_code, r.reason)
                return result
            lines = r.iter_lines(decode_unicode=True)
            def generate():
                for line in lines:
                    if line.startswith('data:'):
                        nonlocal result
                        result += json.loads(line[5:])['token']
                        return result
                return None
            return self.process(generate, stop, on_stream)
        except Exception as e:
            print('backend_kobold',type(e),e)
        return result
