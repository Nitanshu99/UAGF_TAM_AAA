"""Annex III points 1-4, by sub-point: what each covers and the terms that evidence it.

A term ending in ``*`` matches any word it begins (``recruit*`` → "recruiters").
The ``"*"`` key holds section-level terms that evidence the section without
identifying a sub-point. The pre-existing keyword lists are kept inside these
sets, so no system matched before goes unmatched now.
"""
from __future__ import annotations

POINTS_1_TO_4: dict[str, tuple[str, dict[str, tuple[str, tuple[str, ...]]]]] = {
    "1": ("Biometrics (remote ID, categorisation, emotion recognition)", {
        "a": ("remote biometric identification", ("remote biometric identification",
              "biometric identification", "facial recognition", "face recognition", "face",
              "fingerprint*", "iris", "gait", "voice identification")),
        "b": ("biometric categorisation by sensitive attributes",
              ("biometric categori*",)),
        "c": ("emotion recognition", ("emotion recognition", "emotion detection")),
        "*": ("", ("biometric",)),
    }),
    "2": ("Critical infrastructure (energy, water, traffic management)", {
        "a": ("safety component of critical infrastructure", ("critical infrastructure",
              "energy grid", "power grid", "water management", "water supply", "gas supply",
              "electricity supply", "traffic management", "road traffic",
              "transportation infrastructure", "digital infrastructure")),
    }),
    "3": ("Education and vocational training", {
        "a": ("access, admission or assignment to education or vocational training",
              ("admission*", "vocational training", "apprentic*", "dual stud*",
               "educational institution", "school", "university", "enrol*")),
        "b": ("evaluation of learning outcomes", ("learning outcome*", "grading", "exam",
              "exams", "student assessment")),
        "c": ("assessment of the appropriate level of education", ("level of education",
              "placement test*")),
        "d": ("monitoring prohibited behaviour during tests", ("proctor*", "cheating")),
        "*": ("", ("education", "educational", "student*", "learner*")),
    }),
    "4": ("Employment, workers management, self-employment", {
        "a": ("recruitment or selection of natural persons", ("recruitment", "recruit*",
              "hiring", "job candidate*", "candidate profile*", "applicant*", "cv screening",
              "resume screening", "shortlist*", "job advert*", "vacanc*")),
        "b": ("decisions on work relationships, promotion, termination, tasks, performance",
              ("promotion*", "dismissal*", "task allocation", "worker monitoring",
               "performance scoring", "performance evaluation", "employee monitoring")),
        "*": ("", ("employment", "self-employment", "employer*", "workforce",
                   "human resources")),
    }),
}
