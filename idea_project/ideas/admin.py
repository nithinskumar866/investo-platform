from django.contrib import admin
from .models import SignupDetail, Idea, InvestorProfile, VideoResource,Message

admin.site.register(VideoResource)
admin.site.register(InvestorProfile)

class IdeaAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'description', 'tag', 'email')
    search_fields = ('name', 'title', 'description', 'tag')
    list_filter = ('tag',)

admin.site.register(Idea, IdeaAdmin)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'tag')
    search_fields = ('name', 'email')
    list_filter = ('tag',)


class SignupDetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'email')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'timestamp')
    search_fields = ('sender__name', 'receiver__name', 'content')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)

admin.site.register(SignupDetail, SignupDetailAdmin)

admin.site.register(Message, MessageAdmin)

