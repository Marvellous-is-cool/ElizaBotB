from highrise import *
from highrise.webapi import *
from highrise.models_webapi import *
from highrise.models import *


async def equip(self: BaseBot, user: User, message: str):
  # Получить id предмета и категорию из сообщения
  части = message.split(" ")
  if len(части) < 2:
    await self.highrise.chat("Необходимо указать название предмета. (напиши мне !equip, чтобы узнать доступные названия)")
    return
  название_предмета = ""
  for часть in части[1:]:
    название_предмета += часть + " "
  название_предмета = название_предмета[:-1]
  # Проверить, является ли последняя часть числом
  индекс = 0
  if название_предмета[-1].isdigit():
    название_предмета = название_предмета[:-2]
    индекс = int(части[-1])
  предметы = (await self.webapi.get_items(item_name=название_предмета)).items
  # Проверить, найден ли предмет
  if предметы == []:
    await self.highrise.chat(f"Предмет '{название_предмета}' не найден (напиши мне !equip, чтобы узнать доступные предметы)."); return
  elif len(предметы) > 1:
    await self.highrise.chat(
        f"Найдено несколько предметов для '{название_предмета}', используется номер {индекс} из списка {предметы[индекс].item_name}."
    )
  предмет = предметы[индекс]
  id_предмета = предмет.item_id
  категория = предмет.category
  #--------------------------------------------------------#

  проверка = False
  # Проверить, есть ли у бота этот предмет
  инвентарь = (await self.highrise.get_inventory()).items
  for предмет_инвентаря in инвентарь:
    if предмет_инвентаря.id == id_предмета:
      проверка = True
      break
  if проверка == False:
    # Проверить, бесплатный ли предмет
    if предмет.rarity == Rarity.NONE:
      pass
    # Проверить, можно ли купить предмет
    elif not предмет.is_purchasable:
      await self.highrise.chat(f"Предмет '{название_предмета}' нельзя купить (напиши мне !equip для помощи)."); return
    else:
      try:
        response = await self.highrise.buy_item(id_предмета)
        if response != "success":
          await self.highrise.chat(f"Предмет '{название_предмета}' нельзя купить."); return
        else:
          await self.highrise.chat(f"Предмет '{название_предмета}' куплен.")
      except Exception as e:
        print(e)
        await self.highrise.chat(f"Ошибка: {e}. Свяжитесь с @coolbuoy для помощи."); return

  #--------------------------------------------------------#
  новый_предмет = Item(
      type="clothing",
      amount=1,
      id=id_предмета,
      account_bound=False,
      active_palette=0,
  )
  #--------------------------------------------------------#
  # Проверить, используется ли категория предмета уже
  наряд = (await self.highrise.get_my_outfit()).outfit
  предметы_для_удаления = []
  for предмет_наряда in наряд:
    # Категория предмета определяется первой строкой id до "-"
    категория_предмета = предмет_наряда.id.split("-")[0][0:4]
    print(f"{категория_предмета}")
    if категория_предмета == категория[0:4]:
      предметы_для_удаления.append(предмет_наряда)
  for предмет_к_удалению in предметы_для_удаления:
    наряд.remove(предмет_к_удалению)
  # Если предмет — волосы, также надеть hair_back
  if категория == "hair_front":
    id_hair_back = предмет.link_ids[0]
    волосы_сзади = Item(
        type="clothing",
        amount=1,
        id=id_hair_back,
        account_bound=False,
        active_palette=0,
    )
    наряд.append(волосы_сзади)
  наряд.append(новый_предмет)
  await self.highrise.set_outfit(наряд)
