from django.db import models
from django.conf import settings


class Profile(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="profile",
	)
	timezone = models.CharField(max_length=64, default="UTC")
	language = models.CharField(max_length=32, default="en")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Profile for {self.user.email}"
