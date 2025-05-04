/**
 * محسن أداء التطبيق
 * يقوم بتحسين سرعة تحميل الصفحات وتقليل وقت الاستجابة
 */

// تنفيذ الكود بعد تحميل المستند
document.addEventListener('DOMContentLoaded', function() {
    console.log('تحسين الأداء قيد التنفيذ...');

    // تأخير تحميل الصور غير المرئية
    lazyLoadImages();

    // تأخير تحميل JavaScript غير الضروري
    deferNonCriticalJS();

    // تحسين استجابة النماذج
    optimizeForms();

    // تحسين التنقل بين الصفحات
    optimizeNavigation();

    console.log('تم تطبيق تحسينات الأداء');
});

/**
 * تأخير تحميل الصور غير المرئية في الصفحة
 */
function lazyLoadImages() {
    // التحقق من دعم IntersectionObserver
    if ('IntersectionObserver' in window) {
        // تحديد جميع الصور التي تحتاج إلى تحميل متأخر
        const lazyImages = document.querySelectorAll('img[data-src]');

        // إنشاء مراقب التقاطع
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                // إذا كانت الصورة مرئية
                if (entry.isIntersecting) {
                    const image = entry.target;
                    // تحميل الصورة الفعلية
                    image.src = image.dataset.src;
                    // إزالة السمة data-src
                    image.removeAttribute('data-src');
                    // إيقاف مراقبة الصورة
                    observer.unobserve(image);
                }
            });
        });

        // تطبيق المراقب على كل صورة
        lazyImages.forEach(function(image) {
            imageObserver.observe(image);
        });
    } else {
        // التحميل المتأخر البسيط للمتصفحات القديمة
        setTimeout(function() {
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(function(image) {
                image.src = image.dataset.src;
                image.removeAttribute('data-src');
            });
        }, 500);
    }
}

/**
 * تأخير تحميل JavaScript غير الضروري
 */
function deferNonCriticalJS() {
    // تحديد النصوص البرمجية غير الضرورية للتحميل الفوري
    const nonCriticalScripts = document.querySelectorAll('script[data-defer]');

    // تأخير تحميل النصوص البرمجية
    nonCriticalScripts.forEach(function(script) {
        const src = script.getAttribute('src');
        if (src) {
            // إزالة النص البرمجي الأصلي
            script.remove();

            // إنشاء نص برمجي جديد مع تأخير التحميل
            setTimeout(function() {
                const newScript = document.createElement('script');
                newScript.src = src;
                document.body.appendChild(newScript);
            }, 1000);
        }
    });
}

/**
 * تحسين استجابة النماذج
 */
function optimizeForms() {
    // تحسين أداء النماذج الكبيرة
    const forms = document.querySelectorAll('form');

    forms.forEach(function(form) {
        // لا نقوم بتعطيل التحقق التلقائي للمتصفح
        // form.setAttribute('novalidate', 'true');

        // لا نضيف مستمع للتحقق اليدوي لتجنب تعارض مع وظائف النماذج الأصلية
        // نضيف فقط الفئة للتنسيق
        if (!form.classList.contains('no-validation')) {
            form.classList.add('needs-validation');
        }
    });
}

/**
 * تحسين التنقل بين الصفحات
 */
function optimizeNavigation() {
    // تحسين روابط التنقل
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(function(link) {
        // إضافة مؤشر تحميل عند النقر على الرابط
        link.addEventListener('click', function(event) {
            // التحقق من أن الرابط ليس dropdown toggle
            if (!link.classList.contains('dropdown-toggle')) {
                // إظهار مؤشر التحميل
                showLoadingIndicator();
            }
        });
    });

    // تحسين أزرار الإرسال في النماذج
    const submitButtons = document.querySelectorAll('button[type="submit"]');

    submitButtons.forEach(function(button) {
        // نحفظ النص الأصلي للزر في سمة مخصصة
        if (!button.hasAttribute('data-original-text')) {
            button.setAttribute('data-original-text', button.innerHTML);
        }

        // نضيف مستمع للنموذج بدلاً من الزر
        const form = button.closest('form');
        if (form && !form.classList.contains('no-submit-handler')) {
            form.addEventListener('submit', function() {
                // نستخدم النص المحفوظ
                const originalText = button.getAttribute('data-original-text');

                // تغيير نص الزر إلى مؤشر تحميل
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري المعالجة...';
                // لا نقوم بتعطيل الزر لتجنب مشاكل الإرسال
                // button.disabled = true;
            });
        }
    });
}

/**
 * إظهار مؤشر تحميل عند الانتقال بين الصفحات
 */
function showLoadingIndicator() {
    // التحقق من وجود مؤشر تحميل
    if (!document.getElementById('page-loading-indicator')) {
        // إنشاء مؤشر تحميل
        const indicator = document.createElement('div');
        indicator.id = 'page-loading-indicator';
        indicator.innerHTML = '<div class="spinner"></div>';
        indicator.style.position = 'fixed';
        indicator.style.top = '0';
        indicator.style.left = '0';
        indicator.style.width = '100%';
        indicator.style.height = '3px';
        indicator.style.backgroundColor = 'transparent';
        indicator.style.zIndex = '9999';

        // إنشاء شريط التقدم
        const spinner = indicator.querySelector('.spinner');
        spinner.style.height = '100%';
        spinner.style.width = '0';
        spinner.style.backgroundColor = '#2563eb';
        spinner.style.transition = 'width 0.3s ease-in-out';

        // إضافة مؤشر التحميل إلى المستند
        document.body.appendChild(indicator);

        // تحريك شريط التقدم
        setTimeout(function() {
            spinner.style.width = '30%';

            setTimeout(function() {
                spinner.style.width = '60%';

                setTimeout(function() {
                    spinner.style.width = '80%';
                }, 500);
            }, 300);
        }, 100);
    }
}

// تطبيق تحسينات CSS
function applyCSSOptimizations() {
    // تقليل عدد إعادة الرسم وإعادة التخطيط
    document.body.style.willChange = 'transform';

    // تحسين تحميل الخطوط
    if ('fonts' in document) {
        // تحميل الخطوط مسبقًا
        document.fonts.ready.then(function() {
            document.body.classList.add('fonts-loaded');
        });
    }
}

// تنفيذ تحسينات CSS
applyCSSOptimizations();
