from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto,InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import API_TOKEN, ADMINS
from keyboards import main_menu_kb, admin_menu_kb, back_to_main_kb,genres_list_inline
from utils import format_anime_card, save_photo_locally
import database as db
from aiogram.utils.keyboard import InlineKeyboardBuilder

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# =============================
# FSM состояния
# =============================
class AddAnimeStates(StatesGroup):
    title = State()
    description = State()
    year = State()
    rating = State()
    poster = State()
    watch_url = State()
    genres = State()
    waiting_new_genre = State()


class EditSelectState(StatesGroup):
    selecting_anime = State()
    choosing_field = State()
    new_value = State()


# =============================
# Команда /start
# =============================
@dp.message(Command("start"))
async def start_cmd(message: Message):
    kb = main_menu_kb(message.from_user.id)
    await message.answer_video(video='https://media1.tenor.com/m/BZKyV5_iZM4AAAAC/cat-anime.gif',
                               caption="👋 Привет! Рад тебя видеть!\n\n"
                                       "Здесь ты можешь смотреть сериалы, искать новинки и находить что-то по душе.\n\n"
                                       "✨ Выбери действие:" , reply_markup=kb)


# =============================
# Команда /help
# =============================
@dp.message(Command("help"))
async def start_cmd(message: Message):
    kb = main_menu_kb(message.from_user.id)
    await message.answer_video(video='https://media.tenor.com/ESnEITRfhlIAAAAi/happy-mafumafu.gif',
                               caption="Этот бот поможет тебе:\n\n"
                                 "🎬 Смотреть аниме прямо в Telegram;\n"
                                 "🔎 Искать тайтлы по названию;\n"
                                 "⭐ Добавлять понравившиеся аниме в избранное;\n"
                                 "🆕 Следить за новинками и популярными сериалами;\n\n"
                                
                                "Если возникли вопросы или нужна помощь — напиши сюда 👉 @artempost1" , reply_markup=kb)


