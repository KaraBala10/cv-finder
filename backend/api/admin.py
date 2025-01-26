from django.contrib import admin

from .models import Profile, Resume  # Import only your custom models

# Register only your models (DO NOT unregister or re-register User)
admin.site.register(Profile)
admin.site.register(Resume)
