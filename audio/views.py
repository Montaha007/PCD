# audio/views.py
# ============================================================================
# Endpoints:
#
#   GET /api/audio/recommendation/           ← what the Audio page calls.
#                                              Reads from latest DailyProgress.
#   GET /api/audio/recommendation/manual/?disorder=anxiety   ← debug / "explore" UI
#   GET /api/audio/disorders/                ← enum dropdown
# ============================================================================
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from audio.models import Disorder, DisorderRecommendation
from audio.services import recommend_audio_for_user


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_personalised_recommendation(request):
    """
    GET /api/audio/recommendation/

    Returns the audio therapy recommendation derived from the user's latest
    completed DailyProgress (Agent 3's final_output). If no completed run
    exists yet, returns the NORMAL preset so the audio page is never empty.
    """
    rec = recommend_audio_for_user(request.user)
    return Response(rec.to_dict())


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_manual_recommendation(request):
    """
    GET /api/audio/recommendation/manual/?disorder=anxiety

    Kept for an optional "explore other tracks" UI affordance and for
    debugging. The personalised endpoint above is what the audio page
    should call by default.
    """
    disorder = (request.GET.get("disorder") or Disorder.NORMAL).lower()

    valid = [d.value for d in Disorder]
    if disorder not in valid:
        return Response(
            {"error": f"Invalid disorder '{disorder}'. Must be one of {valid}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    recs = (
        DisorderRecommendation.objects
        .filter(disorder=disorder)
        .order_by("priority")
    )
    if not recs.exists():
        return Response(
            {"error": f"No recommendation configured for '{disorder}'."},
            status=status.HTTP_404_NOT_FOUND,
        )

    primary = recs.first()
    alternatives = [
        {
            "brainwave":            r.brainwave,
            "brainwave_display":    r.get_brainwave_display(),
            "target_frequency_hz":  r.target_frequency_hz,
            "carrier_frequency_hz": r.carrier_frequency_hz,
            "rationale":            r.rationale,
        }
        for r in recs[1:]
    ]

    return Response({
        "disorder":                  disorder,
        "disorder_display":          dict(Disorder.choices)[disorder],
        "primary_brainwave":         primary.brainwave,
        "primary_brainwave_display": primary.get_brainwave_display(),
        "target_frequency_hz":       primary.target_frequency_hz,
        "carrier_frequency_hz":      primary.carrier_frequency_hz,
        "rationale":                 primary.rationale or "Recommended for your current state.",
        "alternatives":              alternatives,
        "source_stage":              "manual",
    })


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_disorders(request):
    """GET /api/audio/disorders/  — enum values for any UI dropdown."""
    return Response([
        {"value": d.value, "label": d.label}
        for d in Disorder
    ])