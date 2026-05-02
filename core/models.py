from django.db import models

class BaseModel(models.Model):
	"""Abstract base model providing common timestamp fields.

	Kept intentionally minimal so apps can inherit without extra
	dependencies. Add fields here if you need common behavior.
	"""

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True
