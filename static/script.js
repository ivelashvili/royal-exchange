let ws = null;
let reconnectInterval = null;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateUI(data);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...');
        if (!reconnectInterval) {
            reconnectInterval = setInterval(connectWebSocket, 3000);
        }
    };
}

function updateUI(data) {
    // Обновляем информацию о раунде
    if (data.current_round !== undefined) {
        document.getElementById('current-round').textContent = data.current_round;
    }
    if (data.num_players !== undefined) {
        document.getElementById('num-players').textContent = data.num_players;
    }
    
    // Обновляем турнирную таблицу
    if (data.leaderboard && data.leaderboard.leaderboard) {
        updateLeaderboard(data.leaderboard.leaderboard);
    }
    
    // Обновляем цены
    if (data.prices && data.prices.prices) {
        updatePrices(data.prices.prices);
    }
    
    // Обновляем объекты
    if (data.buildings && data.buildings.buildings) {
        updateBuildings(data.buildings.buildings);
    }
}

function updateLeaderboard(leaderboard) {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';
    
    if (leaderboard.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #e8d5b7;">Игроки еще не добавлены</td></tr>';
        return;
    }
    
    leaderboard.forEach((player, index) => {
        const row = document.createElement('tr');
        
        const growthClass = player.growth_percent > 0 ? 'positive' : 
                           player.growth_percent < 0 ? 'negative' : 'neutral';
        const growthSign = player.growth_percent > 0 ? '+' : '';
        
        row.innerHTML = `
            <td><strong style="color: #3a2a1a;">${index + 1}</strong></td>
            <td style="color: #3a2a1a;">${player.name}</td>
            <td style="color: #3a2a1a;">${Math.round(player.total_value)} монет</td>
            <td class="${growthClass}">${growthSign}${Math.round(player.growth_percent)}%</td>
        `;
        
        tbody.appendChild(row);
    });
}

function updatePrices(prices) {
    const tbody = document.getElementById('prices-body');
    tbody.innerHTML = '';
    
    if (prices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #e8d5b7;">Цены не загружены</td></tr>';
        return;
    }
    
    prices.forEach(price => {
        const row = document.createElement('tr');
        
        const prevClass = price.change_from_prev_percent > 0 ? 'positive' : 
                         price.change_from_prev_percent < 0 ? 'negative' : 'neutral';
        const startClass = price.change_from_start_percent > 0 ? 'positive' : 
                          price.change_from_start_percent < 0 ? 'negative' : 'neutral';
        
        const prevSign = price.change_from_prev_percent > 0 ? '+' : '';
        const startSign = price.change_from_start_percent > 0 ? '+' : '';
        
        // Делаем первую букву заглавной
        const resourceName = price.resource.charAt(0).toUpperCase() + price.resource.slice(1);
        
        row.innerHTML = `
            <td><strong style="color: #3a2a1a;">${resourceName}</strong></td>
            <td style="color: #3a2a1a;">${Math.round(price.current_price)}</td>
            <td class="${prevClass}">${prevSign}${Math.round(price.change_from_prev_percent)}%</td>
            <td class="${startClass}">${startSign}${Math.round(price.change_from_start_percent)}%</td>
        `;
        
        // Добавляем обработчик клика для открытия модального окна
        row.style.cursor = 'pointer';
        row.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Клик по ресурсу:', price.resource);
            console.log('openResourceModal определена?', typeof openResourceModal);
            if (typeof openResourceModal === 'function') {
                openResourceModal(price.resource);
            } else {
                console.error('openResourceModal не определена!');
            }
        });
        
        tbody.appendChild(row);
    });
}

// Маппинг названий объектов на имена файлов картинок
const buildingImages = {
    'Лесоповал': 'лесоповал.png',
    'Каменоломня': 'каменоломня.png',
    'Рыболовня': 'рыболовня.png',
    'Трактир': 'Трактир.png',
    'Теплицы': 'теплицы.png',
    'Посевные поля': 'Посевные поля.png',
    'Ферма': 'ферма.png',
    'Постоялый двор': 'постоялый двор.png',
    'Куртизанские палатки': 'куртизанские палатки.png',
    'Кузнечная': 'кузнечная.png',
    'Золотой рудник': 'золотой рудник.png'
};

