import os
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


client = genai.Client(
    api_key=os.environ["GOOGLE_API_KEY"]
)

# ✅ Prompt must be defined BEFORE model call
prompt = """
You are an expert Customer Success and Retention Analyst for Varicon, a civil construction SaaS platform.
Your role is to analyze client usage data and bug tickets to identify churn risk and provide actionable insights
and generate the content as a solution to boost the client engagement and retention using the following data:
Analyse the problem of the client and their usage of the modules that are here:
Varicon is a comprehensive construction management platform with 14 core modules:
1. Timesheets - Track employee work hours
2. Claims - Submit and manage claims (typically end of month)
3. Tasks - Task management and assignments
4. Purchase Orders - Procurement management
5. Delivery Dockets - Track material deliveries
6. Site Diaries - Daily site documentation
7. Cost Tracking - Project cost management
8. Reports - Analytics and reporting
9. Bills - Invoice and billing management
10. Scheduling - Project and resource scheduling
11. Dashboard - Overview and KPIs
12. Daywork Dockets - Day-based work documentation
13. Variations - Change order management
14. Custom Forms - Customizable data collection forms
15. Suppliers - Supplier management

Based on these the below client might have the issue and make a meaningful solution to boost the client engagement and retention.
Make sure to generate the content in a way that is easy to understand and follow and also make sure to use the data to generate the content as a marketing strategy.

{
    "client_name": "NEWMYOB",
    "risk_factor": "high",
    "churn_probability": 100,
    "total_usage_count": 0,
    "total_modules_used": 0,
    "active_modules": [],
    "most_used_modules": [],
    "least_used_modules": [],
    "usage_trend": "inactive",
    "trend_percentage": 0.0,
    "weeks_active": 0,
    "bug_tickets_affecting": [],
    "usage_health_score": 0,
    "key_concerns": [
      "Extremely low usage volume (0.0% of benchmark).",
      "Limited module breadth (0 modules used, below the 4-module stability threshold).",
      "Client is completely inactive for the entire 12-week period.",
      "Very low engagement, active in only 0 out of 12 weeks."
    ],
    "recommendations": [
      "Conduct an urgent outreach to understand current platform utilization and identify any blockers or unmet needs.",
      "Identify key workflows not being utilized and offer targeted training or use-case demonstrations.",
      "Immediate investigation to confirm client status and potential churn. Urgent outreach required if still a client.",
      "Explore opportunities to integrate Varicon more deeply into daily operations and provide regular touchpoints."
    ],
    "summary": "NEWMYOB shows a high churn risk. Total usage of 0 activities is very low compared to the benchmark. Only 0 modules were used, indicating narrow adoption. The client has been completely inactive for the entire 12-week period. The client was active in 0 out of 12 weeks."
  }
}
"""

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
)

for part in response.parts:
    if part.text:
        print(part.text)
    elif part.inline_data:
        image = part.as_image()
        image.save("generated_image_2.png")
