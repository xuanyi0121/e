import contextlib

from PIL import Image
from os.path import exists
from httpx import ReadTimeout

from pagermaid.listener import listener
from pagermaid.single_utils import safe_remove
from pagermaid.enums import Client, Message, AsyncClient
from pagermaid.utils import lang, pip_install

pip_install("speedtest-cli", alias="speedtest")

from speedtest import (
    Speedtest,
    ShareResultsConnectFailure,
    ShareResultsSubmitFailure,
    NoMatchedServers,
    SpeedtestBestServerFailure,
    SpeedtestHTTPError,
)


def unit_convert(byte):
    """Converts byte into readable formats."""
    power = 1000
    zero = 0
    units = {0: "", 1: "Kb/s", 2: "Mb/s", 3: "Gb/s", 4: "Tb/s"}
    while byte > power:
        byte /= power
        zero += 1
    return f"{round(byte, 2)} {units[zero]}"


async def run_speedtest(request: AsyncClient, message: Message):
    test = Speedtest()
    server = int(message.arguments) if len(message.parameter) == 1 else None
    if server:
        servers = test.get_closest_servers()
        for i in servers:
            if i["id"] == str(server):
                test.servers = [i]
                break
    test.get_best_server(servers=test.servers)
    test.download()
    test.upload()
    with contextlib.suppress(ShareResultsConnectFailure):
        test.results.share()
    result = test.results.dict()
    des = (
        f"**🌈测速服务** \n"
        f"**测速点:** `{result['server']['name']} - "
        f"{result['server']['cc']}` \n"
        f"**服务商:** `{result['server']['sponsor']}` \n"
        f"**上传:** `{unit_convert(result['upload'])}` \n"
        f"**下载:** `{unit_convert(result['download'])}` \n"
        f"**延迟:** `{result['ping']}` \n"
        f"**测试时间: **`{result['timestamp']}`"
    )
    if result["share"]:
        data = await request.get(
            result["share"].replace("http:", "https:"), follow_redirects=True
        )
        with open("speedtest.png", mode="wb") as f:
            f.write(data.content)
        with contextlib.suppress(Exception):
            img = Image.open("speedtest.png")
            c = img.crop((17, 11, 727, 389))
            c.save("speedtest.png")
    return des, "speedtest.png" if exists("speedtest.png") else None


async def get_all_ids():
    test = Speedtest()
    servers = test.get_closest_servers()
    return (
        (
            "附近的测速点有：\n\n"
            + "\n".join(
                f"`{i['id']}` - `{int(i['d'])}km` - `{i['name']}` - `{i['sponsor']}`"
                for i in servers
            ),
            None,
        )
        if servers
        else ("附近没有测速点", None)
    )


@listener(
    command="speedtest",
    description=lang("speedtest_des"),
    parameters="(Server ID/测速点列表)",
)
async def speedtest(client: Client, message: Message, request: AsyncClient):
    """Tests internet speed using speedtest."""
    if message.arguments == "测速点列表":
        msg = message
    else:
        msg: Message = await message.edit(lang("speedtest_processing"))
    try:
        if message.arguments == "测速点列表":
            des, photo = await get_all_ids()
        else:
            des, photo = await run_speedtest(request, message)
    except SpeedtestHTTPError:
        return await msg.edit(lang("speedtest_ConnectFailure"))
    except (ValueError, TypeError):
        return await msg.edit(lang("arg_error"))
    except (SpeedtestBestServerFailure, NoMatchedServers):
        return await msg.edit(lang("speedtest_ServerFailure"))
    except (ShareResultsSubmitFailure, RuntimeError, ReadTimeout):
        return await msg.edit(lang("speedtest_ConnectFailure"))
    if not photo:
        return await msg.edit(des)
    try:
        await client.send_photo(
            message.chat.id,
            photo,
            caption=des,
            reply_to_message_id=message.reply_to_top_message_id
            or message.reply_to_message_id,
        )
    except Exception:
        return await msg.edit(des)
    await msg.safe_delete()
    safe_remove(photo)
