"""
Модуль для расчета динамики цен ресурсов и доходов объектов
Учитывает события, спрос, предложение и масштабируется для разного количества игроков
"""

from typing import Dict, List
import math
from game_config import RESOURCE_PRICES, BUILDING_INCOME

# Параметры системы (можно настраивать)
MARKET_CONFIG = {
    # Максимальное изменение цены за раунд (в процентах от базовой)
    "max_price_change_percent": 50,  # Цена не может измениться больше чем на 50% за раунд
    
    # Параметры насыщения рынка объектами
    "saturation_base_percent": 20,  # Считаем насыщением, если объект есть у 20% игроков
    "saturation_max_penalty": 0.5,  # Максимальное снижение дохода (до 50% от базового)
    "saturation_curve": "logarithmic",  # Тип кривой: "linear", "logarithmic", "square_root"
    
    # Минимальные и максимальные модификаторы
    "min_price_modifier": 0.3,  # Цена не может упасть ниже 30% от базовой
    "max_price_modifier": 3.0,  # Цена не может вырасти выше 300% от базовой
    "min_income_modifier": 0.5,  # Доход не может упасть ниже 50% от базового (даже при полном насыщении)
    "max_income_modifier": 2.0,  # Доход не может вырасти выше 200% от базового
}


class MarketDynamics:
    """Класс для расчета динамики рынка"""
    
    def __init__(self, num_players: int):
        """
        Args:
            num_players: Количество игроков в игре
        """
        self.num_players = num_players
        self.base_prices = RESOURCE_PRICES.copy()
        self.base_incomes = BUILDING_INCOME.copy()
        
    def normalize_by_players(self, value: float) -> float:
        """
        Нормализует значение по количеству игроков
        Используется для того, чтобы система работала одинаково для 5 и 30 игроков
        """
        # Нормализуем к базе в 10 игроков
        return value / (self.num_players / 10.0)
    
    def calculate_demand_modifier(self, players_bought: Dict[str, int]) -> Dict[str, float]:
        """
        Рассчитывает модификатор цены на основе спроса (покупок)
        
        Args:
            players_bought: Словарь {ресурс: количество_игроков_которые_купили}
            
        Returns:
            Словарь {ресурс: модификатор_цены}
        """
        modifiers = {}
        
        for resource in self.base_prices.keys():
            players_count = players_bought.get(resource, 0)
            percent_players = (players_count / self.num_players) * 100 if self.num_players > 0 else 0
            
            # Определяем уровень спроса
            if percent_players > 75:
                # Высокий спрос
                modifier = 1.1
            elif percent_players > 25:
                # Средний спрос
                modifier = 1.0
            else:
                # Низкий спрос
                modifier = 0.9
            
            modifiers[resource] = modifier
        
        return modifiers
    
    def calculate_supply_modifier(self, players_sold: Dict[str, int]) -> Dict[str, float]:
        """
        Рассчитывает модификатор цены на основе предложения (продаж)
        
        Args:
            players_sold: Словарь {ресурс: количество_игроков_которые_продали}
            
        Returns:
            Словарь {ресурс: модификатор_цены}
        """
        modifiers = {}
        
        for resource in self.base_prices.keys():
            players_count = players_sold.get(resource, 0)
            percent_players = (players_count / self.num_players) * 100 if self.num_players > 0 else 0
            
            # Определяем уровень предложения
            if percent_players > 75:
                # Высокое предложение
                modifier = 0.9
            elif percent_players > 25:
                # Среднее предложение
                modifier = 1.0
            else:
                # Низкое предложение
                modifier = 1.1
            
            modifiers[resource] = modifier
        
        return modifiers
    
    def calculate_event_modifier(self, event_modifiers: Dict[str, float]) -> Dict[str, float]:
        """
        Применяет модификаторы от событий
        
        Args:
            event_modifiers: Словарь {ресурс: модификатор_от_события}
                            Например: {"зерно": 1.5, "скот": 0.7}
                            
        Returns:
            Словарь модификаторов (по умолчанию 1.0 для ресурсов без событий)
        """
        modifiers = {}
        for resource in self.base_prices.keys():
            modifiers[resource] = event_modifiers.get(resource, 1.0)
        return modifiers
    
    def calculate_saturation_modifier(self, building_count: int) -> float:
        """
        Рассчитывает модификатор насыщения для объекта
        
        НОВАЯ ЛОГИКА: учитывает процент игроков, а не абсолютное количество
        
        Args:
            building_count: Количество одинаковых объектов
            
        Returns:
            Модификатор дохода (от min_income_modifier до 1.0)
        """
        if building_count == 0:
            return 1.0
        
        # Считаем процент игроков, у которых есть этот объект
        percent_players = (building_count / self.num_players) * 100
        
        # Нормализуем к базовому проценту насыщения (20%)
        saturation_ratio = percent_players / MARKET_CONFIG["saturation_base_percent"]
        
        # Применяем кривую насыщения
        curve_type = MARKET_CONFIG["saturation_curve"]
        
        if curve_type == "linear":
            # Линейная: чем больше объектов, тем сильнее падает доход
            penalty = min(saturation_ratio, 1.0) * (1.0 - MARKET_CONFIG["saturation_max_penalty"])
            
        elif curve_type == "logarithmic":
            # Логарифмическая: быстрое падение в начале, затем замедление
            # Используем log для более плавного снижения
            if saturation_ratio <= 1.0:
                penalty = (1.0 - MARKET_CONFIG["saturation_max_penalty"]) * saturation_ratio
            else:
                # После базового процента снижение замедляется
                log_factor = 1.0 + math.log(saturation_ratio)
                penalty = (1.0 - MARKET_CONFIG["saturation_max_penalty"]) * (1.0 - (1.0 - 1.0/log_factor))
                
        elif curve_type == "square_root":
            # Квадратный корень: более плавное снижение
            sqrt_factor = math.sqrt(saturation_ratio)
            penalty = (1.0 - MARKET_CONFIG["saturation_max_penalty"]) * min(sqrt_factor, 1.0)
            
        else:  # По умолчанию - логарифмическая
            if saturation_ratio <= 1.0:
                penalty = (1.0 - MARKET_CONFIG["saturation_max_penalty"]) * saturation_ratio
            else:
                log_factor = 1.0 + math.log(saturation_ratio)
                penalty = (1.0 - MARKET_CONFIG["saturation_max_penalty"]) * (1.0 - (1.0 - 1.0/log_factor))
        
        # Модификатор = 1.0 - штраф
        modifier = 1.0 - penalty
        
        # Применяем минимальный порог
        modifier = max(MARKET_CONFIG["min_income_modifier"], modifier)
        
        return modifier
    
    def calculate_resource_prices(
        self,
        previous_prices: Dict[str, float],
        players_bought: Dict[str, int],
        players_sold: Dict[str, int],
        event_modifiers: Dict[str, float] = None
    ) -> Dict[str, float]:
        """
        Рассчитывает новые цены на ресурсы с учетом всех факторов
        
        Цены рассчитываются от предыдущего раунда (не от базовой цены).
        Спрос и предложение берутся из предыдущего раунда.
        События применяются из текущего раунда.
        
        Args:
            previous_prices: Цены предыдущего раунда (для первого раунда - базовые цены)
            players_bought: Словарь {ресурс: количество_игроков_которые_купили} из ПРЕДЫДУЩЕГО раунда
            players_sold: Словарь {ресурс: количество_игроков_которые_продали} из ПРЕДЫДУЩЕГО раунда
            event_modifiers: Модификаторы от событий ТЕКУЩЕГО раунда (опционально)
            
        Returns:
            Словарь {ресурс: новая_цена}
        """
        if event_modifiers is None:
            event_modifiers = {}
        
        # Рассчитываем модификаторы
        demand_mods = self.calculate_demand_modifier(players_bought)
        supply_mods = self.calculate_supply_modifier(players_sold)
        event_mods = self.calculate_event_modifier(event_modifiers)
        
        new_prices = {}
        
        for resource, previous_price in previous_prices.items():
            # Комбинируем все модификаторы
            combined_modifier = (
                demand_mods[resource] *
                supply_mods[resource] *
                event_mods[resource]
            )
            
            # Ограничиваем изменение цены за раунд
            # Не позволяем цене измениться больше чем на max_price_change_percent%
            max_change = 1.0 + (MARKET_CONFIG["max_price_change_percent"] / 100.0)
            min_change = 1.0 - (MARKET_CONFIG["max_price_change_percent"] / 100.0)
            combined_modifier = max(min_change, min(max_change, combined_modifier))
            
            # Рассчитываем новую цену от предыдущей (не от базовой!)
            new_price = previous_price * combined_modifier
            
            # Применяем абсолютные ограничения (от базовой цены)
            base_price = self.base_prices[resource]
            new_price = max(
                base_price * MARKET_CONFIG["min_price_modifier"],
                min(base_price * MARKET_CONFIG["max_price_modifier"], new_price)
            )
            
            new_prices[resource] = round(new_price, 2)
        
        return new_prices
    
    def calculate_building_income_modifiers(
        self,
        building_counts: Dict[str, int],
        event_modifiers: Dict[str, float] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Рассчитывает модификаторы дохода для объектов
        
        Args:
            building_counts: Словарь {название_объекта: количество_таких_объектов}
            event_modifiers: Модификаторы от событий для объектов (опционально)
                            Например: {"Ферма": 0.5, "Посевные поля": 0.0}
                            
        Returns:
            Словарь {название_объекта: {тип_дохода: модификатор}}
        """
        if event_modifiers is None:
            event_modifiers = {}
        
        income_modifiers = {}
        
        for building_name in self.base_incomes.keys():
            count = building_counts.get(building_name, 0)
            
            # НОВАЯ ФОРМУЛА: используем процент игроков вместо абсолютного количества
            saturation_modifier = self.calculate_saturation_modifier(count)
            
            # Модификатор от событий
            event_modifier = event_modifiers.get(building_name, 1.0)
            
            # Комбинируем модификаторы
            combined_modifier = saturation_modifier * event_modifier
            
            # Применяем ограничения
            combined_modifier = max(
                MARKET_CONFIG["min_income_modifier"],
                min(MARKET_CONFIG["max_income_modifier"], combined_modifier)
            )
            
            income_modifiers[building_name] = {
                "монеты": combined_modifier,
                "ресурсы": {res: combined_modifier for res in self.base_prices.keys()}
            }
        
        return income_modifiers
    
    def calculate_building_incomes(
        self,
        building_counts: Dict[str, int],
        current_resource_prices: Dict[str, float],
        event_modifiers: Dict[str, float] = None
    ) -> Dict[str, Dict]:
        """
        Рассчитывает актуальные доходы объектов с учетом всех факторов
        
        Args:
            building_counts: Количество каждого типа объектов
            current_resource_prices: Текущие цены на ресурсы
            event_modifiers: Модификаторы от событий
            
        Returns:
            Словарь {название_объекта: {"монеты": количество, "ресурсы": {...}}}
        """
        modifiers = self.calculate_building_income_modifiers(building_counts, event_modifiers)
        new_incomes = {}
        
        for building_name, base_income in self.base_incomes.items():
            modifier = modifiers[building_name]
            
            new_income = {
                "монеты": round(
                    base_income.get("монеты", 0) * modifier["монеты"],
                    2
                ),
                "ресурсы": {}
            }
            
            # Применяем модификатор к ресурсам
            for resource, amount in base_income.get("ресурсы", {}).items():
                new_income["ресурсы"][resource] = round(
                    amount * modifier["ресурсы"][resource],
                    2
                )
            
            new_incomes[building_name] = new_income
        
        return new_incomes


# Примеры для проверки
if __name__ == "__main__":
    print("=== Тест 1: 5 игроков, 3 одинаковых объекта ===")
    market_5 = MarketDynamics(num_players=5)
    modifier_5 = market_5.calculate_saturation_modifier(3)
    print(f"Лесоповал: 3 из 5 игроков (60%) -> модификатор: {modifier_5:.2%}")
    
    print("\n=== Тест 2: 10 игроков, 5 одинаковых объектов ===")
    market_10 = MarketDynamics(num_players=10)
    modifier_10 = market_10.calculate_saturation_modifier(5)
    print(f"Лесоповал: 5 из 10 игроков (50%) -> модификатор: {modifier_10:.2%}")
    
    print("\n=== Тест 3: 30 игроков, 15 одинаковых объектов ===")
    market_30 = MarketDynamics(num_players=30)
    modifier_30 = market_30.calculate_saturation_modifier(15)
    print(f"Лесоповал: 15 из 30 игроков (50%) -> модификатор: {modifier_30:.2%}")
    
    print("\n=== Тест 4: 30 игроков, 20 одинаковых объектов ===")
    modifier_30_20 = market_30.calculate_saturation_modifier(20)
    print(f"Лесоповал: 20 из 30 игроков (67%) -> модификатор: {modifier_30_20:.2%}")
    
    print("\n=== Тест 5: 30 игроков, 25 одинаковых объектов ===")
    modifier_30_25 = market_30.calculate_saturation_modifier(25)
    print(f"Лесоповал: 25 из 30 игроков (83%) -> модификатор: {modifier_30_25:.2%}")
    
    print("\n=== Сравнение: одинаковый процент игроков ===")
    print(f"5 игроков, 3 объекта (60%): {modifier_5:.2%}")
    print(f"30 игроков, 18 объектов (60%): {market_30.calculate_saturation_modifier(18):.2%}")
    print("(Должны быть примерно одинаковые)")
    
    print("\n=== Тест динамики цен ===")
    # Пример: 8 из 10 игроков купили дерево (80% - высокий спрос)
    # 2 из 10 игроков продали дерево (20% - низкое предложение)
    previous_prices = market_10.base_prices.copy()  # Для первого раунда используем базовые
    players_bought = {"дерево": 8, "железо": 5}
    players_sold = {"дерево": 2, "зерно": 7}
    event_modifiers = {"зерно": 1.8, "скот": 0.6}
    
    new_prices = market_10.calculate_resource_prices(previous_prices, players_bought, players_sold, event_modifiers)
    print("\nНовые цены на ресурсы:")
    for resource, price in sorted(new_prices.items()):
        base_price = market_10.base_prices[resource]
        change = ((price - base_price) / base_price) * 100
        print(f"  {resource}: {base_price} -> {price:.2f} ({change:+.1f}%)")

