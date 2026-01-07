"""
Тестовый скрипт для веб-интерфейса
Создает игру с тестовыми данными и симулирует раунды
"""
import asyncio
import uvicorn
from web_server import app, set_game, broadcast_update
from game_engine import Game
import threading
import time

def create_test_game():
    """Создает тестовую игру с несколькими игроками"""
    game = Game(num_players=10)
    
    # Добавляем игроков
    for i in range(1, 11):
        game.add_player(f"player{i}", f"Игрок {i}")
    
    # Раунд 1: Игроки покупают ресурсы и строят объекты
    print("Раунд 1: Игроки совершают действия...")
    
    # Игрок 1 строит Лесоповал
    game.buy_resource("player1", "железо", 5)
    game.buy_resource("player1", "рабы", 3)
    game.start_building("player1", "Лесоповал")
    
    # Игрок 2 строит Каменоломню
    game.buy_resource("player2", "дерево", 10)
    game.buy_resource("player2", "железо", 5)
    game.buy_resource("player2", "рабы", 3)
    game.start_building("player2", "Каменоломня")
    
    # Игрок 3 строит Трактир
    game.buy_resource("player3", "дерево", 14)
    game.buy_resource("player3", "камень", 10)
    game.buy_resource("player3", "железо", 3)
    game.buy_resource("player3", "золото", 1)
    game.start_building("player3", "Трактир")
    
    # Игрок 4 покупает много дерева (для спроса)
    game.buy_resource("player4", "дерево", 20)
    game.buy_resource("player4", "камень", 15)
    
    # Игрок 5 продает ресурсы (для предложения)
    game.buy_resource("player5", "зерно", 10)
    game.sell_resource("player5", "зерно", 5)
    
    # Игрок 6 строит Ферму
    game.buy_resource("player6", "дерево", 16)
    game.buy_resource("player6", "камень", 10)
    game.buy_resource("player6", "скот", 4)
    game.buy_resource("player6", "зерно", 8)
    game.start_building("player6", "Ферма")
    
    # Игрок 7 строит Рыболовню
    game.buy_resource("player7", "дерево", 18)
    game.buy_resource("player7", "железо", 6)
    game.buy_resource("player7", "камень", 5)
    game.start_building("player7", "Рыболовня")
    
    # Обрабатываем раунд 1
    game.process_round()
    print("Раунд 1 завершен")
    
    return game

async def simulate_rounds(game):
    """Симулирует дополнительные раунды"""
    await asyncio.sleep(2)  # Даем время для подключения веб-интерфейса
    
    for round_num in range(2, 6):
        print(f"\nРаунд {round_num}: Игроки совершают действия...")
        
        # Игроки продолжают действовать
        if round_num == 2:
            game.buy_resource("player8", "дерево", 10)
            game.buy_resource("player9", "железо", 8)
            game.buy_resource("player10", "камень", 12)
        elif round_num == 3:
            # Игрок 1 выставляет объект на продажу (если он активен)
            player1 = game.get_player("player1")
            if player1.buildings:
                for building in player1.buildings:
                    if building.status.value == "active":
                        game.put_building_for_sale("player1", building.id)
                        break
        elif round_num == 4:
            # Игроки покупают разные ресурсы для разнообразия
            game.buy_resource("player2", "золото", 2)
            game.buy_resource("player3", "скот", 5)
        
        # Обрабатываем раунд
        result = game.process_round()
        print(f"Раунд {round_num} завершен")
        if result.get("events"):
            print(f"  События: {result['events']['positive']} + {result['events']['negative']}")
        
        # Отправляем обновление в веб-интерфейс
        await broadcast_update()
        
        # Ждем перед следующим раундом
        await asyncio.sleep(5)

def run_simulation(game):
    """Запускает симуляцию в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(simulate_rounds(game))

if __name__ == "__main__":
    # Создаем тестовую игру
    game = create_test_game()
    set_game(game)
    
    # Запускаем симуляцию в отдельном потоке
    simulation_thread = threading.Thread(target=run_simulation, args=(game,), daemon=True)
    simulation_thread.start()
    
    print("\n" + "="*50)
    print("Веб-сервер запускается...")
    print("Откройте в браузере: http://localhost:8000")
    print("Симуляция раундов будет запущена через 2 секунды")
    print("="*50 + "\n")
    
    # Запускаем веб-сервер
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

