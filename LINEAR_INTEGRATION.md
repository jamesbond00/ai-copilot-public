# Linear Integration Guide

This guide explains how to set up and use Linear integration with your AI Copilot project.

## 🚀 Quick Setup

### 1. Get Your Linear API Key

1. Go to [Linear Settings](https://linear.app/settings/api)
2. Click "Create API Key"
3. Give it a name (e.g., "AI Copilot Integration")
4. Copy the API key

### 2. Get Your Team ID

1. Go to your Linear workspace
2. Navigate to the team you want to use
3. The Team ID is in the URL: `https://linear.app/your-workspace/team/TEAM_ID`
4. Copy the Team ID

### 3. Set Environment Variables

Add these to your `.env` file:

```bash
# Linear Integration
LINEAR_API_KEY=lin_api_your_api_key_here
LINEAR_TEAM_ID=your_team_id_here
```

## 🎯 Features

### Automatic Issue Creation
- When AI analysis detects critical issues (confidence > 0.7), you can create Linear issues
- Issues include AI-generated summaries, insights, and recommendations
- Priority is automatically set based on issue severity

### Dashboard Integration
- View recent Linear issues in the sidebar
- See issue statistics and resolution rates
- Create issues directly from analysis results

### Issue Management
- Track issue creation and resolution
- Monitor resolution times
- Get insights into system health vs. project management

## 🔧 Configuration Options

### Priority Mapping
Issues are automatically prioritized based on:
- **Priority 1 (Urgent)**: Critical errors, outages, security issues
- **Priority 2 (High)**: High confidence analyses with important insights
- **Priority 3 (Normal)**: Medium confidence analyses
- **Priority 4 (Low)**: Low confidence analyses

### Default Labels
All created issues are tagged with:
- `ai-copilot` - Identifies issues created by AI
- `automated` - Indicates automated creation
- `monitoring` - Related to system monitoring

### Confidence Threshold
Only analyses with confidence > 0.7 will show the Linear integration options.

## 📊 Usage Examples

### Creating Issues from Analysis
1. Run an analysis in the dashboard
2. If confidence > 0.7, you'll see "Create Linear Issue" button
3. Click to create an issue with:
   - AI-generated title
   - Detailed description with insights and recommendations
   - Appropriate priority level
   - Default labels

### Viewing Issue Statistics
- Click "Issue Statistics" in the sidebar
- See total issues, resolution rate, and average resolution time
- Monitor the effectiveness of your AI-driven issue management

### Managing Issues
- View recent issues in the sidebar
- Track issue status and progress
- Update issues with resolution notes

## 🛠️ Advanced Configuration

### Custom Priority Mapping
You can customize how analysis results map to Linear priorities by modifying the `IssueCreationConfig` in `linear_service.py`.

### Custom Labels
Add custom labels by modifying the `default_labels` parameter when creating the Linear service.

### Webhook Integration
For real-time updates, you can set up Linear webhooks to notify your system when issues are updated or resolved.

## 🔍 Troubleshooting

### Common Issues

**"Linear not configured"**
- Check that `LINEAR_API_KEY` and `LINEAR_TEAM_ID` are set
- Verify the API key is valid
- Ensure the team ID is correct

**"Failed to create Linear issue"**
- Check API key permissions
- Verify team ID exists
- Ensure you have permission to create issues in the team

**"Import error"**
- Make sure all dependencies are installed
- Check that the Linear integration modules are in the correct location

### Debug Mode
Enable debug logging to see detailed information about Linear API calls:

```python
import logging
logging.getLogger("src.integrations.linear_client").setLevel(logging.DEBUG)
```

## 📚 API Reference

### LinearClient
- `create_issue()` - Create a new issue
- `get_issues()` - Retrieve issues
- `update_issue()` - Update an existing issue
- `get_teams()` - Get available teams

### LinearIntegrationService
- `create_issue_from_analysis()` - Create issue from AI analysis
- `get_recent_issues()` - Get recent issues
- `get_issue_statistics()` - Get issue statistics
- `update_issue_with_resolution()` - Update issue with resolution

## 🚀 Next Steps

1. **Set up webhooks** for real-time issue updates
2. **Customize issue templates** for different analysis types
3. **Add issue assignment** based on analysis results
4. **Integrate with Slack** for issue notifications
5. **Create custom dashboards** for issue tracking

## 📞 Support

For issues with Linear integration:
1. Check the troubleshooting section above
2. Review Linear API documentation
3. Check the application logs for detailed error messages
4. Verify your Linear workspace permissions
