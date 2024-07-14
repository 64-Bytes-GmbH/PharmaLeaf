""" DB Logger models """
from datetime import datetime
from django.db import models
from django.utils import timezone


class MainSettings(models.Model):
    """ Grundeinstellung für die App"""

    class Meta:
        """ Meta """
        verbose_name = 'Haupteinstellung'
        verbose_name_plural = 'Haupteinstellungen'

    mail_subject = models.CharField(verbose_name='Betreff in der E-Mail', max_length=255, blank=True, default='Fehlermeldung')

    send_via_api = models.BooleanField(verbose_name='Send via API', default=False)

    # Send via Pushover
    pushover_token = models.CharField(verbose_name='Pushover Token', max_length=255, blank=True)
    pushover_user = models.CharField(verbose_name='Pushover User', max_length=255, blank=True)
    pushover_retry = models.CharField(verbose_name='Pushover Retry', max_length=255, blank=True, default='60')
    pushover_expire = models.CharField(verbose_name='Pushover Expire', max_length=255, blank=True, default='600')

    # E-Mail Eisntellungen
    error_mail = models.CharField(verbose_name='Error E-Mail', max_length=255, blank=True)
    error_mail_password = models.CharField(verbose_name='Error E-Mail Passwort', max_length=255, blank=True)
    error_mail_host = models.CharField(verbose_name='Error E-Mail Host', max_length=255, blank=True, default='smtp.strato.de')
    error_mail_port = models.CharField(verbose_name='Error E-Mail Port', max_length=255, blank=True, default='465')

    def __str__(self):
        return 'Haupteinstellungen'

class EmailRecipients(models.Model):
    """ E-Mail Emfpänger """

    class Meta:
        """ Meta """
        verbose_name = 'E-Mail Emfpänger'
        verbose_name_plural = 'E-Mail Emfpänger'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255)
    email = models.EmailField(verbose_name='E-Mail')

    def __str__(self):
        return f'{ self.name } ({ self.email })'


class Logger(models.Model):
    """ Logger: Speichert Aktivitäten der Nutzer """

    LoggerChoices = [
        ('info', 'INFO'),
        ('warning', 'WARNING'),
        ('error', 'ERROR'),
        ('debug', 'DEBUG'),
        ('notset', 'NotSet'),
        ('fatal', 'FATAL'),
        ('task', 'TASK'),
    ]

    PriorityChoices = [
        ('-2', 'Lowest'),
        ('-1', 'Lower'),
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Emergency'),
    ]

    class Meta:
        """ Meta """  
        verbose_name = 'Logger'
        verbose_name_plural = 'Logger'

    priority = models.CharField(verbose_name='Priorität', max_length=255, choices=PriorityChoices, default='0')
    user = models.CharField(verbose_name='User', max_length=255, default='System')
    category = models.CharField(verbose_name='Kategorie', max_length=255, choices=LoggerChoices, default='info')
    reference = models.CharField(verbose_name='Referenz', max_length=255, null=True)
    message = models.TextField(verbose_name='Message', max_length=65535, blank=True)
    stack_trace = models.TextField(verbose_name='Stack Trace', max_length=65535, blank=True)
    date_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.reference} | {self.message} | {self.date_time.strftime("%d.%m.%Y - %H:%M Uhr")}'
