"""
Запуск веб-сервера
"""
import os
import uvicorn
from web_server import app, set_game
from game_engine import Game

if __name__ == "__main__":
    # Создаем игру (можно будет загружать из БД)
    game = Game(num_players=30)
    set_game(game)
    
    # Запускаем сервер
    # Railway передает порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

