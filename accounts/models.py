from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class CustomUserManager(BaseUserManager):
    """
    The 'factory' that knows how to build a User object.
    Django requires this when you use AbstractBaseUser.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hashes the password — never store raw
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    class GenderChoices(models.TextChoices):
        MALE           = "M",  "Male"
        FEMALE         = "F",  "Female"
        PREFER_NOT     = "X",  "Prefer not to say"

    # ── Identity ──────────────────────────────────────────────
    full_name   = models.CharField(max_length=150)
    age         = models.PositiveSmallIntegerField()          # e.g. 0–32767, enough
    gender      = models.CharField(
                      max_length=1,
                      choices=GenderChoices.choices,
                  )
    country     = models.CharField(max_length=100)            # "pays" → country

    # ── Auth ──────────────────────────────────────────────────
    email       = models.EmailField(unique=True)              # the login key
    # password is inherited from AbstractBaseUser (already hashed)
    insomnia_duration_years = models.PositiveSmallIntegerField(
        default=0,
        help_text="How many years the user has been experiencing insomnia."
    )
    # ── Preferences ───────────────────────────────────────────
    notifications_enabled = models.BooleanField(default=False)

    # ── Django internals ──────────────────────────────────────
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)          # can access /admin
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD  = "email"    # email is now the login identifier
    REQUIRED_FIELDS = [          # asked when using createsuperuser command
        "full_name", "age", "gender", "country"
    ]

    class Meta:
        verbose_name        = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.full_name} ({self.email})"