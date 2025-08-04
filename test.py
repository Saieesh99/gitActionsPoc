import boto3
import json
from datetime import datetime

client = boto3.client("connect", region_name="us-east-1")

instance_id = "125d4a4f-946b-4b2d-aae7-7f7ee3be569c"
security_profile_name = "MyCustomSecurityProfile12"

permissions = [
    "RoutingPolicies.View",
    "TransferDestinations.View",
    "HoursOfOperation.View",
    "Queues.View",
    "PhoneNumbers.View",
    "Users.View",
    "AgentStates.View",
    "BasicAgentAccess",
    "RealtimeContactLens.View",
    "OutboundCallAccess",
    "AccessMetrics",
    "AccessMetrics.RealTimeMetrics.Access",
    "AccessMetrics.HistoricalMetrics.Access",
    "AccessMetrics.AgentActivityAudit.Access",
    "AccessMetrics.Dashboards.Access",
    "AccessMetrics.DashboardsWithMyData.View",
    "ContactSearch.View",
    "MyContacts.View",
    "ContactSearchWithCharacteristics.Access",
    "ContactSearchWithCharacteristics.View",
    "ContactSearchWithKeywords.Access",
    "ContactSearchWithKeywords.View",
    "ConfigureContactAttributes.View",
    "ContactAttributes.View",
    "GraphTrends.View",
    "ContactLensPostContactSummary.View",
    "RedactedData.View",
    "AgentTimeCard.View",
    "ManagerListenIn",
    "ListenCallRecordings",
    "MetricsReports.View"
    ]

response = client.create_security_profile(
    InstanceId=instance_id,
    SecurityProfileName=security_profile_name,
    Permissions=permissions,
    Description="Custom security profile with all required permissions",
    Tags={
        "Environment": "dev"
    }
)

print("Security profile created:", response["SecurityProfileId"])
