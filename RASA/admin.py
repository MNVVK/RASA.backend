from django.contrib import admin
from .models import Engine, Acceptance, EngineAcceptance

admin.site.register(Engine)
admin.site.register(Acceptance)
admin.site.register(EngineAcceptance)
