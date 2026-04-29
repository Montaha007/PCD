# management/commands/seed_audio.py
from django.core.management.base import BaseCommand
from audio.models import DisorderRecommendation, Disorder, BrainwaveType


# (disorder, brainwave, priority, target_freq, carrier, rationale)
RECOMMENDATIONS = [
    (Disorder.ANXIETY,     BrainwaveType.ALPHA, 1, 10.0, 200.0, 'Alpha at 10 Hz promotes relaxed alertness and reduces anxiety.'),
    (Disorder.ANXIETY,     BrainwaveType.THETA, 2, 6.0,  150.0, 'Theta at 6 Hz deepens relaxation and reduces mental chatter.'),

    (Disorder.DEPRESSION,  BrainwaveType.BETA,  1, 18.0, 250.0, 'Beta at 18 Hz boosts alertness and counteracts depressive lethargy.'),
    (Disorder.DEPRESSION,  BrainwaveType.ALPHA, 2, 10.0, 200.0, 'Alpha at 10 Hz balances mood and eases emotional weight.'),

    (Disorder.STRESS,      BrainwaveType.ALPHA, 1, 8.0,  180.0, 'Alpha at 8 Hz induces calm and lowers cortisol.'),
    (Disorder.STRESS,      BrainwaveType.DELTA, 2, 2.5,  100.0, 'Delta at 2.5 Hz promotes deep restorative rest.'),

    (Disorder.BIPOLAR,     BrainwaveType.ALPHA, 1, 10.0, 200.0, 'Alpha at 10 Hz helps stabilize mood swings.'),
    (Disorder.BIPOLAR,     BrainwaveType.THETA, 2, 6.0,  150.0, 'Theta at 6 Hz supports emotional regulation.'),

    (Disorder.SUICIDAL,    BrainwaveType.ALPHA, 1, 10.0, 200.0, 'Alpha at 10 Hz promotes calm and grounding.'),
    (Disorder.SUICIDAL,    BrainwaveType.THETA, 2, 7.0,  160.0, 'Theta at 7 Hz reduces intrusive negative thoughts.'),

    (Disorder.PERSONALITY, BrainwaveType.ALPHA, 1, 10.0, 200.0, 'Alpha at 10 Hz supports emotional balance.'),
    (Disorder.PERSONALITY, BrainwaveType.BETA,  2, 15.0, 220.0, 'Beta at 15 Hz enhances focus and self-awareness.'),

    (Disorder.NORMAL,      BrainwaveType.DELTA, 1, 2.0,  100.0, 'Delta at 2 Hz supports deep sleep and recovery.'),
    (Disorder.NORMAL,      BrainwaveType.ALPHA, 2, 10.0, 200.0, 'Alpha at 10 Hz helps unwind before bed.'),
]


class Command(BaseCommand):
    help = 'Seed audio therapy recommendations'

    def handle(self, *args, **options):
        for disorder, brainwave, priority, target, carrier, rationale in RECOMMENDATIONS:
            DisorderRecommendation.objects.update_or_create(
                disorder=disorder, brainwave=brainwave,
                defaults={
                    'priority': priority,
                    'target_frequency_hz': target,
                    'carrier_frequency_hz': carrier,
                    'rationale': rationale,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(RECOMMENDATIONS)} recommendations.'))
