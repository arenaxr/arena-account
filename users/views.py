from django.shortcuts import  render, redirect
from .forms import NewUserForm
from django.contrib.auth import login
from django.contrib import messages #import messages
from .models import Scene


def homepage(request):
	scenes = Scene.objects.all() #queryset containing all scenes we just created
	return render(request=request, template_name="users/home.html", context={'scenes':scenes})


def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful." )
			return redirect("users:homepage")
		messages.error(request, "Unsuccessful registration. Invalid information.")
	form = NewUserForm
	return render (request=request, template_name="users/register.html", context={"register_form":form})
