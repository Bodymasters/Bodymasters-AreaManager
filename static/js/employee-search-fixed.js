/**
 * ملف مخصص للبحث المباشر عن الموظف وملء بياناته في نموذج المخالفة
 * نسخة محسنة ومصححة
 */

// تنفيذ الكود عند اكتمال تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    console.log('تم تحميل ملف البحث عن الموظف المحسن');

    // تحديد العناصر في الصفحة
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
    fetchEmployeeBtn.addEventListener('click', function(event) {
        event.preventDefault();
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

        console.log(`إرسال طلب البحث عن الموظف برقم: ${employeeId}`);

        // إرسال الطلب باستخدام طريقة POST بشكل مباشر
        $.ajax({
            url: `/api/employee/search?_=${timestamp}`,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(data) {
                console.log('تم استلام البيانات بنجاح:', data);

                if (!data || typeof data !== 'object') {
                    alert('تم استلام بيانات غير صالحة من الخادم');
                    return;
                }

                // ملء حقول النموذج ببيانات الموظف
                fillFormFields(data);
            },
            error: function(xhr, status, error) {
                console.error(`خطأ في الطلب: ${status}, ${error}`);

                let errorMessage = 'حدث خطأ أثناء جلب بيانات الموظف';

                if (xhr.status === 404) {
                    errorMessage = 'لم يتم العثور على الموظف';
                } else if (xhr.status === 403) {
                    errorMessage = 'ليس لديك صلاحية للوصول إلى بيانات هذا الموظف';
                }

                alert(errorMessage);
            },
            complete: function() {
                // إعادة الزر إلى حالته الطبيعية
                fetchEmployeeBtn.disabled = false;
                fetchEmployeeBtn.innerHTML = '<i class="fas fa-search"></i>';
            }
        });
    }

    // دالة مساعدة لإعادة تعيين حقول النموذج
    function clearFormFields() {
        // إعادة تعيين الحقول المرئية
        employeeNameInput.value = '';
        employeeRoleInput.value = '';
        clubNameInput.value = '';
        violationNumberInput.value = '';

        // إعادة تعيين الحقول المخفية
        if (employeeIdHidden) employeeIdHidden.value = '';
        if (employeeNameHidden) employeeNameHidden.value = '';
        if (employeeRoleHidden) employeeRoleHidden.value = '';
        if (clubNameHidden) clubNameHidden.value = '';
        if (violationNumberHidden) violationNumberHidden.value = '';

        // إعادة تعيين خلفية الحقول
        employeeNameInput.style.backgroundColor = '';
        employeeRoleInput.style.backgroundColor = '';
        clubNameInput.style.backgroundColor = '';
        violationNumberInput.style.backgroundColor = '';
    }

    // دالة مساعدة لملء حقول النموذج
    function fillFormFields(data) {
        try {
            console.log('ملء حقول النموذج ببيانات الموظف');

            // ملء الحقول المرئية مع تأثير مرئي
            if (data.name) {
                employeeNameInput.value = data.name;
                highlightField(employeeNameInput);
            }

            if (data.role) {
                employeeRoleInput.value = data.role;
                highlightField(employeeRoleInput);
            }

            if (data.club_name) {
                clubNameInput.value = data.club_name;
                highlightField(clubNameInput);
            }

            if (data.violations_count !== undefined) {
                const violationNumber = data.violations_count + 1;
                violationNumberInput.value = violationNumber;
                highlightField(violationNumberInput);
            }

            // ملء الحقول المخفية
            if (employeeIdHidden) {
                employeeIdHidden.value = employeeIdInput.value.trim();
            }

            if (employeeNameHidden && data.name) {
                employeeNameHidden.value = data.name;
            }

            if (employeeRoleHidden && data.role) {
                employeeRoleHidden.value = data.role;
            }

            if (clubNameHidden && data.club_name) {
                clubNameHidden.value = data.club_name;
            }

            if (violationNumberHidden && data.violations_count !== undefined) {
                violationNumberHidden.value = data.violations_count + 1;
            }

            // طباعة قيم الحقول بعد ملئها للتأكد
            console.log('قيم الحقول الفعلية بعد الملء:');
            console.log(`اسم الموظف: "${employeeNameInput.value}"`);
            console.log(`دور الموظف: "${employeeRoleInput.value}"`);
            console.log(`اسم النادي: "${clubNameInput.value}"`);
            console.log(`رقم المخالفة: "${violationNumberInput.value}"`);
        } catch (error) {
            console.error(`خطأ أثناء ملء حقول النموذج: ${error.message}`);
            alert(`حدث خطأ أثناء ملء بيانات الموظف: ${error.message}`);
        }
    }

    // دالة مساعدة لإضافة تأثير مرئي للحقل
    function highlightField(field) {
        field.style.backgroundColor = '#d1e7dd';
        setTimeout(() => {
            field.style.backgroundColor = '';
        }, 2000);
    }
});
