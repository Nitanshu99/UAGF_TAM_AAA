"""Annex III points 5-8, by sub-point. Same conventions as :mod:`.first_half`."""
from __future__ import annotations

POINTS_5_TO_8: dict[str, tuple[str, dict[str, tuple[str, tuple[str, ...]]]]] = {
    "5": ("Access to essential private/public services and benefits", {
        "a": ("eligibility for public assistance benefits and services",
              ("benefits eligibility", "public assistance", "social assistance",
               "social benefit*", "public service")),
        "b": ("creditworthiness or credit score", ("credit scoring", "credit score*",
              "creditworthiness", "credit", "loan", "loans")),
        "c": ("risk assessment and pricing in life and health insurance",
              ("life insurance", "health insurance", "insurance")),
        "d": ("evaluation and dispatch of emergency calls, patient triage",
              ("emergency call*", "emergency service", "triage")),
        "*": ("", ("essential service", "finance", "banking")),
    }),
    "6": ("Law enforcement", {
        "a": ("risk of a natural person becoming a victim", ("risk of becoming a victim",)),
        "b": ("polygraphs and similar tools", ("polygraph*", "lie detect*")),
        "c": ("reliability of evidence", ("evidence assessment", "reliability of evidence")),
        "d": ("risk of offending or re-offending", ("risk assessment of offenders",
              "reoffend*", "re-offend*", "recidivism", "predictive policing")),
        "e": ("profiling in detection, investigation or prosecution",
              ("judicial investigation", "criminal investigation", "prosecution")),
        "*": ("", ("law enforcement", "police", "crime", "criminal")),
    }),
    "7": ("Migration, asylum, border control", {
        "a": ("polygraphs and similar tools", ("polygraph*",)),
        "b": ("risk assessment of persons entering a Member State",
              ("irregular migration",)),
        "c": ("examination of asylum, visa and residence permit applications",
              ("asylum", "visa", "residence permit*", "refugee")),
        "d": ("detecting, recognising or identifying persons", ("border control",
              "border management", "document authenticity")),
        "*": ("", ("migration", "immigration")),
    }),
    "8": ("Administration of justice and democratic processes", {
        "a": ("assisting judicial authorities with facts and law", ("judiciary", "judicial",
              "court", "legal decision", "administration of justice", "dispute resolution")),
        "b": ("influencing elections, referenda or voting behaviour", ("electoral",
              "election*", "referend*", "voting behaviour", "democratic process")),
    }),
}
