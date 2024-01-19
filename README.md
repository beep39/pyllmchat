# pyllmchat

Python api for chatting with [chub.ai](https://www.chub.ai/) characters inspired by [SillyTavern](https://github.com/SillyTavern/SillyTavern) 

Currently supported backends:
- [Tabbyapi](https://github.com/theroyallab/tabbyAPI)
- [LLamacpp](https://github.com/ggerganov/llama.cpp) (via api)
- [KoboldAI](https://github.com/LostRuins/koboldcpp) (via api)
- [exllama](https://github.com/turboderp/exllama) can be [installed with pip](https://github.com/jllllll/exllama) or dropped in project root.
- [exllamav2](https://github.com/turboderp/exllamav2) can be dropped in project root.

Character cards can be loaded with <code>chat.char.load</code>

Prompt used in chat uses <code>chat.template</code>

Built-in variables are similar to SillyTavern. Additional variables:

<code>{{history}}</code> inserts chat history truncated to <code>max_context_length</code>

<code>{{template}}</code> can be used with <code>chat.prompt</code> to insert filled <code>chat.template</code>

Custom variables can be registered with <code>chat.reg_var</code> to inject dynamic information into context.

<code>chat.prompt</code> supports same template format and can be used to extract information about character state/intentions.

<code>chat.emotion</code> can be used to clasify emotion of character response.

Multiple chat instances can share same backend. <code>chat.say</code> can also be used to insert replies from other chat instances to simulate group chats.

Example console chat: [example_chat.py](https://github.com/beep39/pyllmchat/blob/main/example_chat.py)

I use it with [pymikuvr](https://github.com/beep39/pymikuvr) to tinker with mmd characters in VR
