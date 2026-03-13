from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from accounts.models import Users, UserActivities

class MainListView(TemplateView):
    template_name = 'main.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = Users.objects.count()
        context['actions'] = UserActivities.objects.count()
        return context
    
    