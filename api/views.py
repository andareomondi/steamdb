from django.shortcuts import render
from .models import SteamGame, SteamGameDetail
import requests
import json
from django.http import HttpResponse
from django.views import View
from functools import reduce
from django.db import models
from operator import or_
import operator

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
        data_dict = data.get("applist", {})
        app_list = data_dict.get("apps", []) 
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
API View to get the details of a specific game from the steam database api endpoint
"""
def fetch_game_details(request, appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        app_data = data.get(str(appid), {})
        if app_data.get("success"):
            details = app_data.get("data", {})
            game = SteamGame.objects.get(appid=appid)
            print(game)
            print(details)
            # first check if it's a non-game or game
            if details.get("type", "") != "game":
                print("not a game")
                # delete the game from the SteamGame model if it exists and return a message
                game.delete()
                return HttpResponse(f"AppID {appid} is not a game. Deleted from database.")
            # Check if details already exist
            if not SteamGameDetail.objects.filter(steam_game=game).exists():
                SteamGameDetail.objects.create(
                    name=details.get("name", ""),
                    steam_game=game,
                    is_game=details.get("type", "") == "game",
                    required_age=details.get("required_age", ""),
                    header_image=details.get("header_image", ""),# header image for the game to be used in the frontend
                    about_the_game=details.get("short_description", ""),
                    is_free=details.get("is_free", False),
                    developers=", ".join(details.get("developers", [])),
                    genres=", ".join([genre["description"] for genre in details.get("genres", [])])
                )
                game.has_details = True
                game.save()

            return HttpResponse(f"Details for game {appid} fetched and stored successfully.")
        else:
            return HttpResponse(f"No details found for game {appid}.", status=404)
    else:
        return HttpResponse("Failed to fetch game details from the API.", status=500)

"""
API View to delete all the non games from the database both from SteamGame and SteamGameDetail models.
"""
def delete_non_games(request):
    non_games = SteamGameDetail.objects.filter(is_game=False)
    count = non_games.count()
    for detail in non_games:
        # Delete the associated SteamGame entry
        detail.steam_game.delete()
        # Delete the SteamGameDetail entry
        detail.delete()
    return HttpResponse(f"Deleted {count} non-game entries from the database.")

"""
Api view to delete obvious non-games like DLCs, soundtracks, etc from SteamGameDetail model.
"""
def delete_obvious_non_games(request):
    non_game_keywords = ['DLC', 'Soundtrack', 'Demo', 'Video', 'Comic', 'Guide', 'Tool', 'Driver', 'Theme', 'Server', 'Patch', 'Mod', 'Beta', 'Update', 'winui', 'steamworks', 'steamclient']
    
    # Build Q objects dynamically
    q_objects = [models.Q(name__icontains=keyword) for keyword in non_game_keywords]
    
    # Combine all Q objects with OR
    combined_q = reduce(operator.or_, q_objects)
    
    # Filter records
    non_games = SteamGameDetail.objects.filter(combined_q)
    
    count = non_games.count()
    
    # If you have proper CASCADE relationships set up in your models,
    # you can just delete the SteamGameDetail objects and related objects will be deleted automatically
    deleted_count, deleted_dict = non_games.delete()
    
    return HttpResponse(f"Deleted {count} obvious non-game entries from the database. Details: {deleted_dict}")
"""
Class-based view for the homepage that lists all games from our database.
This view however will be converted to an APIView in the future to serve JSON data to a Next.js frontend.
"""
class HomePageView(View):
    def get(self, request):
        games = SteamGame.objects.all()
        return render(request, 'api/home.html', {'games': games})
