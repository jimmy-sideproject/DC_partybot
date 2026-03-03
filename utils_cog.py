import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import json
import os
from datetime import datetime, timedelta
from config import REMINDERS_DATA_PATH, DATA_DIR
import logging
from pathlib import Path
from typing import Literal

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tree = bot.tree
        self.reminders = {}
        self.logger = logging.getLogger(__name__)
        self.load_reminders()
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()
        self.logger.info("Utils Cog 已卸載")

    def load_reminders(self):
        """載入提醒事項"""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            if not Path(REMINDERS_DATA_PATH).exists():
                with open(REMINDERS_DATA_PATH, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                self.reminders = {}
                return

            with open(REMINDERS_DATA_PATH, "r", encoding="utf-8") as f:
                self.reminders = json.load(f)
            self.logger.info(f"已載入提醒事項")

        except Exception as e:
            self.logger.error(f"載入提醒事項失敗: {e}")
            self.reminders = {}

    def save_reminders(self):
        """儲存提醒事項"""
        try:
            os.makedirs(os.path.dirname(REMINDERS_DATA_PATH), exist_ok=True)
            with open(REMINDERS_DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"儲存提醒事項失敗: {e}")

    def calculate_next_time(self, current_time: datetime, repeat_mode: str) -> datetime:
        """計算下一次提醒時間"""
        if repeat_mode == "daily":
            return current_time + timedelta(days=1)
        elif repeat_mode == "weekly":
            return current_time + timedelta(weeks=1)
        elif repeat_mode == "monthly":
            # 簡單處理：月份+1，若溢出則跳到底
            try:
                # 計算下個月的年份和月份
                next_month = current_time.month + 1
                next_year = current_time.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                
                # 嘗試設定日期，如果日期無效（如 1/31 -> 2/31），則抓該月最後一天
                day = current_time.day
                try:
                    return current_time.replace(year=next_year, month=next_month, day=day)
                except ValueError:
                    # 處理 2/28, 4/30 等情況
                    # 如果原日期是 31 號，但在 2 月只有 28 號，則設為 2/28
                    if day > 28:
                        # 找到該月最後一天
                        last_day_of_month = (datetime(next_year, next_month + 1, 1) - timedelta(days=1)).day if next_month < 12 else 31
                        return current_time.replace(year=next_year, month=next_month, day=min(day, last_day_of_month))
                    else:
                        raise # 應該不會發生
            except Exception as e:
                self.logger.error(f"計算每月重複時發生錯誤: {e}")
                return current_time + timedelta(days=30) # fallback
        return None

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        """檢查提醒事項"""
        try:
            now = datetime.now()
            # 這裡我們需要比對所有提醒的時間
            # 由於提醒是以 "YYYY-MM-DD HH:MM" 為 key 儲存
            
            times_to_process = []
            keys_to_remove = []

            for time_str, reminders in list(self.reminders.items()):
                try:
                    reminder_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    # 如果時間到了或過去了
                    if reminder_time <= now:
                        times_to_process.append((time_str, reminders))
                        keys_to_remove.append(time_str)
                except ValueError:
                    continue

            for time_str, reminders in times_to_process:
                for reminder in reminders:
                    channel_id = reminder.get("channel_id")
                    user_id = reminder.get("user_id")
                    message = reminder.get("message")
                    repeat = reminder.get("repeat", "none")
                    
                    # 發送提醒
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            embed = discord.Embed(
                                title="⏰ 提醒時間到！",
                                description=message,
                                color=discord.Color.gold(),
                                timestamp=now,
                            )
                            repeat_text = {"daily": "每天", "weekly": "每週", "monthly": "每月", "none": "不重複"}.get(repeat, "不重複")
                            embed.set_footer(text=f"循環模式: {repeat_text}")
                            
                            await channel.send(content=f"<@{user_id}>", embed=embed)
                            self.logger.info(f"已發送提醒給用戶 {user_id}: {message}")
                        except Exception as e:
                            self.logger.error(f"發送提醒失敗 Channel={channel_id}: {e}")
                    else:
                        self.logger.warning(f"找不到提醒頻道: {channel_id}")

                    # 處理循環
                    if repeat != "none":
                        try:
                            current_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                            next_dt = self.calculate_next_time(current_dt, repeat)
                            
                            if next_dt:
                                next_time_str = next_dt.strftime("%Y-%m-%d %H:%M")
                                
                                if next_time_str not in self.reminders:
                                    self.reminders[next_time_str] = []
                                
                                # 加入新的提醒
                                new_reminder = reminder.copy()
                                # 這裡不需要修改 user_id, channel_id, repeat
                                self.reminders[next_time_str].append(new_reminder)
                                self.logger.info(f"已排程下一次提醒 ({repeat}): {next_time_str}")
                        except Exception as e:
                            self.logger.error(f"設定下一次提醒失敗: {e}")

            # 移除已處理的舊時間 key
            # 注意：如果有循環提醒，前面已經把新的時間加進去了，所以這裡可以放心地刪除舊的 key
            if keys_to_process := [k for k in keys_to_remove if k in self.reminders]:
                for k in keys_to_process:
                    del self.reminders[k]
                self.save_reminders()

        except Exception as e:
            self.logger.error(f"檢查提醒迴圈錯誤: {e}")

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="remind", description="設定提醒 (格式: [YYYY-]MM-DD HH:MM)")
    @app_commands.describe(
        time_str="時間 (格式: 01-01 12:00 或 2024-01-01 12:00)",
        message="提醒內容",
        repeat_mode="重複模式 (預設: 不重複)"
    )
    @app_commands.choices(repeat_mode=[
        app_commands.Choice(name="不重複", value="none"),
        app_commands.Choice(name="每天", value="daily"),
        app_commands.Choice(name="每週", value="weekly"),
        app_commands.Choice(name="每月", value="monthly")
    ])
    async def remind(
        self, 
        interaction: discord.Interaction, 
        time_str: str, 
        message: str, 
        repeat_mode: app_commands.Choice[str] = None
    ):
        """設定提醒"""
        try:
            # 處理時間格式
            reminder_time = None
            try:
                # 嘗試完整格式 YYYY-MM-DD HH:MM
                try:
                    reminder_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    # 嘗試簡短格式 MM-DD HH:MM，自動補上今年年份
                    current_year = datetime.now().year
                    reminder_time = datetime.strptime(f"{current_year}-{time_str}", "%Y-%m-%d %H:%M")

                if reminder_time < datetime.now():
                    await interaction.response.send_message("⚠️ 時間不能設為過去！", ephemeral=True)
                    return
                
                # 更新 time_str 為完整格式，以便儲存
                time_str = reminder_time.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                await interaction.response.send_message("⚠️ 時間格式錯誤！請使用 MM-DD HH:MM (例如 01-01 12:00) 或完整格式", ephemeral=True)
                return

            repeat_value = repeat_mode.value if repeat_mode else "none"
            repeat_name = repeat_mode.name if repeat_mode else "不重複"
            
            # 確保 key 存在
            if time_str not in self.reminders:
                self.reminders[time_str] = []
            
            self.reminders[time_str].append({
                "user_id": interaction.user.id,
                "channel_id": interaction.channel_id,
                "message": message,
                "repeat": repeat_value,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.save_reminders()
            
            embed = discord.Embed(title="✅ 提醒已設定", color=discord.Color.green())
            embed.add_field(name="時間", value=time_str)
            embed.add_field(name="內容", value=message)
            embed.add_field(name="重複模式", value=repeat_name)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            self.logger.error(f"設定提醒失敗: {e}")
            await interaction.response.send_message(f"設定失敗: {str(e)}", ephemeral=True)

    @app_commands.command(name="list_reminders", description="列出我設定的提醒")
    async def list_reminders(self, interaction: discord.Interaction):
        """列出使用者的提醒"""
        user_reminders = []
        user_id = interaction.user.id
        
        for time_str, reminders in self.reminders.items():
            for i, rem in enumerate(reminders):
                if rem.get("user_id") == user_id:
                     user_reminders.append({
                         "time": time_str, 
                         "message": rem.get("message"),
                         "repeat": rem.get("repeat", "none"),
                     })
        
        if not user_reminders:
            await interaction.response.send_message("📭 你目前沒有設定任何提醒。", ephemeral=True)
            return

        # 排序
        user_reminders.sort(key=lambda x: x["time"])
        
        embed = discord.Embed(title="📋 我的提醒列表", color=discord.Color.blue())
        description = ""
        for i, rem in enumerate(user_reminders):
             repeat_text = {"daily": "每天", "weekly": "每週", "monthly": "每月", "none": "不重複"}.get(rem["repeat"], "不重複")
             description += f"**{i+1}.** `{rem['time']}` - {rem['message']} ({repeat_text})\n"
        
        embed.description = description
        embed.set_footer(text="使用 /delete_reminder <編號> 來刪除提醒")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="delete_reminder", description="刪除提醒")
    @app_commands.describe(index="要刪除的提醒編號 (請先使用 /list_reminders 查看)")
    async def delete_reminder(self, interaction: discord.Interaction, index: int):
        """刪除提醒"""
        user_id = interaction.user.id
        # 使用列表儲存，方便排序與 index 對應
        user_reminders_list_objs = [] 
        
        # 為了正確對應 index，必須使用與 list_reminders 相同的邏輯
        for time_str, reminders in self.reminders.items():
            for i, rem in enumerate(reminders):
                if rem.get("user_id") == user_id:
                     user_reminders_list_objs.append({
                         "key": time_str,
                         "data": rem
                     })
        
        # 排序
        user_reminders_list_objs.sort(key=lambda x: x["key"])

        if index < 1 or index > len(user_reminders_list_objs):
            await interaction.response.send_message(f"❌ 無效的編號。請輸入 1 到 {len(user_reminders_list_objs)} 之間的數字。", ephemeral=True)
            return

        target_obj = user_reminders_list_objs[index-1]
        target_key = target_obj["key"]
        target_data = target_obj["data"]

        # 執行刪除
        if target_key in self.reminders:
            reminders_list = self.reminders[target_key]
            
            # 因為字典中的物件參考是相同的，可以直接 remove
            if target_data in reminders_list:
                reminders_list.remove(target_data)
                
                # 如果該時間點沒有其他提醒了，清理 key
                if not reminders_list:
                    del self.reminders[target_key]
                
                self.save_reminders()
                
                message_preview = target_data.get('message', '無內容')
                await interaction.response.send_message(f"✅ 已刪除提醒 #{index}：`{target_key}` - {message_preview}", ephemeral=True)
            else:
                 await interaction.response.send_message("❌ 刪除失敗，該提醒可能已被刪除。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 刪除失敗，該時間點的提醒已不存在。", ephemeral=True)

    @app_commands.command(name="draw", description="從伺服器或語音頻道抽選使用者")
    @app_commands.describe(
        count="抽取人數",
        source="來源 (選擇範圍)"
    )
    @app_commands.choices(source=[
        app_commands.Choice(name="目前語音頻道", value="voice"),
        app_commands.Choice(name="目前文字頻道", value="text"),
        app_commands.Choice(name="整個伺服器", value="guild")
    ])
    async def draw(
        self, 
        interaction: discord.Interaction, 
        count: int, 
        source: app_commands.Choice[str] = None
    ):
        """抽取使用者"""
        # 延遲回應，因為如果成員很多可能需要時間
        await interaction.response.defer()

        if count < 1:
            await interaction.followup.send("❌ 人數必須大於 1", ephemeral=True)
            return

        target_members = []
        source_name = ""

        # 決定來源
        if source:
            source_value = source.value
        else:
            # 自動偵測：如果在語音且有人，則選語音，否則選文字頻道
            if interaction.user.voice and interaction.user.voice.channel:
                source_value = "voice"
            else:
                source_value = "text" # 預設

        if source_value == "voice":
            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.followup.send("❌ 你不在語音頻道中！", ephemeral=True)
                return
            channel = interaction.user.voice.channel
            target_members = channel.members
            source_name = f"🔊 語音頻道: {channel.name}"
            
        elif source_value == "text":
            channel = interaction.channel
            # 文字頻道的成員獲取可能需要權限或只拿到快取
            # 嘗試使用 channel.members (如果有的話)
            if hasattr(channel, "members"):
                 target_members = channel.members 
            else:
                 # fallback to guild members in this channel?
                 # 對於大型伺服器可能不準確
                 target_members = [m for m in interaction.guild.members if m.permissions_in(channel).read_messages]
            source_name = f"📝 文字頻道: {channel.name}"
            
        elif source_value == "guild":
            if not interaction.guild:
                await interaction.followup.send("❌ 請在伺服器中使用此指令", ephemeral=True)
                return
            target_members = interaction.guild.members
            source_name = f"🏰 伺服器: {interaction.guild.name}"

        # 過濾機器人
        valid_members = [m for m in target_members if not m.bot]
        
        if len(valid_members) < count:
            await interaction.followup.send(
                f"❌ 人數不足！來源 {source_name} 只有 {len(valid_members)} 位人類成員 (機器人已排除)", 
                ephemeral=True
            )
            return

        winners = random.sample(valid_members, count)
        
        # 格式化輸出，避免太多人時刷屏
        if count <= 20:
            winners_mentions = "\n".join([f"🎉 {m.mention}" for m in winners])
        else:
            winners_mentions = f"共抽出 {count} 人\n" + ", ".join([m.display_name for m in winners])

        embed = discord.Embed(
            title="🎲 抽籤結果",
            description=winners_mentions,
            color=discord.Color.random()
        )
        embed.set_footer(text=f"來源: {source_name} | 總人數: {len(valid_members)} | 抽取: {count}")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utils(bot))
