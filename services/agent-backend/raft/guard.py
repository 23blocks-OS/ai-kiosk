"""Child-dose guard, from Lifeboat app/server.py. It runs in code on the finished answer."""
import re

_CHILD = re.compile(r"\b(child|children|kids?|son|daughter|toddler|baby|infant|newborn|grand(son|daughter|kid))\b"
                    r"|\b(\d{1,2})[- ]?(month|week)s?[- ]old\b|\b([1-9]|1[0-2])[- ]?(year|yr)s?[- ]old\b", re.I)
_DOSE = re.compile(r"\d\s*(mg|mcg|ml|tablets?|tabs?|teaspoons?|tsp|capsules?)\b", re.I)
_ADULT_MAX = [(re.compile(r"acetaminophen|paracetamol|tylenol", re.I),
               re.compile(r"\b[34],?000\s*mg|\b[34]\s*g\b|\b8 tablets\b", re.I), "acetaminophen"),
              (re.compile(r"ibuprofen|advil|motrin", re.I),
               re.compile(r"\b(1,?200|2,?400|3,?200)\s*mg", re.I), "ibuprofen")]

WARNING = ("Child dose: check the amount and the daily limit against the source passage before you "
           "give it. A child's daily limit is much lower than an adult's.")


def dose_warning(question, answer):
    """Return a warning text, or None."""
    if not (_CHILD.search(question) and _DOSE.search(answer)):
        return None
    msg = WARNING
    for drug, adult, name in _ADULT_MAX:
        if drug.search(answer) and adult.search(answer):
            msg = (f"This answer mentions an adult daily maximum for {name}. Do not use it for a child. "
                   "Use the child's dose times the doses per day in the source, and check the source passage. " + msg)
    return msg
