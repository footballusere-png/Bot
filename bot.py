except Exception:
                    start_link = f"https://t.me/{bot_username}?start=start"
                    pm_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚀 Start Bot in PM", url=start_link)]
                    ])
                    await callback_query.answer("⚠️ Please start the bot in Personal Chat (PM) first!", show_alert=True)
                    await callback_query.message.reply_text(
                        f"👋 {user_mention}, please start the bot in your Personal Chat (PM) to receive files!",
                        reply_markup=pm_keyboard
                    )
                    return

            is_joined = await check_force_sub(client, user_id)
            if not is_joined:
                join_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url=UPDATE_CHANNEL_LINK)],
                    [InlineKeyboardButton("🔄 I Have Joined", callback_data=data)]
                ])
                await callback_query.answer("⚠️ Please join our update channel first!", show_alert=True)
                if is_pm:
                    await client.send_message(
                        user_id,
                        "⚠️ You must join our update channel to get files!\n\n"
                        "👇 Click the button below to join, then click the movie button again.",
                        reply_markup=join_keyboard
                    )
                else:
                    await callback_query.message.edit_text(
                        "⚠️ You must join our update channel to get files!\n\n"
                        "👇 Click the button below to join, then click 'I Have Joined'.",
                        reply_markup=join_keyboard
                    )
                return

            await callback_query.answer("📥 Sending file...", show_alert=False)
            target_chat = user_id if is_pm else callback_query.message.chat.id
            try:
                sent_file = await main_bot.copy_message(
                    chat_id=target_chat,
                    from_chat_id=MY_CHANNEL,
                    message_id=file_msg_id
                )
                
                # --- AUTO DELETE SENT FILE AFTER 1 HOUR (3600 seconds) ---
                async def auto_delete_file(msg):
                    await asyncio.sleep(3600)
                    try:
                        await msg.delete()
                    except:
                        pass
                asyncio.create_task(auto_delete_file(sent_file))
                # ---------------------------------------------------------

            except Exception:
                await client.send_message(target_chat, "❌ Failed to send file. Please try again later.")

    Thread(target=run_flask, daemon=True).start()

    await userbot.start()
    await main_bot.start()
    print("🚀 Premium Movie Bot & Web Server successfully running!")

    await asyncio.Event().wait()

if name == "main":
    asyncio.run(main())
