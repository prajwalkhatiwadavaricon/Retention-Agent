"""Data models for the Retention Analysis Agent."""

from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    """Risk level classification for clients."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Activity:
    """A single activity record."""
    name: str
    count: int


@dataclass
class WeeklyUsage:
    """Weekly usage data for a client."""
    start_range: str
    end_range: str
    previous_activity_week: str
    current_activity_week: str
    activities: list[Activity] = field(default_factory=list)


@dataclass
class ClientUsage:
    """Complete usage data for a client."""
    client_name: str
    usage: list[WeeklyUsage] = field(default_factory=list)


@dataclass
class JiraTicket:
    """Simplified JIRA ticket data."""
    id: str
    key: str
    client_name: str
    summary: str
    description: str
    priority: str
    status: str
    created: str
    updated: str
    affected_modules: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)


@dataclass
class ClientAnalysisResult:
    """Analysis result for a single client."""
    client_name: str
    risk_factor: str  # high/medium/low
    probability: float  # 0-100 churn probability
    total_modules_used: int
    most_used_modules: list[str]
    least_used_modules: list[str]
    most_bug_prone_modules: list[str]
    usage_trend: str  # increasing/decreasing/stable
    usage_health_score: float  # 0-100
    expected_vs_actual: dict  # comparison
    recommendations: list[str]
    detailed_analysis: str

