from django.db import migrations


def seed_recommendations(apps, schema_editor):
    DisorderRecommendation = apps.get_model('audio', 'DisorderRecommendation')

    def upsert(disorder, brainwave, target_hz, carrier_hz, priority, rationale):
        DisorderRecommendation.objects.update_or_create(
            disorder=disorder,
            brainwave=brainwave,
            defaults={
                'target_frequency_hz': target_hz,
                'carrier_frequency_hz': carrier_hz,
                'priority': priority,
                'rationale': rationale,
            },
        )

    # High anxiety / racing thoughts
    upsert(
        'high_anxiety',
        'theta',
        6.0,
        165.0,
        1,
        'Theta (4-7 Hz) supports calm and reduces anxiety before sleep.',
    )
    upsert(
        'high_anxiety',
        'alpha',
        10.0,
        375.0,
        2,
        'Alpha (8-13 Hz) encourages positivity and gentle relaxation.',
    )

    # Chronic insomnia / trouble staying asleep
    upsert(
        'insomnia',
        'delta',
        3.0,
        200.0,
        1,
        'Delta (0.5-4 Hz) supports deep, restorative sleep.',
    )

    # Depression / low energy
    upsert(
        'low_mood',
        'alpha',
        9.0,
        200.0,
        1,
        'Low alpha (8-10 Hz) balances mood while staying calm.',
    )
    upsert(
        'low_mood',
        'theta',
        5.0,
        200.0,
        2,
        'Theta (4-8 Hz) eases emotional tension and supports rest.',
    )

    # Overwhelmed mind / adrenal fatigue
    upsert(
        'overwhelmed',
        'theta',
        4.5,
        200.0,
        1,
        'Low theta (4-5 Hz) helps the body rest while quieting the mind.',
    )


def unseed_recommendations(apps, schema_editor):
    DisorderRecommendation = apps.get_model('audio', 'DisorderRecommendation')
    DisorderRecommendation.objects.filter(
        disorder__in=['high_anxiety', 'insomnia', 'low_mood', 'overwhelmed']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('audio', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_recommendations, unseed_recommendations),
    ]
