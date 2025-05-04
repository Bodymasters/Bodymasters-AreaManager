-- حذف فترات المتابعة أولاً
DELETE FROM camera_time_slot WHERE camera_check_id = ?;

-- حذف المتابعة نفسها
DELETE FROM camera_check WHERE id = ?;
