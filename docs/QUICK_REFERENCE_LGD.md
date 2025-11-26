# LGD Import Quick Reference

## 🚀 Quick Commands

### Import Target States (Default)
```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
source venv/bin/activate
python3 scripts/import_lgd_fresh.py
```
**Imports:** CG, MP, MH, JH, Bihar, UP, AP, Telangana, Odisha

### Import Specific States
```bash
# Import only Chhattisgarh
python3 scripts/import_lgd_fresh.py --states 22

# Import CG and MP
python3 scripts/import_lgd_fresh.py --states 22 23
```

### Verify Import
```bash
# Check block count
docker exec boloo-postgres psql -U boloo -d boloo -c "SELECT COUNT(*) FROM admin_blocks"

# Check panchayat count
docker exec boloo-postgres psql -U boloo -d boloo -c "SELECT COUNT(*) FROM admin_panchayats"

# Check Bastar specifically
docker exec boloo-postgres psql -U boloo -d boloo -c "SELECT b.name_en, COUNT(p.id) FROM admin_blocks b LEFT JOIN admin_panchayats p ON p.block_lgd_code = b.lgd_code WHERE b.district_lgd_code = '1108' GROUP BY b.name_en"
```

### Test APIs
```bash
# Test blocks API for Bastar
curl "http://localhost:8000/api/dropdown/blocks?district_lgd_code=1108"

# Test panchayats API for Bastar block
curl "http://localhost:8000/api/dropdown/panchayats?block_lgd_code=3593"
```

## 📊 Current Status

| Metric | Count |
|--------|-------|
| **States** | 9 |
| **Blocks** | 2,383 |
| **Panchayats** | 31,145 |

## 🗺️ State Codes

| State | Code |
|-------|------|
| Chhattisgarh | 22 |
| Madhya Pradesh | 23 |
| Maharashtra | 27 |
| Jharkhand | 20 |
| Bihar | 10 |
| Uttar Pradesh | 09 |
| Andhra Pradesh | 28 |
| Telangana | 36 |
| Odisha | 21 |

## 🔧 Troubleshooting

### Issue: No blocks showing
```bash
# Re-import
python3 scripts/import_lgd_fresh.py

# Restart backend
pm2 restart boloo-backend
```

### Issue: Panchayats not loading
```bash
# Check if block exists
curl "http://localhost:8000/api/dropdown/blocks?district_lgd_code=<DISTRICT_CODE>"

# Check panchayats for block
curl "http://localhost:8000/api/dropdown/panchayats?block_lgd_code=<BLOCK_CODE>"
```

### Issue: Old data showing
```bash
# Clear and re-import (will delete old data)
python3 scripts/import_lgd_fresh.py
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `/scripts/import_lgd_fresh.py` | Multi-state import script |
| `/data/lgd/blocks.19Nov2025.csv` | Development Blocks data |
| `/data/lgd/pri_local_bodies.19Nov2025.csv` | Panchayats data |
| `/docs/MULTI_STATE_IMPORT_SUCCESS.md` | Detailed technical report |

## 🎯 Success Criteria

✅ Bastar district shows **7 blocks** (not 1)
✅ Each block has panchayats linked
✅ APIs return correct data
✅ Mobile app can complete address flow

## 📞 Quick Help

**Check logs:**
```bash
pm2 logs boloo-backend
```

**Database access:**
```bash
docker exec -it boloo-postgres psql -U boloo -d boloo
```

**Restart everything:**
```bash
pm2 restart boloo-backend
# Close and reopen mobile app
```

---

*Last Updated: November 19, 2025*
*Import Script: `/backend/scripts/import_lgd_fresh.py`*
*Data Source: Government of India LGD Directory*