# =============================
# Админ-панель
# =============================
@dp.message(F.text == "👑 Админ-панель")
async def admin_panel(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return
    await message.answer("👑 Админ-панель:", reply_markup=admin_menu_kb())


# =============================
# Обработка всех текстовых сообщений
# =============================
@dp.message(F.text)
async def all_text_handler(message: Message, state: FSMContext):
    text = message.text.strip()
    user_id = message.from_user.id
    st = await state.get_state()
    data = await state.get_data()

    if not text:
        return

    # -----------------------------
    # Отмена действия
    # -----------------------------
    if text.lower() == "отмена" or text == "🔙 Отмена":
        await message.answer("✅ Действие отменено.", reply_markup=main_menu_kb(user_id))
        await state.clear()
        return

    # -----------------------------
    # FSM состояния добавления аниме
    # -----------------------------
    if st is not None:
        # Добавление аниме
        if st == AddAnimeStates.title.state:
            await state.update_data(title=text)
            await state.set_state(AddAnimeStates.description)
            await message.answer("Введи описание аниме:", reply_markup=InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup())
            return
        if st == AddAnimeStates.description.state:
            await state.update_data(description=text)
            await state.set_state(AddAnimeStates.year)
            await message.answer("Введи год выхода (число):", reply_markup=InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup())
            return
        if st == AddAnimeStates.year.state:
            try:
                await state.update_data(year=int(text))
                await state.set_state(AddAnimeStates.rating)
                await message.answer("Введи рейтинг (например 8.5):", reply_markup=InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup())
            except ValueError:
                await message.answer("Ожидалось число для года.")
            return
        if st == AddAnimeStates.rating.state:
            try:
                await state.update_data(rating=float(text))
                await state.set_state(AddAnimeStates.poster)
                await message.answer("Отправь постер (фото):", reply_markup=InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup())
            except ValueError:
                await message.answer("Ожидалось число для рейтинга.")
            return
        if st == AddAnimeStates.watch_url.state:
            await state.update_data(watch_url=text)
            await state.set_state(AddAnimeStates.genres)
            await show_genre_selection(message, state)
            return
        if st == AddAnimeStates.waiting_new_genre.state:
            await new_genre_text(message, state)
            return

        # Редактирование поля
        if st == EditSelectState.new_value.state:
            aid = data.get("editing_anime_id")
            field = data.get("edit_field")
            value = text
            if field in ["year", "rating"]:
                try:
                    value = int(value) if field == "year" else float(value)
                except ValueError:
                    await message.answer(f"Ожидалось число для поля {field}.")
                    return
            await db.update_anime_field(aid, field, value)
            await message.answer(f"Поле {field} обновлено ✅", reply_markup=admin_menu_kb())
            await state.clear()
            return

        # Удаление аниме
        if st == "delete_anime":
            try:
                aid = int(text)
            except ValueError:
                await message.answer("Ожидался числовой ID аниме.")
                return
            anime = await db.get_anime(aid)
            if not anime:
                await message.answer("Аниме с таким ID не найдено.")
                return
            await db.delete_anime(aid)
            await message.answer(f"Аниме *{anime['title']}* удалено ✅", parse_mode="Markdown", reply_markup=admin_menu_kb())
            await state.clear()
            return

        # Выбор аниме для редактирования
        if st == EditSelectState.selecting_anime.state:
            try:
                aid = int(text)
            except ValueError:
                await message.answer("Ожидался числовой ID аниме.")
                return
            anime = await db.get_anime(aid)
            if not anime:
                await message.answer("Аниме с таким ID не найдено.")
                return
            await state.update_data(editing_anime_id=aid)
            fields = ["title", "description", "year", "rating", "watch_url", "poster"]
            kb_text = [f"{i+1}. {f}" for i, f in enumerate(fields)]
            cancel_kb = InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup()
            await message.answer("Выберите поле для редактирования:\n" + "\n".join(kb_text), reply_markup=cancel_kb)
            await state.set_state(EditSelectState.choosing_field)
            return

        # Выбор поля для редактирования
        if st == EditSelectState.choosing_field.state:
            fields = ["title", "description", "year", "rating", "watch_url", "poster"]
            try:
                idx = int(text.strip()) - 1
                field = fields[idx]
            except (ValueError, IndexError):
                await message.answer("Неверный выбор.")
                return
            await state.update_data(edit_field=field)
            await state.set_state(EditSelectState.new_value)
            if field == "poster":
                await message.answer("Отправьте новое фото постера.", reply_markup=InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup())
            else:
                await message.answer(f"Введите новое значение для {field}:", reply_markup=InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup())
            return

    # -----------------------------
    # Поиск аниме
    # -----------------------------
    if st == "searching":
        query_text = text.lower()
        # Получаем все аниме
        all_anime = await db.list_all_anime()
        # Фильтруем по совпадению в названии
        matches = [r for r in all_anime if query_text in r[1].lower()]

        if not matches:
            await message.answer("Аниме не найдено по запросу.", reply_markup=back_to_main_kb())
            await state.clear()
            return

        # Показываем первое совпадение
        first_id = matches[0][0]

        # Сохраняем список найденного в состоянии, чтобы потом листать
        await state.update_data(search_results=[r[0] for r in matches])

        # Показываем карточку с навигацией
        await show_anime_with_navigation(message, first_id)
        await state.set_state("browsing_search")  # новое состояние для навигации по результатам поиска
        return

    # -----------------------------
    # Главное меню
    # -----------------------------
    if text == "🎬 Просмотреть аниме":
        rows = await db.list_all_anime()
        if not rows:
            await message.answer("Пока нет добавленного аниме.", reply_markup=back_to_main_kb())
            return
        first_aid = rows[0][0]
        await show_anime_with_navigation(message, first_aid)
        return

    if text == "🔎 Поиск":
        await message.answer("Введите часть названия для поиска.", reply_markup=back_to_main_kb())
        await state.set_state("searching")
        return

    if text == "🧾 Жанры":
        genres = await db.list_genres()
        if not genres:
            await message.answer("Жанров пока нет.", reply_markup=back_to_main_kb())
            return
        await message.answer("Выберите жанр:", reply_markup=genres_list_inline(genres))
        return

    if text == "❤️ Избранное":
        favs = await db.list_favorites(user_id)
        if not favs:
            await message.answer("У тебя нет избранного.", reply_markup=main_menu_kb(user_id))
            return
        first_id = favs[0][0]
        await show_anime_with_navigation(message, first_id, favorite_mode=True)
        return

    if text == "🔙 В главное":
        await message.answer("Главное меню:", reply_markup=main_menu_kb(user_id))
        await state.clear()
        return

    # -----------------------------
    # Админ-панель
    # -----------------------------
    if user_id in ADMINS:
        if text == "➕ Добавить аниме":
            await message.answer("Введи название аниме:", reply_markup=back_to_main_kb())
            await state.set_state(AddAnimeStates.title)
            return

        if text == "✏️ Редактировать аниме":
            rows = await db.list_all_anime()
            if not rows:
                await message.answer("Нет аниме для редактирования.", reply_markup=admin_menu_kb())
                return
            txt = "Выбери ID аниме для редактирования:\n" + "\n".join(f"{r[0]} — {r[1]}" for r in rows)
            cancel_kb = InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup()
            await message.answer(txt, reply_markup=cancel_kb)
            await state.set_state(EditSelectState.selecting_anime)
            return

        if text == "❌ Удалить аниме":
            rows = await db.list_all_anime()
            if not rows:
                await message.answer("Нет аниме для удаления.", reply_markup=admin_menu_kb())
                return
            txt = "Выбери ID аниме для удаления:\n" + "\n".join(f"{r[0]} — {r[1]}" for r in rows)
            cancel_kb = InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup()
            await message.answer(txt, reply_markup=cancel_kb)
            await state.set_state("delete_anime")
            return

        if text == "📋 Список всех аниме":
            rows = await db.list_all_anime()
            if not rows:
                await message.answer("Список пуст.", reply_markup=admin_menu_kb())
                return
            txt = "Список аниме:\n" + "\n".join(f"{r[0]} — {r[1]} ({r[2]}) [{r[3]}]" for r in rows)
            await message.answer(txt, reply_markup=admin_menu_kb())
            return


# =============================
# Жанры и добавление аниме
# =============================
async def show_genre_selection(message_or_call, state: FSMContext, edit=False):
    genres = await db.list_genres()
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    builder = InlineKeyboardBuilder()
    for gid, name in genres:
        mark = "✅" if gid in selected else "▫"
        builder.button(text=f"{mark} {name}", callback_data=f"add_select_genre:{gid}")
    builder.button(text="🆕 Добавить жанр", callback_data="add_new_genre")
    builder.button(text="✅ Готово", callback_data="add_finish_genres")
    builder.adjust(2)
    text = "Выбери жанры для аниме или добавь новый:"
    if edit:
        await message_or_call.edit_message_text(text, reply_markup=builder.as_markup())
    else:
        if isinstance(message_or_call, CallbackQuery):
            await message_or_call.message.answer(text, reply_markup=builder.as_markup())
        else:
            await message_or_call.answer(text, reply_markup=builder.as_markup())


async def new_genre_text(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("Название жанра не может быть пустым.")
        return
    gid = await db.add_genre(new_name)
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    selected.append(gid)
    await state.update_data(selected_genres=selected)
    await state.set_state(AddAnimeStates.genres)
    await message.answer(f"Жанр *{new_name}* добавлен ✅", parse_mode="Markdown")
    await show_genre_selection(message, state)


# =============================
# Обработка фото
# =============================
@dp.message(lambda message: message.photo is not None)
async def photo_handler(message: Message, state: FSMContext):
    st = await state.get_state()
    data = await state.get_data()
    photo = message.photo[-1]
    if st == AddAnimeStates.poster.state:
        title = data.get("title", "new")
        poster_path = await save_photo_locally(bot, photo.file_id, title)
        await state.update_data(poster_file_id=photo.file_id, poster_path=poster_path)
        await state.set_state(AddAnimeStates.watch_url)
        await message.answer("Постер сохранён. Теперь отправь ссылку на канал/просмотр (URL).")
        return
    if st == EditSelectState.new_value.state and data.get("edit_field") == "poster":
        aid = data.get("editing_anime_id")
        poster_path = await save_photo_locally(bot, photo.file_id, f"anime_{aid}")
        await db.update_anime_field(aid, "poster_file_id", photo.file_id)
        await db.update_anime_field(aid, "poster_path", poster_path)
        await message.answer("Постер обновлён.", reply_markup=admin_menu_kb())
        await state.clear()
        return


# =============================
# Навигация аниме (обновлённая версия с перестроенными кнопками)
# =============================
async def show_anime_with_navigation(message_or_call, anime_id: int, edit=False, genre_id: int | None = None, favorite_mode: bool = False, custom_ids: list[int] | None = None):
    """
    Показывает карточку аниме с кнопками:
    ▶️ Смотреть, ❤️ Избранное/Убрать, ⬅️ ➡️ навигация
    custom_ids — список anime_id для навигации (поиск или фильтр)
    """

    if isinstance(message_or_call, CallbackQuery):
        query = message_or_call
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        message_id = query.message.message_id
    else:
        query = None
        user_id = message_or_call.from_user.id
        chat_id = None
        message_id = None

    # Получаем список anime_id
    if custom_ids:
        ids = custom_ids
    elif favorite_mode:
        favs = await db.list_favorites(user_id)
        ids = [fid for fid, _ in favs]
    elif genre_id:
        rows = await db.list_anime_by_genre(genre_id)
        ids = [r[0] for r in rows]
    else:
        rows = await db.list_all_anime()
        ids = [r[0] for r in rows]

    if not ids:
        text = "Пока здесь нет аниме."
        if query:
            await query.message.answer(text)
        else:
            await message_or_call.answer(text)
        return

    if anime_id not in ids:
        anime_id = ids[0]

    idx = ids.index(anime_id)
    anime = await db.get_anime(anime_id)
    if not anime:
        return

    favorites = await db.list_favorites(user_id)
    is_fav = any(fid == anime_id for fid, _ in favorites)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="▶️ Смотреть", callback_data=f"watch:{anime_id}"))
    fav_label = "💔 Убрать из избранного" if is_fav else "❤️ Добавить в избранное"
    builder.row(InlineKeyboardButton(text=fav_label, callback_data=f"fav:{anime_id}:{genre_id or 0}:{int(favorite_mode)}"))

    nav_buttons = []
    if len(ids) > 1 and idx > 0:
        prev_id = ids[idx - 1]
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"nav:{prev_id}:{genre_id or 0}:{int(favorite_mode)}"))
    if len(ids) > 1 and idx < len(ids) - 1:
        next_id = ids[idx + 1]
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"nav:{next_id}:{genre_id or 0}:{int(favorite_mode)}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    caption = format_anime_card(anime)

    if anime.get("poster_file_id"):
        media = InputMediaPhoto(media=anime["poster_file_id"], caption=caption, parse_mode="Markdown")
        if edit and query:
            try:
                await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=builder.as_markup())
            except:
                await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode="Markdown", reply_markup=builder.as_markup())
        else:
            if query:
                await query.message.answer_photo(photo=anime["poster_file_id"], caption=caption, parse_mode="Markdown", reply_markup=builder.as_markup())
            else:
                await message_or_call.answer_photo(photo=anime["poster_file_id"], caption=caption, parse_mode="Markdown", reply_markup=builder.as_markup())
    else:
        if edit and query:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode="Markdown", reply_markup=builder.as_markup())
        else:
            if query:
                await query.message.answer(text=caption, parse_mode="Markdown", reply_markup=builder.as_markup())
            else:
                await message_or_call.answer(text=caption, parse_mode="Markdown", reply_markup=builder.as_markup())



