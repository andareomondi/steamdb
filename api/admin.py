from django.contrib import admin
from .models import SteamGame, SteamGameDetails

# Register your models here.
admin.register(SteamGame)
admin.register(SteamGameDetails)
