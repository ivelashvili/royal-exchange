"""
Игровой движок для "Королевская биржа"
Управляет игровым процессом, раундами, действиями игроков
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from game_config import (
    RESOURCE_PRICES, BUILDING_COSTS, BUILDING_INCOME, 
    BUILDING_CONSTRUCTION_TIME, STARTING_MONEY
)
from game_events import EventSystem
from market_dynamics import MarketDynamics


class BuildingStatus(Enum):
    """Статусы объектов"""
    BUILDING = "building"  # Строится
    COMPLETED = "completed"  # Построен, но еще не приносит доход
    ACTIVE = "active"  # Активен, приносит доход
    FOR_SALE = "for_sale"  # Выставлен на продажу


@dataclass
class Building:
    """Объект игрока"""
    id: str
    name: str
    started_round: int  # Раунд начала строительства
    completed_round: int  # Раунд завершения (started_round + 1)
    status: BuildingStatus = BuildingStatus.BUILDING
    sale_round: Optional[int] = None  # Раунд выставления на продажу
    sale_price: Optional[float] = None  # Цена продажи (фиксируется при выставлении)


@dataclass
class Player:
    """Игрок"""
    id: str
    name: str
    money: float = STARTING_MONEY
    resources: Dict[str, int] = field(default_factory=dict)
    buildings: List[Building] = field(default_factory=list)
    
    def get_resource(self, resource: str) -> int:
        """Получить количество ресурса"""
        return self.resources.get(resource, 0)
    
    def add_resource(self, resource: str, amount: int):
        """Добавить ресурс"""
        if resource not in self.resources:
            self.resources[resource] = 0
        self.resources[resource] += amount
    
    def remove_resource(self, resource: str, amount: int) -> bool:
        """Удалить ресурс (если достаточно)"""
        if self.get_resource(resource) >= amount:
            self.resources[resource] -= amount
            if self.resources[resource] == 0:
                del self.resources[resource]
            return True
        return False
    
    def has_resources(self, costs: Dict[str, int]) -> bool:
        """Проверить, достаточно ли ресурсов"""
        for resource, amount in costs.items():
            if self.get_resource(resource) < amount:
                return False
        return True
    
    def remove_resources(self, costs: Dict[str, int]) -> bool:
        """Удалить ресурсы (если достаточно)"""
        if not self.has_resources(costs):
            return False
        for resource, amount in costs.items():
            self.remove_resource(resource, amount)
        return True
    
    def get_building(self, building_id: str) -> Optional[Building]:
        """Найти объект по ID"""
        for building in self.buildings:
            if building.id == building_id:
                return building
        return None
    
    def remove_building(self, building_id: str) -> bool:
        """Удалить объект"""
        for i, building in enumerate(self.buildings):
            if building.id == building_id:
                self.buildings.pop(i)
                return True
        return False


class Game:
    """Игровой движок"""
    
    def __init__(self, num_players: int = 10):
        """
        Args:
            num_players: Количество игроков
        """
        self.num_players = num_players
        self.current_round = 1
        self.players: List[Player] = []
        
        # Состояние рынка
        self.current_prices = RESOURCE_PRICES.copy()
        self.previous_round_players_bought: Dict[str, int] = {}
        self.previous_round_players_sold: Dict[str, int] = {}
        
        # Системы
        self.market = MarketDynamics(num_players)
        self.event_system = EventSystem()
        
        # История раундов
        self.round_history: List[Dict] = []
        
        # Отслеживание действий текущего раунда (для расчета спроса/предложения)
        self.current_round_players_bought: Dict[str, set] = {}  # {ресурс: set(player_ids)}
        self.current_round_players_sold: Dict[str, set] = {}    # {ресурс: set(player_ids)}
    
    def add_player(self, player_id: str, player_name: str) -> bool:
        """Добавить игрока"""
        if len(self.players) >= self.num_players:
            return False
        if any(p.id == player_id for p in self.players):
            return False  # Игрок уже существует
        
        player = Player(id=player_id, name=player_name)
        self.players.append(player)
        return True
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """Получить игрока по ID"""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def calculate_building_cost(self, building_name: str) -> float:
        """Рассчитать стоимость объекта в монетах по текущим ценам"""
        costs = BUILDING_COSTS.get(building_name, {})
        total = 0
        for resource, amount in costs.items():
            total += amount * self.current_prices.get(resource, 0)
        return total
    
    def calculate_building_sale_price(self, building: Building) -> float:
        """Рассчитать цену продажи объекта (по текущим ценам ресурсов)"""
        costs = BUILDING_COSTS.get(building.name, {})
        total = 0
        for resource, amount in costs.items():
            total += amount * self.current_prices.get(resource, 0)
        return total
    
    # ========== ДЕЙСТВИЯ ИГРОКОВ ==========
    
    def buy_resource(self, player_id: str, resource: str, amount: int) -> Dict:
        """
        Купить ресурс
        
        Returns:
            {"success": bool, "message": str, "cost": float}
        """
        player = self.get_player(player_id)
        if not player:
            return {"success": False, "message": "Игрок не найден"}
        
        if resource not in RESOURCE_PRICES:
            return {"success": False, "message": "Неизвестный ресурс"}
        
        if amount <= 0:
            return {"success": False, "message": "Количество должно быть положительным"}
        
        cost = amount * self.current_prices[resource]
        
        if player.money < cost:
            return {"success": False, "message": f"Недостаточно денег. Нужно {cost:.2f}, есть {player.money:.2f}"}
        
        # Покупаем
        player.money -= cost
        player.add_resource(resource, amount)
        
        # Отслеживаем для расчета спроса
        if resource not in self.current_round_players_bought:
            self.current_round_players_bought[resource] = set()
        self.current_round_players_bought[resource].add(player_id)
        
        return {"success": True, "message": f"Куплено {amount} {resource} за {cost:.2f} монет", "cost": cost}
    
    def sell_resource(self, player_id: str, resource: str, amount: int) -> Dict:
        """
        Продать ресурс
        
        Returns:
            {"success": bool, "message": str, "income": float}
        """
        player = self.get_player(player_id)
        if not player:
            return {"success": False, "message": "Игрок не найден"}
        
        if resource not in RESOURCE_PRICES:
            return {"success": False, "message": "Неизвестный ресурс"}
        
        if amount <= 0:
            return {"success": False, "message": "Количество должно быть положительным"}
        
        if not player.remove_resource(resource, amount):
            return {"success": False, "message": f"Недостаточно {resource}"}
        
        income = amount * self.current_prices[resource]
        player.money += income
        
        # Отслеживаем для расчета предложения
        if resource not in self.current_round_players_sold:
            self.current_round_players_sold[resource] = set()
        self.current_round_players_sold[resource].add(player_id)
        
        return {"success": True, "message": f"Продано {amount} {resource} за {income:.2f} монет", "income": income}
    
    def start_building(self, player_id: str, building_name: str) -> Dict:
        """
        Начать строительство объекта
        
        Returns:
            {"success": bool, "message": str, "building_id": str}
        """
        player = self.get_player(player_id)
        if not player:
            return {"success": False, "message": "Игрок не найден"}
        
        if building_name not in BUILDING_COSTS:
            return {"success": False, "message": "Неизвестный объект"}
        
        costs = BUILDING_COSTS[building_name]
        
        if not player.has_resources(costs):
            return {"success": False, "message": "Недостаточно ресурсов"}
        
        # Списываем ресурсы
        player.remove_resources(costs)
        
        # Создаем объект
        building_id = f"{player_id}_{building_name}_{self.current_round}_{len(player.buildings)}"
        building = Building(
            id=building_id,
            name=building_name,
            started_round=self.current_round,
            completed_round=self.current_round + 1,  # Завершится в следующем раунде
            status=BuildingStatus.BUILDING
        )
        player.buildings.append(building)
        
        return {"success": True, "message": f"Начато строительство {building_name}", "building_id": building_id}
    
    def put_building_for_sale(self, player_id: str, building_id: str) -> Dict:
        """
        Выставить объект на продажу
        
        Returns:
            {"success": bool, "message": str, "sale_price": float}
        """
        player = self.get_player(player_id)
        if not player:
            return {"success": False, "message": "Игрок не найден"}
        
        building = player.get_building(building_id)
        if not building:
            return {"success": False, "message": "Объект не найден"}
        
        if building.status == BuildingStatus.FOR_SALE:
            return {"success": False, "message": "Объект уже выставлен на продажу"}
        
        if building.status == BuildingStatus.BUILDING:
            return {"success": False, "message": "Нельзя продать объект, который еще строится"}
        
        # Фиксируем цену продажи (по текущим ценам ресурсов)
        sale_price = self.calculate_building_sale_price(building)
        building.status = BuildingStatus.FOR_SALE
        building.sale_round = self.current_round
        building.sale_price = sale_price
        
        return {"success": True, "message": f"Объект выставлен на продажу за {sale_price:.2f} монет", "sale_price": sale_price}
    
    # ========== ФАЗЫ РАУНДА ==========
    
    def phase_events(self) -> Dict:
        """
        Фаза 1: События
        Выбирает события и обновляет цены на ресурсы
        """
        if self.current_round == 1:
            # Первый раунд: события не происходят
            return {
                "events": None,
                "prices_changed": False,
                "new_prices": self.current_prices.copy()
            }
        
        # Выбираем события
        positive_event, negative_event = self.event_system.get_random_event_pair()
        resource_mods, building_mods = self.event_system.combine_event_modifiers(
            positive_event, negative_event
        )
        
        # Рассчитываем новые цены
        # Используем спрос/предложение из ПРЕДЫДУЩЕГО раунда
        # и события из ТЕКУЩЕГО раунда
        new_prices = self.market.calculate_resource_prices(
            previous_prices=self.current_prices,
            players_bought=self.previous_round_players_bought,
            players_sold=self.previous_round_players_sold,
            event_modifiers=resource_mods
        )
        
        # Обновляем цены
        self.current_prices = new_prices
        
        return {
            "events": {
                "positive": positive_event["name"],
                "negative": negative_event["name"],
                "positive_description": positive_event["description"],
                "negative_description": negative_event["description"]
            },
            "resource_modifiers": resource_mods,
            "building_modifiers": building_mods,
            "prices_changed": True,
            "new_prices": new_prices.copy()
        }
    
    def phase_income(self, building_modifiers: Dict[str, float]) -> Dict:
        """
        Фаза 2: Начисление доходов
        Продажа объектов и начисление дохода от активных объектов
        """
        income_results = {
            "buildings_sold": [],
            "income_distributed": {}
        }
        
        # 1. Продажа объектов из предыдущего раунда
        # Объекты, выставленные на продажу в предыдущем раунде, продаются сейчас
        for player in self.players:
            buildings_to_remove = []
            for building in player.buildings:
                if (building.status == BuildingStatus.FOR_SALE and 
                    building.sale_round is not None and
                    building.sale_round < self.current_round):
                    # Продаем объект (выставлен в предыдущем раунде)
                    player.money += building.sale_price
                    buildings_to_remove.append(building.id)
                    income_results["buildings_sold"].append({
                        "player_id": player.id,
                        "building_name": building.name,
                        "sale_price": building.sale_price
                    })
            
            # Удаляем проданные объекты
            for building_id in buildings_to_remove:
                player.remove_building(building_id)
        
        # 2. Начисление дохода от активных объектов
        # Объекты, которые были COMPLETED в предыдущем раунде, теперь ACTIVE и приносят доход
        # Считаем количество каждого типа объектов
        building_counts = {}
        for player in self.players:
            for building in player.buildings:
                if building.status == BuildingStatus.ACTIVE:
                    building_counts[building.name] = building_counts.get(building.name, 0) + 1
        
        # Рассчитываем доходы с учетом насыщения и событий
        new_incomes = self.market.calculate_building_incomes(
            building_counts,
            self.current_prices,
            building_modifiers
        )
        
        # Начисляем доходы игрокам
        for player in self.players:
            player_income = {"монеты": 0, "ресурсы": {}}
            
            for building in player.buildings:
                if building.status == BuildingStatus.ACTIVE:
                    income = new_incomes.get(building.name, {"монеты": 0, "ресурсы": {}})
                    
                    # Монеты
                    coins = income.get("монеты", 0)
                    player.money += coins
                    player_income["монеты"] += coins
                    
                    # Ресурсы
                    for resource, amount in income.get("ресурсы", {}).items():
                        player.add_resource(resource, int(amount))
                        if resource not in player_income["ресурсы"]:
                            player_income["ресурсы"][resource] = 0
                        player_income["ресурсы"][resource] += amount
            
            income_results["income_distributed"][player.id] = player_income
        
        return income_results
    
    def phase_purchases(self) -> Dict:
        """
        Фаза 3: Закупки
        Игроки совершают действия (покупка, продажа, строительство)
        Эта фаза собирает данные о спросе и предложении для следующего раунда
        """
        # Преобразуем sets в количество игроков
        players_bought = {
            resource: len(player_ids) 
            for resource, player_ids in self.current_round_players_bought.items()
        }
        players_sold = {
            resource: len(player_ids) 
            for resource, player_ids in self.current_round_players_sold.items()
        }
        
        return {
            "players_bought": players_bought,
            "players_sold": players_sold
        }
    
    def update_state(self, players_bought: Dict[str, int], players_sold: Dict[str, int]):
        """
        Фаза 4: Обновление состояния для следующего раунда
        """
        # Сохраняем данные для следующего раунда
        self.previous_round_players_bought = players_bought.copy()
        self.previous_round_players_sold = players_sold.copy()
        
        # Обновляем статусы объектов
        for player in self.players:
            for building in player.buildings:
                if building.status == BuildingStatus.BUILDING:
                    if self.current_round >= building.completed_round:
                        # Объект завершен в этом раунде
                        # Становится COMPLETED, в следующем раунде станет ACTIVE и начнет приносить доход
                        building.status = BuildingStatus.COMPLETED
                elif building.status == BuildingStatus.COMPLETED:
                    # Объект был завершен в предыдущем раунде, теперь становится активным
                    # В следующем раунде начнет приносить доход
                    building.status = BuildingStatus.ACTIVE
    
    def start_round(self):
        """Начать новый раунд (сбросить отслеживание действий)"""
        self.current_round_players_bought = {}
        self.current_round_players_sold = {}
    
    def process_round(self) -> Dict:
        """
        Обработать полный раунд
        Вызывается после того, как все игроки совершили действия
        
        Returns:
            Результаты раунда
        """
        round_result = {
            "round": self.current_round,
            "events": None,
            "income": None,
            "prices": self.current_prices.copy()
        }
        
        # Фаза 1: События
        events_result = self.phase_events()
        round_result["events"] = events_result["events"]
        round_result["prices"] = events_result["new_prices"]
        
        # Фаза 2: Начисление доходов
        # Сначала обновляем статусы объектов (COMPLETED -> ACTIVE)
        # чтобы они могли приносить доход в этом раунде
        for player in self.players:
            for building in player.buildings:
                if building.status == BuildingStatus.COMPLETED:
                    # Объект был завершен в предыдущем раунде, теперь активен
                    building.status = BuildingStatus.ACTIVE
        
        building_modifiers = events_result.get("building_modifiers", {})
        income_result = self.phase_income(building_modifiers)
        round_result["income"] = income_result
        
        # Фаза 3: Закупки (собираем данные о спросе/предложении)
        purchases_result = self.phase_purchases()
        players_bought = purchases_result["players_bought"]
        players_sold = purchases_result["players_sold"]
        
        # Фаза 4: Обновление состояния
        self.update_state(players_bought, players_sold)
        
        # Сохраняем историю
        self.round_history.append(round_result)
        
        # Переходим к следующему раунду
        self.current_round += 1
        
        # Сбрасываем отслеживание для следующего раунда
        self.start_round()
        
        return round_result
    
    def get_leaderboard(self) -> List[Dict]:
        """Получить турнирную таблицу"""
        players_data = []
        for player in self.players:
            # Считаем стоимость всех ресурсов
            resources_value = sum(
                amount * self.current_prices.get(resource, 0)
                for resource, amount in player.resources.items()
            )
            
            # Считаем стоимость всех объектов
            buildings_value = sum(
                self.calculate_building_sale_price(building)
                for building in player.buildings
                if building.status != BuildingStatus.FOR_SALE
            )
            
            total_value = player.money + resources_value + buildings_value
            
            players_data.append({
                "player_id": player.id,
                "name": player.name,
                "money": round(player.money, 2),
                "resources_value": round(resources_value, 2),
                "buildings_value": round(buildings_value, 2),
                "total_value": round(total_value, 2)
            })
        
        # Сортируем по общей стоимости
        players_data.sort(key=lambda x: x["total_value"], reverse=True)
        
        return players_data
    
    def get_player_state(self, player_id: str) -> Optional[Dict]:
        """Получить полное состояние игрока"""
        player = self.get_player(player_id)
        if not player:
            return None
        
        buildings_data = []
        for building in player.buildings:
            buildings_data.append({
                "id": building.id,
                "name": building.name,
                "status": building.status.value,
                "started_round": building.started_round,
                "completed_round": building.completed_round,
                "sale_round": building.sale_round,
                "sale_price": building.sale_price
            })
        
        return {
            "player_id": player.id,
            "name": player.name,
            "money": round(player.money, 2),
            "resources": player.resources.copy(),
            "buildings": buildings_data,
            "current_prices": self.current_prices.copy(),
            "current_round": self.current_round
        }