# =============================
# Callback обработчики
# =============================
@dp.callback_query()
async def handle_callbacks(query: CallbackQuery, state: FSMContext):
    data = query.data
    user_id = query.from_user.id

    # Отмена действия
    if data == "cancel":
        await query.message.answer("✅ Действие отменено.", reply_markup=main_menu_kb(user_id))
        await state.clear()
        await query.answer()
        return

    # Ссылка на просмотр
    if data.startswith("watch:"):
        aid = int(data.split(":")[1])
        anime = await db.get_anime(aid)
        if anime and anime.get("watch_url"):
            await query.message.answer(f"Смотри аниме прямо в телеграме:\n {anime['watch_url']}")
        else:
            await query.answer("Ссылка не найдена.", show_alert=True)
        await query.answer()
        return

    # Избранное
    if data.startswith("fav:"):
        # ожидаем формат: fav:<anime_id>:<genre_id>:<favorite_mode>
        parts = data.split(":")
        aid = int(parts[1])
        genre_id = int(parts[2]) if len(parts) >= 3 and parts[2] != "0" else None
        favorite_mode = bool(int(parts[3])) if len(parts) >= 4 else False

        # текущее состояние избранного
        faves = await db.list_favorites(user_id)
        is_fav = any(fid == aid for fid, _ in faves)

        # переключаем статус
        if is_fav:
            await db.remove_favorite(user_id, aid)
            await query.answer("Удалено из избранного.")
            is_fav = False
        else:
            await db.add_favorite(user_id, aid)
            await query.answer("Добавлено в избранное.")
            is_fav = True

        # после изменения пересобираем карточку в том же контексте (жанр / избранное / все)
        await show_anime_with_navigation(
            query,
            anime_id=aid,
            edit=True,
            genre_id=genre_id,
            favorite_mode=favorite_mode
        )
        return

    # Навигация
    # -------------------
    # Навигация по аниме (включая поиск и фильтры)
    if data.startswith("nav:"):
        # Формат: nav:<anime_id>:<genre_id>:<favorite_flag>
        parts = data.split(":")
        try:
            target_id = int(parts[1])
        except (IndexError, ValueError):
            await query.answer("Неверные данные навигации.")
            return

        genre_id = None
        favorite_mode = False
        if len(parts) >= 4:
            try:
                g = int(parts[2])
                genre_id = g if g != 0 else None
                favorite_mode = bool(int(parts[3]))
            except Exception:
                genre_id = None
                favorite_mode = False

        # Определяем текущий список ID для навигации
        state_data = await state.get_data()
        if "search_results" in state_data:
            ids = state_data["search_results"]
        elif favorite_mode:
            ids = [fid for fid, _ in await db.list_favorites(query.from_user.id)]
        elif genre_id:
            rows = await db.list_anime_by_genre(genre_id)
            ids = [r[0] for r in rows]
        else:
            rows = await db.list_all_anime()
            ids = [r[0] for r in rows]

        if not ids:
            await query.answer("Нет аниме для навигации.")
            return

        if target_id not in ids:
            new_id = ids[0]
        else:
            idx = ids.index(target_id)
            new_id = ids[idx]

        # Показываем карточку аниме и редактируем текущее сообщение
        await show_anime_with_navigation(
            query,
            anime_id=new_id,
            edit=True,
            genre_id=genre_id,
            favorite_mode=favorite_mode,
            custom_ids=ids if "search_results" in state_data else None
        )
        await query.answer()
        return

    # Выбор жанра
    if data.startswith("add_select_genre:"):
        gid = int(data.split(":")[1])
        genre_data = await state.get_data()
        selected = genre_data.get("selected_genres", [])
        if gid in selected:
            selected.remove(gid)
        else:
            selected.append(gid)
        await state.update_data(selected_genres=selected)
        await show_genre_selection(query, state)
        await query.answer()
        return

    # Добавление нового жанра
    if data == "add_new_genre":
        await state.set_state(AddAnimeStates.waiting_new_genre)
        await query.message.answer("Введите название нового жанра:", reply_markup=InlineKeyboardBuilder().button(text="🔙 Отмена", callback_data="cancel").as_markup())
        await query.answer()
        return

    # Завершение выбора жанров
    if data == "add_finish_genres":
        anime_data = await state.get_data()
        gids = anime_data.get("selected_genres", [])
        title = anime_data.get("title")
        description = anime_data.get("description")
        year = anime_data.get("year")
        rating = anime_data.get("rating")
        watch_url = anime_data.get("watch_url")
        poster_file_id = anime_data.get("poster_file_id")
        poster_path = anime_data.get("poster_path", "")
        if not poster_file_id:
            await query.message.answer("⚠️ Постер не получен. Отправь постер заново.")
            await state.set_state(AddAnimeStates.poster)
            await query.answer()
            return
        new_id = await db.add_anime(title, description, year, rating, poster_file_id, poster_path, watch_url, gids)
        await query.message.answer(f"✅ Аниме *{title}* добавлено (ID {new_id})", parse_mode="Markdown", reply_markup=admin_menu_kb())
        await state.clear()
        await query.answer()
        return

    # Фильтр по жанру
    if data.startswith("genre:"):
        gid = int(data.split(":")[1])
        rows = await db.list_anime_by_genre(gid)
        if not rows:
            await query.answer("В этом жанре пока нет аниме.")
            return
        first_id = rows[0][0]
        await show_anime_with_navigation(query, first_id, genre_id=gid)
        await query.answer()
        return

