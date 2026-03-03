import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from dotenv import load_dotenv
import os
import logging
import sys
from pathlib import Path
import ssl
import certifi

# 設置日誌
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "discord_bot.log"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def setup_ssl():
    """設置 SSL 驗證環境"""
    try:
        # 設置不驗證 SSL 憑證
        ssl._create_default_https_context = ssl._create_unverified_context
        logger.info("已設置 SSL 憑證上下文為不驗證模式")
    except Exception as e:
        logger.error(f"設置 SSL 憑證時發生錯誤: {str(e)}")


def load_token():
    """載入並驗證 Discord Token"""
    # 設置 SSL 環境
    setup_ssl()

    # 嘗試載入 .env 或 .ENV 檔案
    env_files = [".env", ".ENV"]
    for env_file in env_files:
        if Path(env_file).exists():
            load_dotenv(env_file, override=True)
            logger.info(f"已載入環境變數: {env_file}")
            break

    token = os.getenv("DISCORD_TOKEN", "").strip()

    if not token:
        logger.error("找不到 DISCORD_TOKEN 環境變數或變數為空")
        logger.error("請確認 .env 或 .ENV 檔案中包含有效的 DISCORD_TOKEN")
        return None

    if token.startswith("="):
        token = token[1:].strip()

    if not (token.startswith("MT") or token.startswith("NT")):
        logger.warning("Discord Token 格式可能不正確")
        logger.warning("一般的 Bot Token 應該以 'MT' 或 'NT' 開頭")

    # 避免在日誌中顯示敏感資訊，只顯示前5個字元和長度
    masked_token = f"{token[:5]}...（共{len(token)}字元）"
    logger.debug(f"已載入 Token: {masked_token}")
    return token


async def check_ffmpeg():
    """檢查 FFMPEG 是否可用 (已棄用)"""
    return True


class PartyBot(commands.Bot):
    async def setup_hook(self):
        """在機器人啟動前的初始化設置"""
        try:
            # 檢查 FFMPEG (已移除音樂功能，不再需要強制檢查)
            # if not await check_ffmpeg():
            #     logger.error("FFMPEG 未正確安裝，音樂功能可能無法使用")

            # 定義需要載入的 Cogs
            cog_list = [
                "utils_cog",
            ]

            # 追蹤已載入命令和失敗的 cog
            loaded_commands = set()
            failed_cogs = []

            # 載入所有 cog
            for cog in cog_list:
                try:
                    await self.load_extension(cog)
                    logger.info(f"✅ 已載入擴展: {cog}")
                except commands.errors.ExtensionFailed as e:
                    if "CommandAlreadyRegistered" in str(e):
                        logger.warning(f"⚠️ 擴展 {cog} 中的某些命令已經註冊")
                        continue
                    logger.error(f"❌ 載入擴展 {cog} 時發生錯誤: {str(e)}")
                    failed_cogs.append(cog)
                except Exception as e:
                    logger.error(f"❌ 載入擴展 {cog} 時發生錯誤: {str(e)}")
                    failed_cogs.append(cog)

            # 同步指令到 Discord
            logger.info("正在同步指令到 Discord...")
            synced_commands = await self.tree.sync()
            logger.info(f"✅ 成功同步 {len(synced_commands)} 個指令！")

            # 整理並檢查指令
            unique_commands = {}
            for cmd in self.tree.get_commands():
                if cmd.name not in unique_commands:
                    unique_commands[cmd.name] = cmd

            # 輸出註冊的指令資訊
            if unique_commands:
                logger.info("📋 已註冊的指令：")
                for cmd in unique_commands.values():
                    logger.info(f"  - /{cmd.name}: {cmd.description}")
            else:
                logger.warning("⚠️ 沒有任何指令被註冊！")

            # 輸出失敗的 cog
            if failed_cogs:
                logger.warning(f"⚠️ 以下擴展載入失敗: {', '.join(failed_cogs)}")

        except Exception as e:
            logger.error(f"❌ 設置機器人時發生錯誤: {str(e)}", exc_info=True)

    async def on_ready(self):
        """機器人啟動完成時的處理"""
        activity = discord.Activity(
            type=discord.ActivityType.listening, name="/help 獲取指令幫助"
        )
        await self.change_presence(activity=activity)
        logger.info(f"🤖 已登入為 {self.user}")
        logger.info(
            f"🔗 邀請連結: https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions=8&scope=bot%20applications.commands"
        )
        logger.info(f"🌟 機器人已在 {len(self.guilds)} 個伺服器中運行")

    async def on_error(self, event, *args, **kwargs):
        """全局錯誤處理"""
        logger.error(f"❌ 事件 {event} 發生錯誤", exc_info=True)

    async def on_guild_join(self, guild):
        """加入新伺服器時的處理"""
        logger.info(f"🎉 已加入新伺服器: {guild.name} (ID: {guild.id})")

        # 尋找可發送訊息的文字頻道
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(
                    title=f"👋 嗨！我是 {self.user.name}",
                    description="感謝邀請我加入你的伺服器！使用 `/help` 可以查看所有指令。",
                    color=discord.Color.blue(),
                )
                
                # 功能列表
                embed.add_field(
                    name="✨ 主要功能",
                    value="`/draw` - 隨機抽取成員\n`/remind` - 設定定期提醒",
                    inline=True,
                )
                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"無法在 {channel.name} 發送歡迎訊息: {e}")
                break


