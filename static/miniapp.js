// Telegram WebApp API
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Глобальные переменные
let playerState = null;
let prices = [];
let currentRound = 1;
let playerId = null;
let playerName = null;
let isAuthorized = false;
let telegramUser = null;
let updateInterval = null; // Интервал для обновления данных

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Получаем данные пользователя из Telegram
        telegramUser = tg.initDataUnsafe?.user;
        if (!telegramUser) {
            showToast('Ошибка авторизации', 'error');
            return;
        }

        playerId = `tg_${telegramUser.id}`;
        
        // Проверяем, авторизован ли игрок
        await checkAuth();
    } catch (error) {
        console.error('Ошибка инициализации:', error);
        showToast('Ошибка загрузки данных', 'error');
    }
});

// Проверка авторизации
async function checkAuth() {
    try {
        const response = await fetch('/api/miniapp/player/state', {
            headers: {
                'X-Telegram-Init-Data': tg.initData
            }
        });

        if (!response.ok) {
            throw new Error('Ошибка проверки авторизации');
        }

        const data = await response.json();
        
        // Если игрок не найден или нет никнейма - показываем окно авторизации
        if (!data.nickname) {
            showAuthModal();
            return;
        }

        // Игрок авторизован
        isAuthorized = true;
        playerName = data.nickname;
        document.getElementById('main-container').style.display = 'block';
        
        // Загружаем начальные данные
        await loadPlayerState();
        await loadPrices();
        await loadRoundInfo();

        // Обновляем данные каждые 2 секунды (очищаем предыдущий интервал, если есть)
        if (updateInterval) {
            clearInterval(updateInterval);
        }
        updateInterval = setInterval(async () => {
            await loadPlayerState();
            await loadPrices();
            await loadRoundInfo();
        }, 2000);
    } catch (error) {
        console.error('Ошибка проверки авторизации:', error);
        // Если игрок не найден, показываем окно авторизации
        showAuthModal();
    }
}

// Показать окно авторизации
function showAuthModal() {
    const modal = document.getElementById('auth-modal');
    modal.style.display = 'block';
    
    // Предзаполняем никнейм из Telegram
    const telegramName = telegramUser?.first_name || telegramUser?.username || '';
    document.getElementById('nickname-input').value = telegramName;
    
    // Показываем фото из Telegram, если есть
    if (telegramUser?.photo_url) {
        useTelegramPhoto();
    }
}

// Использовать фото из Telegram
function useTelegramPhoto() {
    if (telegramUser?.photo_url) {
        const previewImg = document.getElementById('preview-image');
        const placeholder = document.getElementById('photo-placeholder');
        previewImg.src = telegramUser.photo_url;
        previewImg.style.display = 'block';
        placeholder.style.display = 'none';
    } else {
        showToast('Фото в профиле Telegram не найдено', 'error');
    }
}

// Сохранить данные авторизации
async function saveAuthData() {
    const nickname = document.getElementById('nickname-input').value.trim();
    
    if (!nickname) {
        showToast('Введите никнейм', 'error');
        return;
    }

    if (nickname.length < 2) {
        showToast('Никнейм должен быть не менее 2 символов', 'error');
        return;
    }

    showLoading(true);

    try {
        const photoUrl = telegramUser?.photo_url || null;
        const previewImg = document.getElementById('preview-image');
        const finalPhotoUrl = previewImg.style.display === 'block' ? previewImg.src : null;

        const response = await fetch('/api/miniapp/player/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': tg.initData
            },
            body: JSON.stringify({
                nickname: nickname,
                photo_url: finalPhotoUrl
            })
        });

        const data = await response.json();

        if (data.success) {
            isAuthorized = true;
            playerName = nickname;
            document.getElementById('auth-modal').style.display = 'none';
            document.getElementById('main-container').style.display = 'block';
            
            // Загружаем начальные данные
            await loadPlayerState();
            await loadPrices();
            await loadRoundInfo();

            // Обновляем данные каждые 2 секунды (очищаем предыдущий интервал, если есть)
            if (updateInterval) {
                clearInterval(updateInterval);
            }
            updateInterval = setInterval(async () => {
                await loadPlayerState();
                await loadPrices();
                await loadRoundInfo();
            }, 2000);
        } else {
            showToast(data.message || 'Ошибка сохранения данных', 'error');
        }
    } catch (error) {
        console.error('Ошибка сохранения данных:', error);
        showToast('Ошибка сохранения данных', 'error');
    } finally {
        showLoading(false);
    }
}

