from highrise import BaseBot, __main__, CurrencyItem, Item, Position, AnchorPosition, SessionMetadata, User
from highrise.__main__ import BotDefinition
from asyncio import run as arun
from json import load, dump
import asyncio
import random
import os
from highrise.models import *
from highrise.webapi import *
from functions.equip import equip
from functions.remove import remove
from config import BIRTHDAY_GIRL_USERNAME, PICKUP_LINE_INTERVAL_MINUTES, CUSTOM_PICKUP_LINES
from dotenv import load_dotenv



# Загрузка переменных окружения
load_dotenv()

class Bot(BaseBot):
    def __init__(self):
        super().__init__()
        self.bot_id = None
        self.owner_id = None
        self.bot_status = False
        self.pickup_line_interval = PICKUP_LINE_INTERVAL_MINUTES * 60  # Перевести в секунды
        self.pickup_line_task = None
        self.birthday_girl_username = BIRTHDAY_GIRL_USERNAME
        self.bot_position = None
        self.load_bot_data()
        
        # Романтические фразы для именинницы
        self.pickup_lines = [
            "С днём рождения самую прекрасную душу в этой комнате! 💕",
            "Каждое мгновение с тобой — это праздник, особенно сегодня! 🎉",
            "Ты не просто взрослеешь, ты становишься всё прекраснее с каждым годом! ✨",
            "Сегодня не просто твой день рождения, это годовщина того, как мир стал красивее! 💖",
            "Если бы я мог подарить тебе что-то, это была бы возможность увидеть себя моими глазами! 👀💕",
            "Ты причина, по которой моё сердце бьётся чаще, именинница! 💓",
            "Ещё один год — ещё больше твоей потрясающей красоты! 🌟",
            "Твоя улыбка освещает комнату ярче всех свечей на торте! 🕯️✨",
            "Я влюбляюсь в тебя всё больше с каждым днём, особенно в твой особенный день! 💘",
            "Ты не просто стала старше на год, ты стала ещё удивительнее! 🎂💕",
            "С днём рождения моего самого любимого человека во всей вселенной! 🌍💖",
            "Ты делаешь каждый день праздником, но сегодня особенно! 🎊",
            "Твоя красота затмевает все украшения на празднике! 🎈✨",
            "Я так счастлив отмечать ещё один год твоего чудесного существования! 🍀💕",
            "Говорят, что ты красивая женщина, но у меня нет слов, чтобы описать тебя — красота это слишком мало! 🍷💖"
        ] + CUSTOM_PICKUP_LINES  # Добавить пользовательские фразы из config

    def load_bot_data(self):
        """Загрузить данные о позиции бота из файла"""
        self.create_data_file()
        try:
            with open("./bot_data.json", "r") as file:
                data = load(file)
                pos_data = data.get("bot_position", {"x": 0, "y": 0, "z": 0, "facing": "FrontRight"})
                self.bot_position = Position(pos_data["x"], pos_data["y"], pos_data["z"], pos_data["facing"])
        except Exception as e:
            print(f"Ошибка при загрузке данных бота: {e}")
            self.bot_position = Position(0, 0, 0, "FrontRight")

    def create_data_file(self):
        """Создать файл данных, если он не существует"""
        if not os.path.exists("./bot_data.json"):
            default_data = {"bot_position": {"x": 0, "y": 0, "z": 0, "facing": "FrontRight"}}
            with open("./bot_data.json", "w") as file:
                dump(default_data, file)

    async def set_bot_position(self, user_id):
        """Установить позицию бота на месте игрока"""
        try:
            response = await self.highrise.get_room_users()
            if isinstance(response, GetRoomUsersRequest.GetRoomUsersResponse):
                room_users = response.content
                position = None
                
                for room_user, pos in room_users:
                    if user_id == room_user.id and isinstance(pos, Position):
                        position = pos
                        break
                
                if position:
                    # Сохранить позицию в файл
                    with open("./bot_data.json", "r+") as file:
                        data = load(file)
                        file.seek(0)
                        data["bot_position"] = {
                            "x": position.x,
                            "y": position.y,
                            "z": position.z,
                            "facing": position.facing
                        }
                        dump(data, file)
                        file.truncate()
                    
                    # Обновить позицию бота
                    self.bot_position = position
                    set_position = Position(position.x, position.y + 0.0000001, position.z, facing=position.facing)
                    await self.highrise.teleport(self.bot_id, set_position)
                    await self.highrise.teleport(self.bot_id, position)
                    await self.highrise.walk_to(position)
                    
                    return "Bot position updated! 📍"
                else:
                    return "Failed to get your position! 🤔"
        except Exception as e:
            print(f"Error setting bot position: {e}")
            return f"Error setting position: {e}"

    async def place_bot(self):
        """Place bot at saved position"""
        while not self.bot_status:
            await asyncio.sleep(0.5)
        
        try:
            if self.bot_position and self.bot_position != Position(0, 0, 0, 'FrontRight'):
                await self.highrise.teleport(self.bot_id, self.bot_position)
        except Exception as e:
            print(f"Error placing bot: {e}")

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        self.bot_id = session_metadata.user_id
        self.owner_id = session_metadata.room_info.owner_id
        self.bot_status = True
        
        await self.highrise.chat("Birthday Bot activated! 🎉 Ready to celebrate! 💕")
        
        # Place bot at saved position
        await self.place_bot()
        
        # Start the pickup line task
        await self.start_pickup_line_task()
        print("Birthday bot started...")

    async def start_pickup_line_task(self):
        """Start the periodic pickup line task"""
        if self.pickup_line_task:
            self.pickup_line_task.cancel()
        
        self.pickup_line_task = asyncio.create_task(self.send_pickup_lines_periodically())

    async def send_pickup_lines_periodically(self):
        """Send romantic pickup lines every interval"""
        while True:
            try:
                await asyncio.sleep(self.pickup_line_interval)
                
                # Check if birthday girl is in the room
                try:
                    response = await self.highrise.get_room_users()
                    if isinstance(response, GetRoomUsersRequest.GetRoomUsersResponse):
                        room_users = response.content
                        birthday_girl_present = any(user.username == self.birthday_girl_username 
                                                  for user, pos in room_users)
                        
                        if birthday_girl_present:
                            pickup_line = random.choice(self.pickup_lines)
                            await self.highrise.chat(f"@{self.birthday_girl_username} {pickup_line}")
                except Exception as e:
                    print(f"Error checking room users: {e}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in pickup line task: {e}")
                await asyncio.sleep(self.pickup_line_interval)

    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        """Welcome users when they join"""
        await self.highrise.react("wave", user.id)
        
        if user.username == self.birthday_girl_username:
            await self.highrise.chat(
                f"🎉✨ THE BIRTHDAY QUEEN HAS ARRIVED! ✨🎉 Welcome {user.username}! "
                f"Today is all about celebrating YOU! 💖🎂"
            )
        else:
            await self.highrise.chat(
                f"Welcome {user.username}! 👋 We're celebrating a very special birthday today! "
                f"Join us in making this day magical! 🎈✨"
            )

    async def on_user_leave(self, user: User) -> None:
        """Say goodbye when users leave"""
        if user.username == self.birthday_girl_username:
            await self.highrise.chat(
                f"Aww, our birthday queen {user.username} is leaving! 👑💕 "
                f"Hope you had an amazing time on your special day! 🎉"
            )
        else:
            await self.highrise.chat(
                f"Goodbye {user.username}! 👋 Thanks for helping celebrate this special day! 🎈"
            )

    async def on_chat(self, user: User, message: str) -> None:
        """Handle chat commands"""
        lower_msg = message.lower().strip()
        
        try:
            # Set bot position command (only owner can use this)
            if lower_msg.startswith("!set"):
                if user.id == self.owner_id:
                    result = await self.set_bot_position(user.id)
                    await self.highrise.chat(result)
                else:
                    await self.highrise.chat("Only the room owner can set my position! 🔒")
                return
            
            # Equip command
            if lower_msg.startswith("!equip") or lower_msg.startswith("equip"):
                await equip(self, user, message)
                return
            
            # Remove command  
            if lower_msg.startswith("!remove") or lower_msg.startswith("remove"):
                await remove(self, user, message)
                return
            
            # Set pickup line interval (only owner can change this)
            if lower_msg.startswith("!interval"):
                if user.id == self.owner_id:
                    parts = message.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        new_interval = int(parts[1]) * 60  # Convert minutes to seconds
                        self.pickup_line_interval = new_interval
                        await self.highrise.chat(
                            f"Pickup line interval set to {parts[1]} minutes! 💕"
                        )
                        # Restart the task with new interval
                        await self.start_pickup_line_task()
                    else:
                        await self.highrise.chat(
                            "Usage: !interval <minutes> (e.g., !interval 3 for 3 minutes)"
                        )
                else:
                    await self.highrise.chat("Only the room owner can change the interval! 🔒")
                return
            
            # Birthday girl command (manual trigger)
            if lower_msg.startswith("!birthday") or lower_msg.startswith("birthday"):
                pickup_line = random.choice(self.pickup_lines)
                await self.highrise.chat(f"@{self.birthday_girl_username} {pickup_line}")
                return
            
            # Help command
            if lower_msg in ["!help", "help", "commands"]:
                help_text = (
                    "🎉 Birthday Bot Commands 🎉\n"
                    "• !equip <item_name> - Equip clothing item\n"
                    "• !remove <category> - Remove clothing category\n"
                    "• !set - Set bot position at your location (owner only)\n"
                    "• !birthday - Send a romantic message to birthday girl\n"
                    "• !interval <minutes> - Change pickup line frequency (owner only)\n"
                    "• !help - Show this help message\n\n"
                    f"💕 Sending automatic romantic messages every {self.pickup_line_interval//60} minutes! 💕"
                )
                await self.highrise.chat(help_text)
                return
                
        except Exception as e:
            print(f"Error in on_chat: {e}")
            await self.highrise.chat("Sorry, something went wrong! Please try again. 🤖")

