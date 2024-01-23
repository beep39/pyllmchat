from backend import backend
import requests
import json

class backend_tabbyapi(backend):
    def __init__(self, api_url, apikey, max_context_length=None):
        super().__init__()
        if not api_url.endswith('/'):
            api_url += '/'
        api_url += 'v1/'
        def auth(r):
            r.headers['Authorization'] = 'Bearer ' + apikey
            return r
        self.auth = auth
        if max_context_length:
            self.max_context_length = max_context_length
        else:
            try:
                r = requests.get(api_url+'model', auth=self.auth)
                self.max_context_length = r.json()['parameters']['max_seq_len']
            except Exception:
                print('unable to get max context, using default')
        self.api_url = api_url

    def tokens_count(self, text):
        r = requests.post(self.api_url+'token/encode', json={'text':text }, auth=self.auth)
        return r.json()['length']

    def generate(self, prompt, stop, on_stream=None):
        data = {'prompt':prompt,
                'stream': True,
                'echo': False,
                'stop': [stop],
                'max_tokens': self.max_length,
                'temperature': self.temperature,
                'repetition_penalty': self.rep_pen,
                'repetition_range': self.rep_pen_range,
                'rep_pen_slope': 0,
                'tfs': 1.0,
                'top_k': self.top_k,
                'top_p': self.top_p,
                'min_p': self.min_p,
                'typical': self.typical,
                'mirostat_mode': 0
            }

        result = ''
        try:
            r = requests.post(self.api_url+'completions', json=data, stream=True, auth=self.auth)
            if r.status_code != 200:
                print('backend_tabbyapi', r.status_code, r.reason)
                return result
            r.encoding = 'utf-8'
            lines = r.iter_lines(decode_unicode=True)
            def generate():
                for line in lines:
                    if line.startswith('data:'):
                        line = line[6:]
                        if line == '[DONE]':
                            return None
                        nonlocal result
                        try:
                            result += json.loads(line)['choices'][0]['text']
                            return result
                        except Exception as e:
                            print('backend_tabbyapi',type(e),e,'line:',line)
                            pass
                return None
            return self.process(generate, stop, on_stream)
        except Exception as e:
            print('backend_tabbyapi',type(e),e)
        return result

    def models(self):            
        try:
            r = requests.get(self.api_url+'models', auth=self.auth)
            return list(map(lambda e: e['id'], r.json()['data']))
        except Exception as e:
            print('backend_tabbyapi',type(e),e)

    def load(self, model, max_context_length = None, cache_mode= 'FP16'):
        try:
            r = requests.get(self.api_url+'model/unload', auth=self.auth)
            data = {'name':model,
                    'cache_mode': cache_mode
            }
            if max_context_length:
                data['max_seq_len'] = max_context_length
            r = requests.post(self.api_url+'model/load', json=data, auth=self.auth)
            if r.status_code != 200:
                print(r.json()['detail'])
                return False
            r = requests.get(self.api_url+'model', auth=self.auth)
            if r.status_code != 200:
                print(r.json()['detail'])
                return False
            self.max_context_length = r.json()['parameters']['max_seq_len']
            return True
        except Exception as e:
            print('backend_tabbyapi',type(e),e)
        return False
