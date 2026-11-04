import json

import pytest

from main import should_send_voice_join_video


@pytest.mark.parametrize(
    (
        "is_bot",
        "before_channel_id",
        "after_channel_id",
        "trigger_channel_id",
        "expected",
    ),
    [
        (False, None, 100, 100, True),
        (False, 200, 100, 100, True),
        (False, 100, None, 100, False),
        (False, 100, 100, 100, False),
        (False, None, 200, 100, False),
        (True, None, 100, 100, False),
        (False, None, 100, None, False),
    ],
)
def test_should_send_video_only_when_human_enters_trigger_channel(
    is_bot, before_channel_id, after_channel_id, trigger_channel_id, expected
):
    assert (
        should_send_voice_join_video(
            is_bot, before_channel_id, after_channel_id, trigger_channel_id
        )
        is expected
    )


@pytest.mark.asyncio
async def test_voice_join_sends_video_file_to_target_channel(tmp_path):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock

    import discord

    from main import PartyBot

    video_path = tmp_path / "voice_channel_join.mp4"
    video_path.write_bytes(b"test video")
    bot = PartyBot(command_prefix="!", intents=discord.Intents.none())
    bot.join_video_config_path = tmp_path / "join_video_channels.json"
    bot.join_video_channels = {"1": {"voice_channel_id": 100, "text_channel_id": 200}}
    bot.join_video_path = video_path
    target_channel = MagicMock(spec=discord.TextChannel)
    target_channel.send = AsyncMock()
    bot.get_channel = MagicMock(return_value=target_channel)

    try:
        await bot.on_voice_state_update(
            SimpleNamespace(bot=False, guild=SimpleNamespace(id=1)),
            SimpleNamespace(channel=None),
            SimpleNamespace(channel=SimpleNamespace(id=100)),
        )
    finally:
        await bot.close()

    target_channel.send.assert_awaited_once()
    sent_file = target_channel.send.await_args.kwargs["file"]
    assert sent_file.filename == video_path.name


@pytest.mark.asyncio
async def test_join_video_settings_persist_per_guild(tmp_path):
    import discord

    from main import PartyBot

    bot = PartyBot(command_prefix="!", intents=discord.Intents.none())
    bot.join_video_config_path = tmp_path / "join_video_channels.json"
    bot.join_video_channels = {}

    try:
        assert bot.set_join_video_channels(1, 100, 200)
        assert bot.set_join_video_channels(2, 300, 400)
        persisted = json.loads(bot.join_video_config_path.read_text(encoding="utf-8"))
        assert persisted == {
            "1": {"voice_channel_id": 100, "text_channel_id": 200},
            "2": {"voice_channel_id": 300, "text_channel_id": 400},
        }

        bot.join_video_channels = bot._load_join_video_channels()
        assert bot.join_video_channels["2"]["voice_channel_id"] == 300
        assert bot.clear_join_video_channels(1)
        assert set(bot.join_video_channels) == {"2"}

        bot.join_video_config_path.write_text("{", encoding="utf-8")
        bot.join_video_config_valid = True
        bot.join_video_channels = bot._load_join_video_channels()
        assert not bot.join_video_config_valid
        assert not bot.set_join_video_channels(3, 500, 600)
        assert bot.join_video_config_path.read_text(encoding="utf-8") == "{"
    finally:
        await bot.close()


@pytest.mark.asyncio
async def test_join_video_commands_are_loaded_as_slash_commands():
    import discord

    from main import PartyBot

    bot = PartyBot(command_prefix="!", intents=discord.Intents.none())
    try:
        await bot.load_extension("utils_cog")
        command_names = {command.name for command in bot.tree.get_commands()}
        assert "set_join_video" in command_names
        assert "clear_join_video" in command_names
    finally:
        if bot.get_cog("Utils"):
            await bot.unload_extension("utils_cog")
        await bot.close()