// Загрузка состояния игрока
async function loadPlayerState() {
    try {
        const response = await fetch('/api/miniapp/player/state', {
            headers: {
                'X-Telegram-Init-Data': tg.initData
            }
        });

        if (!response.ok) {
            throw new Error('Ошибка загрузки состояния');
        }

        const data = await response.json();
        playerState = data;

        // Обновляем UI
        updatePlayerInfo();
        updateResources();
        updateBuildings();
    } catch (error) {
        console.error('Ошибка загрузки состояния игрока:', error);
    }
}

// Загрузка цен
async function loadPrices() {
    try {
        const response = await fetch('/api/miniapp/prices');
        if (!response.ok) return;

        const data = await response.json();
        prices = data.prices || [];

        updatePrices();
    } catch (error) {
        console.error('Ошибка загрузки цен:', error);
    }
}

// Загрузка информации о раунде
async function loadRoundInfo() {
    try {
        const response = await fetch('/api/miniapp/round-info');
        if (!response.ok) return;

        const data = await response.json();
        currentRound = data.current_round || 1;

        document.getElementById('current-round').textContent = currentRound;
    } catch (error) {
        console.error('Ошибка загрузки информации о раунде:', error);
    }
}

// Обновление информации об игроке
function updatePlayerInfo() {
    if (!playerState) return;

    document.getElementById('player-money').textContent = Math.round(playerState.money || 0);
    
    // Обновляем имя игрока
    if (playerState.nickname) {
        document.getElementById('player-name').textContent = playerState.nickname;
    }
    
    // Обновляем аватар
    const avatarImg = document.getElementById('player-avatar');
    const avatarPlaceholder = document.getElementById('player-avatar-placeholder');
    
    if (playerState.photo_url) {
        avatarImg.src = playerState.photo_url;
        avatarImg.style.display = 'block';
        avatarPlaceholder.style.display = 'none';
    } else {
        avatarImg.style.display = 'none';
        avatarPlaceholder.style.display = 'flex';
    }
}

// Обновление ресурсов
function updateResources() {
    if (!playerState || !playerState.resources) return;

    const grid = document.getElementById('resources-grid');
    grid.innerHTML = '';

    const resourceNames = ['камень', 'дерево', 'железо', 'скот', 'овощи', 'рабы', 'золото', 'зерно', 'рыба'];

    resourceNames.forEach(resource => {
        const amount = playerState.resources[resource] || 0;
        
        const card = document.createElement('div');
        card.className = 'resource-card';
        card.innerHTML = `
            <div class="resource-name">${capitalizeFirst(resource)}</div>
            <div class="resource-amount">${amount}</div>
        `;
        grid.appendChild(card);
    });
}

// Обновление объектов
function updateBuildings() {
    if (!playerState || !playerState.buildings) return;

    const list = document.getElementById('buildings-list');
    list.innerHTML = '';

    if (playerState.buildings.length === 0) {
        list.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">У вас пока нет объектов</div>';
        return;
    }

    // Группируем объекты по названию
    const buildingsMap = {};
    playerState.buildings.forEach(building => {
        if (!buildingsMap[building.name]) {
            buildingsMap[building.name] = {
                name: building.name,
                count: 0,
                statuses: []
            };
        }
        buildingsMap[building.name].count++;
        buildingsMap[building.name].statuses.push(building.status);
    });

    Object.values(buildingsMap).forEach(building => {
        const card = document.createElement('div');
        card.className = 'building-card';
        
        const statusText = getStatusText(building.statuses[0]);
        
        card.innerHTML = `
            <div>
                <div class="building-name">${building.name}</div>
                <div class="building-status">${statusText}</div>
            </div>
            <div class="building-count">${building.count}</div>
        `;
        list.appendChild(card);
    });
}