// Маппинг названий ресурсов на имена файлов картинок
const resourceImages = {
    'камень': 'камень.png',
    'дерево': 'дерево.png',
    'железо': 'железо.png',
    'скот': 'скот.png',
    'овощи': 'овощи.png',
    'рабы': 'рабы.png',
    'золото': 'золото.png',
    'зерно': 'зерно.png',
    'рыба': 'рыба.png'
};

// Порядок ресурсов для навигации (должен совпадать с порядком в таблице цен - sorted по алфавиту)
const allResourcesOrder = [
    'дерево', 'железо', 'зерно', 'золото', 'камень', 'овощи', 'рабы', 'рыба', 'скот'
];

// Глобальные переменные для навигации ресурсов
let currentResourceIndex = -1;

// Порядок объектов для навигации (должен совпадать с порядком в allBuildings)
const allBuildingsOrder = [
    'Лесоповал', 'Каменоломня', 'Теплицы', 'Трактир',
    'Посевные поля', 'Рыболовня', 'Кузнечная', 'Ферма',
    'Постоялый двор', 'Куртизанские палатки', 'Золотой рудник'
];

// Глобальные переменные для навигации
let currentBuildingIndex = -1;
let buildingsDataCache = {}; // Кэш данных объектов {name: {count, percentage}}

function updateBuildings(buildings) {
    const grid = document.getElementById('buildings-grid');
    grid.innerHTML = '';
    
    // Создаем словарь для быстрого поиска данных по названию
    const buildingsMap = {};
    buildings.forEach(building => {
        buildingsMap[building.name] = building;
    });
    
    // Обновляем кэш данных
    buildingsDataCache = {};
    allBuildingsOrder.forEach(buildingName => {
        const building = buildingsMap[buildingName] || {
            name: buildingName,
            count: 0,
            players_percentage: 0
        };
        buildingsDataCache[buildingName] = {
            count: building.count,
            percentage: Math.round(building.players_percentage)
        };
    });
    
    // Всегда показываем все 11 объектов в порядке 4-4-3
    const allBuildings = [
        // Первый ряд (4 объекта)
        'Лесоповал', 'Каменоломня', 'Теплицы', 'Трактир',
        // Второй ряд (4 объекта)
        'Посевные поля', 'Рыболовня', 'Кузнечная', 'Ферма',
        // Третий ряд (3 объекта)
        'Постоялый двор', 'Куртизанские палатки', 'Золотой рудник'
    ];
    
    allBuildings.forEach(buildingName => {
        const building = buildingsMap[buildingName] || {
            name: buildingName,
            count: 0,
            players_percentage: 0
        };
        
        const card = document.createElement('div');
        card.className = 'building-card';
        // Сохраняем данные карточки для использования в модальном окне
        card.setAttribute('data-building-name', buildingName);
        card.setAttribute('data-building-count', building.count);
        card.setAttribute('data-building-percentage', Math.round(building.players_percentage));
        
        // Получаем имя файла картинки
        const imageFile = buildingImages[building.name] || 'лесоповал.png';
        const imagePath = `/static/images/buildings/${imageFile}`;
        
        card.innerHTML = `
            <div class="building-name">${building.name}</div>
            <img src="${imagePath}" alt="${building.name}" class="building-image" onerror="this.style.display='none'">
            <div class="building-stats">
                <div class="building-count">${building.count}</div>
                <div class="building-percentage-container">
                    <div class="building-percentage">${Math.round(building.players_percentage)}%</div>
                    <div class="building-percentage-label">игроков</div>
                </div>
            </div>
        `;
        
        // Добавляем обработчик клика для открытия модального окна
        card.addEventListener('click', function() {
            const name = this.getAttribute('data-building-name');
            const count = parseInt(this.getAttribute('data-building-count')) || 0;
            const percentage = parseInt(this.getAttribute('data-building-percentage')) || 0;
            openBuildingModal(name, count, percentage);
        });
        
        grid.appendChild(card);
    });
}

