/**
 * حل نهائي لتثبيت شريط التنقل ومنع تداخله مع المحتوى
 */
(function() {
    // تنفيذ الكود فورًا
    fixNavbarImmediately();
    
    // تنفيذ الكود عند تحميل الصفحة
    window.addEventListener('DOMContentLoaded', function() {
        fixNavbarImmediately();
        setTimeout(fixNavbarImmediately, 100);
        setTimeout(fixNavbarImmediately, 500);
        setTimeout(fixNavbarImmediately, 1000);
    });
    
    // تثبيت شريط التنقل عند التمرير
    window.addEventListener('scroll', function() {
        fixNavbarImmediately();
    });
    
    // تثبيت شريط التنقل عند تغيير حجم النافذة
    window.addEventListener('resize', function() {
        fixNavbarImmediately();
    });
    
    // تثبيت شريط التنقل عند تحميل الصفحة بالكامل
    window.addEventListener('load', function() {
        fixNavbarImmediately();
        setTimeout(fixNavbarImmediately, 100);
        setTimeout(fixNavbarImmediately, 500);
        setTimeout(fixNavbarImmediately, 1000);
    });
    
    // دالة لتثبيت شريط التنقل فورًا
    function fixNavbarImmediately() {
        // تثبيت شريط التنقل
        var navbar = document.querySelector('.navbar.fixed-top');
        if (navbar) {
            // تطبيق الأنماط مباشرة على شريط التنقل
            Object.assign(navbar.style, {
                position: 'fixed',
                top: '0',
                left: '0',
                right: '0',
                width: '100%',
                zIndex: '1030',
                margin: '0',
                padding: '0',
                transform: 'none',
                transition: 'none',
                animation: 'none',
                willChange: 'auto'
            });
            
            // تطبيق الأنماط على الجسم
            Object.assign(document.body.style, {
                paddingTop: '70px',
                margin: '0'
            });
            
            // تطبيق الأنماط على المحتوى الرئيسي
            var mainContainer = document.querySelector('main.container-fluid');
            if (mainContainer) {
                Object.assign(mainContainer.style, {
                    marginTop: '20px',
                    paddingTop: '20px'
                });
            }
            
            // تطبيق الأنماط على العناصر التي قد تتداخل مع شريط التنقل
            var elements = document.querySelectorAll('.btn-toolbar, .card, .page-header, h1, h2, h3, .row:first-child');
            elements.forEach(function(element) {
                element.style.marginTop = '15px';
            });
            
            // تعطيل أي تأثيرات حركة على شريط التنقل
            window.removeEventListener('scroll', window.scrollFunction);
        }
    }
})();
