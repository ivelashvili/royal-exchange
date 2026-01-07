"""
Веб-сервер для отображения игры на проекторе
FastAPI + WebSocket для обновлений в реальном времени
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
import json
import asyncio
from urllib.parse import unquote
from game_engine import Game
from game_config import RESOURCE_PRICES

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

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

