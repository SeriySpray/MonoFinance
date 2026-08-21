with open('app_server.py', 'r', encoding='utf-8', errors='ignore') as f:
    code = f.read()

target_start = code.find('def categorize_transaction():')
if target_start != -1:
    code_before = code[:target_start]
    new_func = '''def categorize_transaction():
    data = request.get_json(silent=True, force=True) or {}
    description = data.get('description', '').strip()
    tx_type = data.get('type', 'expense')
    
    if not description:
        def_cat = 'Інші витрати' if tx_type == 'expense' else 'Інші доходи'
        return jsonify({'success': True, 'category': def_cat, 'icon': CATEGORY_ICON_MAP.get(def_cat, 'receipt_long')})
        
    groq_api_key = os.environ.get("GROQ_API_KEY", "")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    
    cat_result = None
    
    allowed_cats = ALLOWED_EXPENSE_CATEGORIES if tx_type == 'expense' else ALLOWED_INCOME_CATEGORIES

    if groq_api_key:
        try:
            import requests
            prompt = f"""Ти інтелектуальний фінансовий аналітик додатка MonoFinance.
Твоє завдання — проаналізувати зміст і контекст опису транзакції та обрати найвідповіднішу категорію зі списку.
Давай моделі повну свободу семантичного розпізнавання природної мови, побутових назв продуктів, страв, покупок та послуг.

СЕМАНТИЧНИЙ ОПИС КАТЕГОРИЗАЦІЇ ВИТРАТ:
- 'Продукти харчування': Будь-які продукти з магазину, сировина, випічка (кексики, кекси, булочки, круасани, хліб, батон), м'ясо (філе, фарш, стейки, птиця, свинина), риба, овочі, фрукти, ягоди, молочка, сир, десерти, солодощі, інгредієнти, супермаркети, пачка товарів, безалкогольні напої тощо.
- 'Кафе та ресторани': Готова їжа з закладів, кав'ярні, фастфуд, обіди, сніданки, вечері, ресторани, бари, доставки (Glovo, Bolt Food), піца, суші, бургери, шаурма.
- 'Транспорт та Авто': Таксі, метро, проїзд, квитки, паливо, заправки, автомийки, ремонт авто.
- 'Комунальні та Житло': Комуналка, оренда житла, інтернет, світло, вода, газ, ремонт.
- 'Здоров'я та Спорт': Аптеки, ліки, медичні послуги, лікарі, аналізи, спортзал, тренування.
- 'Покупки та Одяг': Одяг, взуття, шопінг, техніка, електроніка, гаджети, покупки для дому.
- 'Розваги та Дозвілля': Кіно, ігри, підписки (Netflix, Spotify), концерти, хобі.
- 'Інші витрати': Використовуй ТІЛЬКИ якщо опис не має жодного відношення до харчування, покупок або транспортних послуг.

Список дозволених категорій: {allowed_cats}

Поверни ЛИШЕ валідний JSON у форматі {{"category": "Назва з списку"}}.

Опис операції: "{description}"
Тип операції: {tx_type}"""

            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                },
                timeout=3
            )
            if resp.status_code == 200:
                res_data = resp.json()
                content = res_data['choices'][0]['message']['content']
                parsed = json.loads(content)
                candidate = parsed.get("category", "").strip()
                if candidate in allowed_cats:
                    cat_result = candidate
        except Exception as e:
            print(f"Groq categorization error: {e}")
            
    elif openai_api_key:
        try:
            import requests
            prompt = f"""Ти інтелектуальний фінансовий аналітик додатка MonoFinance.
Проаналізуй опис транзакції та ОБЕРИ ТОЧНО ОДНУ із дозволених категорій.

Список дозволених категорій: {allowed_cats}
Поверни ЛИШЕ JSON об'єкт у форматі {{"category": "Назва з списку"}}.

Опис операції: "{description}"
Тип операції: {tx_type}"""

            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                },
                timeout=3
            )
            if resp.status_code == 200:
                res_data = resp.json()
                content = res_data['choices'][0]['message']['content']
                parsed = json.loads(content)
                candidate = parsed.get("category", "").strip()
                if candidate in allowed_cats:
                    cat_result = candidate
        except Exception as e:
            print(f"OpenAI categorization error: {e}")

    if not cat_result:
        cat_result = fallback_categorize(description, tx_type)

    icon_name = CATEGORY_ICON_MAP.get(cat_result, 'receipt_long')

    return jsonify({
        'success': True,
        'category': cat_result,
        'icon': icon_name
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
'''
    with open('app_server.py', 'w', encoding='utf-8') as f:
        f.write(code_before + new_func)
    print("Replaced categorize_transaction cleanly!")
