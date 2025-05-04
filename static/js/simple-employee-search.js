/**
 * ملف مبسط للبحث عن الموظف - حل جذري
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
        
        // إرسال نموذج بسيط للخادم
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/violations/search-employee';
        
        // إضافة حقل الرقم الوظيفي
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'employee_id';
        input.value = employeeId;
        form.appendChild(input);
        
        // إضافة النموذج إلى الصفحة وإرساله
        document.body.appendChild(form);
        form.submit();
    }
});