// Обновление цен
function updatePrices() {
    const list = document.getElementById('prices-list');
    list.innerHTML = '';

    prices.forEach(price => {
        const item = document.createElement('div');
        item.className = 'price-item';
        
        const changeClass = price.change_from_prev_percent >= 0 ? 'positive' : 'negative';
        const changeSign = price.change_from_prev_percent >= 0 ? '+' : '';
        
        item.innerHTML = `
            <div class="price-resource">${capitalizeFirst(price.resource)}</div>
            <div>
                <span class="price-value">${price.current_price}</span>
                <span class="price-change ${changeClass}">
                    ${changeSign}${Math.round(price.change_from_prev_percent)}%
                </span>
            </div>
        `;
        list.appendChild(item);
    });
}

// Модальные окна
function showBuyResourceModal() {
    const modal = document.getElementById('buy-resource-modal');
    const options = document.getElementById('buy-resource-options');
    options.innerHTML = '';

    prices.forEach(price => {
        const option = document.createElement('div');
        option.className = 'modal-option';
        option.innerHTML = `
            <div class="modal-option-header">
                <span class="modal-option-name">${capitalizeFirst(price.resource)}</span>
                <span class="modal-option-price">${price.current_price} монет</span>
            </div>
            <input type="number" class="amount-input" id="buy-${price.resource}" placeholder="Количество" min="1" value="1">
            <button class="confirm-btn" onclick="buyResource('${price.resource}')">Купить</button>
        `;
        options.appendChild(option);
    });

    modal.style.display = 'block';
}

function showSellResourceModal() {
    if (!playerState || !playerState.resources) return;

    const modal = document.getElementById('sell-resource-modal');
    const options = document.getElementById('sell-resource-options');
    options.innerHTML = '';

    const resourceNames = ['камень', 'дерево', 'железо', 'скот', 'овощи', 'рабы', 'золото', 'зерно', 'рыба'];
    
    resourceNames.forEach(resource => {
        const amount = playerState.resources[resource] || 0;
        if (amount === 0) return;

        const price = prices.find(p => p.resource === resource);
        if (!price) return;

        const option = document.createElement('div');
        option.className = 'modal-option';
        option.innerHTML = `
            <div class="modal-option-header">
                <span class="modal-option-name">${capitalizeFirst(resource)}</span>
                <span class="modal-option-price">${price.current_price} монет</span>
            </div>
            <div class="modal-option-details">У вас: ${amount}</div>
            <input type="number" class="amount-input" id="sell-${resource}" placeholder="Количество" min="1" max="${amount}" value="1">
            <button class="confirm-btn" onclick="sellResource('${resource}')">Продать</button>
        `;
        options.appendChild(option);
    });

    if (options.innerHTML === '') {
        options.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">У вас нет ресурсов для продажи</div>';
    }

    modal.style.display = 'block';
}

function showBuildModal() {
    // Загрузим список доступных объектов через API
    fetch('/api/miniapp/buildings')
        .then(res => res.json())
        .then(data => {
            const modal = document.getElementById('build-modal');
            const options = document.getElementById('build-options');
            options.innerHTML = '';

            data.buildings.forEach(building => {
                const option = document.createElement('div');
                option.className = 'modal-option';
                
                const canBuild = building.can_build;
                if (!canBuild) {
                    option.classList.add('disabled');
                }

                option.innerHTML = `
                    <div class="modal-option-header">
                        <span class="modal-option-name">${building.name}</span>
                        <span class="modal-option-price">${building.cost} монет</span>
                    </div>
                    <div class="modal-option-details">${building.cost_details}</div>
                    ${canBuild ? `<button class="confirm-btn" onclick="buildBuilding('${building.name}')">Построить</button>` : '<div style="color: #dc3545; margin-top: 10px;">Недостаточно ресурсов</div>'}
                `;
                options.appendChild(option);
            });

            modal.style.display = 'block';
        })
        .catch(error => {
            console.error('Ошибка загрузки объектов:', error);
            showToast('Ошибка загрузки объектов', 'error');
        });
}

