# Technical Spec: TG Digest Bot + ETL

## 1. Архитектура
Компоненты:
1. Bot Service (aiogram, Telegram Bot API)
2. Extractor (Telethon, MTProto user session)
3. Transformer (очистка и обрезка постов)
4. Summarizer (LLM)
5. Storage (PostgreSQL)
6. Digest Assembler + Chunking

## 2. ETL режим
MVP: On-demand ETL при вызове `/analytic`:
- Extract: чтение последних 5 текстовых постов канала;
- Transform: clean + truncate;
- Summarize: summary по каналу;
- Load: опционально upsert постов в БД.

## 3. Модель данных (минимум)
- `users(id, tg_user_id unique, created_at)`
- `channels(id, handle unique, title, created_at)`
- `user_channels(user_id, channel_id, added_at, unique(user_id, channel_id))`
- `posts(id, channel_id, tg_msg_id, date, text, permalink, unique(channel_id, tg_msg_id))`
- `digests(id, user_id, created_at, content, cache_key)` (опционально)

## 4. Контракты модулей
- `parsing/channels.py`:
  - `normalize_handle(raw) -> Optional[ChannelHandle]`
  - `parse_channels(text, max_items=50) -> ParseChannelsResult`
- `extractor/telethon_extractor.py`:
  - `fetch_last_posts(client, handle, limit=5) -> list[PostDTO]`
- `transform/posts.py`:
  - `transform_posts(posts, max_chars_per_post=1500) -> list[PostDTO]`
- `summarizer/llm.py`:
  - `summarize_channel(handle, link, posts) -> str`
- `services/analytic.py`:
  - объединяет extract/transform/summarize, обрабатывает ошибки по-канально.

## 5. Лимиты
- `N_POSTS_PER_CHANNEL = 5`
- `MAX_CHANNELS_PER_ANALYTIC_CALL = 50`
- `MAX_CHANNELS_PER_USER = 200`
- `TG_MESSAGE_MAX_LEN` — отправка чанками

## 6. Обработка ошибок
- Доменные ошибки:
  - `ValidationError`
  - `StorageError`
  - `ExtractError`
  - `SummarizeError`
- В `/analytic` ошибки extract/summarize по каналу превращаются в fallback-блок и не прерывают весь дайджест.

## 7. Наблюдаемость
Логировать:
- `tg_user_id`, число каналов;
- длительность `/analytic`;
- статус по каждому каналу (ok/error, число постов);
- коды ошибок Telegram/LLM.
