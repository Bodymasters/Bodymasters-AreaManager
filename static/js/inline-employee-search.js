/**
 * ملف البحث المباشر عن الموظف - حل جذري نهائي محسن
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('تم تحميل ملف البحث المباشر عن الموظف - الحل النهائي المحسن');

    // تحديد العناصر
    const employeeIdInput = document.getElementById('employee_id');
    const fetchEmployeeBtn = document.getElementById('fetch-employee-btn');
    const employeeNameInput = document.getElementById('employee_name');
    const employeeRoleInput = document.getElementById('employee_role');
    const clubNameInput = document.getElementById('club_name');
    const violationNumberInput = document.getElementById('violation_number');

    // الحقول المخفية
    const employeeIdHidden = document.getElementById('employee_id_hidden');
    const employeeNameHidden = document.getElementById('employee_name_hidden');
    const employeeRoleHidden = document.getElementById('employee_role_hidden');
    const clubNameHidden = document.getElementById('club_name_hidden');
    const violationNumberHidden = document.getElementById('violation_number_hidden');

    // التحقق من وجود العناصر الأساسية
    if (!employeeIdInput || !fetchEmployeeBtn) {
        console.error('عناصر النموذج الأساسية غير موجودة');
        return;
    }

    console.log('تم العثور على عناصر النموذج الأساسية');

    // إضافة مستمع الحدث للنقر على زر البحث
    fetchEmployeeBtn.addEventListener('click', function(event) {
        event.preventDefault();
        console.log('تم النقر على زر البحث');
        searchEmployee();
    });

    // إضافة مستمع الحدث للضغط على Enter في حقل الرقم الوظيفي
    employeeIdInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            console.log('تم الضغط على Enter في حقل الرقم الوظيفي');
            searchEmployee();
        }
    });

    // دالة البحث عن الموظف
    function searchEmployee() {
        // الحصول على الرقم الوظيفي
        const employeeId = employeeIdInput.value.trim();

        // التحقق من وجود رقم وظيفي
        if (!employeeId) {
            alert('الرجاء إدخال الرقم الوظيفي');
            return;
        }

        console.log(`البحث عن الموظف برقم: ${employeeId}`);

        // تغيير شكل الزر لإظهار حالة التحميل
        fetchEmployeeBtn.disabled = true;
        fetchEmployeeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        // مسح حقول النموذج
        clearFormFields();

        // طباعة معلومات تشخيصية
        console.log('بدء عملية البحث عن الموظف...');
        console.log('الرقم الوظيفي المدخل:', employeeId);

        // استخدام طريقة POST بدلاً من GET
        const formData = new FormData();
        formData.append('employee_id', employeeId);

        // استخدام مسار API مختلف
        fetch('/api/employee/find', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log(`استجابة الخادم: ${response.status}`);

            if (response.status === 200) {
                return response.json();
            } else if (response.status === 404) {
                throw new Error('لم يتم العثور على الموظف');
            } else if (response.status === 403) {
                throw new Error('ليس لديك صلاحية للوصول إلى بيانات هذا الموظف');
            } else {
                throw new Error('حدث خطأ أثناء جلب بيانات الموظف');
            }
        })
        .then(data => {
            console.log('البيانات المستلمة:', data);

            // ملء حقول النموذج ببيانات الموظف
            fillFormFields(data, employeeId);

            // إظهار رسالة نجاح
            alert(`تم العثور على الموظف: ${data.name}`);

            // إعادة الزر إلى حالته الطبيعية
            resetButton();
        })
        .catch(error => {
            console.error('خطأ:', error);
            alert(error.message || 'حدث خطأ أثناء جلب بيانات الموظف');

            // إعادة الزر إلى حالته الطبيعية
            resetButton();
        });
    }

    // دالة مسح حقول النموذج
    function clearFormFields() {
        // مسح الحقول المرئية إذا كانت موجودة
        if (employeeNameInput) employeeNameInput.value = '';
        if (employeeRoleInput) employeeRoleInput.value = '';
        if (clubNameInput) clubNameInput.value = '';
        if (violationNumberInput) violationNumberInput.value = '';

        // مسح الحقول المخفية
        if (employeeIdHidden) employeeIdHidden.value = '';
        if (employeeNameHidden) employeeNameHidden.value = '';
        if (employeeRoleHidden) employeeRoleHidden.value = '';
        if (clubNameHidden) clubNameHidden.value = '';
        if (violationNumberHidden) violationNumberHidden.value = '';
    }

    // دالة ملء حقول النموذج ببيانات الموظف
    function fillFormFields(data, employeeId) {
        // ملء الحقول المرئية إذا كانت موجودة
        if (employeeNameInput) employeeNameInput.value = data.name || '';
        if (employeeRoleInput) employeeRoleInput.value = data.role || '';
        if (clubNameInput) clubNameInput.value = data.club_name || '';
        if (violationNumberInput) violationNumberInput.value = (data.violations_count + 1) || 1;

        // ملء الحقول المخفية
        if (employeeIdHidden) employeeIdHidden.value = employeeId;
        if (employeeNameHidden) employeeNameHidden.value = data.name || '';
        if (employeeRoleHidden) employeeRoleHidden.value = data.role || '';
        if (clubNameHidden) clubNameHidden.value = data.club_name || '';
        if (violationNumberHidden) violationNumberHidden.value = (data.violations_count + 1) || 1;

        // تمكين زر الحفظ
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
        }

        console.log('تم ملء حقول النموذج بنجاح:', {
            name: data.name,
            role: data.role,
            club_name: data.club_name,
            violations_count: data.violations_count
        });
    }

    // دالة إعادة الزر إلى حالته الطبيعية
    function resetButton() {
        fetchEmployeeBtn.disabled = false;
        fetchEmployeeBtn.innerHTML = '<i class="fas fa-search"></i>';
    }

    // تنفيذ البحث عند تحميل الصفحة إذا كان هناك رقم وظيفي
    if (employeeIdInput.value.trim()) {
        console.log('تنفيذ البحث تلقائياً عند تحميل الصفحة');
        searchEmployee();
    }

    // إذا كانت الصفحة تحتوي على بيانات موظف مسبقة (في حالة التعديل أو الإضافة من صفحة الموظف)
    if (typeof employee !== 'undefined' && employee) {
        console.log('تم العثور على بيانات موظف مسبقة:', employee);

        // ملء حقل الرقم الوظيفي
        if (employeeIdInput && employee.employee_id) {
            employeeIdInput.value = employee.employee_id;
        }

        // ملء الحقول المرئية
        if (employeeNameInput && employee.name) employeeNameInput.value = employee.name;
        if (employeeRoleInput && employee.role) employeeRoleInput.value = employee.role;
        if (clubNameInput && employee.club && employee.club.name) clubNameInput.value = employee.club.name;
        if (violationNumberInput && typeof violations_count !== 'undefined') {
            violationNumberInput.value = violations_count + 1;
        }

        // ملء الحقول المخفية
        if (employeeIdHidden && employee.employee_id) employeeIdHidden.value = employee.employee_id;
        if (employeeNameHidden && employee.name) employeeNameHidden.value = employee.name;
        if (employeeRoleHidden && employee.role) employeeRoleHidden.value = employee.role;
        if (clubNameHidden && employee.club && employee.club.name) clubNameHidden.value = employee.club.name;
        if (violationNumberHidden && typeof violations_count !== 'undefined') {
            violationNumberHidden.value = violations_count + 1;
        }
    }
});
