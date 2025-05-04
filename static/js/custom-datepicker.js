// تهيئة منتقي التاريخ المخصص باستخدام Flatpickr
window.addEventListener('load', function() {
    // استخدام ملف اللغة العربية المضمن
    console.log('Checking for flatpickr.l10ns.ar:', typeof flatpickr.l10ns !== 'undefined' && typeof flatpickr.l10ns.ar !== 'undefined');

    // تعديل إعدادات اللغة العربية
    const arabicConfig = {
        // استخدام اللغة العربية المضمنة
        ...flatpickr.l10ns.ar,

        // تعديل بعض الإعدادات
        firstDayOfWeek: 6, // السبت هو أول يوم في الأسبوع

        // التأكد من أن الأرقام باللغة الإنجليزية
        ordinal: (nth) => {
            return nth;
        }
    };

    // التأكد من أن الأرقام باللغة الإنجليزية
    if (arabicConfig.hasOwnProperty('numeral')) {
        delete arabicConfig.numeral;
    }

    // تهيئة جميع حقول التاريخ
    try {
        console.log('Initializing datepickers...');
        const dateInputs = document.querySelectorAll('.custom-datepicker');
        console.log('Found datepickers:', dateInputs.length);

        if (dateInputs.length > 0) {
            // إضافة Font Awesome إذا لم يكن موجودًا
            if (!document.querySelector('link[href*="font-awesome"]')) {
                const fontAwesomeLink = document.createElement('link');
                fontAwesomeLink.rel = 'stylesheet';
                fontAwesomeLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
                document.head.appendChild(fontAwesomeLink);
            }

            dateInputs.forEach(input => {
                console.log('Initializing datepicker for:', input.id);
                // الحصول على القيمة الحالية للحقل
                const currentValue = input.value;

                // إنشاء منتقي التاريخ
                const datepicker = flatpickr(input, {
                    dateFormat: "Y-m-d",
                    locale: arabicConfig,
                    disableMobile: true,
                    allowInput: true,
                    clickOpens: true,
                    position: "auto",
                    static: false,
                    monthSelectorType: "dropdown",
                    nextArrow: '<i class="fas fa-chevron-right"></i>',
                    prevArrow: '<i class="fas fa-chevron-left"></i>',
                    defaultDate: currentValue || null,
                    onChange: function(selectedDates, dateStr) {
                        input.value = dateStr;
                        const event = new Event('change', { bubbles: true });
                        input.dispatchEvent(event);
                    },
                    // التأكد من أن الأرقام باللغة الإنجليزية
                    formatDate: function(date, format, locale) {
                        // استخدام الدالة الافتراضية لتنسيق التاريخ
                        const formattedDate = flatpickr.formatDate(date, format);
                        // التأكد من أن الأرقام باللغة الإنجليزية
                        return formattedDate;
                    }
                });

                // إضافة أيقونة التقويم
                const container = input.parentElement;
                if (container) {
                    container.classList.add('date-input-container');

                    // إضافة أيقونة فقط إذا لم تكن موجودة بالفعل
                    if (!container.querySelector('.date-input-icon')) {
                        const icon = document.createElement('i');
                        icon.className = 'fas fa-calendar-alt date-input-icon';
                        container.appendChild(icon);

                        // فتح التقويم عند النقر على الأيقونة
                        icon.addEventListener('click', function() {
                            datepicker.open();
                        });
                    }
                }

                // فتح التقويم عند النقر على الحقل
                input.addEventListener('click', function() {
                    datepicker.open();
                });

                console.log('Datepicker initialized for:', input.id);
            });
        }
    } catch (error) {
        console.error('Error initializing datepickers:', error);
    }
});
