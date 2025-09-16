from highrise import *
from highrise.models import *

категории = ["aura","bag","blush","body","dress","earrings","emote","eye","eyebrow","fishing_rod","freckle","fullsuit","glasses",
"gloves","hair_back","hair_front","handbag","hat","jacket","lashes","mole","mouth","necklace","nose","rod","shirt","shoes",
"shorts","skirt","sock","tattoo","watch", "pants"]

async def remove(self: BaseBot, user: User, message: str):
        части = message.split(" ")
        if len(части) != 2:
            await self.highrise.chat("Неверный формат команды. Необходимо указать категорию. (напиши мне 'remove', чтобы получить помощь)")
            return
        if части[1] not in категории:
            await self.highrise.chat("Неверная категория. (напиши мне 'remove', чтобы получить помощь)")
            return
        категория = части[1].lower()
        наряд = (await self.highrise.get_my_outfit()).outfit
        for предмет_наряда in наряд:
            # Категория предмета определяется первой строкой id до символа "-"
            категория_предмета = предмет_наряда.id.split("-")[0][0:3]
            if категория_предмета == категория[0:3]:
                try:
                    наряд.remove(предмет_наряда)
                except:
                    await self.highrise.chat(f"Бот не использует элементы из категории '{категория}'.")
                    return
        response = await self.highrise.set_outfit(наряд)