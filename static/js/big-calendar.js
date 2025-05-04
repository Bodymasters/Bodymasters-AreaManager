/**
 * تقويم مخصص كبير الحجم
 * يستبدل التقويم الافتراضي للمتصفح بتقويم مخصص أكبر حجماً
 */

document.addEventListener('DOMContentLoaded', function() {
    // تحديد جميع حقول التاريخ
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    // تطبيق التقويم المخصص على كل حقل تاريخ
    dateInputs.forEach(function(dateInput) {
        // إخفاء منتقي التاريخ الافتراضي
        dateInput.style.position = 'relative';
        
        // إنشاء زر لفتح التقويم المخصص
        const calendarButton = document.createElement('button');
        calendarButton.type = 'button';
        calendarButton.className = 'calendar-button';
        calendarButton.innerHTML = '<i class="fas fa-calendar-alt"></i>';
        calendarButton.style.position = 'absolute';
        calendarButton.style.right = '10px';
        calendarButton.style.top = '50%';
        calendarButton.style.transform = 'translateY(-50%)';
        calendarButton.style.background = 'transparent';
        calendarButton.style.border = 'none';
        calendarButton.style.fontSize = '20px';
        calendarButton.style.color = '#0d6efd';
        calendarButton.style.cursor = 'pointer';
        calendarButton.style.zIndex = '10';
        
        // إضافة الزر بعد حقل التاريخ
        dateInput.parentNode.style.position = 'relative';
        dateInput.parentNode.appendChild(calendarButton);
        
        // منع فتح التقويم الافتراضي عند النقر على الحقل
        dateInput.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
        
        // فتح التقويم المخصص عند النقر على الزر
        calendarButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // إزالة أي تقويم مفتوح سابقاً
            const existingCalendar = document.querySelector('.big-calendar-container');
            if (existingCalendar) {
                existingCalendar.remove();
            }
            
            // إنشاء التقويم المخصص
            createBigCalendar(dateInput);
        });
    });
});

/**
 * إنشاء تقويم مخصص كبير
 * @param {HTMLInputElement} dateInput - حقل التاريخ
 */
