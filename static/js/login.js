// وظيفة إظهار/إخفاء كلمة المرور
window.onload = function() {
    console.log("تم تحميل صفحة تسجيل الدخول");

    // الحصول على العناصر
    var passwordInput = document.getElementById('password');
    var toggleIcon = document.getElementById('togglePassword');
    var toggleButton = document.getElementById('togglePasswordBtn');

    console.log("حقل كلمة المرور:", passwordInput);
    console.log("أيقونة التبديل:", toggleIcon);
    console.log("زر التبديل:", toggleButton);

    // إضافة مستمع حدث للزر
    if (toggleButton && passwordInput && toggleIcon) {
        toggleButton.onclick = function(e) {
            e.preventDefault();
            console.log("تم النقر على زر إظهار/إخفاء كلمة المرور");

            // تبديل نوع حقل كلمة المرور
            if (passwordInput.type === 'password') {
                console.log("تغيير النوع من password إلى text");
                passwordInput.type = 'text';
                toggleIcon.className = 'fas fa-eye-slash fa-lg';
            } else {
                console.log("تغيير النوع من text إلى password");
                passwordInput.type = 'password';
                toggleIcon.className = 'fas fa-eye fa-lg';
            }

            return false;
        };
    }
};
