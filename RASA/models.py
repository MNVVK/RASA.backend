from django.db import models


class Engine(models.Model):
    title = models.CharField(max_length=400)
    description = models.TextField()
    image_url = models.CharField(max_length=400)

    def __str__(self):
        return self.title
