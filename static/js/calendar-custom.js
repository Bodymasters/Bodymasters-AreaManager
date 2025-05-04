// سكريبت مخصص لتكبير التقويم

document.addEventListener('DOMContentLoaded', function() {
    // تحديد جميع حقول التاريخ
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    // تطبيق التحسينات على كل حقل
    dateInputs.forEach(function(input) {
        // إضافة مستمع الحدث للنقر لفتح منتقي التاريخ
        input.addEventListener('click', function() {
            // فتح التقويم
            this.showPicker();
            
            // تأخير قصير للتأكد من ظهور التقويم
            setTimeout(function() {
                // محاولة تكبير التقويم باستخدام CSS
                const calendarElements = document.querySelectorAll('::-webkit-calendar-picker');
                if (calendarElements.length > 0) {
                    calendarElements.forEach(function(calendar) {
                        calendar.style.transform = 'scale(1.5)';
                        calendar.style.transformOrigin = 'top right';
                    });
                }
                
                // محاولة تكبير التقويم باستخدام طريقة بديلة
                const calendarPopup = document.querySelector('.calendar-popup');
                if (calendarPopup) {
                    calendarPopup.style.transform = 'scale(1.5)';
                    calendarPopup.style.transformOrigin = 'top right';
                }
                
                // محاولة تكبير التقويم باستخدام طريقة أخرى
                const calendarContainer = document.querySelector('.calendar-container');
                if (calendarContainer) {
                    calendarContainer.style.transform = 'scale(1.5)';
                    calendarContainer.style.transformOrigin = 'top right';
                }
                
                // محاولة تكبير التقويم باستخدام طريقة أخرى
                const calendarDays = document.querySelectorAll('.calendar-day');
                if (calendarDays.length > 0) {
                    calendarDays.forEach(function(day) {
                        day.style.fontSize = '18px';
                    });
                }
                
                // محاولة تكبير التقويم باستخدام طريقة أخرى
                const calendarWeekdays = document.querySelectorAll('.calendar-weekday');
                if (calendarWeekdays.length > 0) {
                    calendarWeekdays.forEach(function(weekday) {
                        weekday.style.fontSize = '18px';
                        weekday.style.fontWeight = 'bold';
                    });
                }
                
                // محاولة تكبير التقويم باستخدام طريقة أخرى
                const calendarMonthYear = document.querySelector('.calendar-month-year');
                if (calendarMonthYear) {
                    calendarMonthYear.style.fontSize = '20px';
                    calendarMonthYear.style.fontWeight = 'bold';
                }
            }, 100);
        });
    });
    
    // محاولة تكبير التقويم باستخدام MutationObserver
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    if (node.nodeType === 1 && (
                        node.classList.contains('calendar-popup') || 
                        node.classList.contains('calendar-container') ||
                        node.tagName === 'CALENDAR' ||
                        node.querySelector('.calendar-day')
                    )) {
                        // تكبير التقويم
                        node.style.transform = 'scale(1.5)';
                        node.style.transformOrigin = 'top right';
                        
                        // تكبير حجم الخط في التقويم
                        const days = node.querySelectorAll('.calendar-day');
                        if (days.length > 0) {
                            days.forEach(function(day) {
                                day.style.fontSize = '18px';
                            });
                        }
                        
                        const weekdays = node.querySelectorAll('.calendar-weekday');
                        if (weekdays.length > 0) {
                            weekdays.forEach(function(weekday) {
                                weekday.style.fontSize = '18px';
                                weekday.style.fontWeight = 'bold';
                            });
                        }
                        
                        const monthYear = node.querySelector('.calendar-month-year');
                        if (monthYear) {
                            monthYear.style.fontSize = '20px';
                            monthYear.style.fontWeight = 'bold';
                        }
                    }
                }
            }
        });
    });
    
    // بدء مراقبة التغييرات في DOM
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});
