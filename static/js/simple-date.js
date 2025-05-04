// سكريبت بسيط لتحسين عمل حقول التاريخ
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing date fields...');

    // تحديد جميع حقول التاريخ
    const dateInputs = document.querySelectorAll('input[type="date"]');

    // التأكد من أن حقول التاريخ تعمل بشكل صحيح
    dateInputs.forEach(function(input) {
        console.log('Setting up date field:', input.id);

        // إضافة خاصية lang للتأكد من أن الأرقام بالإنجليزية
        input.setAttribute('lang', 'en');
        input.setAttribute('dir', 'ltr');

        // إضافة خاصية data-date للاحتفاظ بالقيمة الأصلية
        if (input.value) {
            input.setAttribute('data-date', input.value);
        }

        // تعديل placeholder لعرض التنسيق بشكل صحيح
        input.setAttribute('placeholder', 'dd / mm / yyyy');

        // إضافة مستمع للتغيير لتحديث خاصية data-date
        input.addEventListener('change', function(e) {
            console.log('Date changed:', this.value);
            this.setAttribute('data-date', this.value);
        });

        // إضافة مستمع للنقر لفتح منتقي التاريخ
        input.addEventListener('click', function(e) {
            // فتح منتقي التاريخ
            console.log('Date field clicked:', this.id);
            this.showPicker();
        });
    });

    console.log('Date fields initialization complete.');
});
