"""
HTML Email Templates for Client Retention Reports.

Uses the exact Varicon email template with dynamic data from LLM analysis.
"""

from datetime import datetime


def get_risk_colors(risk_factor: str) -> dict:
    """Get color scheme based on risk level."""
    if risk_factor == "high":
        return {
            "bg": "#fef3c7",
            "header_bg": "#d97706", 
            "border": "#d97706",
            "text": "#92400e",
            "metric_color": "#dc2626",
            "issues_bg": "#fee2e2",
            "issues_text": "#991b1b",
        }
    elif risk_factor == "medium":
        return {
            "bg": "#f0f9ff",
            "header_bg": "#3b82f6",
            "border": "#3b82f6", 
            "text": "#1e40af",
            "metric_color": "#d97706",
            "issues_bg": "#fef3c7",
            "issues_text": "#92400e",
        }
    else:  # low
        return {
            "bg": "#ecfdf5",
            "header_bg": "#10b981",
            "border": "#10b981",
            "text": "#065f46",
            "metric_color": "#059669",
            "issues_bg": "#d1fae5",
            "issues_text": "#065f46",
        }


def generate_client_card(client: dict, index: int) -> str:
    """Generate a single client card HTML."""
    risk = client.get("risk_factor", "medium").lower()
    colors = get_risk_colors(risk)
    
    client_name = client.get("client_name", "Unknown")
    health_score = client.get("usage_health_score", 0)
    total_modules = client.get("total_modules_used", 0)
    trend_pct = client.get("trend_percentage", 0)
    churn_prob = client.get("churn_probability", 0)
    
    # Format trend
    trend_sign = "+" if trend_pct > 0 else ""
    trend_color = "#10b981" if trend_pct > 0 else "#dc2626" if trend_pct < 0 else "#d97706"
    
    # Risk label
    risk_label = risk.title() + " Risk"
    
    # Get concerns as list items
    concerns = client.get("key_concerns", [])[:3]
    concerns_html = ""
    for concern in concerns:
        concerns_html += f'<li>{concern}</li>'
    
    if not concerns_html:
        concerns_html = "<li>No specific issues identified</li>"
    
    # Get recommendation
    recommendations = client.get("recommendations", [])
    rec_text = recommendations[0] if recommendations else "Schedule a check-in call to discuss platform usage."
    
    # Issues section title based on risk
    if risk == "high":
        issues_title = "⚠️ Critical Issues Identified"
    elif risk == "medium":
        issues_title = "📊 Areas for Improvement"
    else:
        issues_title = "✅ Strengths & Best Practices"
    
    return f'''
                            <!-- Client {index}: {risk_label} -->
                            <div style="background: {colors['bg']}; border-radius: 8px; padding: 0; margin-bottom: 32px; overflow: hidden; border: 2px solid {colors['border']};">
                                <div style="background: {colors['header_bg']}; padding: 16px 24px;">
                                    <table width="100%" cellspacing="0" cellpadding="0" border="0">
                                        <tr>
                                            <td>
                                                <h3 style="color: white; font-size: 18px; font-weight: 600; margin: 0;">
                                                    <span style="background: white; color: {colors['header_bg']}; width: 28px; height: 28px; border-radius: 50%; display: inline-block; text-align: center; line-height: 28px; margin-right: 12px;">{index}</span>
                                                    {client_name} • {risk_label}
                                                </h3>
                                            </td>
                                        </tr>
                                    </table>
                                </div>

                                <div style="padding: 24px;">
                                    <!-- Client Metrics -->
                                    <table width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 20px;">
                                        <tr>
                                            <td width="25%" style="padding-right: 8px;">
                                                <div style="background: #f8fafc; border-radius: 6px; padding: 12px; text-align: center;">
                                                    <div style="font-size: 20px; font-weight: 600; color: {colors['metric_color']}; margin: 4px 0;">{health_score}%</div>
                                                    <div style="font-size: 11px; color: #6b7280;">Health Score</div>
                                                </div>
                                            </td>
                                            <td width="25%" style="padding: 0 4px;">
                                                <div style="background: #f8fafc; border-radius: 6px; padding: 12px; text-align: center;">
                                                    <div style="font-size: 20px; font-weight: 600; color: {colors['metric_color']}; margin: 4px 0;">{total_modules}/14</div>
                                                    <div style="font-size: 11px; color: #6b7280;">Modules Used</div>
                                                </div>
                                            </td>
                                            <td width="25%" style="padding: 0 4px;">
                                                <div style="background: #f8fafc; border-radius: 6px; padding: 12px; text-align: center;">
                                                    <div style="font-size: 20px; font-weight: 600; color: {trend_color}; margin: 4px 0;">{trend_sign}{trend_pct:.0f}%</div>
                                                    <div style="font-size: 11px; color: #6b7280;">12-Week Trend</div>
                                                </div>
                                            </td>
                                            <td width="25%" style="padding-left: 8px;">
                                                <div style="background: #f8fafc; border-radius: 6px; padding: 12px; text-align: center;">
                                                    <div style="font-size: 20px; font-weight: 600; color: {colors['metric_color']}; margin: 4px 0;">{churn_prob}%</div>
                                                    <div style="font-size: 11px; color: #6b7280;">Churn Risk</div>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Key Issues -->
                                    <div style="background: {colors['issues_bg']}; border-radius: 6px; padding: 16px; margin-bottom: 16px;">
                                        <h4 style="color: {colors['issues_text']}; font-size: 14px; font-weight: 600; margin: 0 0 8px 0;">
                                            {issues_title}
                                        </h4>
                                        <ul style="color: {colors['issues_text']}; font-size: 13px; margin: 0; padding-left: 20px;">
                                            {concerns_html}
                                        </ul>
                                    </div>

                                    <!-- Recommended Action -->
                                    <div style="background: #ecfdf5; border-radius: 6px; padding: 16px;">
                                        <h4 style="color: #065f46; font-size: 14px; font-weight: 600; margin: 0 0 8px 0;">
                                            🎯 Recommended Action
                                        </h4>
                                        <p style="color: #065f46; font-size: 13px; margin: 0;">
                                            {rec_text}
                                        </p>
                                    </div>
                                </div>
                            </div>
'''


