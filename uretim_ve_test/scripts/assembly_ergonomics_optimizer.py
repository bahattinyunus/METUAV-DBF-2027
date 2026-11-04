#!/usr/bin/env python3
"""
AIAA DBF 2027 - Rapid Toolless 5-Minute Aircraft Assembly & Ergonomics Optimizer
Models the critical 300-second staging countdown with 2-crew and 3-crew parallel workflow,
component fastener tolerance budgets, and mistake-proofing (Poka-Yoke) verification.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class AssemblyStep:
    step_id: int
    name: str
    crew_role: str        # 'CREW_1', 'CREW_2', 'SAFETY_OFFICER'
    duration_s: float
    is_toolless: bool
    requires_poka_yoke: bool
    torque_checked: bool
    can_run_parallel_with: List[int]


@dataclass
class AssemblyAuditReport:
    total_duration_s: float
    time_limit_s: float
    safety_margin_s: float
    is_compliant: bool
    crew_utilization_pct: Dict[str, float]
    critical_path_steps: List[str]


class AssemblyErgonomicsOptimizer:
    def __init__(self, time_limit_s: float = 300.0):
        self.time_limit = time_limit_s

        # 10 core assembly steps designed for toolless quick-turnaround
        self.steps: List[AssemblyStep] = [
            AssemblyStep(1, "Govde Sandiktan Cikaris & Sehpa Montaji", "CREW_1", 20.0, True, True, False, [2]),
            AssemblyStep(2, "Inis Takimi Karbon Bacak Pin Kitleme", "CREW_2", 22.0, True, True, True, [1]),
            AssemblyStep(3, "Sol Ana Kanat Spar Gecme & Ball-Lock Pin", "CREW_1", 28.0, True, True, True, [4]),
            AssemblyStep(4, "Sag Ana Kanat Spar Gecme & Ball-Lock Pin", "CREW_2", 28.0, True, True, True, [3]),
            AssemblyStep(5, "Kanat Servo Otomatik D-Sub Konnektor Temasi", "CREW_1", 12.0, True, True, False, [6]),
            AssemblyStep(6, "V-Tail / T-Tail Hizli Kilit Mandal Montaji", "CREW_2", 24.0, True, True, True, [5]),
            AssemblyStep(7, "6S 16000mAh Batarya Kizağı Yerlestirme & Kilit", "CREW_1", 18.0, True, True, False, [8]),
            AssemblyStep(8, "Gorev 2/3 Faydali Yuk Kaseti Kitleme", "CREW_2", 16.0, True, True, True, [7]),
            AssemblyStep(9, "Kabin Ust Kapak Manyetik Mandal Kapatma", "CREW_1", 8.0, True, True, False, [10]),
            AssemblyStep(10, "Guvenlik Pimi Cikarisi & Son Aviyonik Boot Teyidi", "SAFETY_OFFICER", 15.0, True, True, True, [9]),
        ]

    def calculate_parallel_assembly_timeline(self) -> AssemblyAuditReport:
        """
        Calculates total makespan (wall-clock duration) with 2 primary crew members + 1 safety officer.
        """
        # Critical path calculation
        # Step 1 & 2 run parallel: max(20, 22) = 22s
        # Step 3 & 4 run parallel: max(28, 28) = 28s
        # Step 5 & 6 run parallel: max(12, 24) = 24s
        # Step 7 & 8 run parallel: max(18, 16) = 18s
        # Step 9 & 10 run parallel/finish: max(8, 15) = 15s
        # Contingency & verification margin: +15s

        t1_2 = max(self.steps[0].duration_s, self.steps[1].duration_s)
        t3_4 = max(self.steps[2].duration_s, self.steps[3].duration_s)
        t5_6 = max(self.steps[4].duration_s, self.steps[5].duration_s)
        t7_8 = max(self.steps[6].duration_s, self.steps[7].duration_s)
        t9_10 = max(self.steps[8].duration_s, self.steps[9].duration_s)
        t_contingency = 15.0

        total_makespan = t1_2 + t3_4 + t5_6 + t7_8 + t9_10 + t_contingency

        crew1_work = self.steps[0].duration_s + self.steps[2].duration_s + self.steps[4].duration_s + self.steps[6].duration_s + self.steps[8].duration_s
        crew2_work = self.steps[1].duration_s + self.steps[3].duration_s + self.steps[5].duration_s + self.steps[7].duration_s
        safety_work = self.steps[9].duration_s

        utilization = {
            "CREW_1": round((crew1_work / total_makespan) * 100.0, 1),
            "CREW_2": round((crew2_work / total_makespan) * 100.0, 1),
            "SAFETY_OFFICER": round((safety_work / total_makespan) * 100.0, 1)
        }

        critical_path = [s.name for s in self.steps if s.duration_s >= 20.0]

        return AssemblyAuditReport(
            total_duration_s=total_makespan,
            time_limit_s=self.time_limit,
            safety_margin_s=self.time_limit - total_makespan,
            is_compliant=total_makespan <= self.time_limit,
            crew_utilization_pct=utilization,
            critical_path_steps=critical_path
        )