async def main():
    """主程式入口"""
    # 載入 Token
    token = load_token()
    if not token:
        logger.critical("❌ 無法載入 Discord Token，機器人無法啟動")
        return

    # 初始化機器人，設定完整意圖以取得所有必要的事件
    intents = discord.Intents.all()
    bot = PartyBot(
        command_prefix="!",  # 保留前綴指令，但主要使用斜線指令
        intents=intents,
        help_command=None,  # 移除默認幫助指令，改用自訂斜線指令
        activity=discord.Activity(
            type=discord.ActivityType.listening, name="載入中..."
        ),
    )

    # 設定重試參數
    max_retries = 3
    retry_delay = 60  # 秒

    # 嘗試啟動機器人
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.warning(
                    f"⏳ 重試第 {attempt + 1}/{max_retries} 次，等待 {retry_delay} 秒..."
                )
                await asyncio.sleep(retry_delay)

            logger.info("🚀 正在啟動機器人...")
            await bot.start(token)
            break

        except discord.errors.HTTPException as e:
            if e.status == 429:  # 速率限制錯誤
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ 遇到速率限制 (429)，等待後重試: {e}")
                    continue
                else:
                    logger.error("❌ 已達到最大重試次數，機器人啟動失敗")
            else:
                logger.error(f"❌ HTTP 錯誤 ({e.status}): {e}")
            break

        except discord.LoginFailure as e:
            logger.error(f"❌ 登入失敗: {e}")
            logger.error("請檢查 Discord Token 是否正確")
            break

        except Exception as e:
            logger.error(f"❌ 發生未預期的錯誤: {e}", exc_info=True)
            break

        finally:
            # 確保正常關閉連接
            if "bot" in locals() and not bot.is_closed():
                await bot.close()
                logger.info("👋 機器人已關閉連接")


def run_bot():
    """執行機器人"""
    try:
        logger.info("🏁 開始初始化機器人...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚡ 收到中斷信號，正在關閉機器人...")
    except Exception as e:
        logger.critical(f"💥 執行時發生嚴重錯誤: {e}", exc_info=True)

    logger.info("🔄 程式執行結束")


# 自定義幫助指令（斜線指令）
@app_commands.command(name="help", description="顯示所有可用的指令")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 派對機器人指令清單",
        description="以下是所有可用的指令，所有指令都使用斜線 `/` 開頭",
        color=discord.Color.blue(),
    )

    # 娛樂功能
    embed.add_field(
        name="🎮 娛樂指令",
        value=(
            "`/draw <人數>` - 抽取幸運兒 (支援語音/文字頻道/全伺服器)\n"
            "`/remind <時間> <訊息> [重複模式]` - 設定提醒\n"
            "`/list_reminders` - 查看我的提醒\n"
            "`/delete_reminder <編號>` - 刪除提醒"
        ),
        inline=False,
    )

    embed.set_footer(text="如有問題請聯繫伺服器管理員")

    await interaction.response.send_message(embed=embed, ephemeral=True)


# 註冊幫助指令
def setup_help_command(bot):
    bot.tree.add_command(help_command)


if __name__ == "__main__":
    run_bot()
