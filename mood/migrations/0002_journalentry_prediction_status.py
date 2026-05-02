from django.db import migrations, models


PREDICTION_STATUS_MAP = {
    "normal": "NORMAL",
    "anxiety": "ANXIETY",
    "depression": "DEPRESSION",
    "stress": "STRESS",
    "bipolar": "BIPOLAR",
    "suicidal": "SUICIDAL",
    "personality disorder": "PERSONALITY_DISORDER",
}

PREDICTION_STATUSES = [
    "NORMAL",
    "ANXIETY",
    "DEPRESSION",
    "STRESS",
    "BIPOLAR",
    "SUICIDAL",
    "PERSONALITY_DISORDER",
]


def forward_fill_prediction_status(apps, schema_editor):
    JournalEntry = apps.get_model("mood", "JournalEntry")

    queryset = (
        JournalEntry.objects
        .filter(status="COMPLETED")
        .exclude(predicted_mood__isnull=True)
        .exclude(predicted_mood__exact="")
    )

    for entry in queryset.iterator(chunk_size=200):
        status_value = PREDICTION_STATUS_MAP.get(entry.predicted_mood.strip().lower())
        if status_value:
            entry.status = status_value
            entry.save(update_fields=["status"])


def backward_restore_completed(apps, schema_editor):
    JournalEntry = apps.get_model("mood", "JournalEntry")
    JournalEntry.objects.filter(status__in=PREDICTION_STATUSES).update(status="COMPLETED")


class Migration(migrations.Migration):

    dependencies = [
        ("mood", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journalentry",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("PROCESSING", "Processing"),
                    ("COMPLETED", "Completed"),
                    ("FAILED", "Failed"),
                    ("NORMAL", "Normal"),
                    ("ANXIETY", "Anxiety"),
                    ("DEPRESSION", "Depression"),
                    ("STRESS", "Stress"),
                    ("BIPOLAR", "Bipolar"),
                    ("SUICIDAL", "Suicidal"),
                    ("PERSONALITY_DISORDER", "Personality Disorder"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.RunPython(forward_fill_prediction_status, backward_restore_completed),
    ]
