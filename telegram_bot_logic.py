import asyncio
from loguru import logger
import os

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.utils.emoji import emojize

from config import TELEGRAM_TOKEN, twenty_min_past
from yandex_api_connector import get_issues, get_latest_issues


logger.add('logs.json', format='{time} {level} {message}',
           level='INFO', rotation='50 KB', compression='zip', serialize=True)

if TELEGRAM_TOKEN is not None:
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        logger.info("Бот создан")
    except Exception as ex:
        logger.exception("Ошибка при создании бота")
        logger.exception(str(ex))

    # Создаем хранилище данных для бота.
    storage = MemoryStorage()
    try:
        dp = Dispatcher(bot, storage=storage)
        logger.info("Создан диспетчер")
    except Exception as ex:
        logger.exception("Ошибка при создании диспетчера")
        logger.exception(str(ex))
elif TELEGRAM_TOKEN is None:
    logger.warning("Был передан неверный токен. Завершаю работу программы")
    exit()


# Класс в котором будем сохранять данные по email и ответам пользователя.
class Form(StatesGroup):
    """
    Класс содержит переменную для токена и ключ-ответ пользователя.
    toke - используется для запроса тасок с api Яндекса
    yes_or_not - фиксирует состояние диалога на цикле. Либо завершает диалог.
    """
    token = State()
    yes_or_not = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Точка входа в диалог с ботом.
    """
    # Проверка на случай, если пользователь уже начинал диалог, но не был очищен state.
    if await state.get_state() is not None:
        await cancel_handler(message, state)
    await Form.token.set()

    await message.reply(
        "Приветствую!  Давай начнем. Для работы с твоим список задач мне потребуется твой токен" 
        "в организации. Для того, чтобы его получить, необходимо перейти по этой ссылке из под нужного"
        "пользователя и отправить мне сгенерированный там токен: "
        "https://oauth.yandex-team.ru/authorize?response_type=token&client_id=5f671d781aca402ab7460fde4050267b"
                        )
    await bot.send_message(message.chat.id,
                           "Эта ссылка отправит тебя на страницу аутентификации Яндекса. Токен будет храниться внутри"
                           "этог диалога. Если ты захочешь его удалить введи команду /cancel. Она отчистит токен и" 
                           "завершит диалог со мной."
                           )


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Обработчик команды "/cancel". Удаляет все данные по state.
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logger.info('Canceling state %r', current_state)
    await state.finish()
    # Задаем доп. значения для ответа. Необходимо для двойной проверки цикла на выход из него.
    async with state.proxy() as data:
        data['answer'] = None
    await message.reply("Алоха!(что означает 'привет' и 'пока' на гавайском)")


@dp.message_handler(state='*', commands='status')
async def get_all_tasks(message: types.Message, state: FSMContext):
    """
   Обработчик команды "/status". возвращает все задачи, которые есть у юзера на данный момент.
    """
    # Проверяем, что пользователь уже передал email боу. Если нет, выкидываем предупреждение.
    current_state = await state.get_state()
    if current_state is None:
        await message.reply("email адрес не был указан. Повторите запрос после указания email адреса")
        return
    # получаем из state email.
    async with state.proxy() as data:
        tasks = get_issues(data['token'])
        # Отлавливаем вариант, когда email передан неверно.
        if tasks is None:
            await bot.send_message(
                message.chat.id, "Введен некорректный email/такого юзера не существует. Повторите попытку")
            return
        elif len(tasks) == 0:
            await bot.send_message(
                message.chat.id, "У вас пока нет открытых задач")
        elif len(tasks) > 0:
            await bot.send_message(
                message.chat.id,
                md.text(
                    md.text("Ваши текущие задачи:"),
                    sep='\n'
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            # Возвращаем сообщение с таксками.
            await send_issues(message, tasks)


@dp.message_handler(state=Form.token)
async def process_email(message: types.Message, state: FSMContext):
    """
    Функция обрабатывает полученный email и возвращает список всех задач, после чего предлагает перейти к циклу.
    """
    async with state.proxy() as data:
        # Записываем в state значение email по ключу.
        data['token'] = message.text
        # получаем задачи
        tasks = get_issues(data['token'])
        # Проверяем валидность переданного email.
        if tasks is None:
            await bot.send_message(
                message.chat.id, "Введен некорректный token. Повторите попытку")
            return
        elif len(tasks) == 0:
            await bot.send_message(
                message.chat.id, "У вас пока нет открытых задач")
        elif len(tasks) > 0:
            await bot.send_message(
                message.chat.id,
                md.text(
                    md.text("Ваши текущие задачи:"),
                    sep='\n'
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            # Возвращаем сообщение с таксками.
            await send_issues(message, tasks)

        # Создаем клавиатуру.
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("да", "нет")
        # Переходим к следующему стейту. Теперь все сообщения будут обрабатываться следующей функцией.
        await Form.next()
        await bot.send_message(message.chat.id,
                               "Хотите подписаться на обновления вашего трекера задач?",
                               reply_markup=markup)


@dp.message_handler(lambda message: message.text.lower() not in ['да', 'нет'], state=Form.yes_or_not)
async def process_confirm_invalid(message: types.Message):
    """
    Отрабатывем ситуацию, когда пользователь ответил не то, что нужно.
    """
    return await message.reply('Не верный выбор. Воспользуйся клавиатурой. Для тебя же старались')


@dp.message_handler(state=Form.yes_or_not)
async def loop_request(message: types.Message, state: FSMContext):
    """
    Отрабатываем небольшое ветвление, если пользоватлеь хочет, или не хочет получать обновления.
    """
    if message.text.lower() == "нет":
        markup = types.ReplyKeyboardRemove()

        await bot.send_message(
            message.chat.id,
            "Ну, на нет и суда нет. Зачем это все было тогда?",
            reply_markup=markup
        )
        await state.finish()
    else:
        async with state.proxy() as data:
            # Записываем ответ пользователя в соответствующий state.
            data['answer'] = message.text
        # Удаляем клавиатуру.
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(
                message.chat.id,
                "С этого момента, каждые 20 минут, ты будешь получать обновления, если таковые будут",
                reply_markup=markup
            )
        # Проверяем, что стейты по-прежнему не пусты и переходим к циклу обновления.
        current_state = await state.get_state()
        while current_state is not None:
            # Каждый раз в начале цикла проверяем.
            current_state = await state.get_state()

            async with state.proxy() as data:
                # В случае, если пользователь вышел из цикла ключ answer возврощает None(см. def cancel_handler).
                if data['answer'] is None:
                    break
                # Получаем список задач
                tasks = get_latest_issues(data['token'])
                # Проверяем, что список не пустой, тогда высылаем таски.
                if len(tasks) > 0:
                    await send_issues(message, tasks)
                # Получаем задачи.
            await asyncio.sleep(1200)
        # Подчищаем стейты, если пользователь вышел из цикла.
        await state.finish()


async def send_issues(message: types.Message, tasks: list):
    """
    Функция принимает объект message, из которого получает id чата, и токен, который достается из базы диалога.
    Функция запрашивает список новых задач и отправляет их пользователю.
    """
    # Парсим каждую задачу в списке
    for task in tasks:
        if task['warnAt'] <= twenty_min_past:
            await bot.send_message(
                message.chat.id,
                md.text(
                    md.text(f'{emojize(":red_exclamation_mark:" * 3)}'
                            f'Эта задача в огне!'
                            f'{emojize(":red_exclamation_mark:" * 3)}'),
                    md.text(f'*Наименование задачи*: {task["issue"]}'),
                    md.text(f'*Статус*: {task["status"]}'),
                    md.text(f'{emojize(":fire:" * 3)}*Дедлайн*: {task["deadline"]}'),
                    sep='\n',
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await bot.send_message(
                message.chat.id,
                md.text(
                    md.text(f'*Наименование задачи*: {task["issue"]}'),
                    md.text(f'*Статус*: {task["status"]}'),
                    md.text(f'*Дедлайн*: {task["deadline"]}'),
                    sep='\n',
                ),
                parse_mode=ParseMode.MARKDOWN,
            )


if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True)
        logger.info("Бот запущен")
    except Exception as ex:
        logger.exception("Ошибка возникла при запуске приложения")
        logger.exception(str(ex))
