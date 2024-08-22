import os
from telegram import Update, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, PreCheckoutQueryHandler, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

# Загрузка конфигурации из .env файла
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# Настройка SQLAlchemy
engine = create_engine(DATABASE_URL)
Base = declarative_base()


# Определение моделей базы данных
class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    price = Column(Float, nullable=False)


class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    quantity = Column(Integer, default=1)
    item = relationship("Item")


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в наш магазин! Введите /catalog для просмотра товаров.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это меню помощи\n"
        "/catalog - Показать каталог товаров\n"
        "/cart - Показать содержимое вашей корзины\n"
        "/checkout - Оформить заказ\n"
        "Просто отправьте название товара, чтобы добавить его в корзину."
    )
    await update.message.reply_text(help_text)


async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = session.query(Item).all()
    if items:
        message = "Каталог товаров:\n"
        for item in items:
            message += f"{item.name} - {item.price:.2f} RUB\n"
        message += "\nВведите название товара, чтобы добавить его в корзину."
    else:
        message = "Каталог пуст."
    await update.message.reply_text(message)


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item_name = update.message.text.strip()
    item = session.query(Item).filter_by(name=item_name).first()

    if item:
        cart_item = session.query(CartItem).filter_by(user_id=update.message.chat_id, item_id=item.id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=update.message.chat_id, item_id=item.id, quantity=1)
            session.add(cart_item)
        session.commit()
        await update.message.reply_text(f"Товар '{item_name}' добавлен в корзину.")
    else:
        await update.message.reply_text("Товар не найден. Пожалуйста, введите корректное название товара.")


async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart_items = session.query(CartItem).filter_by(user_id=update.message.chat_id).all()
    if cart_items:
        message = "Ваша корзина:\n"
        total = 0
        for cart_item in cart_items:
            item_total = cart_item.quantity * cart_item.item.price
            message += f"{cart_item.item.name} - {cart_item.quantity} шт. - {item_total:.2f} RUB\n"
            total += item_total
        message += f"\nИтого: {total:.2f} RUB"
        message += "\nВведите /checkout для оформления заказа."
    else:
        message = "Ваша корзина пуста."
    await update.message.reply_text(message)


async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart_items = session.query(CartItem).filter_by(user_id=update.message.chat_id).all()
    if cart_items:
        title = "Оплата заказа"
        description = "Оплата товаров из вашей корзины"
        payload = "Custom-Payload"
        currency = "RUB"
        prices = [LabeledPrice(f"{item.item.name} ({item.quantity} шт.)", int(item.item.price * 100 * item.quantity))
                  for item in cart_items]

        await context.bot.send_invoice(
            chat_id=update.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=currency,
            prices=prices,
            start_parameter="test-payment",
        )
    else:
        await update.message.reply_text("Ваша корзина пуста.")


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "Custom-Payload":
        await query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session.query(CartItem).filter_by(user_id=update.message.chat_id).delete()
    session.commit()
    await update.message.reply_text("Спасибо за покупку! Ваш заказ был успешно оформлен.")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))  # Добавляем обработчик команды /help
    app.add_handler(CommandHandler("catalog", catalog))
    app.add_handler(CommandHandler("cart", view_cart))
    app.add_handler(CommandHandler("checkout", checkout))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_to_cart))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    app.run_polling()


if __name__ == '__main__':
    if not session.query(Item).first():
        session.add_all([
            Item(name="Item 1", price=100.0),
            Item(name="Item 2", price=150.0),
            Item(name="Item 3", price=200.0)
        ])
        session.commit()

    main()
