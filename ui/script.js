let devices = [];
let selectedIp = null;
let currentView = 'dashboard';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initial load from Python
    if (window.pywebview) {
        initializeData();
    } else {
        window.addEventListener('pywebviewready', initializeData);
    }

    // Close context menu and modals on click outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.context-menu')) {
            hideContextMenu();
        }
        if (e.target.classList.contains('modal')) {
            closeModal(e.target.id);
        }
    });
});

async function initializeData() {
    await loadPackages();
    await loadDevices();
}

async function loadPackages() {
    const packages = await pywebview.api.get_packages();
    const select = document.getElementById('packageSelect');
    select.innerHTML = '<option value="">Paket Seçilmedi</option>';
    Object.keys(packages).forEach(pkg => {
        const opt = document.createElement('option');
        opt.value = pkg;
        opt.textContent = pkg;
        select.appendChild(opt);
    });
}

async function loadDevices() {
    devices = await pywebview.api.get_devices();
    renderDevices();
    updateStats();
}

function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
    const targetView = document.getElementById(viewId + 'View');
    if (targetView) targetView.style.display = 'block';

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('onclick').includes(viewId)) {
            item.classList.add('active');
        }
    });
    currentView = viewId;
}

function renderDevices() {
    const grid = document.getElementById('deviceGrid');
    const query = document.getElementById('searchInput').value.toLowerCase();

    grid.innerHTML = '';

    devices.forEach(dev => {
        if (query && !dev.ip.includes(query) && !dev.tag.toLowerCase().includes(query)) {
            return;
        }

        const card = document.createElement('div');
        card.className = 'device-card';
        card.oncontextmenu = (e) => showContextMenu(e, dev.ip);

        card.innerHTML = `
            <div class="device-header">
                <span class="device-ip">${dev.ip}</span>
                <div class="status-indicator ${dev.status === 'online' ? 'online' : 'offline'}" id="ind-${dev.ip.replace(/\./g, '-')}"></div>
            </div>
            <div class="device-tag" id="tag-${dev.ip.replace(/\./g, '-')}">${dev.tag || ''}</div>
            <div class="device-stats">
                <span class="latency" id="lat-${dev.ip.replace(/\./g, '-')}">${dev.latency || '--'}ms</span>
                <span class="uptime" id="up-${dev.ip.replace(/\./g, '-')}">${dev.uptime || 0}s</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function updateStats() {
    const online = devices.filter(d => d.status === 'online').length;
    document.getElementById('onlineCount').textContent = online;
    document.getElementById('offlineCount').textContent = devices.length - online;
    document.getElementById('totalCount').textContent = devices.length;
}

// Called by Python bridge
function updateDeviceStatus(ip, status, latency, uptime) {
    const dev = devices.find(d => d.ip === ip);
    if (dev) {
        dev.status = status;
        dev.latency = latency;
        dev.uptime = uptime;

        const ipKey = ip.replace(/\./g, '-');
        const ind = document.getElementById(`ind-${ipKey}`);
        const lat = document.getElementById(`lat-${ipKey}`);
        const up = document.getElementById(`up-${ipKey}`);

        if (ind) {
            ind.className = `status-indicator ${status}`;
        }
        if (lat) lat.textContent = `${latency}ms`;
        if (up) up.textContent = `${uptime}s`;

        updateStats();
    }
}

function updateDeviceTag(ip, tag) {
    const dev = devices.find(d => d.ip === ip);
    if (dev) {
        dev.tag = tag;
        const tagEl = document.getElementById(`tag-${ip.replace(/\./g, '-')}`);
        if (tagEl) tagEl.textContent = tag;
    }
}

// Search
function filterDevices() {
    renderDevices();
}

// Modals
function openAddModal() {
    document.getElementById('addModal').style.display = 'flex';
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

async function confirmBulkAdd() {
    const text = document.getElementById('bulkIps').value;
    if (text) {
        await pywebview.api.bulk_add(text);
        closeModal('addModal');
        await loadDevices();
    }
}

async function resetDashboard() {
    if (confirm('Tüm cihazları temizlemek istediğinize emin misiniz?')) {
        await pywebview.api.reset_devices();
        await loadDevices();
    }
}

// Package Management
async function savePackage() {
    const name = prompt('Paket Adı:');
    if (name) {
        await pywebview.api.save_package(name);
        await loadPackages();
    }
}

async function loadPackage() {
    const name = document.getElementById('packageSelect').value;
    if (name) {
        await pywebview.api.load_package(name);
        await loadDevices();
    }
}

async function deletePackage() {
    const name = document.getElementById('packageSelect').value;
    if (name && confirm(`"${name}" paketini silmek istediğinize emin misiniz?`)) {
        await pywebview.api.delete_package(name);
        await loadPackages();
    }
}

// Context Menu
function showContextMenu(e, ip) {
    e.preventDefault();
    selectedIp = ip;
    const menu = document.getElementById('contextMenu');
    menu.style.display = 'block';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
}

function hideContextMenu() {
    document.getElementById('contextMenu').style.display = 'none';
}

async function handleMenuAction(action) {
    hideContextMenu();
    if (!selectedIp) return;

    switch(action) {
        case 'tag':
            const newTag = prompt('Yeni etiket/açıklama girin:');
            if (newTag !== null) await pywebview.api.manage_tag(selectedIp, newTag);
            break;
        case 'hostname':
            await pywebview.api.find_hostname(selectedIp);
            break;
        case 'manufacturer':
            await pywebview.api.find_manufacturer(selectedIp);
            break;
        case 'web':
            await pywebview.api.open_web_ui(selectedIp);
            break;
        case 'ports':
            await pywebview.api.start_port_scan(selectedIp);
            break;
        case 'traceroute':
            await pywebview.api.start_traceroute(selectedIp);
            break;
        case 'ssh':
            await pywebview.api.connect_remote('ssh', selectedIp);
            break;
        case 'rdp':
            await pywebview.api.connect_remote('rdp', selectedIp);
            break;
        case 'delete':
            await pywebview.api.delete_device(selectedIp);
            await loadDevices();
            break;
    }
}

// Discovery
async function startDiscovery() {
    const start = document.getElementById('scanStart').value;
    const end = document.getElementById('scanEnd').value;

    document.getElementById('scanProgress').style.display = 'block';
    document.getElementById('scanBtn').disabled = true;

    await pywebview.api.start_discovery(start, end);
}

// Called by Python during discovery
function updateScanProgress(current, total) {
    const percent = (current / total) * 100;
    document.getElementById('progressBar').style.width = percent + '%';
    document.getElementById('progressText').textContent = `${current}/${total}`;

    if (current === total) {
        setTimeout(() => {
            document.getElementById('scanProgress').style.display = 'none';
            document.getElementById('scanBtn').disabled = false;
            showView('dashboard');
            loadDevices();
        }, 1000);
    }
}
