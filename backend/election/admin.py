from django.contrib import admin

from .models import Candidate, Voter

admin.site.register(Voter)
admin.site.register(Candidate)
