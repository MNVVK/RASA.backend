from django.contrib import admin
from .models import Service, Application, ApplicationService

admin.site.register(Service)
admin.site.register(Application)
admin.site.register(ApplicationService)
