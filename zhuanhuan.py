import re
import time
from urllib import parse

from pyrogram.types import Message

from pagermaid.listener import listener
from pagermaid.utils import client as http_client, alias_command

backend = "https://api.gdmm.ml/"
config = "https://paste.wmlabs.net/raw/f5f7ff8ec169"

@listener(is_plugin=True, outgoing=True, command=alias_command("zhuanhuan"),
          description='转换节点和订阅链接',
          parameters='<url / node>')
async def convertsub(_, msg: Message):
    try:
        message_raw = msg.reply_to_message and (msg.reply_to_message.caption or msg.reply_to_message.text) or (msg.caption or msg.text)
        await msg.edit('转换中...')
        url_list = re.findall("[-A-Za-z0-9+&@#/%?=~_|!:,.;]+://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]", message_raw)
        url_list = list(set(url_list))
        result = "[[订阅链接]]("+ backend + "sub?target=clash&url=" + parse.quote_plus(url_list[0])
        for url in url_list[1:]:
            if len(url) != 0:
                result = result + "|" + parse.quote_plus(url)
        result = result + "&insert=false&config=" + parse.quote_plus(config) + "&emoji=true&list=false&tfo=false&expand=true&scv=true&fdn=false&new_name=true)"
        await msg.edit(result)
    except:
        await msg.edit('参数错误')
