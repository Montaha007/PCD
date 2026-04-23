"""
Async task placeholders — wire up Celery here when ready.

Example flow:
    1. views.py calls trigger_ai_analysis(entry.id)
    2. trigger_ai_analysis dispatches analyze_entry.delay(entry_id)
    3. Worker calls ai.services.analyze_journal_entry(entry_id)
    4. Worker updates entry.predicted_mood / analysis_text / status
"""


def analyze_entry(entry_id: int) -> None:
    # from mood.models import JournalEntry
    # from ai.services import analyze_journal_entry
    #
    # entry = JournalEntry.objects.get(pk=entry_id)
    # entry.status = JournalEntry.Status.PROCESSING
    # entry.save(update_fields=["status"])
    #
    # try:
    #     result = analyze_journal_entry(entry.content)
    #     entry.predicted_mood = result["mood"]
    #     entry.analysis_text  = result["analysis"]
    #     entry.status         = JournalEntry.Status.COMPLETED
    # except Exception:
    #     entry.status = JournalEntry.Status.FAILED
    # finally:
    #     entry.save(update_fields=["predicted_mood", "analysis_text", "status"])
    pass
