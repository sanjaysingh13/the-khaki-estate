# Production Deployment Guide

This document outlines the steps needed to deploy The Khaki Estate application to production.

## 🚀 Deployment Steps

### 1. Database Migrations
```bash
# Run all database migrations (includes maintenance categories)
python manage.py migrate
```

### 2. Static Files
```bash
# Collect static files for production serving
python manage.py collectstatic --noinput
```

### 3. Optional: Manual Category Population
If you need to re-populate or update maintenance categories manually:
```bash
# Populate maintenance categories (optional - already handled by migration)
python manage.py populate_maintenance_categories

# Or to clear existing and repopulate
python manage.py populate_maintenance_categories --clear
```

## 📊 Maintenance Categories

The system automatically includes **27 maintenance categories** organized by priority:

## 🔔 Notification Types

The system automatically includes **11 notification types** for the notification system:

### Notification Categories:
- **Maintenance**: new_maintenance_request, maintenance_update, urgent_maintenance_request
- **Announcements**: new_announcement, urgent_announcement
- **Events**: event_reminder, event_cancelled
- **Bookings**: booking_confirmed, booking_cancelled
- **System**: welcome_message, account_activated

- **Emergency (Priority 4)**: 6 categories - Immediate response required
- **High Priority (Priority 3)**: 7 categories - Major issues affecting daily life
- **Medium Priority (Priority 2)**: 9 categories - Standard maintenance and repairs
- **Low Priority (Priority 1)**: 5 categories - Routine maintenance and cosmetic issues

### Categories Include:
- **Electrical** (Emergency & Standard)
- **Plumbing** (Emergency & Standard)
- **HVAC** (Air Conditioning, Heating)
- **Safety** (Fire Safety, Security, Gas Leaks)
- **Structural** (Damage, Doors/Windows)
- **Appliances** (Repair, Maintenance)
- **General** (Carpentry, Painting, Flooring)
- **Services** (Cleaning, Pest Control, Landscaping)
- **Common Areas** (Parking, Elevators, Shared Spaces)

## 🔧 Verification

After deployment, verify the categories are available:

1. **Admin Panel**: Visit `/admin/backend/maintenancecategory/`
2. **Maintenance Form**: Check that category dropdown is populated
3. **Database Check**:
   ```bash
   python manage.py shell
   >>> from the_khaki_estate.backend.models import MaintenanceCategory
   >>> print(f"Categories: {MaintenanceCategory.objects.count()}")
   >>> # Should show 27 categories
   ```

## 🔄 Updates

If you need to update categories in the future:

1. **Modify the management command**: `backend/management/commands/populate_maintenance_categories.py`
2. **Run the command**: `python manage.py populate_maintenance_categories`
3. **Or create a new data migration** for automatic deployment

## 📝 Notes

- **Data Migration**: Categories are automatically created via Django migration `0003_auto_20250919_1443.py`
- **Idempotent**: Safe to run multiple times - won't create duplicates
- **Reversible**: Migration can be reversed if needed
- **Priority-based**: Categories include priority levels for request handling
- **Time Estimates**: Each category has realistic resolution time estimates
