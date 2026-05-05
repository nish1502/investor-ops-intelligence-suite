import dateparser
from datetime import datetime
import re

def parse_natural_date(date_string):
    """
    Strictly parses natural language dates.
    Requirements:
    - Prefer Month-Day format (e.g., June 15 over 15 June if ambiguous, though June 15 is clear)
    - Output YYYY-MM-DD
    - Reject if in the past
    - Detect ambiguity (though dateparser is quite deterministic, we can add a check)
    """
    if not date_string:
        return None, None

    # Settings to enforce Month-Day interpretation when ambiguous (e.g. 06/05)
    settings = {
        'DATE_ORDER': 'MDY',
        'PREFER_DATES_FROM': 'future',
        'RELATIVE_BASE': datetime.now()
    }

    # Pre-process: some parsers struggle with "next" + day
    clean_date_str = date_string.lower().strip()
    if clean_date_str.startswith("next "):
        clean_date_str = clean_date_str.replace("next ", "", 1)

    parsed_date = dateparser.parse(clean_date_str, settings=settings, languages=['en'])
    
    if not parsed_date and date_string != clean_date_str:
        # Try original if clean failed (shouldn't happen but safe)
        parsed_date = dateparser.parse(date_string, settings=settings, languages=['en'])

    if not parsed_date:
        return None, "I couldn't quite catch that date. Could you specify it like 'June 15'?"

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # If the year wasn't specified, dateparser might default to current year.
    # If that date has already passed, we might want the next year.
    if parsed_date < today:
        if parsed_date.year == today.year:
            parsed_date = parsed_date.replace(year=today.year + 1)
        else:
            return None, f"The date {parsed_date.strftime('%Y-%m-%d')} has already passed. Please pick a future date."

    # Ambiguity check: if the input is purely numeric like "06/05", it's ambiguous.
    # Natural language like "June 15" or "15 June" is NOT ambiguous in intent.
    # We only care about ambiguity that leads to wrong results.
    # Since we enforced MDY, 06/05 becomes June 5th.
    
    # The requirement says: If ambiguous -> ask clarification: "Did you mean June 15 or 15 June?"
    # This usually refers to numeric formats.
    if re.match(r'^\d{1,2}[/-]\d{1,2}$', date_string.strip()):
         return None, f"I see you provided '{date_string}'. To be sure, did you mean {parsed_date.strftime('%B %d')}? Please specify like 'June 15'."

    return parsed_date.strftime('%Y-%m-%d'), None
