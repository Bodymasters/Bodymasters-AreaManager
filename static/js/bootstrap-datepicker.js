// تهيئة منتقي التاريخ باستخدام Bootstrap Datepicker
$(document).ready(function() {
    console.log('Initializing Bootstrap Datepicker...');
    
    // إضافة Font Awesome إذا لم يكن موجوداً
    if (!$('link[href*="font-awesome"]').length) {
        $('head').append('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">');
    }
    
    // تهيئة جميع حقول التاريخ
    $('.datepicker-input').each(function() {
        var $input = $(this);
        console.log('Initializing datepicker for:', $input.attr('id'));
        
        // تهيئة منتقي التاريخ
        $input.datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true,
            language: 'ar',
            rtl: true,
            orientation: "auto",
            templates: {
                leftArrow: '<i class="fas fa-chevron-right"></i>',
                rightArrow: '<i class="fas fa-chevron-left"></i>'
            }
        });
        
        // إضافة أيقونة التقويم
        var $container = $input.parent();
        $container.addClass('date-input-container');
        
        if (!$container.find('.date-input-icon').length) {
            $container.append('<i class="fas fa-calendar-alt date-input-icon"></i>');
            
            // فتح التقويم عند النقر على الأيقونة
            $container.find('.date-input-icon').on('click', function() {
                $input.datepicker('show');
            });
        }
        
        // فتح التقويم عند النقر على الحقل
        $input.on('click', function() {
            $(this).datepicker('show');
        });
        
        console.log('Datepicker initialized for:', $input.attr('id'));
    });
    
    // تعديل الأرقام لتكون بالإنجليزية
    $.fn.datepicker.dates['ar'] = {
        days: ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"],
        daysShort: ["أحد", "إثن", "ثلا", "أرب", "خمي", "جمع", "سبت"],
        daysMin: ["ح", "ن", "ث", "ر", "خ", "ج", "س"],
        months: ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
        monthsShort: ["ينا", "فبر", "مار", "أبر", "ماي", "يون", "يول", "أغس", "سبت", "أكت", "نوف", "ديس"],
        today: "اليوم",
        clear: "مسح",
        format: "yyyy-mm-dd",
        titleFormat: "MM yyyy",
        weekStart: 6
    };
});
