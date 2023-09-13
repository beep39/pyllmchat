from backend import backend
from random import random
import gc, torch

local_path = 'exllamav2'  #folder in project root
import sys
if not local_path in sys.path:
    sys.path.append(local_path)
from exllamav2 import ExLlamaV2, ExLlamaV2Cache, ExLlamaV2Config, ExLlamaV2Tokenizer
from exllamav2.generator import ExLlamaV2Sampler

class backend_exllamav2(backend):
    def __init__(self, model_directory, max_context_length=None, gpu_split=None):
        super().__init__()
        config = ExLlamaV2Config()
        config.model_dir = model_directory
        config.prepare()
        if max_context_length:
            self.max_context_length = max_context_length
            config.max_seq_len = max_context_length
        else:
            self.max_context_length = config.max_seq_len
        self._model = ExLlamaV2(config)
        self._model.load(gpu_split)
        self._cache = ExLlamaV2Cache(self._model)
        self._tokenizer = ExLlamaV2Tokenizer(config)
        self._settings = ExLlamaV2Sampler.Settings()

    def tokens_count(self, text):
        return self._tokenizer.encode(text).shape[-1]

    def generate(self, prompt, stop, on_stream=None):
        self._settings.temperature = self.temperature
        self._settings.top_p = self.top_p
        self._settings.top_k = self.top_k
        self._settings.typical = self.typical
        self._settings.token_repetition_penalty = self.rep_pen
        self._settings.token_repetition_range = -1

        ids = self._tokenizer.encode(prompt)
        ids = ids[:, -(self.max_context_length-self.max_length):]
        initial_len = ids.shape[-1]
        self._cache.current_seq_len = 0
        self._model.forward(ids[:, :-1], self._cache, input_mask=None, preprocess_only=True)

        def generate():
            nonlocal ids
            logits = self._model.forward(ids[:, -1:], self._cache, input_mask=None).float().cpu()
            token, _ = ExLlamaV2Sampler.sample(logits, self._settings, ids, random())
            ids = torch.cat([ids, token], dim=1)
            if token.item() == self._tokenizer.eos_token_id:
                return None
            return self._tokenizer.decode(ids[:, initial_len:])[0]

        result = self.process(generate, stop, on_stream)
        return result

    def unload(self):
        if self._model is None:
            return

        self._model = None
        self._generator = None
        gc.collect()
        torch.cuda.empty_cache()
