"""
OnTrack AI — MoSPI PAIMANA Data Integration Service
Smart India Hackathon 2026 | Problem Statement: SIH26103

Provides data access, live sync, and normalization for the official Ministry of
Statistics and Programme Implementation (MoSPI) PAIMANA Central Sector Projects dataset.
"""

import os
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ontrack.paimana")

NUMERIC_FIELDS = {
    "Approved_Cost",
    "Planned_Duration",
    "Elapsed_Duration",
    "Physical_Progress",
    "Planned_Progress",
    "Financial_Progress",
    "Expenditure",
    "Milestones_Total",
    "Milestones_Delayed",
    "Average_Milestone_Delay_Days",
    "Procurement_Delay_Days",
    "Land_Acquisition_Progress",
    "Approvals_Pending",
    "Scope_Changes",
    "Time_Overrun_Months",
    "Cost_Overrun_Pct",
    "Time_Overrun_Flag",
    "Cost_Overrun_Flag",
    "Implementation_Risk_Flag",
}

class PaimanaService:
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.base_dir = Path(__file__).resolve().parents[1]
            self.paimana_dir = self.base_dir / "data" / "paimana"
        else:
            self.paimana_dir = Path(data_dir)

        self.normalized_csv = self.paimana_dir / "paimana_normalized.csv"
        self.raw_json = self.paimana_dir / "paimana_raw_projects.json"
        self.raw_csv = self.paimana_dir / "paimana_projects.csv"
        self.metadata_file = self.paimana_dir / "PAIMANA_METADATA.md"

        self._cached_projects: Optional[List[Dict[str, Any]]] = None
        self._cached_mtime: Optional[float] = None

    def is_available(self) -> bool:
        """Checks if the normalized PAIMANA dataset exists on disk and is non-empty."""
        return self.normalized_csv.exists() and self.normalized_csv.stat().st_size > 100

    def get_source_metadata(self) -> Dict[str, Any]:
        """Returns standard metadata for the PAIMANA data source."""
        available = self.is_available()
        count = len(self.load_projects()) if available else 0
        return {
            "source": "sih",
            "source_name": "MoSPI PAIMANA Official Infrastructure Projects",
            "is_synthetic": False,
            "is_available": available,
            "project_count": count,
            "snapshot_date": "August 2026",
            "portal_url": "https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew",
            "report_page": "https://paimana-proj.mospi.gov.in/ReportPage",
            "status": "CONNECTED" if available else "REQUIRES DATA FILE",
        }

    def load_projects(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """
        Loads and returns all normalized PAIMANA projects.
        Caches in memory for fast API responses; auto-reloads if file changes.
        """
        if not self.is_available():
            raise FileNotFoundError(
                f"PAIMANA normalized dataset not found at: {self.normalized_csv}. "
                f"Please ensure data/paimana/paimana_normalized.csv is present."
            )

        current_mtime = self.normalized_csv.stat().st_mtime
        if (
            not force_reload
            and self._cached_projects is not None
            and self._cached_mtime == current_mtime
        ):
            return self._cached_projects

        projects = []
        with self.normalized_csv.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                proj = {}
                for key, val in row.items():
                    if val is None or val == "":
                        proj[key] = None
                    elif key in NUMERIC_FIELDS:
                        try:
                            num = float(val)
                            proj[key] = int(num) if num.is_integer() else num
                        except ValueError:
                            proj[key] = None
                    else:
                        proj[key] = val
                projects.append(proj)

        self._cached_projects = projects
        self._cached_mtime = current_mtime
        logger.info(f"Loaded {len(projects)} PAIMANA projects into memory.")
        return projects

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Finds a single PAIMANA project by Project_ID."""
        clean_id = project_id.strip()
        for p in self.load_projects():
            if str(p.get("Project_ID", "")).strip() == clean_id:
                return p
        return None

# Global singleton service instance
paimana_service = PaimanaService()
