"""
Тест игрового движка
"""
from game_engine import Game

def test_game_engine():
    """Тестирование игрового движка"""
    print("=== ТЕСТ ИГРОВОГО ДВИЖКА ===\n")
    
    # Создаем игру
    game = Game(num_players=3)
    
    # Добавляем игроков
    game.add_player("player1", "Игрок 1")
    game.add_player("player2", "Игрок 2")
    game.add_player("player3", "Игрок 3")
    
    print("Игроки добавлены:")
    for player in game.players:
        print(f"  {player.name} (ID: {player.id}) - {player.money} монет")
    
    print(f"\n=== РАУНД 1 ===\n")
    print("Текущие цены:")
    for resource, price in sorted(game.current_prices.items()):
        print(f"  {resource}: {price} монет")
    
    # Раунд 1: Игроки покупают ресурсы
    print("\n--- Фаза закупок (Раунд 1) ---")
    
    # Игрок 1 покупает дерево
    result = game.buy_resource("player1", "дерево", 10)
    print(f"Игрок 1: {result['message']}")
    
    # Игрок 2 покупает железо
    result = game.buy_resource("player2", "железо", 5)
    print(f"Игрок 2: {result['message']}")
    
    # Игрок 3 покупает камень
    result = game.buy_resource("player3", "камень", 8)
    print(f"Игрок 3: {result['message']}")
    
    # Игрок 1 начинает строительство
    result = game.start_building("player1", "Лесоповал")
    print(f"Игрок 1: {result['message']}")
    
    # Обрабатываем раунд 1
    print("\n--- Обработка раунда 1 ---")
    round_result = game.process_round()
    
    print(f"События: {round_result['events']}")
    print(f"Новые цены:")
    for resource, price in sorted(round_result['prices'].items()):
        old_price = RESOURCE_PRICES[resource]
        if price != old_price:
            change = ((price - old_price) / old_price) * 100
            print(f"  {resource}: {old_price} → {price} ({change:+.1f}%)")
        else:
            print(f"  {resource}: {price} (без изменений)")
    
    print(f"\n=== РАУНД 2 ===\n")
    
    # Проверяем состояние игроков
    print("Состояние игроков:")
    for player in game.players:
        state = game.get_player_state(player.id)
        print(f"\n{player.name}:")
        print(f"  Деньги: {state['money']} монет")
        print(f"  Ресурсы: {state['resources']}")
        print(f"  Объекты: {len(state['buildings'])}")
        for building in state['buildings']:
            print(f"    - {building['name']} ({building['status']})")
    
    # Раунд 2: Игроки продолжают действовать
    print("\n--- Фаза закупок (Раунд 2) ---")
    
    # Игрок 2 покупает еще ресурсы
    result = game.buy_resource("player2", "дерево", 5)
    print(f"Игрок 2: {result['message']}")
    
    # Игрок 3 продает камень
    result = game.sell_resource("player3", "камень", 3)
    print(f"Игрок 3: {result['message']}")
    
    # Обрабатываем раунд 2
    print("\n--- Обработка раунда 2 ---")
    round_result = game.process_round()
    
    if round_result['events']:
        print(f"События:")
        print(f"  Позитивное: {round_result['events']['positive']}")
        print(f"  Негативное: {round_result['events']['negative']}")
    
    print(f"\nДоходы:")
    for player_id, income in round_result['income']['income_distributed'].items():
        player = game.get_player(player_id)
        if income['монеты'] > 0 or income['ресурсы']:
            print(f"  {player.name}: {income['монеты']} монет, ресурсы: {income['ресурсы']}")
    
    print(f"\nНовые цены:")
    for resource, price in sorted(round_result['prices'].items()):
        old_price = game.round_history[-2]['prices'][resource] if len(game.round_history) > 1 else RESOURCE_PRICES[resource]
        if price != old_price:
            change = ((price - old_price) / old_price) * 100
            print(f"  {resource}: {old_price:.2f} → {price:.2f} ({change:+.1f}%)")
    
    print(f"\n=== РАУНД 3 ===\n")
    
    # Проверяем состояние игроков
    print("Состояние игроков:")
    for player in game.players:
        state = game.get_player_state(player.id)
        print(f"\n{player.name}:")
        print(f"  Деньги: {state['money']} монет")
        print(f"  Ресурсы: {state['resources']}")
        print(f"  Объекты: {len(state['buildings'])}")
        for building in state['buildings']:
            print(f"    - {building['name']} ({building['status']})")
    
    # Раунд 3: Игроки получают доходы
    print("\n--- Фаза закупок (Раунд 3) ---")
    # Игроки ничего не делают, просто ждут доходов
    
    # Обрабатываем раунд 3
    print("\n--- Обработка раунда 3 ---")
    round_result = game.process_round()
    
    if round_result['events']:
        print(f"События:")
        print(f"  Позитивное: {round_result['events']['positive']}")
        print(f"  Негативное: {round_result['events']['negative']}")
    
    print(f"\nДоходы:")
    for player_id, income in round_result['income']['income_distributed'].items():
        player = game.get_player(player_id)
        if income['монеты'] > 0 or income['ресурсы']:
            print(f"  {player.name}: {income['монеты']} монет, ресурсы: {income['ресурсы']}")
    
    # Турнирная таблица
    print(f"\n=== ТУРНИРНАЯ ТАБЛИЦА ===\n")
    leaderboard = game.get_leaderboard()
    for i, player_data in enumerate(leaderboard, 1):
        print(f"{i}. {player_data['name']}:")
        print(f"   Деньги: {player_data['money']} монет")
        print(f"   Ресурсы: {player_data['resources_value']} монет")
        print(f"   Объекты: {player_data['buildings_value']} монет")
        print(f"   ИТОГО: {player_data['total_value']} монет")
    
    print("\n✓ Тест завершен успешно!")

if __name__ == "__main__":
    from game_config import RESOURCE_PRICES
    test_game_engine()

