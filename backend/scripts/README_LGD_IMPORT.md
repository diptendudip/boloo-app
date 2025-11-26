# LGD Data Import Instructions

## Problem
The Boloo backend database is missing LGD (Local Government Directory) data, causing states and districts dropdowns to be empty in the mobile web app.

## Solution
Import states and districts data from the JSON file into Azure PostgreSQL database.

## Prerequisites
- Access to Azure PostgreSQL database (boloo-backend-api Azure Web App)
- Database connection string

## Step 1: Get Azure Database Connection String

### Option A: From Azure Portal
1. Go to Azure Portal: https://portal.azure.com
2. Navigate to Resource Group: `cgnet-mvp-rg`
3. Find the PostgreSQL server (should be something like `boloo-db-server`)
4. Click on "Connection strings" in the left menu
5. Copy the connection string, it should look like:
   ```
   postgresql://username@servername:password@servername.postgres.database.azure.com:5432/dbname
   ```

### Option B: From Azure CLI
```bash
# Login to Azure
az login

# Get Web App configuration (to find database connection)
az webapp config appsettings list \
  --name boloo-backend-api \
  --resource-group cgnet-mvp-rg \
  --query "[?name=='DATABASE_URL'].value" \
  --output tsv
```

### Option C: From Azure Web App Configuration
1. Go to Azure Portal: https://portal.azure.com
2. Navigate to App Services → `boloo-backend-api`
3. Click "Configuration" in the left menu
4. Click "Application settings"
5. Find `DATABASE_URL` setting
6. Click "Show value" to reveal the connection string

## Step 2: Run the Import Script

Once you have the DATABASE_URL, run:

```bash
# Navigate to backend directory
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Set the database URL (replace with your actual connection string)
export DATABASE_URL="postgresql://user:password@host.postgres.database.azure.com:5432/dbname"

# Run the import script
python3 scripts/import_lgd_azure.py
```

## Step 3: Verify the Import

After running the script, verify the data was loaded:

```bash
# Test the API endpoint
curl https://boloo-backend-api.azurewebsites.net/api/dropdown/states
```

You should see a JSON response with all Indian states.

## What the Script Does

1. **Connects to Azure PostgreSQL** using the DATABASE_URL
2. **Creates tables** if they don't exist:
   - `admin_states` - Contains all Indian states/UTs
   - `admin_districts` - Contains all districts
3. **Clears existing data** (if any) to avoid duplicates
4. **Imports 35+ states** with proper state codes
5. **Imports 700+ districts** linked to their states
6. **Creates indexes** for optimal query performance
7. **Verifies** the import was successful

## Troubleshooting

### Connection Issues
If you see connection errors:
- Verify the DATABASE_URL is correct
- Check Azure PostgreSQL firewall rules allow your IP
- Ensure the database exists

### Permission Issues
If you see permission errors:
- Ensure the database user has CREATE TABLE permissions
- Check that the user can INSERT data

### Data Already Exists
The script clears existing data before importing. If you want to keep existing data, modify the script to skip the DELETE statements.

## Alternative: Deploy Script to Azure

If you can't connect from your local machine, you can deploy the script to Azure:

1. Add the script to the repository
2. Create a GitHub Action workflow to run it
3. Or SSH into the Azure Web App container and run it there

## Files Created

- `/Users/diptendu/boloo app/boloo-app/backend/scripts/import_lgd_azure.py` - Main import script
- `/Users/diptendu/boloo app/boloo-app/backend/scripts/README_LGD_IMPORT.md` - This file

## Data Source

- **Source File**: `/Users/diptendu/boloo app/boloo-app/backend/data/lgd/states-districts.json`
- **Format**: JSON with nested states and districts
- **Coverage**: All Indian states, UTs, and their districts

## Expected Results

After successful import:
- **States**: 35+ entries (all Indian states and UTs)
- **Districts**: 700+ entries (all districts across India)
- **API Response**: `/api/dropdown/states` returns populated list
- **Mobile App**: State and district dropdowns work correctly
