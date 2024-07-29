import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class Broadcaster(AbstractUser):
    id = models.UUIDField(
        default=uuid.uuid4,
        primary_key=True,
        editable=False
    )
    customer_id = models.TextField(null=True)
