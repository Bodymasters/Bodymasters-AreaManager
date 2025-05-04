from app import db, Permission

# Check if permissions already exist
existing_codes = [p.code for p in Permission.query.all()]

# List of new permissions
new_permissions = [
    {
        'name': 'Add Violation',
        'code': 'add_violation',
        'description': 'Permission to add a new violation'
    },
    {
        'name': 'Edit Violation',
        'code': 'edit_violation',
        'description': 'Permission to edit violations'
    },
    {
        'name': 'Import Violation Types',
        'code': 'import_violation_types',
        'description': 'Permission to import violation types from Excel'
    }
]

# Add only new permissions
added_count = 0
for perm in new_permissions:
    if perm['code'] not in existing_codes:
        permission = Permission(
            name=perm['name'],
            code=perm['code'],
            description=perm['description']
        )
        db.session.add(permission)
        added_count += 1

# Save changes
if added_count > 0:
    db.session.commit()
    print(f'Added {added_count} new permissions successfully')
else:
    print('No new permissions added (all permissions already exist)')
