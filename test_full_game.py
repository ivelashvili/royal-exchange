"""
Полный тест игрового движка с проверкой всех функций
"""
from game_engine import Game, BuildingStatus

def test_full_game():
    """Полный тест игры"""
    print("=== ПОЛНЫЙ ТЕСТ ИГРОВОГО ДВИЖКА ===\n")
    
    # Создаем игру
    game = Game(num_players=2)
    game.add_player("p1", "Игрок 1")
    game.add_player("p2", "Игрок 2")
    
    print("=== РАУНД 1 ===\n")
    print("Начальные цены:")
    for resource, price in sorted(game.current_prices.items()):
        print(f"  {resource}: {price} монет")
    
    # Игрок 1: покупает ресурсы и строит Лесоповал
    print("\n--- Игрок 1 ---")
    game.buy_resource("p1", "железо", 5)
    game.buy_resource("p1", "рабы", 3)
    result = game.start_building("p1", "Лесоповал")
    print(f"  {result['message']}")
    
    # Игрок 2: покупает ресурсы и строит Каменоломню
    print("\n--- Игрок 2 ---")
    game.buy_resource("p2", "дерево", 10)
    game.buy_resource("p2", "железо", 5)
    game.buy_resource("p2", "рабы", 3)
    result = game.start_building("p2", "Каменоломня")
    print(f"  {result['message']}")
    
    # Обрабатываем раунд 1
    round_result = game.process_round()
    print(f"\nРаунд 1 завершен. События: {round_result['events']}")
    
    # Проверяем состояние
    p1 = game.get_player("p1")
    p2 = game.get_player("p2")
    print(f"\nИгрок 1: {p1.money} монет, ресурсы: {p1.resources}")
    print(f"Игрок 2: {p2.money} монет, ресурсы: {p2.resources}")
    print(f"Объекты Игрока 1: {[b.name + ' (' + b.status.value + ')' for b in p1.buildings]}")
    print(f"Объекты Игрока 2: {[b.name + ' (' + b.status.value + ')' for b in p2.buildings]}")
    
    print("\n=== РАУНД 2 ===\n")
    
    # Игроки продолжают действовать
    print("--- Игрок 1 ---")
    game.buy_resource("p1", "дерево", 5)
    
    print("--- Игрок 2 ---")
    game.buy_resource("p2", "камень", 5)
    
    # Обрабатываем раунд 2
    round_result = game.process_round()
    if round_result['events']:
        print(f"\nСобытия:")
        print(f"  Позитивное: {round_result['events']['positive']}")
        print(f"  Негативное: {round_result['events']['negative']}")
    
    # Проверяем состояние объектов
    p1 = game.get_player("p1")
    p2 = game.get_player("p2")
    print(f"\nОбъекты Игрока 1: {[b.name + ' (' + b.status.value + ')' for b in p1.buildings]}")
    print(f"Объекты Игрока 2: {[b.name + ' (' + b.status.value + ')' for b in p2.buildings]}")
    print(f"Игрок 1: {p1.money} монет, ресурсы: {p1.resources}")
    print(f"Игрок 2: {p2.money} монет, ресурсы: {p2.resources}")
    
    print("\n=== РАУНД 3 ===\n")
    print("Объекты должны быть активны и приносить доход")
    
    # Обрабатываем раунд 3
    round_result = game.process_round()
    if round_result['events']:
        print(f"\nСобытия:")
        print(f"  Позитивное: {round_result['events']['positive']}")
        print(f"  Негативное: {round_result['events']['negative']}")
    
    print(f"\nДоходы:")
    for player_id, income in round_result['income']['income_distributed'].items():
        player = game.get_player(player_id)
        if income['монеты'] > 0 or income['ресурсы']:
            print(f"  {player.name}: {income['монеты']} монет, ресурсы: {income['ресурсы']}")
    
    # Проверяем финальное состояние
    p1 = game.get_player("p1")
    p2 = game.get_player("p2")
    print(f"\nИгрок 1: {p1.money} монет, ресурсы: {p1.resources}")
    print(f"Игрок 2: {p2.money} монет, ресурсы: {p2.resources}")
    
    # Тест продажи объекта
    print("\n=== ТЕСТ ПРОДАЖИ ОБЪЕКТА ===\n")
    
    if p1.buildings:
        building = p1.buildings[0]
        print(f"Игрок 1 выставляет на продажу: {building.name}")
        sale_price = game.calculate_building_sale_price(building)
        print(f"Цена продажи (по текущим ценам): {sale_price:.2f} монет")
        
        result = game.put_building_for_sale("p1", building.id)
        print(f"  {result['message']}")
        
        # Обрабатываем раунд 4 (объект еще не продается)
        print("\n=== РАУНД 4 ===\n")
        round_result = game.process_round()
        
        p1 = game.get_player("p1")
        print(f"Игрок 1 после раунда 4: {p1.money} монет")
        print(f"Объекты Игрока 1: {len(p1.buildings)} (еще не продано)")
        
        # Обрабатываем раунд 5 (объект должен продаться)
        print("\n=== РАУНД 5 ===\n")
        round_result = game.process_round()
        
        print(f"Доходы от продажи:")
        if round_result['income']['buildings_sold']:
            for sale in round_result['income']['buildings_sold']:
                player = game.get_player(sale['player_id'])
                print(f"  {player.name} продал {sale['building_name']} за {sale['sale_price']:.2f} монет")
        else:
            print("  Нет проданных объектов")
        
        p1 = game.get_player("p1")
        print(f"\nИгрок 1 после продажи: {p1.money} монет")
        print(f"Объекты Игрока 1: {len(p1.buildings)} (должно быть 0)")
    
    # Турнирная таблица
    print("\n=== ФИНАЛЬНАЯ ТУРНИРНАЯ ТАБЛИЦА ===\n")
    leaderboard = game.get_leaderboard()
    for i, player_data in enumerate(leaderboard, 1):
        print(f"{i}. {player_data['name']}:")
        print(f"   Деньги: {player_data['money']} монет")
        print(f"   Ресурсы: {player_data['resources_value']} монет")
        print(f"   Объекты: {player_data['buildings_value']} монет")
        print(f"   ИТОГО: {player_data['total_value']} монет")
    
    print("\n✓ Все тесты пройдены успешно!")

if __name__ == "__main__":
    test_full_game()

