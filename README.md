# pyllmchat

This project is a python wrapper for llm that can use [chub.ai](https://www.chub.ai/) character cards.

Currently supported backends:
- [KoboldAI](https://github.com/LostRuins/koboldcpp) (via api)
- [exllama](https://github.com/turboderp/exllama) can be [installed with pip](https://github.com/jllllll/exllama) or dropped in project root

Prompt used in chat uses <code>chat.template</code>

Built-in variables are similar to [SillyTavern](https://github.com/SillyTavern/SillyTavern) 

<code>{{template}}</code> variable can be used with <code>chat.prompt</code> to insert filled <code>chat.template</code>

<code>{{history}}</code> inserts chat history truncated to <code>max_context_length</code>

Additional variables can be registered with <code>chat.reg_var</code> and can be used to inject dynamic information into context

<code>chat.prompt</code> also uses template and can be used to extract information about character state/intentions.

<code>chat.emotion</code> can be used to clasify emotion of character response

Multiple chat instances can share same backend. <code>chat.say</code> can also be used to insert replies from other chat instances to simulate group chats

Example console chat: [example_chat.py](https://github.com/beep39/pyllmchat/blob/main/example_chat.py)

I use it with [pymikuvr](https://github.com/beep39/pymikuvr) to tinker with mmd characters in vr
