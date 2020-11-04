from django.db import models


class Scene(models.Model):
    """Model representing a scene (but not a specific copy of a scene)."""
    title = models.CharField(max_length=200)
    summary = models.TextField(
        max_length=1000, help_text='Enter a brief description of the scene')

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the url to access a detail record for this scene."""
        return reverse('scene-detail', args=[str(self.id)])
