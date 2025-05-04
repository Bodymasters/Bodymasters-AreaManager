"""
محسن قاعدة البيانات
يحتوي على وظائف لتحسين استعلامات قاعدة البيانات وتقليل وقت الاستجابة
"""

import time
import functools
from flask import current_app, g
from sqlalchemy import text
from sqlalchemy.orm import joinedload

# قاموس للتخزين المؤقت للاستعلامات
query_cache = {}
# وقت انتهاء صلاحية التخزين المؤقت (بالثواني)
CACHE_EXPIRY = 60  # دقيقة واحدة

def cached_query(expiry=CACHE_EXPIRY):
    """
    مزخرف لتخزين نتائج الاستعلامات مؤقتًا
    
    :param expiry: وقت انتهاء صلاحية التخزين المؤقت بالثواني
    :return: نتيجة الاستعلام المخزنة مؤقتًا أو نتيجة استعلام جديدة
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # إنشاء مفتاح فريد للاستعلام
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # التحقق من وجود النتيجة في التخزين المؤقت
            if cache_key in query_cache:
                cached_result, timestamp = query_cache[cache_key]
                # التحقق من صلاحية التخزين المؤقت
                if time.time() - timestamp < expiry:
                    return cached_result
            
            # تنفيذ الاستعلام وتخزين النتيجة
            result = func(*args, **kwargs)
            query_cache[cache_key] = (result, time.time())
            return result
        return wrapper
    return decorator

def optimize_query(query, model, eager_load=None):
    """
    تحسين استعلام SQLAlchemy
    
    :param query: استعلام SQLAlchemy
    :param model: نموذج SQLAlchemy
    :param eager_load: قائمة بالعلاقات التي يجب تحميلها مسبقًا
    :return: استعلام محسن
    """
    # تحميل العلاقات مسبقًا لتقليل عدد الاستعلامات
    if eager_load:
        for relation in eager_load:
            query = query.options(joinedload(getattr(model, relation)))
    
    return query

def get_db_stats():
    """
    الحصول على إحصائيات قاعدة البيانات
    
    :return: قاموس يحتوي على إحصائيات قاعدة البيانات
    """
    from app import db
    
    stats = {}
    
    try:
        # الحصول على عدد الاستعلامات
        stats['query_count'] = getattr(g, '_query_count', 0)
        
        # الحصول على حجم قاعدة البيانات
        result = db.session.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"))
        stats['db_size'] = result.scalar() / (1024 * 1024)  # تحويل إلى ميجابايت
        
        # الحصول على عدد الصفوف في الجداول الرئيسية
        tables = ['user', 'club', 'facility', 'check', 'check_item', 'employee']
        for table in tables:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            stats[f'{table}_count'] = result.scalar()
        
    except Exception as e:
        current_app.logger.error(f"Error getting DB stats: {str(e)}")
        stats['error'] = str(e)
    
    return stats

def count_queries(func):
    """
    مزخرف لحساب عدد الاستعلامات في دالة
    
    :param func: الدالة المراد حساب استعلاماتها
    :return: الدالة المزخرفة
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # تهيئة عداد الاستعلامات
        if not hasattr(g, '_query_count'):
            g._query_count = 0
        
        # حفظ عدد الاستعلامات قبل تنفيذ الدالة
        before_count = g._query_count
        
        # تنفيذ الدالة
        result = func(*args, **kwargs)
        
        # حساب عدد الاستعلامات الجديدة
        after_count = g._query_count
        query_count = after_count - before_count
        
        # تسجيل عدد الاستعلامات
        current_app.logger.debug(f"Function {func.__name__} executed {query_count} queries")
        
        return result
    return wrapper

def clear_cache():
    """
    مسح التخزين المؤقت للاستعلامات
    """
    global query_cache
    query_cache = {}
    current_app.logger.info("Query cache cleared")

def optimize_db_session():
    """
    تحسين جلسة قاعدة البيانات
    """
    from app import db
    
    # تعيين وقت انتهاء صلاحية الجلسة
    db.session.expire_on_commit = False
    
    # تعيين حجم الدفعة للعمليات الكبيرة
    db.session.configure(execution_options={"stream_results": True})
    
    return db.session
