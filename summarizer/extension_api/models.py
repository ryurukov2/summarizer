from django.db import models
from ..auth_app.models import Account
class Summaries(models.Model):
    Models_choices = models.TextChoices("gpt-3.5-turbo", "gpt-4")

    account_id = models.ForeignKey(to=Account, on_delete=models.DO_NOTHING)
    date = models.DateTimeField(blank=False, auto_now=False, auto_now_add=True)
    original_text = models.TextField(blank=False, null=False)
    summarized_text = models.TextField(blank=True, null=True)
    model_used = models.CharField(blank=True, null=True, choices=Models_choices.choices, max_length=20)
    tokens_used = models.IntegerField(blank=True, null=True, default=0)