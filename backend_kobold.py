from backend import backend
import requests
import tiktoken
import json

class backend_kobold(backend):
    def __init__(self, api_url, max_context_length=None):
        super().__init__()
        if not api_url.endswith('/'):
            api_url += '/'
        api_url += 'extra/generate/stream/'
        if max_context_length:
            self.max_context_length = max_context_length
        self.api_url = api_url
        self.sampler_order = [6,0,1,3,4,2,5]
        self.pad_tokens = 64
        self._tokenizer = tiktoken.get_encoding("gpt2")

    def tokens_count(self, text):
        return len(self._tokenizer.encode(text))

    def check_length(self, token_count):
        return token_count + self.pad_tokens <= self.max_context_length

    def generate(self, prompt, stop, on_stream=None):
        data = {'prompt':prompt,
                'stop_sequence': [stop],

                "max_context_length": self.max_context_length,
                "max_length": self.max_length,
                "temperature": self.temperature,

                "rep_pen": self.rep_pen,
                "rep_pen_range": 600,
                "rep_pen_slope": 0,
                "tfs": 1,
                "top_a": 0,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "typical": 1,

                "sampler_order": self.sampler_order,
                'use_story': False,
                "use_memory": False,
                "use_authors_note": False,
                "use_world_info": False,
                "singleline": False
            }

        result = ''
        try:
            r = requests.post(self.api_url, json=data, stream=True)
            if r.status_code != 200:
                print('model_kobold', r.status_code, r.reason)
                return result
            lines = r.iter_lines(decode_unicode=True)
            def generate():
                for line in lines:
                    if line.startswith('data:'):
                        nonlocal result
                        result += json.loads(line[5:])["token"]
                        return result
                return None
            return self.process(generate, stop, on_stream)
        except Exception as e:
            print('backend_kobold',type(e),e)
        return result
