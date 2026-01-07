"""
Веб-сервер для отображения игры на проекторе
FastAPI + WebSocket для обновлений в реальном времени
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Optional
import json
import asyncio
import hmac
import hashlib
import base64
from urllib.parse import unquote, parse_qs
from game_engine import Game, BuildingStatus
from game_config import RESOURCE_PRICES, BUILDING_COSTS, BUILDING_INCOME

app = FastAPI(title="Королевская биржа - Веб-интерфейс")

# Глобальное состояние игры (будет инициализировано)
game_instance: Game = None
previous_leaderboard: List[Dict] = []
initial_prices: Dict[str, float] = RESOURCE_PRICES.copy()

# WebSocket подключения
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup():
    """Инициализация при старте"""
    global game_instance
    # Игра будет создана отдельно или передана сюда
    pass

def set_game(game: Game):
    """Установить игровой экземпляр"""
    global game_instance
    game_instance = game

@app.get("/", response_class=HTMLResponse)
async def get_main_page():
    """Главная страница"""
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/miniapp", response_class=HTMLResponse)
async def get_miniapp_page():
    """Страница Telegram Mini App"""
    with open("templates/miniapp.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/leaderboard")
async def get_leaderboard():
    """Получить турнирную таблицу с приростом"""
    if not game_instance:
        return {"error": "Игра не инициализирована"}
    
    current_leaderboard = game_instance.get_leaderboard()
    global previous_leaderboard
    
    # Добавляем прирост от предыдущего раунда
    result = []
    for player in current_leaderboard:
        player_data = player.copy()
        
        # Ищем предыдущее значение
        prev_player = next(
            (p for p in previous_leaderboard if p["player_id"] == player["player_id"]),
            None
        )
        
        if prev_player:
            prev_value = prev_player["total_value"]
            if prev_value > 0:
                growth = ((player["total_value"] - prev_value) / prev_value) * 100
            else:
                growth = 0
        else:
            growth = 0
        
        player_data["growth_percent"] = round(growth, 2)
        # Округляем все значения до целых
        player_data["money"] = int(round(player_data["money"]))
        player_data["resources_value"] = int(round(player_data["resources_value"]))
        player_data["buildings_value"] = int(round(player_data["buildings_value"]))
        player_data["total_value"] = int(round(player_data["total_value"]))
        result.append(player_data)
    
    previous_leaderboard = current_leaderboard.copy()
    return {"leaderboard": result}

@app.get("/api/prices")
async def get_prices():
    """Получить текущие цены с изменениями"""
    if not game_instance:
        return {"error": "Игра не инициализирована"}
    
    current_prices = game_instance.current_prices
    global initial_prices
    
    # Получаем предыдущие цены
    # round_history содержит цены ПОСЛЕ обработки раунда
    # Для получения предыдущих цен нужно взять цены из предыдущего элемента истории
    previous_prices = {}
    if len(game_instance.round_history) >= 2:
        # Берем цены из предпоследнего раунда (предыдущего)
        previous_prices = game_instance.round_history[-2].get("prices", initial_prices.copy())
    elif len(game_instance.round_history) == 1:
        # Если это второй раунд, предыдущие цены - начальные (до первого раунда)
        previous_prices = initial_prices.copy()
    else:
        # Первый раунд - предыдущих цен нет, используем начальные
        previous_prices = initial_prices.copy()
    
    result = []
    for resource, current_price in sorted(current_prices.items()):
        initial_price = initial_prices.get(resource, current_price)
        prev_price = previous_prices.get(resource, current_price)
        
        # Изменение от предыдущего раунда
        if prev_price > 0:
            change_from_prev = ((current_price - prev_price) / prev_price) * 100
        else:
            change_from_prev = 0
        
        # Изменение с начала игры
        if initial_price > 0:
            change_from_start = ((current_price - initial_price) / initial_price) * 100
        else:
            change_from_start = 0
        
        result.append({
            "resource": resource,
            "current_price": int(round(current_price)),
            "change_from_prev_percent": round(change_from_prev, 2),
            "change_from_start_percent": round(change_from_start, 2)
        })
    
    return {"prices": result}

@app.get("/api/buildings")
async def get_buildings():
    """Получить статистику по построенным объектам"""
    if not game_instance:
        return {"error": "Игра не инициализирована"}
    
    building_counts = {}
    players_with_building = {}  # Сколько игроков имеют хотя бы один такой объект
    
    for player in game_instance.players:
        player_buildings = set()  # Уникальные объекты игрока
        for building in player.buildings:
            if building.status.value != "for_sale":
                building_counts[building.name] = building_counts.get(building.name, 0) + 1
                player_buildings.add(building.name)
        
        # Подсчитываем игроков с каждым объектом
        for building_name in player_buildings:
            players_with_building[building_name] = players_with_building.get(building_name, 0) + 1
    
    result = []
    num_players = len(game_instance.players)
    for building_name, count in sorted(building_counts.items()):
        players_count = players_with_building.get(building_name, 0)
        players_percentage = round((players_count / num_players) * 100) if num_players > 0 else 0
        
        result.append({
            "name": building_name,
            "count": count,
            "players_percentage": players_percentage
        })
    
    return {"buildings": result}

@app.get("/api/resource/{resource_name}")
async def get_resource_details(resource_name: str):
    """Получить детальную информацию о ресурсе, включая историю цен и спрос/предложение"""
    if not game_instance:
        return {"error": "Игра не инициализирована"}
    
    # Декодируем имя ресурса из URL (для кириллицы)
    resource_name = unquote(resource_name)
    
    global initial_prices
    
    # Получаем текущую цену
    current_price = game_instance.current_prices.get(resource_name, 0)
    initial_price = initial_prices.get(resource_name, current_price)
    
    # Получаем предыдущие цены для расчета изменений
    previous_prices = {}
    if len(game_instance.round_history) >= 2:
        previous_prices = game_instance.round_history[-2].get("prices", initial_prices.copy())
    elif len(game_instance.round_history) == 1:
        previous_prices = initial_prices.copy()
    else:
        previous_prices = initial_prices.copy()
    
    prev_price = previous_prices.get(resource_name, current_price)
    
    # Изменение от предыдущего раунда
    if prev_price > 0:
        change_from_prev = ((current_price - prev_price) / prev_price) * 100
    else:
        change_from_prev = 0
    
    # Изменение с начала игры
    if initial_price > 0:
        change_from_start = ((current_price - initial_price) / initial_price) * 100
    else:
        change_from_start = 0
    
    # История цен (с начала игры до текущего раунда)
    # Стандартизация: в точке 0 (раунд 0) цена = 0
    price_history = []
    price_history.append({"round": 0, "price": 0})  # Начальная точка - цена 0
    
    for i, round_data in enumerate(game_instance.round_history, start=1):
        round_prices = round_data.get("prices", {})
        price = round_prices.get(resource_name, initial_price)
        price_history.append({"round": i, "price": price})
    
    # Добавляем текущую цену
    price_history.append({"round": game_instance.current_round, "price": current_price})
    
    # Определяем уровень спроса и предложения
    num_players = len(game_instance.players)
    players_bought = game_instance.previous_round_players_bought.get(resource_name, 0)
    players_sold = game_instance.previous_round_players_sold.get(resource_name, 0)
    
    # Спрос (по логике из market_dynamics.py: >75% высокий, >25% средний, иначе низкий)
    if num_players > 0:
        demand_percent = (players_bought / num_players) * 100
        if demand_percent > 75:
            demand_level = "высокий"
        elif demand_percent > 25:
            demand_level = "базовый"
        else:
            demand_level = "низкий"
    else:
        demand_level = "базовый"
    
    # Предложение (по логике из market_dynamics.py: >75% высокое, >25% среднее, иначе низкое)
    if num_players > 0:
        supply_percent = (players_sold / num_players) * 100
        if supply_percent > 75:
            supply_level = "высокое"
        elif supply_percent > 25:
            supply_level = "базовое"
        else:
            supply_level = "низкое"
    else:
        supply_level = "базовое"
    
    return {
        "name": resource_name,
        "current_price": int(round(current_price)),
        "change_from_prev_percent": round(change_from_prev, 2),
        "change_from_start_percent": round(change_from_start, 2),
        "demand_level": demand_level,
        "supply_level": supply_level,
        "price_history": price_history
    }

@app.get("/api/building/{building_name}")
async def get_building_details(building_name: str):
    """Получить детальную информацию об объекте, включая список владельцев"""
    if not game_instance:
        return {"error": "Игра не инициализирована"}
    
    # Подсчитываем общее количество объектов
    total_count = 0
    owners = {}  # {player_id: {name: str, count: int}}
    
    for player in game_instance.players:
        player_building_count = 0
        for building in player.buildings:
            if building.name == building_name and building.status.value != "for_sale":
                total_count += 1
                player_building_count += 1
        
        if player_building_count > 0:
            owners[player.id] = {
                "name": player.name,
                "count": player_building_count
            }
    
    # Подсчитываем процент игроков
    num_players = len(game_instance.players)
    players_count = len(owners)
    players_percentage = round((players_count / num_players) * 100) if num_players > 0 else 0
    
    # Сортируем владельцев по количеству объектов (от большего к меньшему)
    owners_list = sorted(owners.values(), key=lambda x: x["count"], reverse=True)
    
    return {
        "name": building_name,
        "count": total_count,
        "players_percentage": players_percentage,
        "owners": owners_list
    }

@app.get("/api/game_state")
async def get_game_state():
    """Получить полное состояние игры"""
    if not game_instance:
        return {"error": "Игра не инициализирована"}
    
    leaderboard_data = await get_leaderboard()
    prices_data = await get_prices()
    buildings_data = await get_buildings()
    
    return {
        "current_round": game_instance.current_round,
        "num_players": len(game_instance.players),
        "leaderboard": leaderboard_data,
        "prices": prices_data,
        "buildings": buildings_data
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для обновлений в реальном времени"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Отправляем обновление каждую секунду
            state = await get_game_state()
            await websocket.send_json(state)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_update():
    """Отправить обновление всем подключенным клиентам"""
    if not active_connections:
        return
    
    state = await get_game_state()
    
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(state)
        except:
            disconnected.append(connection)
    
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

# ========== TELEGRAM MINI APP API ==========

def verify_telegram_auth(init_data: str) -> Optional[Dict]:
    """
    Проверка авторизации через Telegram WebApp API
    В продакшене нужно использовать секретный ключ бота
    Для тестирования упрощенная проверка
    """
    try:
        # Парсим init_data
        params = parse_qs(init_data)
        
        # Извлекаем данные пользователя
        user_str = params.get('user', [None])[0]
        if not user_str:
            return None
        
        user = json.loads(user_str)
        return user
    except Exception as e:
        print(f"Ошибка проверки авторизации: {e}")
        return None

def get_player_id_from_telegram(init_data: str) -> Optional[str]:
    """Получить player_id из Telegram данных"""
    user = verify_telegram_auth(init_data)
    if not user:
        return None
    return f"tg_{user.get('id')}"

@app.get("/api/miniapp/player/state")
async def get_player_state(request: Request, x_telegram_init_data: Optional[str] = Header(None)):
    """Получить состояние игрока"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    player_id = get_player_id_from_telegram(x_telegram_init_data)
    if not player_id:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    
    player = game_instance.get_player(player_id)
    if not player:
        # Игрок не найден - нужно авторизоваться
        return {
            "player_id": None,
            "nickname": None,
            "photo_url": None,
            "money": 0,
            "resources": {},
            "buildings": []
        }
    
    # Формируем ответ
    buildings_data = []
    for building in player.buildings:
        buildings_data.append({
            "id": building.id,
            "name": building.name,
            "status": building.status.value
        })
    
    return {
        "player_id": player.id,
        "name": player.name,
        "nickname": player.nickname,
        "photo_url": player.photo_url,
        "money": int(round(player.money)),
        "resources": player.resources.copy(),
        "buildings": buildings_data
    }

