"""
Signal placeholder — auto-trigger AI analysis after a JournalEntry is created.

To activate, call mood.apps.MoodConfig.ready() or import this module in AppConfig.ready().
"""
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import JournalEntry
# from .tasks import analyze_entry
#
# @receiver(post_save, sender=JournalEntry, dispatch_uid="trigger_mood_ai")
# def on_entry_created(sender, instance, created, **kwargs):
#     if created:
#         analyze_entry(instance.id)   # swap for analyze_entry.delay() with Celery
