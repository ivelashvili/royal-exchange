"""
Сценарный анализ игры "Королевская биржа"
Симуляция 10 раундов с различными наборами событий
"""
import random
from typing import Dict, List
from game_config import RESOURCE_PRICES, BUILDING_INCOME, BUILDING_COSTS
from game_events import EVENT_PAIRS, EventSystem, POSITIVE_EVENTS, NEGATIVE_EVENTS
from market_dynamics import MarketDynamics

# Создаем словари для быстрого поиска событий
positive_events_dict = {e["name"]: e for e in POSITIVE_EVENTS}
negative_events_dict = {e["name"]: e for e in NEGATIVE_EVENTS}

def calculate_building_cost(costs: Dict[str, int]) -> float:
    """Рассчитывает стоимость объекта в монетах"""
    total = 0
    for resource, amount in costs.items():
        total += amount * RESOURCE_PRICES.get(resource, 0)
    return total

def simulate_game_scenario(event_pairs: List[tuple], num_rounds: int = 10) -> Dict:
    """
    Симулирует игру с заданным набором пар событий
    
    Args:
        event_pairs: Список пар событий (positive_event, negative_event)
        num_rounds: Количество раундов
        
    Returns:
        Словарь с результатами симуляции
    """
    # Инициализация
    current_prices = RESOURCE_PRICES.copy()
    base_prices = RESOURCE_PRICES.copy()
    
    # Для упрощения: считаем что спрос/предложение нейтральны (только события влияют)
    total_bought = {res: 0 for res in RESOURCE_PRICES.keys()}
    total_sold = {res: 0 for res in RESOURCE_PRICES.keys()}
    
    # Словарь для накопления доходов объектов
    building_total_income = {name: {"монеты": 0, "ресурсы": {}} for name in BUILDING_INCOME.keys()}
    
    # Симулируем каждый раунд
    for round_num, (positive_event, negative_event) in enumerate(event_pairs[:num_rounds], 1):
        # Получаем модификаторы от событий
        resource_mods, building_mods = EventSystem().combine_event_modifiers(
            positive_event, negative_event
        )
        
        # Применяем модификаторы к ценам (упрощенно - только события)
        for resource in current_prices.keys():
            if resource in resource_mods:
                # Применяем модификатор события
                current_prices[resource] *= resource_mods[resource]
            # Ограничиваем изменения (как в market_dynamics)
            max_change = 1.0 + 0.50  # 50% за раунд
            min_change = 1.0 - 0.50
            price_change = current_prices[resource] / base_prices[resource]
            if price_change > max_change:
                current_prices[resource] = base_prices[resource] * max_change
            elif price_change < min_change:
                current_prices[resource] = base_prices[resource] * min_change
            
            # Абсолютные ограничения
            current_prices[resource] = max(
                base_prices[resource] * 0.3,
                min(base_prices[resource] * 3.0, current_prices[resource])
            )
        
        # Рассчитываем доходы объектов с учетом модификаторов
        for building_name, base_income in BUILDING_INCOME.items():
            modifier = building_mods.get(building_name, 1.0)
            
            # Монеты
            coins = base_income.get("монеты", 0) * modifier
            building_total_income[building_name]["монеты"] += coins
            
            # Ресурсы
            for resource, amount in base_income.get("ресурсы", {}).items():
                actual_amount = amount * modifier
                if resource not in building_total_income[building_name]["ресурсы"]:
                    building_total_income[building_name]["ресурсы"][resource] = 0
                building_total_income[building_name]["ресурсы"][resource] += actual_amount
    
    # Рассчитываем итоговые изменения цен
    price_changes = {}
    for resource in base_prices.keys():
        change_percent = ((current_prices[resource] - base_prices[resource]) / base_prices[resource]) * 100
        price_changes[resource] = {
            "start": base_prices[resource],
            "end": current_prices[resource],
            "change_percent": change_percent
        }
    
    # Рассчитываем общую стоимость доходов объектов
    building_results = {}
    for building_name, income_data in building_total_income.items():
        total_value = income_data["монеты"]
        
        # Добавляем стоимость ресурсов по финальным ценам
        for resource, amount in income_data["ресурсы"].items():
            total_value += amount * current_prices[resource]
        
        # Стоимость объекта
        building_cost = calculate_building_cost(BUILDING_COSTS[building_name])
        
        building_results[building_name] = {
            "cost": building_cost,
            "total_income_coins": income_data["монеты"],
            "total_income_resources": income_data["ресурсы"].copy(),
            "total_income_value": total_value,
            "roi_percent": (total_value / building_cost * 100) if building_cost > 0 else 0
        }
    
    return {
        "price_changes": price_changes,
        "building_results": building_results,
        "events_used": [(pos["name"], neg["name"]) for pos, neg in event_pairs[:num_rounds]]
    }

def generate_scenario_analysis(num_scenarios: int = 10, rounds_per_scenario: int = 10) -> List[Dict]:
    """
    Генерирует несколько сценариев игры
    
    Args:
        num_scenarios: Количество сценариев
        rounds_per_scenario: Количество раундов в каждом сценарии
        
    Returns:
        Список результатов симуляций
    """
    results = []
    event_system = EventSystem()
    
    for scenario_num in range(num_scenarios):
        # Генерируем набор пар событий
        # Используем все доступные пары, перемешивая их
        available_pairs = EVENT_PAIRS.copy()
        random.shuffle(available_pairs)
        
        # Берем нужное количество пар (с повторениями если нужно)
        event_pairs = []
        for i in range(rounds_per_scenario):
            if not available_pairs:
                available_pairs = EVENT_PAIRS.copy()
                random.shuffle(available_pairs)
            pair_dict = available_pairs.pop(0)
            
            # Получаем полные объекты событий
            positive_event = positive_events_dict[pair_dict["positive"]]
            negative_event = negative_events_dict[pair_dict["negative"]]
            event_pairs.append((positive_event, negative_event))
        
        # Симулируем сценарий
        result = simulate_game_scenario(event_pairs, rounds_per_scenario)
        result["scenario_num"] = scenario_num + 1
        results.append(result)
    
    return results

if __name__ == "__main__":
    print("Генерация сценариев...")
    scenarios = generate_scenario_analysis(10, 10)
    
    print(f"\nСгенерировано {len(scenarios)} сценариев")
    print("\nПример первого сценария:")
    scenario = scenarios[0]
    print(f"\nСценарий {scenario['scenario_num']}:")
    print("\nИзменения цен на ресурсы:")
    for resource, data in sorted(scenario["price_changes"].items()):
        print(f"  {resource}: {data['start']:.2f} -> {data['end']:.2f} ({data['change_percent']:+.1f}%)")
    
    print("\nДоходы объектов (топ-5):")
    sorted_buildings = sorted(
        scenario["building_results"].items(),
        key=lambda x: x[1]["total_income_value"],
        reverse=True
    )
    for building, data in sorted_buildings[:5]:
        print(f"  {building}: {data['total_income_value']:.2f} монет (ROI: {data['roi_percent']:.1f}%)")

