""" Admin page - register models """
from django.contrib import admin
from django.utils.html import format_html
from .models import Logger, MainSettings, EmailRecipients

class LoggerAdmin(admin.ModelAdmin):
    """ Admin logger """

    list_display = [
        'get_category_display',
        'reference',
        'message',
        'get_date_time',
    ]
    search_fields = [
        'reference',
        'message',
        'stack_trace'
    ]
    list_filter = [
        'category',
    ]

    def get_category_display(self, obj):
        """ Get categroy display name """

        if obj.category in ['info', 'notset']:
            color = '#4AC1D2'
        elif obj.category in ['error', 'fatal']:
            color = '#e33030'
        elif obj.category in ['warning', 'debug']:
            color = '#f0bb29'
        elif obj.category in ['task']:
            color = '#10B981'
        else:
            color = '#4AC1D2'

        return format_html('<span style="color: {color};">{msg}</span>', color=color, msg=obj.get_category_display() if obj.category else '')

    get_category_display.short_description = 'Kategorie'

    def get_date_time(self, obj):
        """ Get date_time as strptime """
        return obj.date_time.strftime('%d.%m.%Y - %H:%M:%S Uhr')

admin.site.register(MainSettings)
admin.site.register(EmailRecipients)
admin.site.register(Logger, LoggerAdmin)
