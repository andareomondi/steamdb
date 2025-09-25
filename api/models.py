from django.db import models

# Create your models here.
class SteamGame(models.Model):
    """
    A model representing all the steam games without their specific details. Just their respective IDs, names and if we have details for them.
    The option for details will be done in another model and linked through a ForeignKey.
    """
    appid = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    has_details = models.BooleanField(default=False)

    def __str__(self):
        return self.name
class SteamGameDetails(models.Model):
    """
    A model representing the details of a steam game. Linked to the SteamGame model through a ForeignKey.
    This model will contain all the details we can get from the Steam API for a specific game.
    """
    name = models.CharField(max_length=255)
    steam_game = models.OneToOneField(SteamGame, on_delete=models.CASCADE, related_name='details')
    required_age = models.CharField(max_length=10, blank=True, null=True)
    is_free = models.BooleanField(default=False)
    about_the_game = models.TextField(blank=True, null=True)
    header_image = models.URLField(max_length=500, blank=True, null=True)
    website = models.URLField(max_length=500, blank=True, null=True)
    developers = models.TextField(blank=True, null=True)
    price_overview = models.JSONField(blank=True, null=True)
    categories = models.JSONField(blank=True, null=True)
    genres = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} Details by {self.developers}"
