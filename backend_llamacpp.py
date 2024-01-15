from backend import backend
import requests
import json

class backend_llamacpp(backend):
    def __init__(self, api_url, max_context_length=None):
        super().__init__()
        if not api_url.endswith('/'):
            api_url += '/'
        if max_context_length:
            self.max_context_length = max_context_length
        else:
            try:
                r = requests.get(api_url+'model.json')
                self.max_context_length = r.json()['n_ctx']
            except:
                print('unable to get max context, using default')
        self.api_url = api_url

    def tokens_count(self, text):
        r = requests.post(self.api_url+'tokenize', json={'content':text })
        return len(r.json()['tokens'])

    def generate(self, prompt, stop, on_stream=None):
        data = {'prompt':prompt,
                'stream': True,
                'stop_sequence': [stop],
                'n_predict': self.max_length,
                'temperature': self.temperature,
                'repeat_penalty': self.rep_pen,
                'repeat_last_n': self.rep_pen_range,
                'rep_pen_slope': 0,
                'tfs_z': 1.0,
                'top_k': self.top_k,
                'top_p': self.top_p,
                'min_p': self.min_p,
                'typical_p': self.typical,
                'mirostat': 0
            }

        result = ''
        try:
            r = requests.post(self.api_url+'completion', json=data, stream=True)
            if r.status_code != 200:
                print('backend_llamacpp', r.status_code, r.reason)
                return result
            r.encoding = 'utf-8'
            lines = r.iter_lines(decode_unicode=True)
            def generate():
                for line in lines:
                    if line.startswith('data:'):
                        nonlocal result
                        result += json.loads(line[5:])['content']
                        return result
                return None
            return self.process(generate, stop, on_stream)
        except Exception as e:
            print('backend_llamacpp',type(e),e)
        return result
