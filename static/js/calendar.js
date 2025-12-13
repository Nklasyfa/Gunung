/**
 * Interactive Calendar Component for Pemesanan Tiket
 * Displays available dates with prices and allows date/jalur selection
 */

(function () {
    'use strict';

    var tiketData = [];
    var currentMonth = new Date().getMonth();
    var currentYear = new Date().getFullYear();
    var selectedDate = null;
    var availableDates = {};

    var monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];

    // Format currency
    function formatCurrency(value) {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }

    // Parse tiket data from hidden element
    function loadTiketData() {
        try {
            var tiketRaw = document.getElementById('tiketDataRaw');
            if (tiketRaw) {
                tiketData = JSON.parse(tiketRaw.getAttribute('data-tiket')) || [];
            }
        } catch (e) {
            console.error('Invalid tiket data', e);
            tiketData = [];
        }

        // Check if jalur is pre-selected (from URL parameter)
        var selectedJalurId = null;
        var jalurInfoDiv = document.querySelector('[data-jalur-id]');
        if (jalurInfoDiv) {
            selectedJalurId = parseInt(jalurInfoDiv.getAttribute('data-jalur-id'));
        }

        // Filter tiket by jalur_id if one is selected
        if (selectedJalurId) {
            tiketData = tiketData.filter(function (t) {
                return t.jalur_id === selectedJalurId;
            });
        }

        // Index by date
        availableDates = {};
        tiketData.forEach(function (t) {
            if (t.tdate) {
                if (!availableDates[t.tdate]) {
                    availableDates[t.tdate] = [];
                }
                availableDates[t.tdate].push(t);
            }
        });
    }

    // Render calendar grid
    function renderCalendar() {
        var calendarGrid = document.getElementById('calendarGrid');
        if (!calendarGrid) return;

        var calendarMonth = document.getElementById('calendarMonth');
        var calendarYear = document.getElementById('calendarYear');

        if (calendarMonth) calendarMonth.textContent = monthNames[currentMonth];
        if (calendarYear) calendarYear.textContent = currentYear;

        calendarGrid.innerHTML = '';

        var firstDay = new Date(currentYear, currentMonth, 1).getDay();
        var daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        var today = new Date();
        today.setHours(0, 0, 0, 0);

        // Empty cells for days before first day of month
        for (var i = 0; i < firstDay; i++) {
            var emptyCell = document.createElement('div');
            emptyCell.style.height = '50px';
            calendarGrid.appendChild(emptyCell);
        }

        // Day cells
        for (var day = 1; day <= daysInMonth; day++) {
            var dateStr = currentYear + '-' + String(currentMonth + 1).padStart(2, '0') + '-' + String(day).padStart(2, '0');
            var cellDate = new Date(currentYear, currentMonth, day);
            var isPast = cellDate < today;
            var isAvailable = availableDates[dateStr] && availableDates[dateStr].length > 0;
            var isSelected = selectedDate === dateStr;

            var cell = document.createElement('div');
            cell.className = 'cal-day';
            cell.setAttribute('data-date', dateStr);

            // Apply styles based on state
            if (isPast) {
                cell.classList.add('cal-day-past');
            } else if (isSelected) {
                cell.classList.add('cal-day-selected');
            } else if (isAvailable) {
                cell.classList.add('cal-day-available');
            } else {
                cell.classList.add('cal-day-unavailable');
            }

            // Day number
            var daySpan = document.createElement('span');
            daySpan.className = 'cal-day-num';
            daySpan.textContent = day;
            cell.appendChild(daySpan);

            // Price for available dates
            if (isAvailable && !isPast) {
                var prices = availableDates[dateStr].map(function (t) { return t.harga || 0; });
                var minPrice = Math.min.apply(null, prices);
                var priceSpan = document.createElement('span');
                priceSpan.className = 'cal-day-price';
                priceSpan.textContent = Math.floor(minPrice / 1000) + 'K';
                cell.appendChild(priceSpan);

                // Click handler
                (function (ds) {
                    cell.addEventListener('click', function () {
                        selectDate(ds);
                    });
                })(dateStr);
            }

            calendarGrid.appendChild(cell);
        }
    }

    // Handle date selection
    function selectDate(dateStr) {
        selectedDate = dateStr;
        var ticketsForDate = availableDates[dateStr] || [];

        if (ticketsForDate.length === 1) {
            selectTiket(ticketsForDate[0]);
        } else if (ticketsForDate.length > 1) {
            showJalurSelection(ticketsForDate);
        }

        renderCalendar();
    }

    // Show jalur selection when multiple jalur available
    function showJalurSelection(tickets) {
        var jalurSelection = document.getElementById('jalurSelection');
        var jalurOptions = document.getElementById('jalurOptions');
        var selectedDateDisplay = document.getElementById('selectedDateDisplay');

        if (!jalurSelection || !jalurOptions) return;

        jalurOptions.innerHTML = '';

        tickets.forEach(function (t) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'jalur-option-btn';
            btn.innerHTML = '<strong>' + (t.nama_jalur || 'Jalur') + '</strong><br><small>' + formatCurrency(t.harga || 0) + '</small>';
            btn.addEventListener('click', function () {
                selectTiket(t);
            });
            jalurOptions.appendChild(btn);
        });

        jalurSelection.style.display = 'block';
        if (selectedDateDisplay) selectedDateDisplay.style.display = 'none';
    }

    // Handle tiket selection
    function selectTiket(tiket) {
        var tiketInput = document.getElementById('tiket_id');
        if (tiketInput) tiketInput.value = tiket.tiket_id;

        var selectedDateDisplay = document.getElementById('selectedDateDisplay');
        var selectedDateText = document.getElementById('selectedDateText');
        var selectedJalurText = document.getElementById('selectedJalurText');
        var selectedPriceText = document.getElementById('selectedPriceText');
        var jalurSelection = document.getElementById('jalurSelection');

        if (selectedDateDisplay) selectedDateDisplay.style.display = 'block';

        if (selectedDateText && tiket.tdate) {
            var parts = tiket.tdate.split('-');
            selectedDateText.textContent = parts[2] + ' ' + monthNames[parseInt(parts[1]) - 1] + ' ' + parts[0];
        }

        if (selectedJalurText) {
            selectedJalurText.textContent = 'Jalur: ' + (tiket.nama_jalur || '-');
        }

        if (selectedPriceText) {
            selectedPriceText.textContent = formatCurrency(tiket.harga || 0);
        }

        if (jalurSelection) jalurSelection.style.display = 'none';

        // Trigger price update
        if (typeof window.updatePrice === 'function') {
            window.updatePrice();
        }

        renderCalendar();
    }

    // Navigation handlers
    function prevMonth() {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar();
    }

    function nextMonth() {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    }

    // Initialize calendar
    function initCalendar() {
        loadTiketData();

        var prevBtn = document.getElementById('prevMonth');
        var nextBtn = document.getElementById('nextMonth');

        if (prevBtn) {
            prevBtn.addEventListener('click', prevMonth);
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', nextMonth);
        }

        renderCalendar();
    }

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCalendar);
    } else {
        initCalendar();
    }

})();
