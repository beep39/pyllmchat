from chat import chat
from backend_kobold import backend_kobold
#from backend_exllama import backend_exllama

backend = backend_kobold('http://localhost:5001/api', 2048)
#backend = backend_exllama('Pygmalion-13B-SuperHOT-8K-GPTQ', 8196)
backend.max_length = 100
chat = chat(backend)

if not 'Miku' in chat.char.list():
    chat.char.download('https://chub.ai/characters/pitanon/miku-d1b931c6')
chat.char.load('Miku')

def on_stream(text, final, offset):
    print(text[offset:], end='\n' if final else '', flush=True)
#on_stream = None

greeting = chat.start()
if greeting:
    print(chat.char.name + ':', greeting)
while(True):
    prompt = input(chat.user.name + ': ')
    if on_stream:
        print(chat.char.name + ': ', end='')
        chat.say(prompt, on_stream)
    else:
        print(chat.char.name + ':', chat.say(prompt))
