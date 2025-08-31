from django.contrib import admin
from .models import Engine, Acceptance, EngineAcceptance, CustomUser, Attribute, EngineAttribute

admin.site.register(Engine)
admin.site.register(Acceptance)
admin.site.register(EngineAcceptance)
admin.site.register(Attribute)
admin.site.register(EngineAttribute)
admin.site.register(CustomUser)
