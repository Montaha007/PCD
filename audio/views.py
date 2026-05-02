# audiotherapy/views.py
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import DisorderRecommendation, Disorder, BrainwaveType


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_recommendations(request):
    """
    GET /api/audio/recommendations/?disorder=high_anxiety
    Returns the recommended brainwave band + frequency for the given disorder.
    """
    disorder = request.GET.get('disorder', Disorder.HIGH_ANXIETY).lower()

    if disorder not in [d.value for d in Disorder]:
        return Response(
            {"error": f"Invalid disorder '{disorder}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    recs = (
        DisorderRecommendation.objects
        .filter(disorder=disorder)
        .order_by('priority')
    )
    if not recs.exists():
        return Response(
            {"error": f"No recommendation configured for '{disorder}'."},
            status=status.HTTP_404_NOT_FOUND,
        )

    primary = recs.first()
    alternatives = [
        {
            'brainwave':           r.brainwave,
            'brainwave_display':   r.get_brainwave_display(),
            'target_frequency_hz': r.target_frequency_hz,
            'carrier_frequency_hz': r.carrier_frequency_hz,
            'rationale':           r.rationale,
        }
        for r in recs[1:]
    ]

    return Response({
        'disorder':                  disorder,
        'disorder_display':          dict(Disorder.choices)[disorder],
        'primary_brainwave':         primary.brainwave,
        'primary_brainwave_display': primary.get_brainwave_display(),
        'target_frequency_hz':       primary.target_frequency_hz,
        'carrier_frequency_hz':      primary.carrier_frequency_hz,
        'rationale':                 primary.rationale or 'Recommended for your current state.',
        'alternatives':              alternatives,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_disorders(request):
    preferred = [
        Disorder.HIGH_ANXIETY,
        Disorder.INSOMNIA,
        Disorder.LOW_MOOD,
        Disorder.OVERWHELMED,
    ]
    return Response([
        {'value': d.value, 'label': d.label}
        for d in preferred
    ])