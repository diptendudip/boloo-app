# Database Migration Guide for Boloo App

## Issue: Multiple Migration Heads & Data Integrity

### Problem
The database migrations encountered two issues:
1. **Multiple migration heads**: Feed tables, push notifications, and attachments migrations were created separately
2. **Data integrity**: Existing users have null `phone` values, but migration requires NOT NULL constraint

### Solution Steps

## Step 1: Fix Existing Data

Before running migrations, update existing users with null phone numbers:

```sql
-- Connect to database
psql -U your_username -d boloo_db

-- Check users with null phones
SELECT id, email, phone FROM users WHERE phone IS NULL;

-- Option 1: Set temporary placeholder phone numbers
UPDATE users
SET phone = '+919999900000'  -- Temporary placeholder
WHERE phone IS NULL;

-- Option 2: Delete test users without phones (if safe)
DELETE FROM users WHERE phone IS NULL AND email LIKE '%@test.com';
```

## Step 2: Run Merged Migration

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend

# The merge has already been created: merge_all_feature_migrations.py
# Now run the migration
alembic upgrade head
```

## Step 3: Verify Migration Success

```bash
# Check current migration version
alembic current

# Should show: merge_all_feature_migrations (head)

# Verify new tables exist
psql -U your_username -d boloo_db -c "\dt"
```

## Expected New Tables

After successful migration:
- ✅ `feed_posts` - Social feed posts
- ✅ `feed_likes` - Post likes
- ✅ `feed_comments` - Post comments
- ✅ `feed_shares` - Post shares
- ✅ `case_attachments` - Photo/document uploads
- ✅ `case_updates` - Case status updates
- ✅ Updated `users` table with `push_token`, `notification_settings`, `is_first_timer`

## Step 4: Verify Data

```sql
-- Check all tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Verify columns in users table
\d users

-- Should include:
--  - phone (NOT NULL)
--  - email (NOT NULL)
--  - push_token (TEXT, nullable)
--  - notification_settings (JSONB, nullable)
--  - is_first_timer (BOOLEAN, default true)
```

## Alternative: Fresh Database Setup

If you have a development database and don't need existing data:

```bash
# Drop and recreate database
dropdb boloo_db
createdb boloo_db

# Run all migrations from scratch
cd /Users/diptendu/boloo\ app/boloo-app/backend
alembic upgrade head
```

## Migration Files Created

1. **001_initial_schema.py** - Base tables (User, Case, OTP, etc.)
2. **002_update_user_phone_email_fields.py** - Make phone/email NOT NULL
3. **003_add_attachments_and_updates.py** - CaseAttachment, CaseUpdate tables
4. **004_add_feed_tables.py** - Feed system tables
5. **add_push_notifications.py** - Push notification fields
6. **merge_all_feature_migrations.py** - Merges all heads into single path

## Troubleshooting

### Error: "column 'phone' contains null values"
**Solution**: Update or delete users with null phones (see Step 1)

### Error: "Multiple heads"
**Solution**: Already handled - merge file created

### Error: "Table already exists"
**Solution**: Check if migrations were partially applied:
```bash
alembic current  # Check current version
alembic downgrade <previous_version>  # Rollback if needed
```

## Production Deployment

For production database:

1. **Backup first**:
   ```bash
   pg_dump -U username -d boloo_db > backup_$(date +%Y%m%d).sql
   ```

2. **Fix data in staging first**
3. **Test migrations in staging**
4. **Apply to production during maintenance window**
5. **Verify all services running**

## Next Steps

After successful migration:
- ✅ Restart backend server
- ✅ Test feed API endpoints
- ✅ Test upload endpoints
- ✅ Test push notification registration
- ✅ Verify mobile app can connect