function showSellBuildingModal() {
    if (!playerState || !playerState.buildings) return;

    const modal = document.getElementById('sell-building-modal');
    const options = document.getElementById('sell-building-options');
    options.innerHTML = '';

    // Группируем объекты
    const buildingsMap = {};
    playerState.buildings.forEach(building => {
        if (building.status === 'active' || building.status === 'completed') {
            if (!buildingsMap[building.name]) {
                buildingsMap[building.name] = {
                    name: building.name,
                    count: 0,
                    building_id: building.id
                };
            }
            buildingsMap[building.name].count++;
        }
    });

    if (Object.keys(buildingsMap).length === 0) {
        options.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">У вас нет объектов для продажи</div>';
        modal.style.display = 'block';
        return;
    }

    Object.values(buildingsMap).forEach(building => {
        const option = document.createElement('div');
        option.className = 'modal-option';
        option.innerHTML = `
            <div class="modal-option-header">
                <span class="modal-option-name">${building.name}</span>
                <span class="modal-option-price">Количество: ${building.count}</span>
            </div>
            <button class="confirm-btn" onclick="sellBuilding('${building.building_id}')">Продать</button>
        `;
        options.appendChild(option);
    });

    modal.style.display = 'block';
}

// Действия игрока
async function buyResource(resource) {
    const amount = parseInt(document.getElementById(`buy-${resource}`).value);
    if (!amount || amount < 1) {
        showToast('Введите количество', 'error');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/api/miniapp/player/buy-resource', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': tg.initData
            },
            body: JSON.stringify({ resource, amount })
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message || 'Ресурс куплен', 'success');
            closeModal('buy-resource-modal');
            await loadPlayerState();
        } else {
            showToast(data.message || 'Ошибка покупки', 'error');
        }
    } catch (error) {
        console.error('Ошибка покупки ресурса:', error);
        showToast('Ошибка покупки ресурса', 'error');
    } finally {
        showLoading(false);
    }
}

async function sellResource(resource) {
    const amount = parseInt(document.getElementById(`sell-${resource}`).value);
    if (!amount || amount < 1) {
        showToast('Введите количество', 'error');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/api/miniapp/player/sell-resource', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': tg.initData
            },
            body: JSON.stringify({ resource, amount })
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message || 'Ресурс продан', 'success');
            closeModal('sell-resource-modal');
            await loadPlayerState();
        } else {
            showToast(data.message || 'Ошибка продажи', 'error');
        }
    } catch (error) {
        console.error('Ошибка продажи ресурса:', error);
        showToast('Ошибка продажи ресурса', 'error');
    } finally {
        showLoading(false);
    }
}

async function buildBuilding(buildingName) {
    showLoading(true);

    try {
        const response = await fetch('/api/miniapp/player/build', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': tg.initData
            },
            body: JSON.stringify({ building_name: buildingName })
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message || 'Объект начат', 'success');
            closeModal('build-modal');
            await loadPlayerState();
        } else {
            showToast(data.message || 'Ошибка строительства', 'error');
        }
    } catch (error) {
        console.error('Ошибка строительства:', error);
        showToast('Ошибка строительства', 'error');
    } finally {
        showLoading(false);
    }
}

async function sellBuilding(buildingId) {
    showLoading(true);

    try {
        const response = await fetch('/api/miniapp/player/sell-building', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': tg.initData
            },
            body: JSON.stringify({ building_id: buildingId })
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message || 'Объект выставлен на продажу', 'success');
            closeModal('sell-building-modal');
            await loadPlayerState();
        } else {
            showToast(data.message || 'Ошибка продажи объекта', 'error');
        }
    } catch (error) {
        console.error('Ошибка продажи объекта:', error);
        showToast('Ошибка продажи объекта', 'error');
    } finally {
        showLoading(false);
    }
}

// Вспомогательные функции
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function showLoading(show) {
    document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function getStatusText(status) {
    const statusMap = {
        'building': 'Строится',
        'completed': 'Построен',
        'active': 'Активен',
        'for_sale': 'На продаже'
    };
    return statusMap[status] || status;
}

// Закрытие модальных окон при клике вне их
window.onclick = function(event) {
    const modals = ['buy-resource-modal', 'sell-resource-modal', 'build-modal', 'sell-building-modal'];
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

