from django.shortcuts import render
from .models import SteamGame, SteamGameDetail
import requests
import json
from django.http import HttpResponse
from django.views import View

# Create your views here.
"""
Simple function-based view to list all the games and their details if available.
"""
def game_list(request):
    games = SteamGame.objects.all()
    return render(request, 'game_list.html', {'games': games})
def game_detail(request, appid):
    game = SteamGame.objects.get(appid=appid)
    details = None
    if game.has_details:
        details = SteamGameDetail.objects.get(steam_game=game)
    return render(request, 'game_detail.html', {'game': game, 'details': details})

"""
API View to get the list of games from the steam database api endpoint
"""
def fetch_games(request):
    url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Parsing the data to a python dictionary
        data_dict = json.loads(data)
        app_list = data_dict["applist"]["apps"]
        for app in app_list:
            appid = app["appid"]
            name = app["name"]
            # Check if the game already exists in the database
            if not SteamGame.objects.filter(appid=appid).exists():
                SteamGame.objects.create(appid=appid, name=name)
        return HttpResponse("Games fetched and stored successfully.") 
    else:
        return HttpResponse("Failed to fetch games from the API.", status=500)

"""
Class-based view for the homepage that lists all games from our database.
This view however will be converted to an APIView in the future to serve JSON data to a Next.js frontend.
"""
class HomePageView(View):
    def get(self, request):
        games = SteamGame.objects.all()
        return render(request, 'api/home.html', {'games': games})
