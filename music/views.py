from django.shortcuts import render,get_object_or_404
from django.contrib.auth import logout
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth.models import User,auth
from django.contrib import messages
from .models import Album,Song
from .forms import AlbumForm, SongForm, UserForm
from django.db.models import Q

AUDIO_FILE_TYPES = ['wav', 'mp3', 'ogg']
IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']

# Create your views here.

def create_album(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    else:
        form = AlbumForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.album_logo = request.FILES['album_logo']
            file_type = album.album_logo.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in IMAGE_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Image file must be PNG, JPG, or JPEG',
                }
                return render(request, 'create_album.html', context)
            album.save()
            return render(request, 'detail.html', {'album': album})
        context = {
            "form": form,
        }
        return render(request, 'create_album.html', context)


def create_song(request, album_id):
    form = SongForm(request.POST or None, request.FILES or None)
    album = get_object_or_404(Album, pk=album_id)
    if form.is_valid():
        albums_songs = album.song_set.all()
        for s in albums_songs:
            if s.song_title == form.cleaned_data.get("song_title"):
                context = {'album': album,'form': form,'error_message': 'You already added that song'}
                return render(request, 'create_song.html', context)
        song = form.save(commit=False)
        song.album = album
        song.audio_file = request.FILES['audio_file']
        file_type = song.audio_file.url.split('.')[-1]
        file_type = file_type.lower()
        if file_type not in AUDIO_FILE_TYPES:
            context = {'album': album,'form': form,'error_message': 'Audio file must be WAV, MP3, or OGG'}
            return render(request, 'create_song.html', context)
        song.save()
        return render(request, 'detail.html', {'album': album})
    context = {'album': album,'form': form}
    return render(request, 'create_song.html', context)


def delete_album(request, album_id):
    album = Album.objects.get(pk=album_id)
    album.delete()
    albums = Album.objects.filter(user=request.user)
    return render(request, 'index.html', {'albums': albums})


def delete_song(request, album_id, song_id):
    album = get_object_or_404(Album, pk=album_id)
    song = Song.objects.get(pk=song_id)
    song.delete()
    return render(request, 'detail.html', {'album': album})

def favorite(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    try:
        if song.is_favorite:
            song.is_favorite = False
        else:
            song.is_favorite = True
        song.save()
    except (KeyError, Song.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})


def favorite_album(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    try:
        if album.is_favorite:
            album.is_favorite = False
        else:
            album.is_favorite = True
        album.save()
    except (KeyError, Album.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})

def songs(request, filter_by):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    else:
        try:
            song_ids = []
            for album in Album.objects.filter(user=request.user):
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids)
            if filter_by == 'favorites':
                users_songs = users_songs.filter(is_favorite=True)
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'songs.html', {
            'song_list': users_songs,
            'filter_by': filter_by,
        })
        


def index(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    else:
        albums = Album.objects.filter(user=request.user)
        song_results = Song.objects.all()
        query = request.GET.get("q")
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            return render(request, 'index.html', {
                'albums': albums,
                'songs': song_results,
            })
        else:
            return render(request, 'index.html', {'albums': albums})
        



def detail(request,album_id):
    if request.user.is_authenticated:
        user = request.user
        album = get_object_or_404(Album,pk=album_id)
        return render(request,'detail.html',{'album':album})
    else:
        return render(request,'login.html')

def register(request):
    if request.method=='POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        email = request.POST['email']
        if password1 == password2 :
            if User.objects.filter(username=username).exists():
                messages.info(request,'Username Already Taken...')
                return render(request,'register.html')
            elif User.objects.filter(email=email).exists():
                messages.info(request,'Email Already Taken...')
                return render(request,'register.html')
            else:
                user = User.objects.create_user(username=username,password=password1,email=email,first_name=first_name,last_name=last_name)
                user.save()
                return render(request,'login.html')
        else:
            print('password not matching..')
            return render(request,'register.html')
    else:
        return render(request,'register.html')


def login_user(request):
    if request.method=='POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username,password=password)

        if user is not None:
            auth.login(request,user)
            albums = Album.objects.filter(user=request.user)
            return render(request,'index.html',{'albums':albums})
        else:
            messages.info(request,'Invalid Credential')
            return render(request,'login.html')
    else:
        return render(request,'login.html')


def logout_user(request):
    auth.logout(request)
    return render(request,'login.html')
