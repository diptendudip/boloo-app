# Setup bultoo.com (Apex Domain Without www)

## Current Status
- ✅ www.bultoo.com → Working
- ⏳ bultoo.com → Needs DNS configuration

## DNS Records to Add in GoDaddy

### Step 1: Add TXT Record (For Azure Validation)

Go to GoDaddy DNS Management and add:

```
Type: TXT
Name: @ (or leave blank for apex domain)
Value: _ohia1qbsu4uwy391rgwe7o9bt4df4se
TTL: 1 Hour
```

### Step 2: Add A Record (For Actual Traffic)

```
Type: A
Name: @ (or leave blank for apex domain)
Value: 13.86.4.76
TTL: 1 Hour
```

**Alternative**: If GoDaddy supports ALIAS/ANAME records, use:
```
Type: ALIAS (or ANAME)
Name: @ (or leave blank)
Value: lemon-coast-0f65c5710.3.azurestaticapps.net
TTL: 1 Hour
```

## After Adding DNS Records

1. Wait 5-10 minutes for DNS propagation
2. Azure will automatically validate the TXT record
3. Then bultoo.com will work alongside www.bultoo.com

## Testing

After DNS propagates:
- https://bultoo.com → Your Boloo app
- https://www.bultoo.com → Your Boloo app (already working)

## Note

You **cannot use CNAME** for apex domain (@) - that's why we need:
- **TXT record** for Azure validation
- **A record** (IP) or **ALIAS record** (domain) for actual traffic
