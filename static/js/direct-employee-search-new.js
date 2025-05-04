/**
 * ملف البحث المباشر عن الموظف - حل جذري
 */
document.addEventListener('DOMContentLoaded', function() {
    // تحديد العناصر
    const employeeIdInput = document.getElementById('employee_id');
    const fetchEmployeeBtn = document.getElementById('fetch-employee-btn');
    const employeeNameInput = document.getElementById('employee_name');
    const employeeRoleInput = document.getElementById('employee_role');
    const clubNameInput = document.getElementById('club_name');
    const violationNumberInput = document.getElementById('violation_number');
    
    // الحقول المخفية
    const employeeIdHidden = document.getElementById('employee_id_hidden');
    
    // إضافة مستمع الحدث للنقر على زر البحث
    if (fetchEmployeeBtn) {
        fetchEmployeeBtn.addEventListener('click', function(event) {
            event.preventDefault();
            searchEmployee();
        });
    }
    
    // إضافة مستمع الحدث للضغط على Enter في حقل الرقم الوظيفي
    if (employeeIdInput) {
        employeeIdInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                searchEmployee();
            }
        });
    }
    
    // دالة البحث عن الموظف
    function searchEmployee() {
        // الحصول على الرقم الوظيفي
        const employeeId = employeeIdInput.value.trim();
        
        // التحقق من وجود رقم وظيفي
        if (!employeeId) {
            alert('الرجاء إدخال الرقم الوظيفي');
            return;
        }
        
        // تغيير شكل الزر لإظهار حالة التحميل
        fetchEmployeeBtn.disabled = true;
        fetchEmployeeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        // إرسال طلب GET مباشر للحصول على بيانات الموظف
        fetch(`/api/employee/${employeeId}`)
            .then(response => {
                console.log(`استجابة الخادم: ${response.status}`);
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('لم يتم العثور على الموظف');
                    } else if (response.status === 403) {
                        throw new Error('ليس لديك صلاحية للوصول إلى بيانات هذا الموظف');
                    } else {
                        throw new Error('حدث خطأ أثناء جلب بيانات الموظف');
                    }
                }
                return response.json();
            })
            .then(data => {
                console.log('البيانات المستلمة:', data);
                
                // ملء حقول النموذج ببيانات الموظف
                employeeNameInput.value = data.name || '';
                employeeRoleInput.value = data.role || '';
                clubNameInput.value = data.club_name || '';
                violationNumberInput.value = (data.violations_count + 1) || 1;
                
                // ملء الحقول المخفية
                if (employeeIdHidden) {
                    employeeIdHidden.value = employeeId;
                }
                
                // تمكين زر الحفظ
                const submitButton = document.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = false;
                }
                
                // إظهار رسالة نجاح
                alert(`تم العثور على الموظف: ${data.name}`);
            })
            .catch(error => {
                console.error('خطأ:', error.message);
                alert(error.message);
                
                // مسح حقول النموذج
                employeeNameInput.value = '';
                employeeRoleInput.value = '';
                clubNameInput.value = '';
                violationNumberInput.value = '';
                
                if (employeeIdHidden) {
                    employeeIdHidden.value = '';
                }
            })
            .finally(() => {
                // إعادة الزر إلى حالته الطبيعية
                fetchEmployeeBtn.disabled = false;
                fetchEmployeeBtn.innerHTML = '<i class="fas fa-search"></i>';
            });
    }
    
    // تنفيذ البحث عند تحميل الصفحة إذا كان هناك رقم وظيفي
    if (employeeIdInput && employeeIdInput.value.trim()) {
        searchEmployee();
    }
});