@app.post("/api/miniapp/player/auth")
async def save_player_auth(request: Request, x_telegram_init_data: Optional[str] = Header(None)):
    """Сохранить данные авторизации игрока (никнейм и фото)"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    player_id = get_player_id_from_telegram(x_telegram_init_data)
    if not player_id:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    
    data = await request.json()
    nickname = data.get("nickname", "").strip()
    photo_url = data.get("photo_url")
    
    if not nickname or len(nickname) < 2:
        return {"success": False, "message": "Никнейм должен быть не менее 2 символов"}
    
    # Проверяем, существует ли игрок
    player = game_instance.get_player(player_id)
    if not player:
        # Создаем нового игрока
        user = verify_telegram_auth(x_telegram_init_data)
        default_name = user.get('first_name', user.get('username', 'Игрок')) if user else 'Игрок'
        game_instance.add_player(player_id, default_name)
        player = game_instance.get_player(player_id)
    
    # Обновляем никнейм и фото
    player.nickname = nickname
    player.photo_url = photo_url
    
    return {
        "success": True,
        "message": "Данные сохранены",
        "nickname": nickname,
        "photo_url": photo_url
    }

@app.get("/api/miniapp/prices")
async def get_miniapp_prices():
    """Получить текущие цены (упрощенная версия для Mini App)"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    result = []
    for resource, price in sorted(game_instance.current_prices.items()):
        result.append({
            "resource": resource,
            "current_price": int(round(price)),
            "change_from_prev_percent": 0  # Упрощенно, можно добавить расчет
        })
    
    return {"prices": result}

