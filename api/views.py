from django.shortcuts import render
from .models import SteamGame, SteamGameDetail
import requests
import json
from django.http import HttpResponse
from django.views import View
from functools import reduce
from django.db import models
from operator import or_

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
        app_data = data.get(str(appid), {})
        if app_data.get("success"):
            details = app_data.get("data", {})
            game = SteamGame.objects.get(appid=appid)
            # first check if it's a non-game or game
            if details.get("type", "") != "game":
                print("not a game")
                # delete the game from the SteamGame model if it exists and return a message
                game.delete()
                return HttpResponse(f"AppID {appid} is not a game. Deleted from database.")
            # Check if details already exist
            if not SteamGameDetail.objects.filter(steam_game=game).exists():
                try:
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
                except:
                    return HttpResponse(f"Failed to store details for game {appid}.", status=500)

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
    non_game_keywords = ['DLC', 'Soundtrack', 'Demo', 'Video', 'Comic', 'Guide', 'Tool', 'Driver', 'Theme', 'Server', 'Patch', 'Mod', 'Beta', 'Update', 'winui', 'steamworks', 'steamclient', 'vr', 'vrchat', 'vr game', 'vr experience', 'vr app', 'vr demo', 'steam', 'source', 'sdk', 'workshop', 'editor', 'map', 'level', 'plugin', 'addon', 'extension', 'utility', 'application', 'app', 'software', 'framework', 'library', 'engine', 'platform', 'service', 'toolkit', 'package', 'bundle', 'collection', 'playtest', 'test', 'testing', 'experiment', 'experimental', 'prototype', 'concept', 'idea', 'vision', 'demo reel', 'showcase', 'preview', 'trailer', 'teaser', 'clip', 'footage', 'sneak peek', 'behind the scenes', 'making of', 'interview', 'featurette', 'documentary', 'deleted scenes', 'client', 'server', 'multiplayer', 'singleplayer', 'co-op', 'cooperative', 'online', 'offline', 'lan', 'local', 'cross-platform', 'crossplay', 'modding', 'customization', 'skins', 'themes', 'avatars', 'emotes', 'badges', 'achievements', 'leaderboards', 'stats', 'progression', 'inventory', 'marketplace', 'trading', 'economy', 'currency', 'microtransactions', 'in-app purchases', 'pack']
    q = SteamGame.objects.filter(
        reduce(or_, (models.Q(name__icontains=kw) for kw in non_game_keywords))
        )
    count = q.count()
    for game in q:
        if game.has_details:
            try:
                detail = SteamGameDetail.objects.get(steam_game=game)
                detail.delete()
            except SteamGameDetail.DoesNotExist:
                pass
        game.delete()
    return HttpResponse(f"Deleted {count} obvious non-game entries from the database.")


"""
Api view to get the record from a get parameter and search the SteamGame model for matching names. And automatically fetch details for those games if not already present.
"""
def search_and_fetch(request):
    if request.method == "GET":
        query = request.GET.get('q', '')
        if query:
            games = SteamGame.objects.filter(name__icontains=query)
            for game in games:
                if not game.has_details:
                    fetch_game_details(request, game.appid)
            # This will be replaced with a json response in the future
            return render(request, 'api/game_list.html', {'games': games})
        else:
            return HttpResponse("No search query provided.", status=400)
    else:
        return HttpResponse("Invalid request method.", status=405)


"""
API view to fetch details for all games that do not have details yet.
"""
def fetch_details_for_all(request):
    games_without_details = SteamGame.objects.filter(has_details=False)
    count = games_without_details.count()
    for game in games_without_details:
        fetch_game_details(request, game.appid)
    return HttpResponse(f"Fetched details for {count} games without details.")


"""
Class-based view for the homepage that lists all games from our database.
This view however will be converted to an APIView in the future to serve JSON data to a Next.js frontend.
"""
class HomePageView(View):
    def get(self, request):
        games = SteamGame.objects.all()
        return render(request, 'api/home.html', {'games': games})