def generate_action_items(analysis_results: list[dict]) -> str:
    """Generate the recommended actions section."""
    high_risk = [c for c in analysis_results if c.get("risk_factor") == "high"]
    medium_risk = [c for c in analysis_results if c.get("risk_factor") == "medium"]
    
    actions_html = ""
    
    # High priority actions
    for client in high_risk[:2]:
        client_name = client.get("client_name", "Unknown")
        rec = client.get("recommendations", ["Schedule urgent review"])[0]
        actions_html += f'''
                                <div style="margin-bottom: 12px;">
                                    <div style="padding: 16px; background: #fee2e2; border-radius: 8px; border-left: 4px solid #dc2626;">
                                        <strong style="color: #991b1b; font-size: 15px;">🚨 High Priority - {client_name}</strong>
                                        <p style="color: #991b1b; font-size: 13px; margin: 4px 0 0 0;">{rec}</p>
                                    </div>
                                </div>
'''
    
    # Medium priority actions
    for client in medium_risk[:2]:
        client_name = client.get("client_name", "Unknown")
        rec = client.get("recommendations", ["Schedule check-in"])[0]
        actions_html += f'''
                                <div style="margin-bottom: 12px;">
                                    <div style="padding: 16px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #d97706;">
                                        <strong style="color: #92400e; font-size: 15px;">⚠️ Medium Priority - {client_name}</strong>
                                        <p style="color: #92400e; font-size: 13px; margin: 4px 0 0 0;">{rec}</p>
                                    </div>
                                </div>
'''
    
    if not actions_html:
        actions_html = '''
                                <div style="padding: 16px; background: #d1fae5; border-radius: 8px; border-left: 4px solid #10b981;">
                                    <strong style="color: #065f46; font-size: 15px;">✅ All Clients Healthy</strong>
                                    <p style="color: #065f46; font-size: 13px; margin: 4px 0 0 0;">No urgent actions required. Continue regular check-ins.</p>
                                </div>
'''
    
    return actions_html


def generate_email_html(analysis_results: list[dict], cs_rep_name: str = "Varicon CS Team") -> str:
    """
    Generate the complete HTML email from analysis results.
    
    Uses the exact Varicon email template with dynamic data.
    """
    # Count risks
    high_risk = [c for c in analysis_results if c.get("risk_factor") == "high"]
    medium_risk = [c for c in analysis_results if c.get("risk_factor") == "medium"]
    low_risk = [c for c in analysis_results if c.get("risk_factor") == "low"]
    
    total_clients = len(analysis_results)
    at_risk_count = len(high_risk) + len(medium_risk)
    
    # Calculate average health score
    avg_health = sum(c.get("usage_health_score", 0) for c in analysis_results) / max(total_clients, 1)
    
    # Sort clients by risk
    sorted_clients = high_risk + medium_risk + low_risk
    
    # Generate client cards
    client_cards = ""
    for i, client in enumerate(sorted_clients, 1):
        client_cards += generate_client_card(client, i)
    
    # Generate action items
    action_items = generate_action_items(analysis_results)
    
    # Current date
    report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Client Usage Analytics - Varicon CS Team</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600&family=Roboto+Flex:wght@400;600&display=swap" rel="stylesheet">
