class backend():
    def __init__(self):
        self.max_context_length = 2048
        self.max_length = 150
        self.temperature = 1.1
        self.rep_pen = 1.11
        self.rep_pen_range = 500
        self.top_k = 0
        self.top_p = 1.0
        self.min_p = 0.95
        self.typical = 0.0
        self._cancel = False

    def tokens_count(self, text):
        return len(text)

    def check_length(self, token_count):
        return token_count <= self.max_context_length

    def generate(self, prompt, stop, on_stream=None):
        return None

    def cancel(self):
        self._cancel = True

    def process(self, generate, stop, on_stream=None):
        def match_stop(text):
            e = len(stop)
            for i in range(1,e+1):
                if text.endswith(stop[:i]):
                    if i == e:
                        raise Exception
                    return True
            return False

        offset = 0
        result = ''
        self._cancel = False
        for _ in range(self.max_length):
            if self._cancel:
                break

            generated = generate()
            if generated == None:
                break
            try:
                if match_stop(generated):
                    continue
            except:
                result = generated[:-len(stop)]
                break
            result = generated
            if on_stream:
                on_stream(result, False, offset)
            offset = len(result)
        if on_stream:
            on_stream(result, True, offset)
        return result
