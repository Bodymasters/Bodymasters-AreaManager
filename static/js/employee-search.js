/**
 * ملف مخصص للبحث عن الموظف وملء بياناته في نموذج المخالفة
 */

// تنفيذ الكود عند اكتمال تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // تحديد العناصر في الصفحة
    const employeeIdInput = document.getElementById('employee_id');
    const fetchEmployeeBtn = document.getElementById('fetch-employee-btn');
    const employeeNameInput = document.getElementById('employee_name');
    const employeeRoleInput = document.getElementById('employee_role');
    const clubNameInput = document.getElementById('club_name');
    const violationNumberInput = document.getElementById('violation_number');
    
    // التأكد من وجود العناصر المطلوبة
    if (!employeeIdInput || !fetchEmployeeBtn || !employeeNameInput || 
        !employeeRoleInput || !clubNameInput || !violationNumberInput) {
        console.error('بعض عناصر النموذج غير موجودة في الصفحة');
        return;
    }
    
    // إضافة مستمع الحدث للنقر على زر البحث
    fetchEmployeeBtn.addEventListener('click', function() {
        searchEmployee();
    });
    
    // إضافة مستمع الحدث للضغط على Enter في حقل الرقم الوظيفي
    employeeIdInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
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
        
        // تغيير شكل الزر لإظهار حالة التحميل
        fetchEmployeeBtn.disabled = true;
        fetchEmployeeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        // إعادة تعيين حقول النموذج
        clearFormFields();
        
        // إرسال طلب AJAX للحصول على بيانات الموظف
        console.log(`البحث عن الموظف برقم: ${employeeId}`);
        
        // إنشاء كائن FormData
        const formData = new FormData();
        formData.append('employee_id', employeeId);
        
        // إرسال الطلب باستخدام طريقة POST
        fetch('/api/employee/search', {
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
            // ملء الحقول المرئية
            if (data.name) {
                employeeNameInput.value = data.name;
                console.log(`تم تعيين اسم الموظف إلى: ${data.name}`);
            }
            
            if (data.role) {
                employeeRoleInput.value = data.role;
                console.log(`تم تعيين دور الموظف إلى: ${data.role}`);
            }
            
            if (data.club_name) {
                clubNameInput.value = data.club_name;
                console.log(`تم تعيين اسم النادي إلى: ${data.club_name}`);
            }
            
            if (data.violations_count !== undefined) {
                const violationNumber = data.violations_count + 1;
                violationNumberInput.value = violationNumber;
                console.log(`تم تعيين رقم المخالفة إلى: ${violationNumber}`);
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
            
            // التحقق من أن الحقول ليست فارغة
            if (!employeeNameInput.value) {
                console.error('حقل اسم الموظف فارغ بعد الملء');
            }
        } catch (error) {
            console.error(`خطأ أثناء ملء حقول النموذج: ${error.message}`);
        }
    }
    
    // إضافة التحقق من صحة النموذج قبل الإرسال
    const violationForm = document.getElementById('violation-form');
    if (violationForm) {
        violationForm.addEventListener('submit', function(event) {
            // التحقق من وجود بيانات الموظف
            if (!employeeNameInput.value) {
                event.preventDefault();
                alert('الرجاء البحث عن الموظف أولاً باستخدام زر البحث');
                return false;
            }
            
            // نقل قيمة الرقم الوظيفي من حقل الإدخال إلى الحقل المخفي
            if (document.getElementById('employee_id_hidden')) {
                document.getElementById('employee_id_hidden').value = employeeIdInput.value.trim();
            }
            
            console.log('يتم إرسال النموذج ببيانات الموظف:', {
                id: employeeIdInput.value.trim(),
                name: employeeNameInput.value,
                role: employeeRoleInput.value,
                club: clubNameInput.value,
                violation_number: violationNumberInput.value
            });
            
            return true;
        });
    }
});
