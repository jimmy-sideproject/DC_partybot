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
    bot.join_video_voice_channel_id = 100
    bot.join_video_text_channel_id = 200
    bot.join_video_path = video_path
    target_channel = MagicMock(spec=discord.TextChannel)
    target_channel.send = AsyncMock()
    bot.get_channel = MagicMock(return_value=target_channel)

    try:
        await bot.on_voice_state_update(
            SimpleNamespace(bot=False),
            SimpleNamespace(channel=None),
            SimpleNamespace(channel=SimpleNamespace(id=100)),
        )
    finally:
        await bot.close()

    target_channel.send.assert_awaited_once()
    sent_file = target_channel.send.await_args.kwargs["file"]
    assert sent_file.filename == video_path.name