function createBigCalendar(dateInput) {
    // الحصول على التاريخ الحالي أو التاريخ المحدد في الحقل
    let currentDate = new Date();
    if (dateInput.value) {
        currentDate = new Date(dateInput.value);
    }
    
    // إنشاء حاوية التقويم
    const calendarContainer = document.createElement('div');
    calendarContainer.className = 'big-calendar-container';
    calendarContainer.style.position = 'absolute';
    calendarContainer.style.top = '100%';
    calendarContainer.style.right = '0';
    calendarContainer.style.width = '400px';
    calendarContainer.style.backgroundColor = '#fff';
    calendarContainer.style.border = '1px solid #ddd';
    calendarContainer.style.borderRadius = '8px';
    calendarContainer.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    calendarContainer.style.zIndex = '1000';
    calendarContainer.style.padding = '15px';
    calendarContainer.style.direction = 'rtl';
    calendarContainer.style.fontFamily = 'Cairo, Arial, sans-serif';
    
    // إنشاء رأس التقويم (الشهر والسنة)
    const calendarHeader = document.createElement('div');
    calendarHeader.className = 'big-calendar-header';
    calendarHeader.style.display = 'flex';
    calendarHeader.style.justifyContent = 'space-between';
    calendarHeader.style.alignItems = 'center';
    calendarHeader.style.marginBottom = '15px';
    
    // أزرار التنقل بين الشهور
    const prevMonthButton = document.createElement('button');
    prevMonthButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
    prevMonthButton.style.background = 'transparent';
    prevMonthButton.style.border = 'none';
    prevMonthButton.style.fontSize = '24px';
    prevMonthButton.style.cursor = 'pointer';
    prevMonthButton.style.color = '#0d6efd';
    
    const nextMonthButton = document.createElement('button');
    nextMonthButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
    nextMonthButton.style.background = 'transparent';
    nextMonthButton.style.border = 'none';
    nextMonthButton.style.fontSize = '24px';
    nextMonthButton.style.cursor = 'pointer';
    nextMonthButton.style.color = '#0d6efd';
    
    // عنوان الشهر والسنة
    const monthYearTitle = document.createElement('h3');
    monthYearTitle.style.margin = '0';
    monthYearTitle.style.fontSize = '22px';
    monthYearTitle.style.fontWeight = 'bold';
    
    // إضافة العناصر إلى رأس التقويم
    calendarHeader.appendChild(prevMonthButton);
    calendarHeader.appendChild(monthYearTitle);
    calendarHeader.appendChild(nextMonthButton);
    
    // إنشاء جدول التقويم
    const calendarTable = document.createElement('table');
    calendarTable.className = 'big-calendar-table';
    calendarTable.style.width = '100%';
    calendarTable.style.borderCollapse = 'collapse';
    calendarTable.style.textAlign = 'center';
    
    // إنشاء صف أيام الأسبوع
    const weekdaysRow = document.createElement('tr');
    weekdaysRow.style.borderBottom = '1px solid #ddd';
    
    // أسماء أيام الأسبوع
    const weekdays = ['ح', 'ن', 'ث', 'ر', 'خ', 'ج', 'س'];
    
    weekdays.forEach(function(day) {
        const th = document.createElement('th');
        th.textContent = day;
        th.style.padding = '10px';
        th.style.fontSize = '18px';
        th.style.fontWeight = 'bold';
        th.style.color = '#0d6efd';
        weekdaysRow.appendChild(th);
    });
    
    calendarTable.appendChild(weekdaysRow);
    
    // إضافة أزرار اليوم والشهر
    const calendarFooter = document.createElement('div');
    calendarFooter.className = 'big-calendar-footer';
    calendarFooter.style.display = 'flex';
    calendarFooter.style.justifyContent = 'space-between';
    calendarFooter.style.marginTop = '15px';
    
    const todayButton = document.createElement('button');
    todayButton.textContent = 'اليوم';
    todayButton.style.padding = '8px 15px';
    todayButton.style.backgroundColor = '#0d6efd';
    todayButton.style.color = '#fff';
    todayButton.style.border = 'none';
    todayButton.style.borderRadius = '4px';
    todayButton.style.cursor = 'pointer';
    todayButton.style.fontSize = '16px';
    
    const clearButton = document.createElement('button');
    clearButton.textContent = 'مسح';
    clearButton.style.padding = '8px 15px';
    clearButton.style.backgroundColor = '#dc3545';
    clearButton.style.color = '#fff';
    clearButton.style.border = 'none';
    clearButton.style.borderRadius = '4px';
    clearButton.style.cursor = 'pointer';
    clearButton.style.fontSize = '16px';
    
    calendarFooter.appendChild(todayButton);
    calendarFooter.appendChild(clearButton);
    
    // إضافة العناصر إلى حاوية التقويم
    calendarContainer.appendChild(calendarHeader);
    calendarContainer.appendChild(calendarTable);
    calendarContainer.appendChild(calendarFooter);
    
    // إضافة التقويم إلى الصفحة
    dateInput.parentNode.style.position = 'relative';
    dateInput.parentNode.appendChild(calendarContainer);
    
    // تحديث عرض التقويم
    updateCalendar(currentDate, monthYearTitle, calendarTable, dateInput);
    
    // إضافة مستمعي الأحداث للأزرار
    prevMonthButton.addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() - 1);
        updateCalendar(currentDate, monthYearTitle, calendarTable, dateInput);
    });
    
    nextMonthButton.addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() + 1);
        updateCalendar(currentDate, monthYearTitle, calendarTable, dateInput);
    });
    
    todayButton.addEventListener('click', function() {
        currentDate = new Date();
        updateCalendar(currentDate, monthYearTitle, calendarTable, dateInput);
        selectDate(currentDate, dateInput);
    });
    
    clearButton.addEventListener('click', function() {
        dateInput.value = '';
        calendarContainer.remove();
    });
    
    // إغلاق التقويم عند النقر خارجه
    document.addEventListener('click', function closeCalendar(e) {
        if (!calendarContainer.contains(e.target) && e.target !== dateInput) {
            calendarContainer.remove();
            document.removeEventListener('click', closeCalendar);
        }
    });
}

/**
 * تحديث عرض التقويم
 * @param {Date} date - التاريخ الحالي
 * @param {HTMLElement} monthYearTitle - عنصر عنوان الشهر والسنة
 * @param {HTMLTableElement} calendarTable - جدول التقويم
 * @param {HTMLInputElement} dateInput - حقل التاريخ
 */
