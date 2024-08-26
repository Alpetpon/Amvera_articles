import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

tracked_items = {}
notification_channel = None

def get_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    price_tag = soup.find('span', {'class': 'price'})

    if price_tag:
        price = float(price_tag.text.replace('\u2009', '').replace('₽', '').replace(' ', '').strip())
        return price
    return None

@bot.command()
async def track(ctx, url: str):
    price = get_price(url)
    if price:
        tracked_items[url] = price
        await ctx.send(f"Товар добавлен в отслеживание. Текущая цена: {price} ₽")
    else:
        await ctx.send("Не удалось получить цену для этого товара.")

@bot.command()
async def untrack(ctx, url: str):
    if url in tracked_items:
        del tracked_items[url]
        await ctx.send(f"Товар удален из отслеживания.")
    else:
        await ctx.send("Этот товар не отслеживается.")

@bot.command()
async def list(ctx):
    if tracked_items:
        message = "Отслеживаемые товары:\n"
        for url, price in tracked_items.items():
            message += f"{url} - Текущая цена: {price} ₽\n"
        await ctx.send(message)
    else:
        await ctx.send("Список отслеживаемых товаров пуст.")

@bot.command()
async def setchannel(ctx):
    global notification_channel
    notification_channel = ctx.channel
    await ctx.send(f"Уведомления о изменении цен будут отправляться в канал: {ctx.channel.name}")

@bot.command()
async def update(ctx):
    await ctx.send("Обновление цен...")
    await price_check()

@tasks.loop(minutes=60)
async def price_check():
    for url, old_price in tracked_items.items():
        new_price = get_price(url)
        if new_price and new_price != old_price:
            tracked_items[url] = new_price
            if notification_channel:
                await notification_channel.send(
                    f"Цена на товар изменилась! Новая цена: {new_price} ₽ (Старая цена: {old_price} ₽)\n{url}")
            else:
                print("Канал для уведомлений не установлен.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    price_check.start()

bot.run(TOKEN)
