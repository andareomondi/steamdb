from django.contrib import admin
from .models import SteamGame, SteamGameDetail

# Register your models here.
admin.site.register(SteamGame)
admin.site.register(SteamGameDetail)