function updateCalendar(date, monthYearTitle, calendarTable, dateInput) {
    // أسماء الشهور بالعربية
    const months = [
        'يناير', 'فبراير', 'مارس', 'إبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ];
    
    // تحديث عنوان الشهر والسنة
    monthYearTitle.textContent = months[date.getMonth()] + ' ' + date.getFullYear();
    
    // إزالة صفوف الأيام السابقة
    while (calendarTable.rows.length > 1) {
        calendarTable.deleteRow(1);
    }
    
    // الحصول على اليوم الأول من الشهر
    const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
    // الحصول على اليوم الأخير من الشهر
    const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
    
    // الحصول على يوم الأسبوع للأول من الشهر (0 = الأحد، 6 = السبت)
    let firstDayOfWeek = firstDay.getDay();
    
    // عدد الأيام في الشهر
    const daysInMonth = lastDay.getDate();
    
    // إنشاء صفوف وخلايا التقويم
    let date1 = 1;
    let date2 = 1;
    
    // الحصول على التاريخ المحدد حالياً في الحقل
    const selectedDate = dateInput.value ? new Date(dateInput.value) : null;
    
    // الحصول على التاريخ الحالي
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // إنشاء صفوف التقويم
    for (let i = 0; i < 6; i++) {
        // إنشاء صف جديد
        const row = document.createElement('tr');
        row.style.height = '50px';
        
        // إنشاء خلايا الصف
        for (let j = 0; j < 7; j++) {
            // إنشاء خلية جديدة
            const cell = document.createElement('td');
            cell.style.padding = '10px';
            cell.style.fontSize = '18px';
            cell.style.cursor = 'pointer';
            cell.style.borderRadius = '50%';
            cell.style.width = '40px';
            cell.style.height = '40px';
            
            // إذا كنا في الصف الأول وقبل اليوم الأول من الشهر
            if (i === 0 && j < firstDayOfWeek) {
                // حساب الأيام من الشهر السابق
                const prevMonthLastDay = new Date(date.getFullYear(), date.getMonth(), 0).getDate();
                const prevMonthDay = prevMonthLastDay - (firstDayOfWeek - j - 1);
                
                cell.textContent = prevMonthDay;
                cell.style.color = '#aaa';
                
                // إضافة مستمع الحدث للنقر على يوم من الشهر السابق
                cell.addEventListener('click', function() {
                    const newDate = new Date(date.getFullYear(), date.getMonth() - 1, prevMonthDay);
                    selectDate(newDate, dateInput);
                });
            }
            // إذا كنا بعد آخر يوم في الشهر
            else if (date1 > daysInMonth) {
                cell.textContent = date2++;
                cell.style.color = '#aaa';
                
                // إضافة مستمع الحدث للنقر على يوم من الشهر التالي
                cell.addEventListener('click', function() {
                    const newDate = new Date(date.getFullYear(), date.getMonth() + 1, cell.textContent);
                    selectDate(newDate, dateInput);
                });
            }
            // أيام الشهر الحالي
            else {
                cell.textContent = date1;
                
                // التحقق مما إذا كان هذا اليوم هو اليوم المحدد
                const currentDate = new Date(date.getFullYear(), date.getMonth(), date1);
                
                if (selectedDate && 
                    currentDate.getDate() === selectedDate.getDate() && 
                    currentDate.getMonth() === selectedDate.getMonth() && 
                    currentDate.getFullYear() === selectedDate.getFullYear()) {
                    cell.style.backgroundColor = '#0d6efd';
                    cell.style.color = '#fff';
                }
                // التحقق مما إذا كان هذا اليوم هو اليوم الحالي
                else if (currentDate.getTime() === today.getTime()) {
                    cell.style.backgroundColor = '#e9ecef';
                    cell.style.fontWeight = 'bold';
                }
                
                // إضافة مستمع الحدث للنقر على يوم
                cell.addEventListener('click', function() {
                    const newDate = new Date(date.getFullYear(), date.getMonth(), parseInt(cell.textContent));
                    selectDate(newDate, dateInput);
                });
                
                // إضافة تأثير التحويم
                cell.addEventListener('mouseover', function() {
                    if (!(selectedDate && 
                        currentDate.getDate() === selectedDate.getDate() && 
                        currentDate.getMonth() === selectedDate.getMonth() && 
                        currentDate.getFullYear() === selectedDate.getFullYear())) {
                        cell.style.backgroundColor = '#f8f9fa';
                    }
                });
                
                cell.addEventListener('mouseout', function() {
                    if (selectedDate && 
                        currentDate.getDate() === selectedDate.getDate() && 
                        currentDate.getMonth() === selectedDate.getMonth() && 
                        currentDate.getFullYear() === selectedDate.getFullYear()) {
                        cell.style.backgroundColor = '#0d6efd';
                    }
                    else if (currentDate.getTime() === today.getTime()) {
                        cell.style.backgroundColor = '#e9ecef';
                    }
                    else {
                        cell.style.backgroundColor = '';
                    }
                });
                
                date1++;
            }
            
            row.appendChild(cell);
        }
        
        // إضافة الصف إلى الجدول
        calendarTable.appendChild(row);
        
        // إذا انتهينا من عرض جميع أيام الشهر، نخرج من الحلقة
        if (date1 > daysInMonth) {
            // إذا كان الصف الأخير فارغاً (كل الخلايا من الشهر التالي)، نحذفه
            if (date2 > 7) {
                calendarTable.deleteRow(calendarTable.rows.length - 1);
            }
            break;
        }
    }
}

/**
 * اختيار تاريخ وتحديثه في حقل الإدخال
 * @param {Date} date - التاريخ المختار
 * @param {HTMLInputElement} dateInput - حقل التاريخ
 */
function selectDate(date, dateInput) {
    // تنسيق التاريخ بتنسيق YYYY-MM-DD
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;
    
    // تحديث قيمة حقل الإدخال
    dateInput.value = formattedDate;
    
    // إغلاق التقويم
    const calendarContainer = document.querySelector('.big-calendar-container');
    if (calendarContainer) {
        calendarContainer.remove();
    }
    
    // إطلاق حدث التغيير لتحديث أي مستمعي أحداث مرتبطين بالحقل
    const event = new Event('change', { bubbles: true });
    dateInput.dispatchEvent(event);
}
