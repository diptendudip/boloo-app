# Boloo Web App User Guide

## Welcome to Boloo Web Admin

The Boloo Web Admin is a powerful desktop interface for managing your Boloo platform. This guide will help you navigate and use all features effectively.

## Access Information

### Live Application
- **URL**: https://orange-sand-00170940f.3.azurestaticapps.net
- **Supported Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
- **Minimum Screen Resolution**: 1280x720
- **Optimal Resolution**: 1920x1080 or higher

### System Requirements
- Modern web browser (updated within last 6 months)
- JavaScript enabled
- Cookies enabled
- Stable internet connection (minimum 1 Mbps)

## Getting Started

### First Login
1. Navigate to https://orange-sand-00170940f.3.azurestaticapps.net
2. You'll see the Boloo dashboard
3. The interface is optimized for desktop use

### Interface Overview

```
┌─────────────────────────────────────────────────────┐
│  Boloo Logo    [Navigation Menu]      [User Menu]   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [Sidebar]           [Main Content Area]            │
│  - Dashboard                                         │
│  - Cases                                             │
│  - Entities                                          │
│  - Taxonomies                                        │
│  - Users                                             │
│  - Monitoring                                        │
│  - Analytics                                         │
│  - Settings                                          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Main Features

### 1. Dashboard (/)

**Purpose**: Overview of your Boloo system

**Key Metrics Displayed**:
- Total cases count
- Active entities
- Recent activity
- System health status
- Quick access cards

**What You Can Do**:
- View summary statistics
- Access quick actions
- Monitor system status at a glance
- Navigate to detailed sections

**Tips**:
- Dashboard refreshes automatically every 30 seconds
- Click on any metric card for detailed view
- Use filters to customize time range

### 2. Cases (/cases)

**Purpose**: Manage and track all cases in the system

**Features**:
- View all cases in a list or grid
- Filter by status, date, assignee
- Search cases by keywords
- Create new cases
- Edit existing cases
- Assign cases to users
- Track case progress

**Actions Available**:
- **Create Case**: Click "New Case" button
- **View Details**: Click on any case
- **Edit Case**: Click edit icon
- **Delete Case**: Click delete icon (with confirmation)
- **Bulk Actions**: Select multiple cases for bulk operations

**Status Options**:
- Open
- In Progress
- Under Review
- Resolved
- Closed

**Tips**:
- Use keyboard shortcuts: `N` for new case, `/` for search
- Export cases to CSV/Excel
- Set up saved filters for common views

### 3. Entities (/entities)

**Purpose**: Track and manage entities within cases

**Features**:
- Entity directory
- Relationship mapping
- Entity profiles
- Timeline of entity activities
- Document attachments

**Entity Types**:
- People
- Organizations
- Locations
- Evidence
- Documents

**What You Can Do**:
- Add new entities
- Link entities to cases
- View entity relationships
- Upload supporting documents
- Track entity history

**Tips**:
- Use relationship graph for visual connections
- Tag entities for easier organization
- Set up entity alerts

### 4. Taxonomies (/taxonomies)

**Purpose**: Define and manage system taxonomies

**Features**:
- Category management
- Tag creation
- Hierarchical organization
- Custom field definitions

**Use Cases**:
- Case categorization
- Evidence classification
- Document types
- Priority levels
- Custom metadata

**What You Can Do**:
- Create new taxonomies
- Define taxonomy hierarchies
- Set default values
- Archive outdated taxonomies

**Tips**:
- Plan taxonomy structure before creating
- Use consistent naming conventions
- Review and update taxonomies quarterly

### 5. Users (/users)

**Purpose**: Manage user accounts and permissions

**Features**:
- User directory
- Role management
- Permission settings
- Activity logs
- Account status

**User Roles**:
- Admin (full access)
- Manager (manage cases and users)
- Investigator (manage cases)
- Viewer (read-only)

**What You Can Do**:
- Create user accounts
- Assign roles and permissions
- Deactivate users
- Reset passwords
- View user activity

**Security Features**:
- Password complexity requirements
- Session timeout after inactivity
- Audit trail of all actions

**Tips**:
- Follow principle of least privilege
- Review user access quarterly
- Monitor user activity logs

### 6. Monitoring (/monitoring)

**Purpose**: System health and performance monitoring

**Features**:
- Real-time metrics
- System logs
- Error tracking
- Performance graphs
- Uptime monitoring

**Metrics Tracked**:
- API response times
- Database performance
- Error rates
- Active users
- Storage usage

**What You Can Do**:
- View system health dashboard
- Check recent errors
- Monitor performance trends
- Set up alerts (future feature)

**Alert Thresholds**:
- Response time > 2 seconds
- Error rate > 1%
- Storage > 80% capacity

**Tips**:
- Check monitoring daily
- Investigate spike patterns
- Export logs for analysis

### 7. Analytics (/analytics)

**Purpose**: Advanced data analysis and reporting

**Features**:
- Custom reports
- Data visualization
- Trend analysis
- Exportable charts
- Scheduled reports

**Report Types**:
- Case statistics
- User productivity
- Entity relationships
- Timeline analysis
- Custom queries

**Visualizations**:
- Bar charts
- Line graphs
- Pie charts
- Heat maps
- Relationship graphs

**What You Can Do**:
- Create custom reports
- Schedule automated reports
- Export to PDF/Excel
- Share reports with team
- Save report templates

**Tips**:
- Start with pre-built templates
- Use date filters for trending
- Export data for deeper analysis

### 8. Settings (/settings)

**Purpose**: Configure application preferences

**Available Settings**:
- Profile settings
- Notification preferences
- Display options
- Integration settings
- Security settings

**Configuration Options**:
- Theme (light/dark mode)
- Language preferences
- Date/time format
- Default views
- Email notifications

**What You Can Do**:
- Update profile information
- Change password
- Configure notifications
- Set default preferences
- Manage integrations

**Tips**:
- Review settings after first login
- Enable important notifications
- Use dark mode for reduced eye strain

## Keyboard Shortcuts

### Global Shortcuts
- `?` - Show help
- `/` - Focus search
- `Esc` - Close dialogs/modals
- `Ctrl/Cmd + K` - Quick command palette

### Navigation
- `G + D` - Go to Dashboard
- `G + C` - Go to Cases
- `G + E` - Go to Entities
- `G + U` - Go to Users
- `G + M` - Go to Monitoring
- `G + A` - Go to Analytics

### Actions
- `N` - New item (context-dependent)
- `E` - Edit selected item
- `Del` - Delete selected item
- `Ctrl/Cmd + S` - Save
- `Ctrl/Cmd + Enter` - Submit form

## Common Workflows

### Creating a New Case

1. Click "Cases" in sidebar or press `G + C`
2. Click "New Case" button or press `N`
3. Fill in required fields:
   - Case title
   - Description
   - Category (from taxonomies)
   - Priority level
   - Assigned user
4. Click "Save" or press `Ctrl/Cmd + S`
5. Case is created and you're redirected to case details

### Adding Entities to a Case

1. Open a case (from Cases page)
2. Scroll to "Related Entities" section
3. Click "Add Entity"
4. Search for existing entity or create new
5. Define relationship type
6. Click "Link Entity"
7. Entity is now associated with the case

### Generating a Report

1. Go to Analytics page (`G + A`)
2. Select report type from templates
3. Configure parameters:
   - Date range
   - Filters
   - Grouping options
4. Click "Generate Report"
5. Review visualizations
6. Export to PDF or Excel if needed

### Managing User Permissions

1. Go to Users page (`G + U`)
2. Search for user
3. Click on user name
4. Go to "Permissions" tab
5. Select role from dropdown
6. Check/uncheck specific permissions
7. Click "Save Changes"
8. User permissions updated immediately

## Best Practices

### Data Entry
- Use consistent naming conventions
- Fill all required fields
- Add detailed descriptions
- Attach relevant documents
- Tag appropriately using taxonomies

### Organization
- Create logical case structures
- Use taxonomies for consistency
- Link related entities
- Maintain clean user directory
- Archive completed cases regularly

### Security
- Log out when leaving workstation
- Use strong, unique passwords
- Review permissions regularly
- Monitor user activity
- Report suspicious activity

### Performance
- Close unused browser tabs
- Clear browser cache periodically
- Use filters to limit large datasets
- Export large reports instead of viewing
- Schedule resource-intensive reports

## Troubleshooting

### Common Issues

**Issue**: Page not loading
- **Solution**: Refresh browser (F5 or Cmd+R)
- Check internet connection
- Clear browser cache and cookies
- Try incognito/private mode

**Issue**: Can't save changes
- **Solution**: Check for validation errors in red
- Ensure all required fields filled
- Check internet connection
- Try refreshing and re-entering data

**Issue**: Slow performance
- **Solution**: Close other browser tabs
- Reduce number of filters
- Use date range to limit data
- Clear browser cache
- Check system monitoring page

**Issue**: Can't access certain features
- **Solution**: Check your user role/permissions
- Contact administrator for access
- Verify you're on correct page
- Try logging out and back in

**Issue**: Data not appearing
- **Solution**: Check filter settings
- Verify date range selection
- Ensure data was saved properly
- Try refreshing the page
- Check with administrator

### Getting Help

1. **In-App Help**: Click `?` for context-sensitive help
2. **System Status**: Check /monitoring for system issues
3. **Administrator**: Contact your system administrator
4. **Documentation**: Refer to this guide
5. **Support**: Email support team (if configured)

## Mobile Access

### Mobile Browser Support
While the web app is optimized for desktop, it can be accessed on mobile devices:

**Supported**:
- Modern mobile browsers (Chrome, Safari)
- Tablet devices (iPad, Android tablets)
- Basic functionality available

**Limitations on Mobile**:
- Some advanced features limited
- Smaller screen may affect usability
- Charts may not render optimally
- File uploads may have restrictions

**Recommendation**: For mobile use, consider the Boloo iOS app for better experience.

## Privacy and Data

### Data Handling
- All data transmitted over HTTPS
- Session timeout after 30 minutes of inactivity
- No data stored locally in browser
- Audit logs maintained for all actions

### Privacy Features
- User activity tracking for security
- Secure session management
- No third-party tracking
- GDPR compliant (when configured)

## Updates and Maintenance

### Automatic Updates
- Web app updates automatically
- No user action required
- Changes deployed transparently
- Check changelog for new features

### Maintenance Windows
- Scheduled maintenance announced in advance
- Typically occurs during low-usage hours
- Downtime minimal (< 5 minutes usually)
- Status page shows current system state

### Browser Compatibility
- Keep browser updated to latest version
- Unsupported browsers may have issues
- Enable JavaScript and cookies
- Disable browser extensions if issues occur

## Tips for Maximum Productivity

1. **Learn Keyboard Shortcuts**: Saves time on common actions
2. **Use Saved Filters**: Quick access to common views
3. **Set Up Notifications**: Stay informed of important changes
4. **Customize Dashboard**: Show metrics most relevant to you
5. **Use Bulk Actions**: Process multiple items efficiently
6. **Export Data**: Analyze in external tools when needed
7. **Create Report Templates**: Reuse for regular reporting
8. **Organize with Taxonomies**: Consistent categorization
9. **Link Related Items**: Better context and traceability
10. **Review Analytics**: Data-driven decision making

## Comparison: Web vs Mobile

| Feature | Web App | iOS App |
|---------|---------|---------|
| Full Dashboard | ✅ Yes | ✅ Yes |
| Case Management | ✅ Full | ✅ Full |
| Entity Management | ✅ Full | ✅ Full |
| Advanced Analytics | ✅ Yes | ⚠️ Limited |
| Bulk Operations | ✅ Yes | ❌ No |
| System Monitoring | ✅ Yes | ❌ No |
| Taxonomy Management | ✅ Yes | ❌ No |
| Keyboard Shortcuts | ✅ Yes | ❌ No |
| Offline Mode | ❌ No | ✅ Yes |
| Push Notifications | ❌ No | ✅ Yes |
| Camera Integration | ❌ No | ✅ Yes |
| Biometric Auth | ❌ No | ✅ Yes |
| Best For | Desktop work, admin | Field work, quick access |

## Frequently Asked Questions

**Q: Do I need to install anything?**
A: No, the web app runs entirely in your browser. Just navigate to the URL.

**Q: Can I use it offline?**
A: No, the web app requires internet connection. Use the mobile app for offline access.

**Q: How often does data refresh?**
A: Dashboard auto-refreshes every 30 seconds. Other pages refresh on manual reload.

**Q: Can I access it from multiple devices?**
A: Yes, use the same credentials on any supported browser.

**Q: Are my changes saved automatically?**
A: No, you must click "Save" to commit changes.

**Q: What happens if I lose connection while working?**
A: Unsaved changes may be lost. Save frequently and check monitoring page.

**Q: Can I export data?**
A: Yes, most views offer export to CSV, Excel, or PDF.

**Q: How do I report a bug?**
A: Contact your administrator or use in-app feedback (if available).

**Q: Can I customize the interface?**
A: Yes, visit Settings to configure theme, layout, and preferences.

**Q: Is my data secure?**
A: Yes, all data is transmitted over HTTPS and stored securely in Azure.

## Additional Resources

### Documentation
- Deployment Guide: `docs/WEB_VERSION_DEPLOYMENT.md`
- API Documentation: `docs/API.md`
- Backend Deployment: `docs/BACKEND_DEPLOYMENT.md`

### External Links
- Azure Static Web Apps: https://azure.microsoft.com/services/app-service/static/
- Next.js Documentation: https://nextjs.org/docs
- React Documentation: https://react.dev

### Support Contacts
- System Administrator: Contact your organization
- Technical Support: Check with your admin for support channel
- Emergency: Refer to your organization's IT support

---

**Document Version**: 1.0.0
**Last Updated**: November 2024
**App Version**: 1.0.0
**Applies To**: Boloo Web Admin (https://orange-sand-00170940f.3.azurestaticapps.net)
