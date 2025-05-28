// static/js/main.js
document.addEventListener('DOMContentLoaded', function () {
    // --- GLOBAL AYARLAR ve SABİTLER ---
    const JS_CONFIG_MAX_HISTORY_POINTS_LOCAL = typeof JS_CONFIG_MAX_HISTORY_POINTS !== 'undefined' ? parseInt(JS_CONFIG_MAX_HISTORY_POINTS, 10) : 30;
    const JS_MAX_API_POINTS_FOR_MAIN_CHARTS_LOCAL = typeof JS_MAX_API_POINTS_FOR_MAIN_CHARTS !== 'undefined' ? parseInt(JS_MAX_API_POINTS_FOR_MAIN_CHARTS, 10) : 30;
    const ALL_CITIES_JS = Array.isArray(ALL_CITIES_LIST_FROM_FLASK) ? ALL_CITIES_LIST_FROM_FLASK : [];
    
    const popularCityButtonsContainer = document.querySelector('.popular-cities');
    const POPULAR_CITIES_JS_FQ_LIST = popularCityButtonsContainer 
        ? Array.from(popularCityButtonsContainer.querySelectorAll('.city-button')).map(btn => btn.dataset.city)
        : ["İstanbul,TR", "Ankara,TR", "İzmir,TR", "Mersin,TR", "Antalya,TR", "Adana,TR", "Bursa,TR"]; // Fallback

    const DEFAULT_START_CITY_FQ = "Mersin,TR";
    const DEFAULT_START_CITY_NAME = "Mersin";

    let currentSelectedCityFQ = null;
    let currentDisplayCityName = null;
    let socket = null;

    // --- DOM ELEMENTLERİ ---
    const themeToggleButton = document.getElementById('theme-toggle-button');
    const body = document.body;
    const themeIcon = themeToggleButton ? themeToggleButton.querySelector('i') : null;
    const popularCityButtons = popularCityButtonsContainer ? Array.from(popularCityButtonsContainer.querySelectorAll('.city-button')) : [];
    const otherCitiesButton = document.getElementById('other-cities-button');
    const otherCitiesDropdown = document.getElementById('other-cities-dropdown');
    const otherCitiesSearchInput = document.getElementById('other-cities-search');
    const otherCitiesUl = document.getElementById('other-cities-list');
    const otherCitiesContainer = document.querySelector('.other-cities-container');
    const cityNameDisplayElement = document.getElementById('city-name-display');
    const serverUpdateElement = document.getElementById('last-update-server');
    
    let tempChart, humidityChart, tempInterpolationChart, tempPredictionChart;
    const allChartsInstances = [];

    // --- TEMA DEĞİŞTİRİCİ ---
    function applyTheme(theme) {
        body.classList.toggle('dark-theme', theme === 'dark');
        if (themeIcon) {
            themeIcon.classList.toggle('fa-sun', theme === 'light');
            themeIcon.classList.toggle('fa-moon', theme === 'dark');
        }
        updateAllChartThemes(theme);
    }
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            const newTheme = body.classList.contains('dark-theme') ? 'light' : 'dark';
            localStorage.setItem('theme', newTheme);
            applyTheme(newTheme);
        });
    }

    // --- ŞEHİR SEÇİM MENÜSÜ ---
    function setActiveCityUI(cityFQ) {
        popularCityButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.city === cityFQ);
        });
        if (otherCitiesUl) {
            Array.from(otherCitiesUl.children).forEach(li => {
                if (li.dataset && li.dataset.city) {
                    li.classList.toggle('highlighted-by-js', li.dataset.city === cityFQ);
                }
            });
        }
        if (otherCitiesButton) {
            const isSelectedCityPopular = POPULAR_CITIES_JS_FQ_LIST.includes(cityFQ);
            otherCitiesButton.classList.toggle('active', !isSelectedCityPopular && !!cityFQ);
        }
    }
    
    function populateOtherCities(searchTerm = "") {
        if (!otherCitiesUl || !ALL_CITIES_JS) return;
        otherCitiesUl.innerHTML = '';
        const filteredCities = ALL_CITIES_JS.filter(cityFQ => {
            const cityNameOnly = cityFQ.split(',')[0].toLowerCase();
            return !POPULAR_CITIES_JS_FQ_LIST.includes(cityFQ) && cityNameOnly.includes(searchTerm.toLowerCase());
        });
        if (filteredCities.length === 0) {
            const li = document.createElement('li');
            li.textContent = searchTerm ? 'Arama sonucu bulunamadı.' : 'Filtrelenecek başka şehir yok.';
            li.style.cssText = "text-align:center; color:var(--text-muted-color); padding: 10px; cursor:default;";
            otherCitiesUl.appendChild(li);
            return;
        }
        filteredCities.forEach(cityFQ => {
            const li = document.createElement('li');
            li.dataset.city = cityFQ;
            li.textContent = cityFQ.split(',')[0];
            if (cityFQ === currentSelectedCityFQ) {
                li.classList.add('highlighted-by-js');
            }
            otherCitiesUl.appendChild(li);
        });
    }

    function handleCitySelection(cityFQ, cityName) {
        if (!cityFQ) { return; }
        if (cityFQ === currentSelectedCityFQ && cityName === currentDisplayCityName) {
            if(otherCitiesDropdown && otherCitiesDropdown.classList.contains('open')) {
                otherCitiesDropdown.classList.remove('open');
                if(otherCitiesButton) otherCitiesButton.classList.remove('open');
            }
            return; 
        }
        currentSelectedCityFQ = cityFQ;       
        currentDisplayCityName = cityName; 
        if (cityNameDisplayElement) cityNameDisplayElement.textContent = cityName;
        setActiveCityUI(cityFQ);
        subscribeToCity(cityFQ, cityName);
    }

    popularCityButtons.forEach(button => {
        button.addEventListener('click', function() {
            handleCitySelection(this.dataset.city, this.textContent);
        });
    });
    if (otherCitiesButton) {
        otherCitiesButton.addEventListener('click', function(event) {
            event.stopPropagation();
            const isOpen = otherCitiesDropdown.classList.toggle('open');
            this.classList.toggle('open', isOpen);
            if (isOpen) {
                populateOtherCities(otherCitiesSearchInput ? otherCitiesSearchInput.value : ""); 
                if(otherCitiesSearchInput) otherCitiesSearchInput.focus();
            }
        });
    }
    if (otherCitiesSearchInput) {
        otherCitiesSearchInput.addEventListener('input', function() { populateOtherCities(this.value); });
        otherCitiesSearchInput.addEventListener('click', function(event) { event.stopPropagation(); });
    }
    if (otherCitiesUl) {
        otherCitiesUl.addEventListener('click', function(event) {
            const clickedLi = event.target.closest('li');
            if (clickedLi && clickedLi.dataset.city) {
                handleCitySelection(clickedLi.dataset.city, clickedLi.textContent);
                if(otherCitiesDropdown) otherCitiesDropdown.classList.remove('open');
                if(otherCitiesButton) otherCitiesButton.classList.remove('open');
            }
        });
    }
    document.addEventListener('click', function(event) {
        if (otherCitiesDropdown && otherCitiesDropdown.classList.contains('open')) {
            if (otherCitiesContainer && !otherCitiesContainer.contains(event.target) && event.target !== otherCitiesButton) {
                otherCitiesDropdown.classList.remove('open');
                if (otherCitiesButton) otherCitiesButton.classList.remove('open');
            }
        }
    });

    // --- SOCKET.IO ---
    function subscribeToCity(cityFQ, displayCityName) {
        if (!socket || !socket.connected) { 
            console.warn("Socket bağlı değil. Abone olunmuyor.");
            return; 
        }
        socket.emit('subscribe_to_city', { city: cityFQ });
        if (cityNameDisplayElement) cityNameDisplayElement.textContent = displayCityName;
        clearUIFields(); 
        resetAllCharts();
        if (serverUpdateElement) serverUpdateElement.textContent = `'${displayCityName}' için veri bekleniyor...`;
    }
    function initializeSocket() {
        if (socket && socket.connected) return;
        if (socket) socket.disconnect();
        socket = io(location.protocol + '//' + document.domain + ':' + location.port + '/weather', {
            reconnectionAttempts: 5, reconnectionDelay: 3000, timeout: 10000
        });
        socket.on('connect', () => {
            console.log(`Socket BAĞLANDI: ${socket.id}`);
            let cityToSelectFQ = currentSelectedCityFQ || DEFAULT_START_CITY_FQ;
            let cityToSelectName = currentDisplayCityName || DEFAULT_START_CITY_NAME;
            handleCitySelection(cityToSelectFQ, cityToSelectName);
        });
        socket.on('weather_update', (data) => { updateUI(data); });
        socket.on('error_occurred', (errorData) => { console.error('Sunucu hatası:', errorData.message); if(serverUpdateElement) serverUpdateElement.textContent = `Hata: ${errorData.message}`; });
        socket.on('disconnect', (reason) => { console.warn('Socket kesildi:', reason); });
        socket.on('connect_error', (err) => { console.error('Socket bağlantı hatası:', err.message); });
    }

    // --- GRAFİK FONKSİYONLARI ---
    function getChartThemeOptions(theme) {
        const isDark = theme === 'dark';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';
        const textColor = isDark ? '#cbd5e0' : '#4a5568';
        const titleColor = isDark ? '#e2e8f0' : '#2d3748';
        return {
            scales: {
                x: { grid: { color: gridColor, borderColor: gridColor }, ticks: { color: textColor }, title: { display: true, text: 'Zaman (UTC)', color: titleColor, font: { weight: '500' } } },
                y: { grid: { color: gridColor, borderColor: gridColor }, ticks: { color: textColor }, title: { display: true, /* text yLabel ile gelecek */ color: titleColor, font: { weight: '500' } } }
            },
            plugins: { legend: { labels: { color: textColor, font: { weight: '500' } } } }
        };
    }
    function createAndRegisterChart(id, yAxisLabel, datasetsConfig) {
        const ctxElement = document.getElementById(id);
        if (!ctxElement) { console.error(`Chart canvas element with id "${id}" not found.`); return null; }
        const ctx = ctxElement.getContext('2d');
        if (!ctx) { console.error(`Could not get 2D context for chart canvas "${id}".`); return null; }
        const currentLocalTheme = localStorage.getItem('theme') || 'light';
        const themeChartOptions = getChartThemeOptions(currentLocalTheme);
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false, // TAŞMA SORUNU İÇİN false
            animation: { duration: 200 },
            interaction: { intersect: false, mode: 'index' },
            scales: {
                x: { ...themeChartOptions.scales.x, type: 'time', time: { unit: 'minute', tooltipFormat: 'HH:mm:ss', displayFormats: { minute: 'HH:mm' } } },
                y: { ...themeChartOptions.scales.y, beginAtZero: false, title: { ...themeChartOptions.scales.y.title, text: yAxisLabel } }
            },
            plugins: { legend: { position: 'top', ...themeChartOptions.plugins.legend } }
        };
        try {
            const chartInstance = new Chart(ctx, { type: 'line', data: { datasets: datasetsConfig }, options: chartOptions });
            allChartsInstances.push(chartInstance);
            return chartInstance;
        } catch (e) { console.error(`Error creating chart "${id}":`, e); return null; }
    }
    function updateAllChartThemes(theme) {
        if (allChartsInstances.length === 0) return;
        const themeOptions = getChartThemeOptions(theme);
        allChartsInstances.forEach(chart => {
            if (chart && chart.options && chart.options.scales && chart.options.plugins) {
                if (chart.options.scales.x) {
                    Object.assign(chart.options.scales.x.grid, themeOptions.scales.x.grid);
                    Object.assign(chart.options.scales.x.ticks, themeOptions.scales.x.ticks);
                    if (chart.options.scales.x.title) Object.assign(chart.options.scales.x.title, { color: themeOptions.scales.x.title.color, font: themeOptions.scales.x.title.font });
                }
                if (chart.options.scales.y) {
                    Object.assign(chart.options.scales.y.grid, themeOptions.scales.y.grid);
                    Object.assign(chart.options.scales.y.ticks, themeOptions.scales.y.ticks);
                    if (chart.options.scales.y.title) Object.assign(chart.options.scales.y.title, { color: themeOptions.scales.y.title.color, font: themeOptions.scales.y.title.font });
                }
                if (chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                    Object.assign(chart.options.plugins.legend.labels, themeOptions.plugins.legend.labels);
                }
                try { chart.update('none'); } catch(e) { /* console.warn(`Chart theme update error for ${chart.canvas.id}:`, e); */ }
            }
        });
    }
    function initializeCharts() {
        console.log("Grafikler başlatılıyor...");
        try {
            tempChart = createAndRegisterChart('tempChart', 'Sıcaklık (°C)', [{ label: 'Sıcaklık', data: [], borderColor: 'rgba(255, 99, 132, 0.8)', backgroundColor: 'rgba(255, 99, 132, 0.3)', tension: 0.2, fill: true, pointRadius: 2, pointHoverRadius: 5 }]);
            humidityChart = createAndRegisterChart('humidityChart', 'Nem (%)', [{ label: 'Nem', data: [], borderColor: 'rgba(54, 162, 235, 0.8)', backgroundColor: 'rgba(54, 162, 235, 0.3)', tension: 0.2, fill: true, pointRadius: 2, pointHoverRadius: 5 }]);
            tempInterpolationChart = createAndRegisterChart('tempInterpolationChart', 'Sıcaklık (°C)', [
                { label: 'Orijinal (API)', data: [], borderColor: 'rgba(255, 99, 132, 0.7)', borderWidth: 2, pointRadius: 3, order: 3, tension: 0.1 },
                { label: 'Lineer İnterp.', data: [], borderColor: 'rgba(75, 192, 192, 0.7)', borderWidth: 2, borderDash: [5, 5], pointRadius: 1, order: 2, tension: 0.1 },
                { label: 'Kübik Spline', data: [], borderColor: 'rgba(153, 102, 255, 0.7)', borderWidth: 2, pointRadius: 1, order: 1, tension: 0.3 }
            ]);
            tempPredictionChart = createAndRegisterChart('tempPredictionChart', 'Sıcaklık (°C)', [
                { label: 'Geçmiş (API)', data: [], borderColor: 'rgba(100, 100, 100, 0.5)', borderWidth: 2, pointRadius: 3, order: 3, tension: 0.1 },
                { label: 'Tahmin (Lineer)', data: [], borderColor: 'rgba(255, 159, 64, 0.8)', borderWidth: 2, borderDash: [8, 4], pointStyle: 'triangle', pointRadius: 4, order: 2, tension: 0.1 },
                { label: 'Tahmin (Kübik)', data: [], borderColor: 'rgba(200, 100, 255, 0.8)', borderWidth: 2, borderDash: [3, 3], pointStyle: 'rectRot', pointRadius: 4, order: 1, tension: 0.3 }
            ]);
            if (allChartsInstances.length > 0) { applyTheme(localStorage.getItem('theme') || 'light'); }
            else { console.warn("Hiç grafik başlatılamadı."); }
        } catch (e) { console.error("Ana grafik oluşturma bloğunda hata:", e); }
    }

    // --- UI GÜNCELLEME ve YARDIMCI FONKSİYONLARI ---
    function resetAllCharts() {
        allChartsInstances.forEach(chart => {
            if (chart && chart.data && chart.data.datasets) {
                chart.data.datasets.forEach(dataset => { dataset.data = []; });
                try { chart.update('none'); } catch(e) {}
            }
        });
    }
    function addDataToChart(chart, timestamp, value, maxPoints = JS_MAX_API_POINTS_FOR_MAIN_CHARTS_LOCAL) {
        if (!chart || value === null || value === undefined || !timestamp) { return; }
        const timestampMs = new Date(timestamp).valueOf();
        if (chart.data && chart.data.datasets && chart.data.datasets.length > 0) {
            const dataset = chart.data.datasets[0].data;
            dataset.push({ x: timestampMs, y: parseFloat(value) });
            while (dataset.length > maxPoints) { dataset.shift(); }
            try { chart.update(); } catch(e) {}
        }
    }
    function updateInterpolationChartUI(originalSeries, linearSeries, cubicSeries) {
        if (!tempInterpolationChart || !tempInterpolationChart.data) return;
        const format = (arr) => (arr || []).map(p => ({ x: new Date(p[0]).valueOf(), y: parseFloat(p[1]) }));
        const limitedOriginal = (originalSeries || []).slice(-JS_CONFIG_MAX_HISTORY_POINTS_LOCAL);
        tempInterpolationChart.data.datasets[0].data = format(limitedOriginal);
        tempInterpolationChart.data.datasets[1].data = format(linearSeries);
        tempInterpolationChart.data.datasets[2].data = format(cubicSeries);
        try { tempInterpolationChart.update(); } catch(e) {}
    }
    function updatePredictionChartUI(originalSeries, predictedLinearSeries, predictedCubicSeries) {
        if (!tempPredictionChart || !tempPredictionChart.data) return;
        const format = (arr) => (arr || []).map(p => ({ x: new Date(p[0]).valueOf(), y: parseFloat(p[1]) }));
        const historicalData = (originalSeries || []).slice(-JS_CONFIG_MAX_HISTORY_POINTS_LOCAL);
        tempPredictionChart.data.datasets[0].data = format(historicalData);
        tempPredictionChart.data.datasets[1].data = format(predictedLinearSeries);
        tempPredictionChart.data.datasets[2].data = format(predictedCubicSeries);
        try { tempPredictionChart.update(); } catch(e) {}
    }
    function clearUIFields() {
        const ids = ['temp_val', 'feels_like_val', 'hum_val', 'pres_val', 'wind_val', 'weather_desc', 'sunrise_val', 'sunset_val', 'nm_total_rain_trapezoidal_val', 'nm_total_rain_simpson_val', 'nm_temp_derivative_central_val', 'rain_1h_val', 'last-update-client'];
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (id === 'rain_1h_val') el.textContent = '0';
                else if (id === 'last-update-client') el.textContent = new Date().toLocaleTimeString('tr-TR');
                else el.textContent = '--';
            }
        });
        const weatherIconEl = document.getElementById('weather-icon');
        if (weatherIconEl) weatherIconEl.src = "";
        if (serverUpdateElement) { serverUpdateElement.textContent = currentDisplayCityName ? `'${currentDisplayCityName}' için veri bekleniyor...` : 'Şehir seçiliyor...'; }
        if (cityNameDisplayElement) { cityNameDisplayElement.textContent = currentDisplayCityName || '--'; }
    }
    function updateUI(data) {
        if (!data || !data.city) { return; }
        const dataCityFQString = data.city_fq ? data.city_fq.toLowerCase() : null;
        const dataCityDisplayString = data.city.toLowerCase();
        const currentSelectedCityFQString = currentSelectedCityFQ ? currentSelectedCityFQ.toLowerCase() : null;
        const currentDisplayCityString = currentDisplayCityName ? currentDisplayCityName.toLowerCase() : null;
        let match = false;
        if (currentSelectedCityFQString && dataCityFQString) { match = (dataCityFQString === currentSelectedCityFQString); }
        else if (currentDisplayCityString) { match = (dataCityDisplayString === currentDisplayCityString); }
        else { match = true; }
        if (!match) { return; }
        if (!currentDisplayCityName && data.city) currentDisplayCityName = data.city;
        if (!currentSelectedCityFQ && data.city_fq) currentSelectedCityFQ = data.city_fq;
        const UIMap = {
            'city-name-display': data.city,
            'temp_val': data.temperature?.toFixed(1), 'feels_like_val': data.feels_like?.toFixed(1),
            'hum_val': data.humidity, 'pres_val': data.pressure, 'wind_val': data.wind_speed?.toFixed(1),
            'weather_desc': data.description, 'rain_1h_val': data.rain_last_1h?.toFixed(1) || '0',
            'sunrise_val': data.sunrise, 'sunset_val': data.sunset,
            'nm_total_rain_trapezoidal_val': data.nm_total_rain_trapezoidal?.toFixed(3),
            'nm_total_rain_simpson_val': data.nm_total_rain_simpson?.toFixed(3),
            'nm_temp_derivative_central_val': data.nm_temp_derivative_central?.toFixed(3),
            'last-update-client': new Date().toLocaleTimeString('tr-TR'),
            'last-update-server': data.timestamp ? new Date(data.timestamp).toLocaleString('tr-TR', {dateStyle:'short', timeStyle:'medium'}) + " (UTC)" : '--'
        };
        for (const id in UIMap) {
            const el = document.getElementById(id);
            if (el) el.textContent = (UIMap[id] !== undefined && UIMap[id] !== null && UIMap[id] !== '') ? UIMap[id] : '--';
        }
        const weatherIconEl = document.getElementById('weather-icon');
        if (weatherIconEl) weatherIconEl.src = data.icon_code ? `http://openweathermap.org/img/wn/${data.icon_code}@4x.png` : "";
        if (data.timestamp) {
            if (tempChart) addDataToChart(tempChart, data.timestamp, data.temperature);
            if (humidityChart) addDataToChart(humidityChart, data.timestamp, data.humidity);
            if (data.nm_original_temp_series_for_plot) {
                if (tempInterpolationChart) updateInterpolationChartUI(data.nm_original_temp_series_for_plot, data.nm_interpolated_temps_linear, data.nm_interpolated_temps_cubic);
                if (tempPredictionChart) updatePredictionChartUI(data.nm_original_temp_series_for_plot, data.nm_predicted_temps_linear, data.nm_predicted_temps_cubic);
            }
        }
        if (cityNameDisplayElement && currentDisplayCityName) cityNameDisplayElement.textContent = currentDisplayCityName;
    }

    // --- BAŞLANGIÇ ---
    initializeCharts(); 
    initializeSocket(); 
    if(otherCitiesButton && otherCitiesUl) { populateOtherCities(); }
    if (!currentSelectedCityFQ) { clearUIFields(); }
});