async def main():
    # Get credentials from environment variables
    room_id = os.getenv("ROOM_ID")
    bot_token = os.getenv("BOT_TOKEN")
    
    # Debug information
    print(f"🔍 Debug info:")
    print(f"   ROOM_ID found: {'✅' if room_id else '❌'}")
    print(f"   BOT_TOKEN found: {'✅' if bot_token else '❌'}")
    
    if room_id:
        print(f"   ROOM_ID: {room_id}")
        print(f"   ROOM_ID length: {len(room_id)} characters")
    
    if bot_token:
        print(f"   BOT_TOKEN length: {len(bot_token)} characters")
        # Check for common issues
        if bot_token.strip() != bot_token:
            print("⚠️  Warning: BOT_TOKEN has leading/trailing whitespace")
        if '%' in bot_token:
            print("⚠️  Warning: BOT_TOKEN contains % character (may be copy-paste artifact)")
    
    if not room_id:
        print("❌ Error: ROOM_ID not found in environment variables!")
        print("Please set ROOM_ID in your .env file")
        return
    
    if not bot_token:
        print("❌ Error: BOT_TOKEN not found in environment variables!")
        print("Please set BOT_TOKEN in your .env file")
        return
    
    # Clean the credentials (remove any trailing % or whitespace)
    room_id = room_id.strip().rstrip('%') if room_id else None
    bot_token = bot_token.strip().rstrip('%') if bot_token else None
    
    print(f"🎉 Starting bot for room: {room_id}")
    print(f"🤖 Using bot token ending in: ...{bot_token[-8:] if len(bot_token) >= 8 else 'short_token'}")
    
    try:
        definitions = [BotDefinition(Bot(), room_id, bot_token)]
        await __main__.main(definitions)
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        if "Invalid room id" in str(e):
            print("💡 Room ID troubleshooting:")
            print("   • Make sure the ROOM_ID in your .env file is correct")
            print("   • The bot must be invited to the room as a bot")
            print("   • Check that the room exists and is accessible")
        elif "API token not found" in str(e) or "Invalid token" in str(e):
            print("💡 Bot token troubleshooting:")
            print("   • Make sure your BOT_TOKEN in .env is correct and complete")
            print("   • Verify the token is from your Highrise developer account")
            print("   • Check for any extra characters or spaces")
        raise


if __name__ == "__main__":
    arun(main())