// Модальное окно для деталей объекта
const modal = document.getElementById('building-modal');
const modalClose = document.querySelector('.modal-close');

// Кнопки навигации
const modalNavLeft = document.getElementById('modal-nav-left');
const modalNavRight = document.getElementById('modal-nav-right');

// Обработчики навигации
modalNavLeft.addEventListener('click', () => {
    navigateToPrevious();
});

modalNavRight.addEventListener('click', () => {
    navigateToNext();
});

// Закрытие модального окна
modalClose.addEventListener('click', () => {
    modal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// Навигация с клавиатуры
document.addEventListener('keydown', (event) => {
    if (modal.style.display === 'block') {
        if (event.key === 'ArrowLeft') {
            navigateToPrevious();
        } else if (event.key === 'ArrowRight') {
            navigateToNext();
        } else if (event.key === 'Escape') {
            modal.style.display = 'none';
        }
    }
});

// Функция для открытия модального окна с деталями объекта
async function openBuildingModal(buildingName, cardCount, cardPercentage) {
    // Находим индекс текущего объекта
    currentBuildingIndex = allBuildingsOrder.indexOf(buildingName);
    if (currentBuildingIndex === -1) {
        currentBuildingIndex = 0;
    }
    
    // Загружаем данные для текущего объекта
    await loadBuildingModalData(buildingName, cardCount, cardPercentage);
    
    // Обновляем состояние кнопок навигации
    updateNavigationButtons();
}

// Функция для загрузки данных объекта в модальное окно
async function loadBuildingModalData(buildingName, cardCount, cardPercentage) {
    try {
        // Используем данные из кэша, если они есть, иначе из параметров
        const cachedData = buildingsDataCache[buildingName];
        const count = cachedData ? cachedData.count : cardCount;
        const percentage = cachedData ? cachedData.percentage : cardPercentage;
        
        // Сначала заполняем данные из карточки (чтобы они совпадали)
        const imageFile = buildingImages[buildingName] || 'лесоповал.png';
        document.getElementById('modal-building-image').src = `/static/images/buildings/${imageFile}`;
        document.getElementById('modal-building-name').textContent = buildingName;
        document.getElementById('modal-building-count').textContent = count;
        document.getElementById('modal-building-percentage').textContent = `${percentage}%`;
        
        // Затем загружаем детальную информацию (владельцев)
        const response = await fetch(`/api/building/${encodeURIComponent(buildingName)}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Ошибка загрузки данных:', data.error);
            return;
        }
        
        // Используем данные из карточки/кэша, чтобы они точно совпадали
        document.getElementById('modal-building-count').textContent = count;
        document.getElementById('modal-building-percentage').textContent = `${percentage}%`;
        
        // Заполняем правую часть - список владельцев
        const ownersList = document.getElementById('modal-owners-list');
        ownersList.innerHTML = '';
        
        if (data.owners && data.owners.length > 0) {
            data.owners.forEach(owner => {
                const ownerItem = document.createElement('div');
                ownerItem.className = 'modal-owner-item';
                ownerItem.innerHTML = `
                    <span class="modal-owner-name">${owner.name}</span>
                    <span class="modal-owner-count">${owner.count}</span>
                `;
                ownersList.appendChild(ownerItem);
            });
        } else {
            ownersList.innerHTML = '<div style="text-align: center; color: #3a2a1a; padding: 20px;">Нет владельцев</div>';
        }
        
        // Показываем модальное окно
        modal.style.display = 'block';
    } catch (error) {
        console.error('Ошибка при загрузке деталей объекта:', error);
    }
}

// Функция для обновления состояния кнопок навигации
function updateNavigationButtons() {
    const leftButton = document.getElementById('modal-nav-left');
    const rightButton = document.getElementById('modal-nav-right');
    
    // Левая кнопка: отключена на первом объекте
    leftButton.disabled = (currentBuildingIndex === 0);
    
    // Правая кнопка: отключена на последнем объекте
    rightButton.disabled = (currentBuildingIndex === allBuildingsOrder.length - 1);
}

// Функция для переключения на предыдущий объект
async function navigateToPrevious() {
    if (currentBuildingIndex > 0) {
        currentBuildingIndex--;
        const buildingName = allBuildingsOrder[currentBuildingIndex];
        const cachedData = buildingsDataCache[buildingName] || { count: 0, percentage: 0 };
        await loadBuildingModalData(buildingName, cachedData.count, cachedData.percentage);
        updateNavigationButtons();
    }
}

// Функция для переключения на следующий объект
async function navigateToNext() {
    if (currentBuildingIndex < allBuildingsOrder.length - 1) {
        currentBuildingIndex++;
        const buildingName = allBuildingsOrder[currentBuildingIndex];
        const cachedData = buildingsDataCache[buildingName] || { count: 0, percentage: 0 };
        await loadBuildingModalData(buildingName, cachedData.count, cachedData.percentage);
        updateNavigationButtons();
    }
}

// Модальное окно для деталей ресурса - инициализация после загрузки DOM
let resourceModal, resourceModalClose;
let resourceModalNavLeft, resourceModalNavRight;

// Функция для открытия модального окна с деталями ресурса
async function openResourceModal(resourceName) {
    // Находим индекс текущего ресурса
    currentResourceIndex = allResourcesOrder.indexOf(resourceName);
    if (currentResourceIndex === -1) {
        currentResourceIndex = 0;
    }
    
    // Загружаем данные для текущего ресурса
    await loadResourceModalData(resourceName);
    
    // Обновляем состояние кнопок навигации
    updateResourceNavigationButtons();
}

// Функция для загрузки данных ресурса в модальное окно
async function loadResourceModalData(resourceName) {
    try {
        const response = await fetch(`/api/resource/${encodeURIComponent(resourceName)}`);
        
        if (!response.ok) {
            console.error('Ошибка API:', response.status, response.statusText);
            return;
        }
        
        const data = await response.json();
        
        if (data.error) {
            console.error('Ошибка загрузки данных:', data.error);
            return;
        }
        
        // Заполняем данные
        const resourceNameCapitalized = data.name.charAt(0).toUpperCase() + data.name.slice(1);
        document.getElementById('resource-modal-name').textContent = resourceNameCapitalized;
        document.getElementById('resource-modal-price').textContent = `${data.current_price} монет`;
        
        // Загружаем картинку ресурса
        const imageFile = resourceImages[resourceName] || `${resourceName}.png`;
        const imagePath = `/static/images/resources/${imageFile}`;
        const imageEl = document.getElementById('resource-modal-image');
        imageEl.src = imagePath;
        imageEl.alt = resourceNameCapitalized;
        imageEl.style.display = 'block';
        imageEl.onerror = function() {
            this.style.display = 'none';
        };
        
        // Изменение за раунд
        const changeRoundClass = data.change_from_prev_percent > 0 ? 'positive' : 
                                 data.change_from_prev_percent < 0 ? 'negative' : 'neutral';
        const changeRoundSign = data.change_from_prev_percent > 0 ? '+' : '';
        const changeRoundEl = document.getElementById('resource-modal-change-round');
        changeRoundEl.textContent = `${changeRoundSign}${Math.round(data.change_from_prev_percent)}%`;
        changeRoundEl.className = `modal-stat-value ${changeRoundClass}`;
        
        // Изменение с начала игры
        const changeStartClass = data.change_from_start_percent > 0 ? 'positive' : 
                                data.change_from_start_percent < 0 ? 'negative' : 'neutral';
        const changeStartSign = data.change_from_start_percent > 0 ? '+' : '';
        const changeStartEl = document.getElementById('resource-modal-change-start');
        changeStartEl.textContent = `${changeStartSign}${Math.round(data.change_from_start_percent)}%`;
        changeStartEl.className = `modal-stat-value ${changeStartClass}`;
        
        // Спрос и предложение
        const demandEl = document.getElementById('resource-modal-demand');
        demandEl.textContent = data.demand_level;
        demandEl.setAttribute('data-level', data.demand_level);
        
        const supplyEl = document.getElementById('resource-modal-supply');
        supplyEl.textContent = data.supply_level;
        supplyEl.setAttribute('data-level', data.supply_level);
        
        // Показываем модальное окно
        if (resourceModal) {
            resourceModal.style.display = 'block';
        } else {
            // Попробуем найти его снова
            resourceModal = document.getElementById('resource-modal');
            if (resourceModal) {
                resourceModal.style.display = 'block';
            }
        }
        
        // Отрисовываем график после отображения модального окна (чтобы canvas имел правильный размер)
        setTimeout(() => {
            drawPriceChart(data.price_history);
        }, 100);
    } catch (error) {
        console.error('Ошибка при загрузке деталей ресурса:', error);
    }
}

// Функция для обновления состояния кнопок навигации ресурсов
function updateResourceNavigationButtons() {
    if (!resourceModalNavLeft || !resourceModalNavRight) return;
    
    // Левая кнопка: отключена на первом ресурсе
    resourceModalNavLeft.disabled = (currentResourceIndex === 0);
    
    // Правая кнопка: отключена на последнем ресурсе
    resourceModalNavRight.disabled = (currentResourceIndex === allResourcesOrder.length - 1);
}

// Функция для переключения на предыдущий ресурс
async function navigateToPreviousResource() {
    if (currentResourceIndex > 0) {
        currentResourceIndex--;
        const resourceName = allResourcesOrder[currentResourceIndex];
        await loadResourceModalData(resourceName);
        updateResourceNavigationButtons();
    }
}

// Функция для переключения на следующий ресурс
async function navigateToNextResource() {
    if (currentResourceIndex < allResourcesOrder.length - 1) {
        currentResourceIndex++;
        const resourceName = allResourcesOrder[currentResourceIndex];
        await loadResourceModalData(resourceName);
        updateResourceNavigationButtons();
    }
}

// Функция для отрисовки графика цены
function drawPriceChart(priceHistory) {
    const canvas = document.getElementById('resource-price-chart');
    if (!canvas) {
        console.error('Canvas не найден');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Устанавливаем размер canvas
    const container = canvas.parentElement;
    if (container) {
        canvas.width = container.clientWidth - 20; // Учитываем padding
    } else {
        canvas.width = canvas.offsetWidth || 400;
    }
    canvas.height = 300;
    
    if (!priceHistory || priceHistory.length === 0) {
        ctx.fillStyle = '#3a2a1a';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Нет данных для графика', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    // Очищаем canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Параметры графика
    const padding = 40;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;
    
    // Стандартизируем: в точке 0 (раунд 0) цена должна быть 0
    let standardizedHistory = priceHistory.map((point, index) => {
        if (index === 0 && point.round === 0) {
            return { round: 0, price: 0 };
        }
        return point;
    });
    
    // Убираем последнюю точку, если она дублирует предыдущую (последний шаг графика прямой)
    if (standardizedHistory.length > 2) {
        const lastPoint = standardizedHistory[standardizedHistory.length - 1];
        const prevPoint = standardizedHistory[standardizedHistory.length - 2];
        
        // Если последняя точка имеет тот же раунд, что и предыдущая, или ту же цену - убираем её
        if (lastPoint.round === prevPoint.round || lastPoint.price === prevPoint.price) {
            standardizedHistory = standardizedHistory.slice(0, -1);
        }
    }
    
    // Находим минимальное и максимальное значение цены
    // Для оси Y: минимум всегда 0, максимум - максимальная цена
    const prices = standardizedHistory.map(h => h.price);
    const minPrice = 0; // Ось Y всегда начинается с 0
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 1; // Избегаем деления на ноль
    
    // Рисуем оси
    ctx.strokeStyle = '#8b4513';
    ctx.lineWidth = 2;
    
    // Ось X (раунды)
    ctx.beginPath();
    ctx.moveTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();
    
    // Ось Y (цена)
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, canvas.height - padding);
    ctx.stroke();
    
    // Рисуем сетку и подписи
    ctx.strokeStyle = '#8b4513';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    
    // Горизонтальные линии (цены)
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
        const y = padding + (chartHeight / gridLines) * i;
        const price = maxPrice - (priceRange / gridLines) * i;
        
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(canvas.width - padding, y);
        ctx.stroke();
        
        // Подпись цены
        ctx.fillStyle = '#3a2a1a';
        ctx.font = '12px Arial';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(price).toString(), padding - 10, y + 4);
    }
    
    ctx.setLineDash([]);
    
    // Рисуем график
    // Линия начинается с цены первого раунда (пропускаем точку 0)
    ctx.strokeStyle = '#006400'; // Темно-зеленый цвет
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    let lineStarted = false;
    standardizedHistory.forEach((point, index) => {
        const x = padding + (chartWidth / (standardizedHistory.length - 1)) * index;
        const y = padding + chartHeight - ((point.price - minPrice) / priceRange) * chartHeight;
        
        // Пропускаем точку 0 (раунд 0), начинаем линию с первого раунда
        if (index === 0) {
            // Не рисуем линию от точки 0, но сохраняем координату для точки
            return;
        }
        
        if (!lineStarted) {
            // Начинаем линию с цены первого раунда
            ctx.moveTo(x, y);
            lineStarted = true;
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
    
    // Рисуем точки (включая точку 0)
    ctx.fillStyle = '#006400'; // Темно-зеленый цвет
    standardizedHistory.forEach((point, index) => {
        const x = padding + (chartWidth / (standardizedHistory.length - 1)) * index;
        const y = padding + chartHeight - ((point.price - minPrice) / priceRange) * chartHeight;
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        
        // Подпись раунда
        if (index === 0 || index === standardizedHistory.length - 1 || index % Math.ceil(standardizedHistory.length / 5) === 0) {
            ctx.fillStyle = '#3a2a1a';
            ctx.font = '11px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(point.round.toString(), x, canvas.height - padding + 20);
            ctx.fillStyle = '#006400'; // Темно-зеленый цвет
        }
    });
    
    // Подписи осей
    ctx.fillStyle = '#3a2a1a';
    ctx.font = '14px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Раунд', canvas.width / 2, canvas.height - 10);
    
    ctx.save();
    ctx.translate(15, canvas.height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Цена (монеты)', 0, 0);
    ctx.restore();
}

// Подключаемся при загрузке страницы
window.addEventListener('load', () => {
    // Инициализация модального окна ресурса
    resourceModal = document.getElementById('resource-modal');
    resourceModalClose = document.getElementById('resource-modal-close');
    resourceModalNavLeft = document.getElementById('resource-modal-nav-left');
    resourceModalNavRight = document.getElementById('resource-modal-nav-right');
    
    // Обработчики навигации ресурсов
    if (resourceModalNavLeft) {
        resourceModalNavLeft.addEventListener('click', () => {
            navigateToPreviousResource();
        });
    }
    
    if (resourceModalNavRight) {
        resourceModalNavRight.addEventListener('click', () => {
            navigateToNextResource();
        });
    }
    
    if (resourceModalClose) {
        resourceModalClose.addEventListener('click', () => {
            if (resourceModal) {
                resourceModal.style.display = 'none';
            }
        });
    }
    
    // Закрытие при клике вне модального окна - исправлено для избежания конфликта
    document.addEventListener('click', (event) => {
        if (resourceModal && event.target === resourceModal) {
            resourceModal.style.display = 'none';
        }
    });
    
    // Навигация с клавиатуры для ресурсов
    document.addEventListener('keydown', (event) => {
        if (resourceModal && resourceModal.style.display === 'block') {
            if (event.key === 'ArrowLeft') {
                navigateToPreviousResource();
            } else if (event.key === 'ArrowRight') {
                navigateToNextResource();
            } else if (event.key === 'Escape') {
                resourceModal.style.display = 'none';
            }
        }
    });
    
    connectWebSocket();
});

