/**
 * كود JavaScript لتثبيت شريط التنقل بشكل نهائي
 */
(function() {
    // تنفيذ الكود عند تحميل الصفحة
    document.addEventListener('DOMContentLoaded', function() {
        // تثبيت شريط التنقل
        fixNavbar();
        
        // تثبيت شريط التنقل عند التمرير
        window.addEventListener('scroll', fixNavbar);
        
        // تثبيت شريط التنقل عند تغيير حجم النافذة
        window.addEventListener('resize', fixNavbar);
    });
    
    // دالة لتثبيت شريط التنقل
    function fixNavbar() {
        // الحصول على شريط التنقل
        var navbar = document.querySelector('.navbar.fixed-top');
        
        // التأكد من وجود شريط التنقل
        if (navbar) {
            // تثبيت شريط التنقل
            navbar.style.position = 'fixed';
            navbar.style.top = '0';
            navbar.style.left = '0';
            navbar.style.right = '0';
            navbar.style.width = '100%';
            navbar.style.zIndex = '1030';
            navbar.style.transform = 'none';
            navbar.style.transition = 'none';
            navbar.style.animation = 'none';
            navbar.style.willChange = 'auto';
            
            // إضافة padding للجسم لمنع تداخل المحتوى مع شريط التنقل
            document.body.style.paddingTop = '55px';
            
            // إضافة هامش للمحتوى الرئيسي
            var mainContainer = document.querySelector('main.container-fluid');
            if (mainContainer) {
                mainContainer.style.marginTop = '10px';
            }
        }
    }
})();
