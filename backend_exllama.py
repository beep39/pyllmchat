from backend import backend
from os import path
from glob import glob
try:
    from exllama.generator import ExLlamaGenerator
    from exllama.model import ExLlama, ExLlamaCache, ExLlamaConfig
    from exllama.tokenizer import ExLlamaTokenizer
except ModuleNotFoundError:
    local_path = 'exllama'  #exllama folder in project root
    import sys
    if not local_path in sys.path:
        sys.path.append(local_path)
    from generator import ExLlamaGenerator
    from model import ExLlama, ExLlamaCache, ExLlamaConfig
    from tokenizer import ExLlamaTokenizer

class backend_exllama(backend):
    def __init__(self, model_directory, max_context_length=2048):
        super().__init__()
        self.max_context_length = max_context_length
        tokenizer_path = path.join(model_directory, "tokenizer.model")
        self._tokenizer = ExLlamaTokenizer(tokenizer_path)

        model_config_path = path.join(model_directory, "config.json")
        st_pattern = path.join(model_directory, "*.safetensors")
        model_path = glob(st_pattern)[0]
        config = ExLlamaConfig(model_config_path)
        config.max_seq_len = max_context_length
        config.model_path = model_path
        self._model = ExLlama(config)
        self._cache = ExLlamaCache(self._model)
        self._generator = ExLlamaGenerator(self._model, self._tokenizer, self._cache)
        self._generator.settings.token_repetition_penalty_sustain = config.max_seq_len
        self._generator.disallow_tokens([self._tokenizer.eos_token_id])

    def tokens_count(self, text):
        return self._tokenizer.encode(text).shape[-1]

    def generate(self, prompt, stop, on_stream=None):
        self._generator.settings.temperature = self.temperature
        self._generator.settings.top_p = self.top_p
        self._generator.settings.top_k = self.top_k
        self._generator.settings.typical = 0.0
        self._generator.settings.token_repetition_penalty_max = self.rep_pen

        ids = self._generator.tokenizer.encode(prompt, max_seq_len=self.max_context_length)
        ids = ids[:, -(self.max_context_length-self.max_length):]
        self._generator.gen_begin_reuse(ids)
        initial_len = self._generator.sequence[0].shape[0]

        def generate():
            token = self._generator.gen_single_token()
            if token.item() == self._generator.tokenizer.eos_token_id:
                return None
            return self._generator.tokenizer.decode(self._generator.sequence[0][initial_len:])

        result = self.process(generate, stop, on_stream)
        self._generator.end_beam_search()
        return result