@app.get("/api/miniapp/round-info")
async def get_round_info():
    """Получить информацию о текущем раунде"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    return {
        "current_round": game_instance.current_round,
        "num_players": len(game_instance.players)
    }

@app.get("/api/miniapp/buildings")
async def get_available_buildings(request: Request, x_telegram_init_data: Optional[str] = Header(None)):
    """Получить список доступных объектов для строительства"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    player_id = get_player_id_from_telegram(x_telegram_init_data)
    if not player_id:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    
    player = game_instance.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    
    result = []
    for building_name, costs in BUILDING_COSTS.items():
        can_build = player.has_resources(costs)
        cost = game_instance.calculate_building_cost(building_name)
        
        # Формируем описание стоимости
        cost_details = []
        for resource, amount in costs.items():
            cost_details.append(f"{amount} {resource}")
        
        result.append({
            "name": building_name,
            "cost": int(round(cost)),
            "cost_details": ", ".join(cost_details),
            "can_build": can_build
        })
    
    return {"buildings": result}

@app.post("/api/miniapp/player/buy-resource")
async def buy_resource_miniapp(request: Request, x_telegram_init_data: Optional[str] = Header(None)):
    """Купить ресурс"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    player_id = get_player_id_from_telegram(x_telegram_init_data)
    if not player_id:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    
    data = await request.json()
    resource = data.get("resource")
    amount = data.get("amount", 1)
    
    result = game_instance.buy_resource(player_id, resource, amount)
    result["cost"] = int(round(result.get("cost", 0)))
    
    return result

@app.post("/api/miniapp/player/sell-resource")
async def sell_resource_miniapp(request: Request, x_telegram_init_data: Optional[str] = Header(None)):
    """Продать ресурс"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    player_id = get_player_id_from_telegram(x_telegram_init_data)
    if not player_id:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    
    data = await request.json()
    resource = data.get("resource")
    amount = data.get("amount", 1)
    
    result = game_instance.sell_resource(player_id, resource, amount)
    result["income"] = int(round(result.get("income", 0)))
    
    return result

@app.post("/api/miniapp/player/build")
async def build_miniapp(request: Request, x_telegram_init_data: Optional[str] = Header(None)):
    """Построить объект"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    player_id = get_player_id_from_telegram(x_telegram_init_data)
    if not player_id:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    
    data = await request.json()
    building_name = data.get("building_name")
    
    result = game_instance.start_building(player_id, building_name)
    return result

@app.post("/api/miniapp/player/sell-building")
async def sell_building_miniapp(request: Request, x_telegram_init_data: Optional[str] = Header(None)):
    """Продать объект"""
    if not game_instance:
        raise HTTPException(status_code=500, detail="Игра не инициализирована")
    
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    player_id = get_player_id_from_telegram(x_telegram_init_data)
    if not player_id:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    
    data = await request.json()
    building_id = data.get("building_id")
    
    result = game_instance.put_building_for_sale(player_id, building_id)
    return result

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

