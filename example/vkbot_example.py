import asyncio
from vkbottle.bot import Bot, Message

from   dotenv     import find_dotenv, dotenv_values
PROJECT_ROOT    = f"{find_dotenv('venv')[0:-5]}"
SECRETS         = dotenv_values()
DATA_DIR        = f"{PROJECT_ROOT}/data"

# Замени на свой токен сообщества
TOKEN = SECRETS['VK_TEST_TOKEN']

bot = Bot(token=TOKEN)


@bot.on.message(text=["привет", "здравствуй", "хай", "hi", "hello"])
async def greet_handler(message: Message):
    await message.answer("Привет! Я бот этого сообщества 🤖")


@bot.on.message(text=["что ты умеешь", "помощь", "/help"])
async def help_handler(message: Message):
    await message.answer(
        "Я умею:\n"
        "• Отвечать на приветствия\n"
        "• Рассказывать о себе\n"
        "\nНапиши «привет» чтобы начать!"
    )


@bot.on.message()
async def fallback_handler(message: Message):
    await message.answer("Не понял тебя 🤔 Напиши «помощь» чтобы узнать что я умею.")


if __name__ == "__main__":
    bot.run_forever()