</head>
<body style="font-family: 'Roboto Flex', Arial, sans-serif; background-color: #e5f1fc; margin: 0; padding: 20px; min-height: 100vh;">
    <table width="600" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto; background-color: #ffffff; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); border-radius: 8px; overflow: hidden;">
        <!-- Header Section -->
        <tr>
          <td width="100%">
            <table width="100%" cellspacing="0" cellpadding="0" border="0">
              <tr>
                <td width="100%" style="vertical-align: middle; background-color: #ffffff" bgcolor="#ffffff">
                  <table width="100%" border="0" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="vertical-align: middle">
                        <table width="100%" cellspacing="0" cellpadding="0" border="0">
                          <tr>
                            <td style="vertical-align: middle; padding-left: 24px; padding-right: 24px;">
                              <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                <tr><td height="32" style="height: 32px;"></td></tr>
                                <tr>
                                  <td>
                                    <img src="https://mystaticimg.s3.ap-southeast-2.amazonaws.com/icons/varicon-icon.png" width="132" border="0" style="min-width: 132px; width: 132px; height: auto; display: block;" />
                                  </td>
                                </tr>
                                <tr><td height="40" style="height: 40px;"></td></tr>
                              </table>
                            </td>
                          </tr>
                        </table>
                      </td>
                      <td style="vertical-align: middle" width="42">
                        <table cellspacing="0" cellpadding="0" border="0">
                          <tr>
                            <td width="42" align="right" style="height: 126px">
                              <img src="https://mystaticimg.s3.ap-southeast-2.amazonaws.com/icons/right-border.png" width="300" border="0" style="height: auto; display: block;">
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Content Section -->
        <tr>
            <td style="padding: 40px 48px;">
                <table width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td>
                            <!-- CS Representative Header -->
                            <div style="background: #f0f9ff; border-radius: 8px; padding: 24px; margin-bottom: 32px; border-left: 4px solid #3b82f6;">
                                <h2 style="color: #1e40af; font-size: 22px; font-weight: 600; margin: 0 0 8px 0;">
                                    👤 Client Portfolio Analytics
                                </h2>
                                <p style="color: #4b5563; font-size: 15px; margin: 0;">
                                    CS Representative: <strong style="color: #1e40af;">Amir Mitri</strong> • Portfolio Size: {total_clients} Clients
                                </p>
                            </div>

                            <!-- Portfolio Summary Metrics -->
                            <h2 style="color: #233759; font-size: 18px; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">📊 Portfolio Overview</h2>

                            <table width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 32px;">
                                <tr>
                                    <td width="25%" style="padding-right: 8px;">
                                        <div style="background: #f8fafc; border-radius: 8px; padding: 16px; text-align: center; border: 1px solid #e5e7eb; min-height: 80px;">
                                            <div style="font-size: 28px; font-weight: 600; color: #233759; margin: 8px 0;">{total_clients}</div>
                                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase;">Total Clients</div>
                                        </div>
                                    </td>
                                    <td width="25%" style="padding: 0 4px;">
                                        <div style="background: #f8fafc; border-radius: 8px; padding: 16px; text-align: center; border: 1px solid #e5e7eb; min-height: 80px;">
                                            <div style="font-size: 28px; font-weight: 600; color: #dc2626; margin: 8px 0;">{at_risk_count}</div>
                                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase;">At-Risk</div>
                                        </div>
                                    </td>
                                    <td width="25%" style="padding: 0 4px;">
                                        <div style="background: #f8fafc; border-radius: 8px; padding: 16px; text-align: center; border: 1px solid #e5e7eb; min-height: 80px;">
                                            <div style="font-size: 28px; font-weight: 600; color: #233759; margin: 8px 0;">{len(high_risk)}</div>
                                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase;">High Risk</div>
                                        </div>
                                    </td>
                                    <td width="25%" style="padding-left: 8px;">
                                        <div style="background: #f8fafc; border-radius: 8px; padding: 16px; text-align: center; border: 1px solid #e5e7eb; min-height: 80px;">
                                            <div style="font-size: 28px; font-weight: 600; color: #233759; margin: 8px 0;">{avg_health:.0f}%</div>
                                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase;">Avg Health</div>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Client Cards -->
{client_cards}

                            <!-- Weekly Priority Tasks -->
                            <h2 style="color: #233759; font-size: 18px; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">🎯 Recommended Actions</h2>

                            <div style="width: 100%; margin-bottom: 32px;">
{action_items}
                            </div>

                            <!-- CTA Button -->
                            <table width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top: 32px; margin-bottom: 32px;">
                                <tr>
                                    <td align="center">
                                        <a href="https://api-development.varicontest.com.au/cs/feature-module-dashboard/" style="display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px;">
                                            View Detailed Analytics Dashboard
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Footer Note -->
                            <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin-top: 24px; border-top: 1px solid #e5e7eb;">
                                <p style="color: #6b7280; font-size: 12px; text-align: center; margin: 0 0 8px 0;">
                                    <strong>Predictive Client Retention & Engagement AI • Automated Portfolio Analysis</strong>
                                </p>
                                <p style="color: #6b7280; font-size: 11px; text-align: center; margin: 0;">
                                    This report includes analysis for {total_clients} clients.<br>
                                    Generated: {report_date}
                                </p>
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>

        <!-- Footer Section -->
        <tr>
            <td width="100%">
              <table width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td width="100%" style="vertical-align: bottom; background-color: #eaedf1" bgcolor="#eaedf1">
                    <table width="100%" border="0" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="vertical-align: bottom" width="30">
                          <img src="https://mystaticimg.s3.ap-southeast-2.amazonaws.com/email-images/right_pointed_traingle.png" width="57" border="0" style="min-width: 57px; width: 57px; height: auto; display: block;" />
                        </td>
                        <td style="vertical-align: bottom">
                          <table width="100%" cellspacing="0" cellpadding="0" border="0">
                            <tr>
                              <td align="center" style="padding: 24px 48px;">
                                <!-- Social Links -->
                                <table cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 16px;">
                                  <tr>
                                    <td style="padding: 0 16px;">
                                      <a target="_blank" href="https://www.linkedin.com/company/variconconstruction/">
                                        <img src="https://mystaticimg.s3.ap-southeast-2.amazonaws.com/email-images/linked_in.png" width="26" alt="LinkedIn" border="0" />
                                      </a>
                                    </td>
                                    <td style="padding: 0 16px;">
                                      <a target="_blank" href="https://www.facebook.com/variconaustralia/">
                                        <img src="https://mystaticimg.s3.ap-southeast-2.amazonaws.com/email-images/facebook.png" width="26" alt="Facebook" border="0" />
                                      </a>
                                    </td>
                                    <td style="padding: 0 16px;">
                                      <a target="_blank" href="mailto:info@varicon.com.au">
                                        <img src="https://mystaticimg.s3.ap-southeast-2.amazonaws.com/email-images/mail.png" width="26" alt="Email" border="0" />
                                      </a>
                                    </td>
                                  </tr>
                                </table>
                                
                                <!-- Address -->
                                <p style="color: #233759; font-size: 12px; margin: 0 0 16px 0;">
                                  123 Business St, Sydney NSW 2000, Australia
                                </p>
                                
                                <!-- App Store Links -->
                                <table cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 16px;">
                                  <tr>
                                    <td style="padding: 0 8px;">
                                      <a target="_blank" href="https://play.google.com/store/apps/details?id=com.varicon.varicon">
                                        <img src="https://mystaticimg.s3.ap-southeast-2.amazonaws.com/icons/image+4.png" width="125" border="0" />
                                      </a>
                                    </td>
                                    <td style="padding: 0 8px;">
                                      <a target="_blank" href="https://apps.apple.com/us/app/varicon/id1559357669">
                                        <img src="https://mystaticimg.s3.ap-southeast-2.amazonaws.com/icons/image+5.png" width="125" border="0" />
                                      </a>
                                    </td>
                                  </tr>
                                </table>
                                
                                <!-- Links -->
                                <p style="margin: 0 0 16px 0;">
                                  <a href="https://varicon.com.au/" style="color: #5f6d83; font-size: 10px; text-decoration: none; padding: 0 15px;">Visit Us</a>
                                  <a href="https://varicon.com.au/privacy" style="color: #5f6d83; font-size: 10px; text-decoration: none; padding: 0 15px;">Privacy Policy</a>
                                  <a href="https://varicon.com.au/terms" style="color: #5f6d83; font-size: 10px; text-decoration: none; padding: 0 15px;">Terms of Use</a>
                                </p>
                                
                                <!-- Logo -->
                                <a target="_blank" href="https://varicon.com.au">
                                  <img src="https://plugin.markaimg.com/public/74e76c9c/jrcDKL4Yqy8Lsl1p3Nj4e2UxyGNELq.png" width="74" border="0" />
                                </a>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
    </table>
</body>
</html>'''
