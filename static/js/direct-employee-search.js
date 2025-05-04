/**
 * ملف مخصص للبحث المباشر عن الموظف وملء بياناته في نموذج المخالفة
 * هذا الملف يستخدم طريقة مباشرة للبحث عن الموظف وعرض البيانات
 */

// تنفيذ الكود عند اكتمال تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    console.log('تم تحميل ملف البحث المباشر عن الموظف');

    // تحديد العناصر في الصفحة
    const employeeIdInput = document.getElementById('employee_id');
    const fetchEmployeeBtn = document.getElementById('fetch-employee-btn');
    const employeeNameInput = document.getElementById('employee_name');
    const employeeRoleInput = document.getElementById('employee_role');
    const clubNameInput = document.getElementById('club_name');
    const violationNumberInput = document.getElementById('violation_number');

    // التأكد من وجود العناصر المطلوبة
    if (!employeeIdInput || !fetchEmployeeBtn) {
        console.error('عناصر البحث عن الموظف غير موجودة في الصفحة');
        return;
    }

    if (!employeeNameInput || !employeeRoleInput || !clubNameInput || !violationNumberInput) {
        console.error('حقول بيانات الموظف غير موجودة في الصفحة');
        return;
    }

    console.log('تم العثور على جميع عناصر النموذج');

    // إضافة مستمع الحدث للنقر على زر البحث
    fetchEmployeeBtn.addEventListener('click', function() {
        console.log('تم النقر على زر البحث عن الموظف');
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

        // إعادة تعيين حقول النموذج
        clearFormFields();

        // إنشاء كائن FormData
        const formData = new FormData();
        formData.append('employee_id', employeeId);

        // إضافة طابع زمني لمنع التخزين المؤقت
        const timestamp = new Date().getTime();

        // إرسال الطلب باستخدام طريقة POST
        fetch(`/api/employee/direct-search?_=${timestamp}`, {
            method: 'POST',
            body: formData,
            cache: 'no-store'
        })
        .then(response => {
            console.log(`حالة الاستجابة: ${response.status}`);

            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'حدث خطأ أثناء جلب بيانات الموظف');
                });
            }

            return response.json();
        })
        .then(data => {
            console.log('البيانات المستلمة:', data);

            // ملء حقول النموذج ببيانات الموظف
            fillFormFields(data);
        })
        .catch(error => {
            console.error(`خطأ: ${error.message}`);
            alert(error.message);
        })
        .finally(() => {
            // إعادة الزر إلى حالته الطبيعية
            fetchEmployeeBtn.disabled = false;
            fetchEmployeeBtn.innerHTML = '<i class="fas fa-search"></i>';
        });
    }

    // دالة مساعدة لإعادة تعيين حقول النموذج
    function clearFormFields() {
        employeeNameInput.value = '';
        employeeRoleInput.value = '';
        clubNameInput.value = '';
        violationNumberInput.value = '';

        // إعادة تعيين الحقول المخفية أيضاً
        if (document.getElementById('employee_id_hidden')) {
            document.getElementById('employee_id_hidden').value = '';
        }
        if (document.getElementById('employee_name_hidden')) {
            document.getElementById('employee_name_hidden').value = '';
        }
        if (document.getElementById('employee_role_hidden')) {
            document.getElementById('employee_role_hidden').value = '';
        }
        if (document.getElementById('club_name_hidden')) {
            document.getElementById('club_name_hidden').value = '';
        }
        if (document.getElementById('violation_number_hidden')) {
            document.getElementById('violation_number_hidden').value = '';
        }
    }

    // دالة مساعدة لملء حقول النموذج
    function fillFormFields(data) {
        try {
            console.log('ملء حقول النموذج ببيانات الموظف');

            // ملء الحقول المرئية
            if (data.name) {
                employeeNameInput.value = data.name;
                console.log(`تم تعيين اسم الموظف إلى: ${data.name}`);

                // إضافة تأثير مرئي لتأكيد تغيير القيمة
                employeeNameInput.style.backgroundColor = '#d1e7dd';
                setTimeout(() => {
                    employeeNameInput.style.backgroundColor = '';
                }, 2000);
            }

            if (data.role) {
                employeeRoleInput.value = data.role;
                console.log(`تم تعيين دور الموظف إلى: ${data.role}`);

                // إضافة تأثير مرئي لتأكيد تغيير القيمة
                employeeRoleInput.style.backgroundColor = '#d1e7dd';
                setTimeout(() => {
                    employeeRoleInput.style.backgroundColor = '';
                }, 2000);
            }

            if (data.club_name) {
                clubNameInput.value = data.club_name;
                console.log(`تم تعيين اسم النادي إلى: ${data.club_name}`);

                // إضافة تأثير مرئي لتأكيد تغيير القيمة
                clubNameInput.style.backgroundColor = '#d1e7dd';
                setTimeout(() => {
                    clubNameInput.style.backgroundColor = '';
                }, 2000);
            }

            if (data.violations_count !== undefined) {
                const violationNumber = data.violations_count + 1;
                violationNumberInput.value = violationNumber;
                console.log(`تم تعيين رقم المخالفة إلى: ${violationNumber}`);

                // إضافة تأثير مرئي لتأكيد تغيير القيمة
                violationNumberInput.style.backgroundColor = '#d1e7dd';
                setTimeout(() => {
                    violationNumberInput.style.backgroundColor = '';
                }, 2000);
            }

            // ملء الحقول المخفية
            if (document.getElementById('employee_id_hidden')) {
                document.getElementById('employee_id_hidden').value = employeeIdInput.value.trim();
            }

            if (document.getElementById('employee_name_hidden')) {
                document.getElementById('employee_name_hidden').value = data.name || '';
            }

            if (document.getElementById('employee_role_hidden')) {
                document.getElementById('employee_role_hidden').value = data.role || '';
            }

            if (document.getElementById('club_name_hidden')) {
                document.getElementById('club_name_hidden').value = data.club_name || '';
            }

            if (document.getElementById('violation_number_hidden')) {
                document.getElementById('violation_number_hidden').value =
                    (data.violations_count !== undefined) ? (data.violations_count + 1) : '';
            }

            // طباعة قيم الحقول بعد ملئها للتأكد
            console.log('قيم الحقول الفعلية بعد الملء:');
            console.log(`اسم الموظف: "${employeeNameInput.value}"`);
            console.log(`دور الموظف: "${employeeRoleInput.value}"`);
            console.log(`اسم النادي: "${clubNameInput.value}"`);
            console.log(`رقم المخالفة: "${violationNumberInput.value}"`);
        } catch (error) {
            console.error(`خطأ أثناء ملء حقول النموذج: ${error.message}`);
        }
    }
});
