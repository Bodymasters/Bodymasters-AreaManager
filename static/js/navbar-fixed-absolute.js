/**
 * تثبيت شريط التنقل بشكل مطلق ونهائي
 */
(function() {
    // تنفيذ الكود فورًا
    fixNavbarAbsolutely();
    
    // تنفيذ الكود عند تحميل الصفحة
    document.addEventListener('DOMContentLoaded', function() {
        fixNavbarAbsolutely();
        setTimeout(fixNavbarAbsolutely, 100);
        setTimeout(fixNavbarAbsolutely, 500);
        setTimeout(fixNavbarAbsolutely, 1000);
    });
    
    // تنفيذ الكود عند تحميل الصفحة بالكامل
    window.addEventListener('load', function() {
        fixNavbarAbsolutely();
        setTimeout(fixNavbarAbsolutely, 100);
        setTimeout(fixNavbarAbsolutely, 500);
        setTimeout(fixNavbarAbsolutely, 1000);
    });
    
    // تنفيذ الكود عند التمرير
    window.addEventListener('scroll', function() {
        fixNavbarAbsolutely();
    });
    
    // تنفيذ الكود عند تغيير حجم النافذة
    window.addEventListener('resize', function() {
        fixNavbarAbsolutely();
    });
    
    // دالة لتثبيت شريط التنقل بشكل مطلق
    function fixNavbarAbsolutely() {
        // الحصول على شريط التنقل
        var navbar = document.querySelector('.navbar.fixed-top');
        
        // التأكد من وجود شريط التنقل
        if (navbar) {
            // تثبيت شريط التنقل بشكل مطلق
            navbar.style.cssText = 'position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important; width: 100% !important; z-index: 1030 !important; margin: 0 !important; padding: 0 !important; height: 45px !important; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2) !important; transform: none !important; transition: none !important; animation: none !important; will-change: auto !important;';
            
            // إضافة padding للجسم لمنع تداخل المحتوى مع شريط التنقل
            document.body.style.cssText = 'padding-top: 70px !important; margin: 0 !important; overflow-x: hidden !important;';
            
            // إضافة هامش للمحتوى الرئيسي
            var mainContainer = document.querySelector('main.container-fluid');
            if (mainContainer) {
                mainContainer.style.cssText = 'margin-top: 20px !important; padding-top: 20px !important;';
            }
            
            // إضافة هامش للعناصر التي قد تتداخل مع شريط التنقل
            var elements = document.querySelectorAll('.btn-toolbar, .card, .page-header, h1, h2, h3, .row:first-child');
            for (var i = 0; i < elements.length; i++) {
                elements[i].style.cssText = 'margin-top: 15px !important;';
            }
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.onscroll = null;
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.scrollFunction = null;
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.scrollTo = function() {};
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.scrollBy = function() {};
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.scroll = function() {};
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.scrollIntoView = function() {};
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.scrollIntoViewIfNeeded = function() {};
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.scrollByLines = function() {};
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.scrollByPages = function() {};
        }
    }
})();
