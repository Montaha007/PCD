from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Profile
from .serializers import ProfileSerializer


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def my_profile(request):
	profile, _ = Profile.objects.get_or_create(user=request.user)

	if request.method == "GET":
		serializer = ProfileSerializer(profile)
		return Response(serializer.data, status=status.HTTP_200_OK)

	serializer = ProfileSerializer(profile, data=request.data, partial=True)
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status=status.HTTP_200_OK)

	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
