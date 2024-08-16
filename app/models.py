# Create your models here.

import os
import re
import mimetypes
import uuid
from datetime import datetime
from django.utils import timezone
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

# Hinweis: Vorher wurde User von django.contrib.auth.model importiert
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum
from django.conf import settings
from django.core.files import File
from django.contrib.auth.models import User

from .choices import *
from .models_utils import *


def invoice_layout_upload(instance, filename):
    """ Upload von layouts """

    upload_to = 'layouts/'

    ext = filename.split('.')[-1]
    
    try:
        this = MainSettings.objects.get(id=instance.id)
        if this.invoice_layout != "":
            path = this.invoice_layout.path
            os.remove(path)
            
        filename = '{}.{}'.format('invoice_layout', ext)
    except Exception:
        filename = '{}.{}'.format('invoice_layout', ext)

    return os.path.join(upload_to, filename)

def prepaid_envelope_upload(instance, filename):
    """ Upload von layouts """

    upload_to = 'main_files/'

    ext = filename.split('.')[-1]
    
    try:
        this = MainSettings.objects.get(id=instance.id)
        if this.prepaid_envelope != "":
            path = this.prepaid_envelope.path
            os.remove(path)
            
        filename = '{}.{}'.format('Freiumschlag', ext)
    except Exception:
        filename = '{}.{}'.format('Freiumschlag', ext)

    return os.path.join(upload_to, filename)

def logo_upload(instance, filename):
    """ Uploaden eines Logos """

    upload_to = 'logo/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = MainSettings.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)
            
        filename = '{}.{}'.format('logo' + now, ext)
    except Exception:
        filename = '{}.{}'.format('logo' + now, ext)

    return os.path.join(upload_to, filename)

class MainSettings(models.Model):
    """ Grundeinstellung für die App"""
    
    class Meta:
        """ Meta """
        verbose_name = 'Haupteinstellung'
        verbose_name_plural = 'Haupteinstellungen'

    company_name = models.CharField(verbose_name='Filialname', max_length=255, blank=True)
    street = models.CharField(verbose_name='Straße', max_length=255, blank=True)
    street_number = models.CharField(verbose_name='Hausnummer', max_length=255, blank=True)
    postalcode = models.CharField(verbose_name='Postleitzahl', max_length=255, blank=True)
    city = models.CharField(verbose_name='Ort', max_length=255, blank=True)
    manager = models.CharField(verbose_name='Geschäftsführer', max_length=255, blank=True)
    phone = models.CharField(verbose_name='Telefon', max_length=255, blank=True)
    email = models.CharField(verbose_name='E-Mail', max_length=255, blank=True)
    tax_id = models.CharField(verbose_name='Umsatzsteuer-Id', max_length=255, blank=True)
    regnumber = models.CharField(verbose_name='Handelsregisternummer', max_length=255, blank=True)
    regcourt = models.CharField(verbose_name='Registergericht', max_length=255, blank=True)

    domain = models.CharField(verbose_name='Domain', max_length=255, blank=True, default='higreen-apotheke.de')

    # Logo
    logo = models.FileField(verbose_name='Logo', blank=True, upload_to=logo_upload)

    # Uploads
    invoice_layout = models.FileField(verbose_name='Rechnungslayout (.pdf)', blank=True, upload_to=invoice_layout_upload)
    prepaid_envelope = models.FileField(verbose_name='Freiumschlag (.pdf)', blank=True, upload_to=prepaid_envelope_upload)

    # APIs
    google_api =  models.CharField(verbose_name='Google Api', max_length=255, blank=True)

    # Paypal
    paypal_base_url = models.CharField(verbose_name='PayPal Base Url', max_length=255, blank=True, default='https://api-m.sandbox.paypal.com')
    paypal_api_client_id = models.CharField(verbose_name='PayPal Client Id', max_length=255, blank=True)
    paypal_api_secret = models.CharField(verbose_name='PayPal Secret', max_length=255, blank=True)
    paypal_payment = models.BooleanField(verbose_name='PayPal Zahlung aktiv', default=False)
    
    # Better payment
    better_payment_base_url = models.CharField(verbose_name='Better Payment Base Url', max_length=255, blank=True, default='https://api.crefoeasycheckout.de')
    better_payment_outgoing_key = models.CharField(verbose_name='Better Payment Outgoing Key', max_length=255, blank=True)
    better_payment_api = models.CharField(verbose_name='Better Payment API', max_length=255, blank=True)
    better_payment_active = models.BooleanField(verbose_name='Better Payment Zahlung aktiv', default=False)

    # Boniversum
    boniversum_active = models.BooleanField(verbose_name='Kreditabfrage aktiv', default=False)
    boniversum_base_url = models.CharField(verbose_name='Boniversum Base Url', max_length=255, blank=True, default='https://api.boniversum.com')
    boniversum_prodid = models.CharField(verbose_name='Boniversum ProdID', max_length=255, blank=True)
    boniversum_username = models.CharField(verbose_name='Boniversum Benutzername', max_length=255, blank=True)
    boniversum_password = models.CharField(verbose_name='Boniversum Passwort', max_length=255, blank=True)
    boniversum_ident_check = models.CharField(verbose_name='Boniversum Identifizierungswerte (; getrennt)', max_length=255, default='2')
    boniversum_min_credit_score = models.PositiveIntegerField(verbose_name='Boniversum Min. Score', default=1000)

    # Mailgun
    mailgun_api_key = models.CharField(verbose_name='Mailgun API Key', max_length=255, blank=True)
    mailgun_domain = models.CharField(verbose_name='Mailgun Domain', max_length=255, blank=True, default='https://api.eu.mailgun.net')

    # Brevo
    brevo_api_key = models.CharField(verbose_name='Brevo API Key', max_length=255, blank=True)
    brevo_base_url = models.CharField(verbose_name='Brevo Base Url', max_length=255, blank=True, default='https://api.brevo.com')
    brevo_sender_email = models.CharField(verbose_name='Brevo Absender E-Mail', max_length=255, blank=True)
    brevo_sender_name = models.CharField(verbose_name='Brevo Absender Name', max_length=255, blank=True)

    # E-Mail Eisntellungen
    error_mail = models.CharField(verbose_name='Error E-Mail', max_length=255, blank=True, default='info@higreen-apotheke.de')
    error_mail_password = models.CharField(verbose_name='Error E-Mail Passwort', max_length=255, blank=True)
    error_mail_host = models.CharField(verbose_name='Error E-Mail Host', max_length=255, blank=True, default='smtp.strato.de')
    error_mail_port = models.CharField(verbose_name='Error E-Mail Port', max_length=255, blank=True, default='465')

    # E-Mil über Anbieter
    mail_via_api = models.BooleanField(verbose_name='E-Mail über API Schnittstelle', default=False)

    # Wartungsarbeiten
    maintenance = models.BooleanField(verbose_name="Wartungsarbeiten", default=False)

    # Testmodus
    test_mode = models.BooleanField(verbose_name='Testmodus', default=True)
    
    # Rechtsliches
    agb = models.TextField(verbose_name='AGB', max_length=65535, blank=True)
    privacy_policy = models.TextField(verbose_name='Datenschutzerklärung', max_length=65535, blank=True)

    def __str__(self):
        return 'Haupteinstellungen'

class EmailSettings(models.Model):
    """ E-Mail Einstellungen"""

    class Meta:
        verbose_name = 'E-Mail Einstellung'
        verbose_name_plural = 'E-Mail Einstellungen'

    info_email = models.EmailField(verbose_name='Info Mail', max_length=255, blank=True)
    info_email_host = models.CharField(verbose_name='Info Email host', max_length=255, blank=True)
    info_email_password = models.CharField(verbose_name='Info Email Host Passwort', max_length=255, blank=True)
    info_email_port = models.CharField(verbose_name='Info Email Port', max_length=255, blank=True)

    no_reply_email = models.EmailField(verbose_name='No-Reply Mail', max_length=255, blank=True)
    no_reply_email_host = models.CharField(verbose_name='No-Reply Email host', max_length=255, blank=True)
    no_reply_email_password = models.CharField(verbose_name='No-Reply Email Host Passwort', max_length=255, blank=True)
    no_reply_email_port = models.CharField(verbose_name='No-Reply Email Port', max_length=255, blank=True)

    contact_email = models.EmailField(verbose_name='Kontakt Mail', max_length=255, blank=True)
    contact_email_host = models.CharField(verbose_name='Kontakt Email host', max_length=255, blank=True)
    contact_email_password = models.CharField(verbose_name='Kontakt Email Host Passwort', max_length=255, blank=True)
    contact_email_port = models.CharField(verbose_name='Kontakt Email Port', max_length=255, blank=True)

class EmailLogger(models.Model):
    """ E-Mail logs """

    class Meta:
        verbose_name = 'E-Mail Log'
        verbose_name_plural = 'E-Mail Logs'
    
    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)
    email_type = models.CharField(verbose_name='E-Mail Typ', max_length=255, blank=True)
    to_email = models.CharField(verbose_name='E-Mail', max_length=255, blank=True)
    from_email = models.CharField(verbose_name='Von', max_length=255, blank=True)
    pharmacy = models.ForeignKey('Pharmacies', verbose_name='Apotheke', on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(verbose_name='Betreff', max_length=255, blank=True)
    message = models.TextField(verbose_name='Text', max_length=65535, blank=True)
    date_time = models.DateTimeField(verbose_name='Datum', default=timezone.now, editable=False)
    sent_success = models.BooleanField(verbose_name='Erfolgreich gesendet', default=False)

    def __str__(self):
        return f'{self.name} - {self.date_time.strftime("%d.%m.%Y - %H:%M Uhr")}'

class PriceSettings(models.Model):
    """ Standard Preiseinstellungen """

    class Meta:
        """ Meta """
        verbose_name = 'Preiseinstellungen'
        verbose_name_plural= 'Preiseinstellungen'

    tax_rate = models.FloatField(verbose_name='Steuerrate', default=0.19)

    min_order_amount = models.FloatField(verbose_name='Mindesbestellmenge', default=10)

    reminder_fee = models.FloatField(verbose_name='Mahngebühr', default=5)

    # Blüte
    aek_package = models.FloatField(verbose_name='AEK Verpackungsgebühr', default=2.00)
    aek_package_prepared = models.FloatField(verbose_name='AEK Verpackungsgebühr zubereitet', default=2.22)

    # Extrakt
    triglycerides_price = models.FloatField(verbose_name='Mittelkettige Triglyceride (Miglyol 812)', default=1.03)
    bottle_price = models.FloatField(verbose_name='Braunglasflasche (Gl 18)', default=0.30)
    dosing_pipette = models.FloatField(verbose_name='Kolbendosierpipette 1ml', default=0.56)
    screw_mount = models.FloatField(verbose_name='Schraubmontur mit Steckeinsatz und kindersicherem Verschluss', default=0.19)

    date_time = models.DateTimeField(verbose_name='Letztes Update', default=datetime.now, editable=False)

    def save(self, *args, **kwargs):
        """ Save """

        self.date_time = datetime.now()

        return super(PriceSettings, self).save(*args, **kwargs)

    def __str__(self):
        return f'Preiseinstellungen Stand {self.date_time.strftime("%d.%m.%Y - %H:%M Uhr")}'

class Pharmacies(models.Model):
    """ Apotheken """

    class Meta:
        """ Meta """
        verbose_name = 'Apotheke'
        verbose_name_plural = 'Apotheken'

    # Apothekendetails
    name = models.CharField(verbose_name='Apotheke', max_length=255, blank=True)
    street = models.CharField(verbose_name='Straße', max_length=255, blank=True)
    street_number = models.CharField(verbose_name='Hausnummer', max_length=255, blank=True)
    postalcode = models.CharField(verbose_name='PLZ', max_length=255, blank=True)
    city = models.CharField(verbose_name='Stadt', max_length=255, blank=True)

    # Rechnungsadresse
    invoice_name = models.CharField(verbose_name='Rechnung - Name', max_length=255, blank=True, default='Kleeblatt Apotheke am Ostwall')
    invoice_street = models.CharField(verbose_name='Rechnung - Straße', max_length=255, blank=True, default='Ostwall')
    invoice_street_number = models.CharField(verbose_name='Rechnung - Hausnummer', max_length=255, blank=True, default='165')
    invoice_postalcode = models.CharField(verbose_name='Rechnung - Postleitzahl', max_length=255, blank=True, default='47798')
    invoice_city = models.CharField(verbose_name='Rechnung Ort', max_length=255, blank=True, default='Krefeld')

    # Kontaktdaten
    contact_name = models.CharField(verbose_name='Kontaktperson', max_length=255, blank=True)
    phonenumber = models.CharField(verbose_name='Telefon', max_length=255, blank=True)
    email = models.CharField(verbose_name='E-Mail', max_length=255, blank=True)

    # Rechtliche Daten
    responsible_pharmacist = models.CharField(verbose_name='Verantwortlicher Apotheker', max_length=255, blank=True)
    responsible_for_content = models.CharField(verbose_name='Inhaltlich Verantwortliche gemäß §6 MStDV', max_length=255, blank=True)
    register_court = models.CharField(verbose_name='Registergericht', max_length=255, blank=True)
    register_number = models.CharField(verbose_name='Registernummer', max_length=255, blank=True)
    responsible_supervicory_authority = models.CharField(verbose_name='Zuständige Aufsichtsbehörde', max_length=255, blank=True)
    responsible_chamber = models.CharField(verbose_name='Zuständige Apothekerkammer', max_length=255, blank=True)
    tax_idenfitication = models.CharField(verbose_name='Umsatzsteuer-Identifikationsnummer', max_length=255, blank=True)
    
    active = models.BooleanField(verbose_name='Aktiv', default=False)
    
    # Identifikationen
    pharmacy_id = models.CharField(verbose_name='Apotheken ID', max_length=255, blank=True)
    pharmacy_ext_id = models.IntegerField(verbose_name='Externe ID', null=True, blank=True, unique=False)

    # Apotheke überlastet
    pharmacy_overloaded = models.BooleanField(verbose_name='Apotheke überlastet', default=False)
    
    # Zahlungsdetails
    bank_name = models.CharField(verbose_name='Bank Name', max_length=255, blank=True)
    bank_iban = models.CharField(verbose_name='IBAN', max_length=255, blank=True)
    bank_bic = models.CharField(verbose_name='BIC', max_length=255, blank=True)

    # PayPal
    paypal_active = models.BooleanField(verbose_name='PayPal aktiv', default=False)
    paypal_email = models.CharField(verbose_name='PayPal E-Mail', max_length=255, blank=True)
    
    # DHL
    dhl_active = models.BooleanField(verbose_name='DHL aktiv', default=False)
    dhl_api_key = models.CharField(verbose_name='DHL Api Key', max_length=255, blank=True)
    dhl_secret_key = models.CharField(verbose_name='DHL Secret Key', max_length=255, blank=True)
    dhl_base_url_test = models.CharField(verbose_name='DHL TEST Base Url', max_length=255, blank=True, default='https://api-sandbox.dhl.com')
    dhl_baser_url_prod = models.CharField(verbose_name='DHL PROD Base Url', max_length=255, blank=True, default='https://api-eu.dhl.com')
    dhl_z_username = models.CharField(verbose_name='DHL Z Username', max_length=255, blank=True)
    dhl_z_password = models.CharField(verbose_name='DHL Z Passwort', max_length=255, blank=True)
    dhl_username = models.CharField(verbose_name='DHL PROD Username', max_length=255, blank=True)
    dhl_password = models.CharField(verbose_name='DHL PROD Passwort', max_length=255, blank=True)
    dhl_account_number = models.CharField(verbose_name='DHL PROD Kundenummer', max_length=255, blank=True)  
    dhl_billing_number = models.CharField(verbose_name='DHL PROD Abrechnungsnummer', max_length=255, blank=True)
    dhl_shipping_product = models.CharField(verbose_name='DHL PROD Lieferprodukt', max_length=255, blank=True)

    # GO Express
    go_express_active = models.BooleanField(verbose_name='GO Express aktiv', default=False)
    go_express_base_url_test = models.CharField(verbose_name='GO Express TEST Base Url', max_length=255, blank=True, default='https://ws-tst.api.general-overnight.com')
    go_express_base_url_prod = models.CharField(verbose_name='GO Express PROD Base Url', max_length=255, blank=True, default='https://ws.api.general-overnight.com')
    go_express_username = models.CharField(verbose_name='GO Express Benutzername', max_length=255, blank=True)
    go_express_password = models.CharField(verbose_name='GO Express Passwort', max_length=255, blank=True)
    go_express_track_username = models.CharField(verbose_name='GO Express Track Benutzername', max_length=255, blank=True)
    go_express_track_password = models.CharField(verbose_name='GO Express Track Passwort', max_length=255, blank=True)
    go_express_responsible_station = models.CharField(verbose_name='GO Express Verantwortliche Station', max_length=255, blank=True, default='DUS')
    go_express_customer_id = models.CharField(verbose_name='GO Express Kunden ID', max_length=255, blank=True, default='19916')

    # E-Mail Settings
    sending_mail = models.CharField(verbose_name='E-Mail Adresse', max_length=255, blank=True)
    sending_mail_host = models.CharField(verbose_name='E-Mail Host', max_length=255, blank=True)
    sending_mail_password = models.CharField(verbose_name='E-Mail Passwort', max_length=255, blank=True)
    sending_mail_port = models.CharField(verbose_name='E-Mail Port', max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.pharmacy_ext_id is None or self.pharmacy_ext_id == '':
            self.pharmacy_ext_id = self.get_next_pharmacy_ext_id()
        super().save(*args, **kwargs)

    @classmethod
    def get_next_pharmacy_ext_id(cls):
        last_pharmacy = cls.objects.all().order_by('pharmacy_ext_id').last()

        if not last_pharmacy or last_pharmacy.pharmacy_ext_id is None:
            return 1001
        return int(last_pharmacy.pharmacy_ext_id) + 1

    def __str__(self):
        return f'{self.city} - {self.name}'

class StandardFillingProtocolIds(models.Model):
    """ Standard-Abfüllprotokoll-ID """

    class Meta:
        """ Meta """
        verbose_name = 'Standard-Abfüllprotokoll-ID'
        verbose_name_plural = 'Standard-Abfüllprotokoll-IDs'

    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    date = models.DateField(verbose_name='Datum', default=timezone.now)
    protocol_id = models.CharField(verbose_name='Protokoll ID', max_length=255, blank=False, unique=True)

    def __str__(self):
        return f'{self.pharmacy}: {self.protocol_id} - {self.date}'
    
class PharmacyEmployees(models.Model):
    """ Apothekenmitarbeiter """

    class Meta:
        """ Meta """
        verbose_name = 'Apothekenmitarbeiter'
        verbose_name_plural = 'Apothekenmitarbeiter'

    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    first_name = models.CharField(verbose_name='Name', max_length=255, blank=True)
    last_name = models.CharField(verbose_name='Nachname', max_length=255, blank=True)
    short_name = models.CharField(verbose_name='Kürzel', max_length=255, blank=True)
    is_default = models.BooleanField(verbose_name='Standard', default=False)

    def __str__(self):
        return f'{self.pharmacy} | {self.first_name} {self.last_name}'

class CancellationReasons(models.Model):
    """ Stornierungsgründe """

    class Meta:
        """ Meta """
        verbose_name = 'Stornierungsgrund'
        verbose_name_plural = 'Stornierungsgründe'

    name = models.CharField(verbose_name='Grund', max_length=255, unique=True)
    email_text = models.TextField(verbose_name='E-Mail Text', max_length=65535)

    def __str__(self):
        return f'{self.name}'

class PagesMetaDatas(models.Model):
    """ Metaddaten für die einzelnen Seiten """

    class Meta:
        """ Meta """
        verbose_name = 'Metadaten'
        verbose_name_plural = 'Metadaten'

    page = models.CharField(verbose_name='Seite', max_length=255, choices=ViewsChoices)
    meta_title = models.CharField(verbose_name='Meta:Titel', max_length=255, blank=True)
    meta_description = models.TextField(verbose_name='Meta:Beschreibung', max_length=65535, blank=True)

    def __str__(self):
        return f'{self.get_page_display()}'

class DeliveryTypes(models.Model):
    """ Versandarten """

    class Meta:
        """ Meta """
        verbose_name = 'Versandart'
        verbose_name_plural = 'Versandarten'

    name = models.CharField(verbose_name='Bezeichnung', choices=DeliveryTypeChoices, max_length=255)
    intern_price = models.FloatField(verbose_name='Interne Kosten', default=0)
    price = models.FloatField(verbose_name='Lieferkosten (Kunde)', default=0)
    free_deliver_amount = models.FloatField(verbose_name='Betrag für kostenlose Lieferung', default=0)

    def __str__(self):
        return f'{ self.get_name_display() } - {self.price:,.2f}€'

class EmailTemplates(models.Model):
    """ E-Mail Vorlagen """

    class Meta:
        """ Meta """
        verbose_name = 'E-Mail Vorlage'
        verbose_name_plural = 'E-Mail Vorlagen'

    email_type = models.CharField(verbose_name='E-Mail Typ', max_length=255, choices=EmailTypes)
    name = models.CharField(verbose_name='Bezeichnung', max_length=255)
    subject = models.CharField(verbose_name='Betreff', max_length=255)
    template_id = models.IntegerField(verbose_name='Template ID', default=0)

class EmailRecipients(models.Model):
    """ E-Mail Emfpänger """

    class Meta:
        """ Meta """
        verbose_name = 'E-Mail Emfpänger'
        verbose_name_plural = 'E-Mail Emfpänger'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255)
    email = models.EmailField(verbose_name='E-Mail')
    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    category = models.CharField(verbose_name='Kategorie', max_length=255, choices=EmailRecipientCategories)

    def __str__(self):
        return f'{ self.get_category_display() }: { self.name } ({ self.email })'

class OpeningHours(models.Model):
    """ Öffnungszeiten """

    class Meta:
        """ Meta """
        verbose_name = 'Öffnungszeiten'
        verbose_name_plural = 'Öffnungszeiten'

    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    day = models.CharField(verbose_name='Tag', max_length=255, choices=DaysChoices)
    from_time = models.TimeField(verbose_name='Von')
    to_time = models.TimeField(verbose_name='Bis')
    closed = models.BooleanField(verbose_name='Geschlossen', default=False)

    def __str__(self):
        return f'{ self.pharmacy.name } { self.get_day_display() } - { self.from_time.strftime("%H:%M") } - { self.to_time.strftime("%H:%M") }'
    
class PackagePickupTimes(models.Model):
    """ Abholzeiten für Pakete von DHL oder GoExpress """

    class Meta:
        """ Meta """
        verbose_name = 'Abholzeiten Pakete'
        verbose_name_plural = 'Abholzeiten Pakete'

    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    day = models.CharField(verbose_name='Tag', max_length=255, choices=DaysChoices)
    from_time = models.TimeField(verbose_name='Von')
    to_time = models.TimeField(verbose_name='Bis')
    closed = models.BooleanField(verbose_name='Geschlossen', default=False)

    def __str__(self):
        return f'{ self.pharmacy.name } { self.get_day_display() } - { self.from_time.strftime("%H:%M") } - { self.to_time.strftime("%H:%M") }'

######################## Terpene ########################
class NaturalOccurrence(models.Model):
    """ Natürliches Vorkommen """

    class Meta:
        """ Meta """
        verbose_name = 'Natürliches Vorkommen'
        verbose_name_plural = 'Natürliches Vorkommen'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)

    def __str__(self):
        return '%s'%(self.name)

class Flavors(models.Model):
    """ Aromen """

    class Meta:
        """ Meta """
        verbose_name = 'Aroma'
        verbose_name_plural = 'Aromen'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)

    def __str__(self):
        return '%s'%(self.name)

class TerpeneEffects(models.Model):
    """ Terpenwirkungen """

    class Meta:
        """ Meta """
        verbose_name = 'Terpenwirkung'
        verbose_name_plural = 'Terpenwirkungen'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)

    def __str__(self):
        return '%s'%(self.name)

class Indications(models.Model):
    """ Indikationen """

    class Meta:
        """ Meta """
        verbose_name = 'Indikation'
        verbose_name_plural = 'Indikationen'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)

    def __str__(self):
        return '%s'%(self.name)

def terpene_icon_upload(instance, filename):
    """ Uploaden eines Logos """

    upload_to = 'terpene/icons/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = Terpene.objects.get(id=instance.id)
        if this.img != "":
            path = this.img.path
            os.remove(path)
            
        filename = '{}.{}'.format(instance.name + now, ext)
    except Exception:
        filename = '{}.{}'.format(instance.name + now, ext)

    return os.path.join(upload_to, filename)

class Terpene(models.Model):
    """ Terpene """

    class Meta:
        verbose_name = 'Terpene'
        verbose_name_plural = 'Terpene'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)
    natural_occurrence = models.ManyToManyField(NaturalOccurrence, verbose_name='Natürliches Vorkommen in', blank=True)
    flavors = models.ManyToManyField(Flavors, verbose_name='Aromen', blank=True)
    terpene_effect = models.ManyToManyField(TerpeneEffects, verbose_name='Mögliche Terpenwirkungen', blank=True)
    indications = models.ManyToManyField(Indications, verbose_name='Indikationen', blank=True)
    description = models.TextField(verbose_name='Beschreibung', max_length=65535, blank=True, null=True)
    img = models.FileField(verbose_name='Icon', blank=True, upload_to=terpene_icon_upload)

    def __str__(self):
        return '%s'%(self.name)

@receiver(post_save, sender=Terpene)
#pylint: disable=unused-argument
def add_terpene_images(sender, instance, **kwargs):
    """ Calculate total after update """
    
    if not instance.img:

        try:
            directory = os.path.join(settings.STATIC_DIR, 'app', 'img', 'terpene', instance.name + '.svg')
            
            with open(directory, 'rb') as image_file:
                instance.img.save(os.path.basename(directory), File(image_file))

        except OSError:
            pass

######################## Produkte ########################
class Cultivar(models.Model):
    """ Kultivar """

    class Meta:
        """ Meta """
        verbose_name = 'Kultivar'
        verbose_name_plural = 'Kultivar'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)

    def __str__(self):
        return '%s'%(self.name)

def genetic_img_upload(instance, filename):
    """ Upload genetic image """

    upload_to = 'genetics/image/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]

    try:
        this = Genetics.objects.get(id=instance.id)
        if this.img != "":
            path = this.img.path
            os.remove(path)

        filename = f'{instance.name + now}.{ext}'
    except Exception:
        filename = f'{instance.name + now}.{ext}'

    return os.path.join(upload_to, filename)

def genetic_icon_upload(instance, filename):
    """ upload genetic icon """

    upload_to = 'genetics/icons/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]

    try:
        this = Genetics.objects.get(id=instance.id)
        if this.icon != "":
            path = this.icon.path
            os.remove(path)

        filename = f'{instance.name + now}.{ext}'
    except Exception:
        filename = f'{instance.name + now}.{ext}'

    return os.path.join(upload_to, filename)

class Genetics(models.Model):
    """ Genetik """

    class Meta:
        """ Meta """
        verbose_name = 'Genetik'
        verbose_name_plural = 'Genetik'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)
    description = models.TextField(verbose_name='Beschreibung', max_length=65535, blank=True)
    icon = models.FileField(verbose_name='Icon', blank=True, upload_to=genetic_icon_upload)
    img = models.ImageField(verbose_name='Bild', blank=True, upload_to=genetic_img_upload)
    show_in_slider = models.BooleanField(default=False, null=True)

    def __str__(self):
        return '%s'%(self.name)

class Manufacturer(models.Model):
    """ Hersteller """

    class Meta:
        """ Meta """
        verbose_name = 'Hersteller'
        verbose_name_plural = 'Hersteller'

    name = models.CharField(verbose_name='Name', max_length=255, blank=True)
    description = models.TextField(verbose_name='Beschreibung', max_length=65535, blank=True)

    def __str__(self):
        return '%s'%(self.name)

class CountryOfOrigin(models.Model):
    """ Herkunftsland """

    class Meta:
        """ Meta """
        verbose_name = 'Herkunftsland'
        verbose_name_plural = 'Herkunftsländer'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)

    def __str__(self):
        return '%s'%(self.name)

class PZNChoices(models.Model):
    """ PZN Auswahlmöglichkeiten """

    class Meta:
        """ Meta """
        verbose_name = 'PZN Auswahl'
        verbose_name_plural = 'PZN Auswahl'

    amount = models.PositiveBigIntegerField(verbose_name='Menge')
    unit = models.CharField(verbose_name='Einheit', max_length=255, choices=UnitChoices)

    def __str__(self):
        return f'{self.id}. {self.amount}{self.unit}'

class Supplier(models.Model):
    """ Lieferant """

    class Meta:
        """ Meta """
        verbose_name = 'Lieferant'
        verbose_name_plural = 'Lieferanten'

    name = models.CharField(verbose_name='Name', max_length=255, blank=True)

    def __str__(self):
        return f'{self.name}'

def product_image_upload(instance, filename):
    """ Uploaden eines Produktbildes """

    upload_to = 'products/' + str(instance.product.id) + '/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = ProductImages.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)
            
        filename = '{}.{}'.format('product' + now, ext)
    except Exception:
        filename = '{}.{}'.format('product' + now, ext)

    return os.path.join(upload_to, filename)

class Products(models.Model):
    """ Cannabis Products """

    class Meta:
        """ Meta """
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'

    priority = models.IntegerField(verbose_name='Priorität', choices=PriorityChoices, default=0)
    number = models.CharField(verbose_name='Artikelnummer', max_length=255, blank=True)
    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)
    cultivar = models.ForeignKey(Cultivar, verbose_name='Kultivar', on_delete=models.SET_NULL, null=True, blank=True)
    genetics = models.ForeignKey(Genetics, verbose_name='Genetik', on_delete=models.SET_NULL, null=True, blank=True)
    thc_value = models.FloatField(verbose_name='THC Wert', default=0.0)
    max_cbd_value = models.FloatField(verbose_name='Maximaler CBD Wert', default=0.1)
    manufacturer = models.ForeignKey(Manufacturer, verbose_name='Hersteller', on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, verbose_name='Lieferant', on_delete=models.SET_NULL, null=True, blank=True)
    supplier_text = models.CharField(verbose_name='Lieferant', max_length=255, blank=True)
    country_of_origin = models.ForeignKey(CountryOfOrigin, verbose_name='Herkunftsland', on_delete=models.SET_NULL, null=True, blank=True)
    treatment = models.CharField(verbose_name='Behandlung', max_length=255, choices=TreatmentChoices, blank=True, default='unirradiated')
    main_terpene = models.ManyToManyField(Terpene, verbose_name='Hauptterpene', max_length=255)
    form = models.CharField(verbose_name='Form', max_length=255, choices=CannabisFormChoices, default='flower')
    description = models.TextField(verbose_name='Beschreibung', max_length=65535, blank=True, null=True)

    meta_title = models.CharField(verbose_name='Meta-Titel', max_length=255, blank=True)
    meta_description = models.TextField(verbose_name='Meta-Beschreibung', max_length=65535, blank=True)

    url_name = models.CharField(verbose_name='URL Bezeichnung', max_length=255, null=True, blank=True)

    # Für Extrakte
    rel_density = models.FloatField(verbose_name='Relative Dichte (g/ml)', default=0.95)

    # purchase_price = models.FloatField(verbose_name='Einkaufspreis', default=6.25)
    # pirce_per_unit = models.FloatField(verbose_name='Preis pro Einheit (g oder ml)', default=0)

    # selling_price = models.FloatField(verbose_name='Kassenpatienten VK Preis', default=9.52)
    # self_payer_selling_price = models.FloatField(verbose_name='Selbstzahler VK Preis (Netto)', default=0)
    # self_payer_selling_price_brutto = models.FloatField(verbose_name='Selbstzahler VK Preis (Brutto)', default=0)

    # price_surcharge = models.FloatField(verbose_name='Selbstzahler Aufschlag in Prozent vom EK', default=1)

    # status = models.CharField(verbose_name='Status', max_length=255, choices=ProductStatusChoices, default='2')

    # active = models.BooleanField(verbose_name='Aktiv', default=True)

    # special_offer = models.BooleanField(verbose_name='Spezieller Preis', default=False)

    def save(self, *args, **kwargs):
        """ Define save """

        if self.url_name == '' or not self.url_name:
            url_name = re.sub(r'[^a-zA-Z0-9]', '-', self.name)
            url_name = re.sub(r'-+', '-', url_name)
            self.url_name = url_name.lower()

        # self.self_payer_selling_price = round(self.purchase_price * (1 + self.price_surcharge), 2)
        # self.self_payer_selling_price_brutto = round(self.self_payer_selling_price * (1 + PriceSettings.objects.first().tax_rate), 2)

        # if not self.pirce_per_unit:
        #     self.pirce_per_unit = self.purchase_price

        return super().save(*args, **kwargs)

    def __str__(self):
        return '%s'%(self.name)

class ProductImages(models.Model):
    """ Produktbilder """

    class Meta:
        """ Meta """
        verbose_name = 'Produktbild'
        verbose_name_plural = 'Produktbilder'

    product = models.ForeignKey(Products, verbose_name='Produkt', on_delete=models.CASCADE)
    position = models.PositiveIntegerField(verbose_name='Position', default=1)
    img = models.ImageField(verbose_name='Bild', upload_to=product_image_upload)
    main_image = models.BooleanField(verbose_name='Hauptbild', default=False)

    def save(self, *args, **kwargs):

        try:
            ProductImages.objects.get(position=self.position, product=self.product)
        except MultipleObjectsReturned:
            nums = list(ProductImages.objects.filter(product=self.product).values_list('position' ,flat=True))
            self.position = find_position(nums)
        except ObjectDoesNotExist:
            pass

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):

        os.remove(self.img.path)

        return super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.product.id} - Pos. {self.position}, MainImage: {self.main_image}'
    
class ProductThresholds(models.Model):
    """ Produktgrenzen (Menge) """

    class Meta:
        """ Meta """
        verbose_name = 'Produktgrenze (Menge)'
        verbose_name_plural = 'Produktgrenzen (Menge)'
        unique_together = ('product',)

    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, verbose_name='Produkt', on_delete=models.CASCADE)
    threshold = models.PositiveSmallIntegerField(verbose_name='Preis', default=100, null=True, blank=True)

    def __str__(self):
        return f'{self.product.name} - {self.threshold}'

class ProductPrices(models.Model):
    """ Produkt Preise """

    class Meta:
        """ Meta """
        verbose_name = 'Produkt Preis'
        verbose_name_plural = 'Produkt Preise'

    unique_together = ('pharmacy', 'product')

    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, verbose_name='Produkt', on_delete=models.CASCADE) 

    purchase_price = models.FloatField(verbose_name='Einkaufspreis (Netto)', default=0)
    pirce_per_unit = models.FloatField(verbose_name='Preis pro Einheit (g oder ml) (Netto)', default=0)

    price_surcharge = models.FloatField(verbose_name='Selbstzahler Aufschlag in Prozent vom EK', default=1)

    selling_price = models.FloatField(verbose_name='Kassenpatienten VK Preis (Netto)', default=9.52)
    self_payer_selling_price = models.FloatField(verbose_name='Selbstzahler VK Preis (Netto)', default=0)
    self_payer_selling_price_brutto = models.FloatField(verbose_name='Selbstzahler VK Preis (Brutto)', default=0)

    status = models.CharField(verbose_name='Status', max_length=255, choices=ProductStatusChoices, default='0')

    active = models.BooleanField(verbose_name='Aktiv', default=False)
    special_offer = models.BooleanField(verbose_name='Spezieller Preis', default=False)

    def save(self, *args, **kwargs):
        """ Define save """

        if not self.pirce_per_unit:
            self.pirce_per_unit = self.purchase_price

        if self.price_surcharge and self.self_payer_selling_price:
            self.price_surcharge = round((self.self_payer_selling_price - self.purchase_price) / self.purchase_price, 4)
            self.self_payer_selling_price_brutto = round(self.self_payer_selling_price * (1 + PriceSettings.objects.first().tax_rate), 2)

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.number}. {self.product.name}'

@receiver(post_delete, sender=ProductImages)
#pylint: disable=unused-argument
def delete_product_images(sender, instance, **kwargs):
    """ Calculate total after update """

    try:
        os.remove(instance.img.path)

    except OSError:
        pass

class PZNAmounts(models.Model):
    """ PZN Nummern """

    class Meta:
        """ Meta """
        verbose_name = 'PZN Nummer'
        verbose_name_plural = 'PZN Nummern'

    product = models.ForeignKey(Products, verbose_name='Produkt', on_delete=models.CASCADE)
    pzn_choice = models.ForeignKey(PZNChoices, verbose_name='PZN Auswahl', on_delete=models.CASCADE)
    number = models.CharField(verbose_name='PZN Nummer', max_length=255, unique=True)
    
    def __str__(self):
        return f'{self.product.number} {self.product.name} - {self.pzn_choice.amount}{self.pzn_choice.get_unit_display()} - {self.number}'

class ProductOrders(models.Model):
    """ Produktbestellungen """
    
    class Meta:
        """ Meta """
        verbose_name = 'Produktbestellung'
        verbose_name_plural = 'Produktbestellungen'

    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, verbose_name='Produkt', on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name='Menge', default=0)
    status = models.CharField(verbose_name='Status', max_length=255, choices=ProductOrderStatus, default='ordered')
    date_time = models.DateTimeField(verbose_name='Bestelldatum', default=datetime.now)

    def __str__(self):
        return f'{self.pharmacy.name} - {self.product.name} - {self.amount}'

######################## Ratgeber ########################
def faq_banner_image_upload(instance, filename):
    """ Uploaden eines Banners """

    upload_to = 'faq/banner/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = FAQGroups.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)
            
        filename = '{}.{}'.format('banner_image' + now, ext)
    except Exception:
        filename = '{}.{}'.format('banner_image' + now, ext)

    return os.path.join(upload_to, filename)

class FAQGroups(models.Model):
    """ FAQ Gruppen """

    class Meta:
        """ Meta """
        verbose_name = 'FAQ Gruppen'
        verbose_name_plural = 'FAQ Gruppen'

    position = models.PositiveIntegerField(verbose_name='Position', default=1)
    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)
    teaser = models.TextField(verbose_name='Teaser', max_length=65535, blank=True)
    banner_image = models.ImageField(verbose_name='Banner Bild', upload_to=faq_banner_image_upload, blank=True)

    def __str__(self):
        return f'{self.position}. {self.name}'

class FAQs(models.Model):
    """ FAQs """

    class Meta:
        """ Meta """
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    group = models.ForeignKey(FAQGroups, verbose_name='FAQ Gruppe', on_delete=models.CASCADE)
    position = models.PositiveIntegerField(verbose_name='Position', default=1)
    question = models.CharField(verbose_name='Frage', max_length=255, blank=True)
    answer = models.TextField(verbose_name='Antwort', max_length=65535, blank=True)

    def save(self, *args, **kwargs):

        try:
            FAQs.objects.get(position=self.position, group=self.group)
            nums = list(FAQs.objects.filter(group=self.group).values_list('position' ,flat=True))
            self.position = find_position(nums)
        except ObjectDoesNotExist:
            pass

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.position}. {self.question}'

class Lexicon(models.Model):
    """ FAQs """

    class Meta:
        """ Meta """
        verbose_name = 'Lexikon'
        verbose_name_plural = 'Lexikon'

    position = models.PositiveIntegerField(verbose_name='Position', default=1)
    title = models.CharField(verbose_name='Titel', max_length=255, blank=True)
    description = models.TextField(verbose_name='Beschreibung', max_length=65535, blank=True)

    def save(self, *args, **kwargs):

        try:
            Lexicon.objects.get(position=self.position)
            nums = list(Lexicon.objects.all().values_list('position' ,flat=True))
            self.position = find_position(nums)
        except ObjectDoesNotExist:
            pass

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.position}. {self.title}'

def block_image_upload(instance, filename):
    """ Uploaden eines Images """

    upload_to = 'blogs/images'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = CannabisBlog.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)
            
        filename = '{}.{}'.format('block_image' + now, ext)
    except Exception:
        filename = '{}.{}'.format('block_image' + now, ext)

    return os.path.join(upload_to, filename)

def banner_image_upload(instance, filename):
    """ Uploaden eines Banners """

    upload_to = 'blogs/banner/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = CannabisBlog.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)
            
        filename = '{}.{}'.format('banner_image' + now, ext)
    except Exception:
        filename = '{}.{}'.format('banner_image' + now, ext)

    return os.path.join(upload_to, filename)

class CannabisBlog(models.Model):
    """ Cannabis Blog """

    class Meta:
        """ Meta """
        verbose_name = 'Blog'
        verbose_name_plural = 'Blogs'

    title = models.CharField(verbose_name='Titel', max_length=255, blank=True)
    teaser = models.TextField(verbose_name='Teaser Text Html', max_length=65535, blank=True)
    text = models.TextField(verbose_name='Info Text Html', max_length=65535, blank=True, default='<p></p>')
    block_image = models.ImageField(verbose_name='Bild für den Block', upload_to=block_image_upload, blank=True, null=True)
    banner_image = models.ImageField(verbose_name='Bild für den Banner', upload_to=banner_image_upload, blank=True, null=True)
    color = models.CharField(verbose_name='Farbe las Hex', max_length=255, blank=True)
    source = models.TextField(verbose_name='Quelle', max_length=65535, blank=True)

    color = models.CharField(verbose_name='Farbschema', max_length=255, blank=True, null=True, default='#899a71')
    url_name = models.CharField(verbose_name='URL Bezeichnung', max_length=255, blank=True)
    
    def save(self, *args, **kwargs):
        """ define save """

        if self.url_name == '' or not self.url_name:
            url_name = re.sub(r'[^a-zA-Z]', '-', self.title)
            url_name = re.sub(r'-+', '-', url_name)
            self.url_name = url_name.lower()

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title}'

######################## Kunde ########################
class Customers(models.Model):
    """ Kunden """

    class Meta:
        """ Meta name """
        verbose_name = 'Kunde'
        verbose_name_plural = 'Kunden'

    user = models.ForeignKey(User, verbose_name='Benutzer', on_delete=models.CASCADE)
    pharmacies = models.ManyToManyField(Pharmacies, verbose_name='Apotheken', blank=True)

    salutation = models.CharField(verbose_name='Anrede', max_length=255, choices=SalutationChoices, blank=True)

    # Rechnungsadresse
    birth_date = models.DateField(verbose_name='Geburtsdatum', blank=True, null=True)
    street = models.CharField(verbose_name='Straße', max_length=255, blank=True)
    street_number = models.CharField(verbose_name='Hausnummer', max_length=255, blank=True)
    address_addition = models.CharField(verbose_name='Adresszusatz', max_length=255, blank=True)
    postcode = models.CharField(verbose_name='Postcode', max_length=255, blank=True)
    city = models.CharField(verbose_name='Stadt', max_length=255, blank=True)
    state = models.CharField(verbose_name='Bundesland', max_length=255, blank=True, choices=StateChoices)
    country = models.CharField(verbose_name='Land', max_length=255, blank=True, choices=CountryChoices)
    phone = models.CharField(verbose_name='Telefon', max_length=255, blank=True)

    customer_type = models.CharField(verbose_name='Patiententyp', max_length=255, choices=CustomerTypeChoices, blank=True, default='self_payer')

    payment_type = models.CharField(verbose_name="Zahlmethode", max_length=255, choices=PaymentTypeChoices, blank=True)
    delivery_type = models.CharField(verbose_name="Lieferart", max_length=255, choices=DeliveryTypeChoices, blank=True)

    health_insurance_company = models.CharField(verbose_name='Gesetz. Krankenversicherung', max_length=255, blank=True)
    health_insurance_contact_person = models.CharField(verbose_name='Kontakt bei Krankenversicherung', max_length=255, blank=True)

    newsletter = models.BooleanField(verbose_name='Newsletter erhalten', default=False)

    can_trigger_order = models.BooleanField(verbose_name='Darf Bestellung auslösen', default=False)

    blocked = models.BooleanField(verbose_name='Blockiert', default=False)
    blocked_date = models.DateField(verbose_name='Blockiert bis (Datum)', blank=True, null=True)
    blocked_reason = models.TextField(verbose_name='Grund der Blockierung', max_length=65535, blank=True)
    
    def save(self, *args, **kwargs):
        """ Define save """

        self.street = self.street.strip()
        self.street_number = self.street_number.strip()
        self.postcode = self.postcode.strip()
        self.city = self.city.strip()

        return super().save(*args, **kwargs)

    @property
    def get_street_address(self):
        """ Combine street and street_number """
        return ('%s %s')%(self.street, self.street_number)
    
    @property
    def get_complete_address(self):
        """ Get complete address """
        return ('%s %s, %s %s')%(self.street, self.street_number, self.postcode, self.city)

    def __str__(self):
        return '%s %s (%s)'%(self.user.first_name, self.user.last_name, self.user.email)

class ProductRequest(models.Model):
    """ Produktanfragen """

    class Meta:
        """ Meta """
        verbose_name = 'Produktanfrage'
        verbose_name_plural = 'Produktanfragen'

    customer = models.ForeignKey(Customers, verbose_name='Kunde', on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Products, verbose_name='Produkt', on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name='Menge', null=False)
    email = models.CharField(verbose_name='E-Mail Adresse', max_length=255, null=False)
    status = models.CharField(verbose_name='Status', max_length=64, choices=ProductRequestChoices, null=False, default='open')
    reject_reason = models.CharField(verbose_name='Ablehnungsgrund', max_length=128, choices=ProductRequestRejectChoices, null=True, blank=True)
    datetime = models.DateTimeField(verbose_name='Datum/Uhrzeit', default=timezone.now)
    available_until = models.DateField(verbose_name='Verfügbar bis', blank=True, null=True)
    ordered = models.BooleanField(verbose_name='Bestellt', default=False)
    declined = models.BooleanField(verbose_name='Kunde hat abgelehnt', default=False)

    def __str__(self):
        return f'{self.email} | {self.product} | {self.amount} | {self.status}'

class NewsletterSubscriber(models.Model):
    """ Newsletter Abonnenten """

    class Meta:
        """ Meta """
        verbose_name = 'Newsletter Abonnent'
        verbose_name_plural = 'Newsletter Abonnenten'

    customer = models.ForeignKey(Customers, verbose_name='Kunde', on_delete=models.SET_NULL, null=True)
    email = models.CharField(verbose_name='E-Mail Adresse', max_length=255, blank=True)
    date_time = models.DateTimeField(verbose_name='Aboniert am', default=datetime.now)

    def __str__(self):
        return f'{self.email}'

@receiver(post_save, sender=Customers)
#pylint: disable=unused-argument
def create_newsletter_item(sender, instance, **kwargs):
    """ Create Newsletter item """
    if instance.newsletter:
        NewsletterSubscriber.objects.get_or_create(customer=instance, email=instance.user.email)

@receiver(post_delete, sender=Customers)
#pylint: disable=unused-argument
def delete_newsletter_item(sender, instance, **kwargs):
    """ Delete Newsletter item """
    try:
        NewsletterSubscriber.objects.get(customer=instance).delete()
    except ObjectDoesNotExist:
        pass

class CompetitionUsers(models.Model):
    """ Wettbewerbsteilnehmer """

    class Meta:
        """ Meta """
        verbose_name = 'Wettbewerbsteilnehmer'
        verbose_name_plural = 'Wettbewerbsteilnehmer'

    name = models.CharField(verbose_name='Name', max_length=255, blank=True)
    email = models.CharField(verbose_name='E-Mail Adresse', max_length=255, blank=True)
    birthdate = models.DateField(verbose_name='Geburtsdatum', blank=True, null=True)
    phonenumber = models.CharField(verbose_name='Telefonnummer', max_length=255, blank=True)
    date_time = models.DateTimeField(verbose_name='Teilgenommen am', default=datetime.now)

    def __str__(self):
        return f'{ self.name } - {self.email}'

######################## Orders ########################
class Orders(models.Model):
    """ Bestellungen """

    class Meta:
        """ Meta """
        verbose_name = 'Bestellung'
        verbose_name_plural = 'Bestellungen'

    number = models.CharField(verbose_name='Bestellnummer', max_length=255, blank=True)
    external_id = models.CharField(verbose_name='Externe Bestell-ID', max_length=255, blank=True)

    # Kundendaten
    customer = models.ForeignKey(Customers, verbose_name='Kunde', on_delete=models.SET_NULL, null=True, blank=True)
    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.SET_NULL, null=True, blank=True)

    customer_type = models.CharField(verbose_name='Patiententyp', max_length=255, choices=CustomerTypeChoices, blank=True, default='self_payer')

    cost_absorption = models.BooleanField(verbose_name='Kostenübernahme vorhanden', default=False)

    salutation = models.CharField(verbose_name='Anrede', max_length=255, choices=SalutationChoices, blank=True)
    first_name = models.CharField(verbose_name='Vorname', max_length=255, blank=True)
    last_name = models.CharField(verbose_name='Nachname', max_length=255, blank=True)
    birth_date = models.DateField(verbose_name='Geburtsdatum', blank=True, null=True)

    # Rechnungsadresse
    street = models.CharField(verbose_name='Straße', max_length=255, blank=True)
    street_number = models.CharField(verbose_name='Hausnummer', max_length=255, blank=True)
    postalcode = models.CharField(verbose_name='Postleitzahl', max_length=255, blank=True)
    city = models.CharField(verbose_name='Stadt', max_length=255, blank=True)
    state = models.CharField(verbose_name='Bundesland', max_length=255, blank=True, choices=StateChoices)
    country = models.CharField(verbose_name='Land', max_length=255, blank=True, choices=CountryChoices)
    comment = models.TextField(verbose_name='Kommentar zur Adresse', max_length=1000, blank=True)
    phone_number = models.CharField(verbose_name='Telefonnummer', max_length=255, blank=True)
    email_address = models.EmailField(verbose_name='E-Mail Adresse', max_length=100, blank=True)

    # Lieferadresse
    del_first_name = models.CharField(verbose_name='Liefer Vorname', max_length=255, blank=True)
    del_last_name = models.CharField(verbose_name='Liefer Nachname', max_length=255, blank=True)
    del_street = models.CharField(verbose_name='Liefer Straße', max_length=255, blank=True)
    del_street_number = models.CharField(verbose_name='Liefer Hausnummer', max_length=255, blank=True)
    del_postalcode = models.CharField(verbose_name='Liefer Postleitzahl', max_length=255, blank=True)
    del_city = models.CharField(verbose_name='Liefer Stadt', max_length=255, blank=True)
    del_state = models.CharField(verbose_name='Liefer Bundesland', max_length=255, blank=True, choices=StateChoices)
    del_country = models.CharField(verbose_name='Liefer Land', max_length=255, blank=True, choices=CountryChoices)
    del_comment = models.TextField(verbose_name='Kommentar zur Lieferadresse', max_length=1000, blank=True)

    delivery_address_as_invoice = models.BooleanField(verbose_name='Lieferadresse = Rechnungsadresse', default=True)

    order_time = models.DateTimeField(verbose_name='Bestellzeit', default=timezone.now)

    shipment_label_type = models.CharField(verbose_name='Versandlabel-Typ', max_length=255, blank=True, choices=DeliveryTypeChoices)
    shipment_shipment_no = models.CharField(verbose_name='Sendungsnummer', max_length=255, blank=True)
    shipment_ref_no = models.TextField(verbose_name='Referenznummer', max_length=65535, blank=True)
    shipment_label_b64_string = models.TextField(verbose_name='Sendungslabel als B64 String', max_length=65535, blank=True)
    shipment_pickup_order_uuid = models.CharField(verbose_name="Abholbestellnummer", max_length=255, blank=True)
    shipment_pickup_date = models.DateField(verbose_name="Abholdatum", blank=True, null=True)

    subtotal = models.FloatField(verbose_name='Zwischensumme (Netto)', default=0)
    tax_amount = models.FloatField(verbose_name='MwSt. (Netto)', default=0)
    subtotal_brutto = models.FloatField(verbose_name='Zwischensumme (Brutto)', default=0)

    # Mahngebühr
    reminder_fee = models.FloatField(verbose_name='Mahngebühr', default=0)

    discount = models.FloatField(verbose_name='Rabatt in €', default=0)

    # BTM Gebühr
    btm_fee = models.FloatField(verbose_name='BTM Gebühr', default=0)

    delivery_type = models.CharField(verbose_name='Liefertyp', max_length=255, choices=DeliveryTypeChoices, blank=True)
    delivery_costs = models.FloatField(verbose_name='Lieferkosten', default=0)
    intern_delivery_costs = models.FloatField(verbose_name='Interne Lieferkosten', default=0)

    # Payment Fee
    payment_fee = models.FloatField(verbose_name='Bearbeitungsgebühr Bezahlmethode', default=0)

    # Summe Brutto
    total = models.FloatField(verbose_name='Verkaufspreis (Brutto)', default=0)

    # Versicherungsbeteiligung
    co_payment = models.FloatField(verbose_name='Zuzahlung (Kunde)', default=0)
    insurance_participation = models.FloatField(verbose_name='Versicherungsbeteiligung', default=0)

    # Versicherungsdaten
    health_insurance_company = models.CharField(verbose_name='Gesetz. Krankenversicherung', max_length=255, blank=True)
    health_insurance_contact_person = models.CharField(verbose_name='Kontakt bei Krankenversicherung', max_length=255, blank=True)

    # Zu zahlender Betrag
    amount_payable = models.FloatField(verbose_name='Zu zahlender Betrag', default=0)

    # Payment
    payment_type = models.CharField(verbose_name='Bezahlmethode', max_length=255, choices=PaymentTypeChoices, blank=True)
    paypal_plan_id = models.CharField(verbose_name='Paypal Plan Id', max_length=255, blank=True)

    # Nur für Kauf auf Rechnung
    ident_check = models.BooleanField(verbose_name='Identität geprüft (Kauf auf Rechnung)', default=False)
    ident_number = models.CharField(verbose_name='Ausweisnummer (Kauf auf Rechnung)', max_length=64, blank=True)
    credit_check = models.BooleanField(verbose_name='Bonitätsprüfung durchgeführt (Kauf auf Rechnung)', default=False)

    ordered = models.BooleanField(verbose_name='Bestellt', default=False)

    payment_status = models.CharField(verbose_name='Zahlungsstatus', max_length=255, choices=[(choice[0], choice[1]) for choice in PaymentStatusChoices], default='pending')
    recipe_status = models.CharField(verbose_name='Original Rezeptstatus', max_length=255, choices=RecipeStatusChoices, default='not_received')
    online_recipe_status = models.CharField(verbose_name='Online Rezeptstatus', max_length=255, choices=OnlineRecipeStatusChoices, default='open')

    status = models.CharField(verbose_name='Status', max_length=255, choices=[(choice[0], choice[1]) for choice in OrderStatusChoices], default='open')
    queries_comment = models.TextField(verbose_name='Rückfragen', max_length=65535, blank=True)
    clarified_comment = models.TextField(verbose_name='Klärung', max_length=65535, blank=True)
    intern_comment = models.TextField(verbose_name='Interne Notiz', max_length=65535, blank=True)
    shipped_on = models.DateTimeField(verbose_name='Versendet am', null=True, blank=True)
    delivered_on = models.DateTimeField(verbose_name='Geliefert am', null=True, blank=True)
    payed_on = models.DateTimeField(verbose_name='Bezahlt am', null=True, blank=True)

    invoice_reminder_send_on = models.DateTimeField(verbose_name='Zahlungserinnerung am', null=True, blank=True)
    last_reminder_send_on = models.DateTimeField(verbose_name='Mahnung am', null=True, blank=True)

    # Erstellt von
    created_by = models.ForeignKey(User, verbose_name='Erstellt von', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_created_by')

    # Ansay order id
    ansay_order_id = models.CharField(verbose_name='Ansay Bestellnummer', max_length=255, blank=True)

    cancellation_reason = models.ForeignKey(CancellationReasons, verbose_name='Stornierungsgrund', on_delete=models.SET_NULL, null=True, blank=True)

    is_packed = models.BooleanField(verbose_name='Verpackt', default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Saves the original value from ordered
        self.__original_ordered = self.ordered

        # Saves the original value from status
        self.__original_status = self.status

        # Relevant fields for credit score check
        relevant_fields = {
            'salutation': self.salutation,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'street': self.street,
            'street_number': self.street_number,
            'postalcode': self.postalcode,
            'city': self.city,
            'birth_date': self.birth_date,
        }

        self._original_data = {field: getattr(self, field) for field in relevant_fields}

    def save(self, *args, **kwargs):
        """ Save """

        # Customer details
        if self.customer:
            if not self.customer_type or self.customer_type == '':
                self.customer_type = self.customer.customer_type

            if not self.salutation or self.salutation == '':
                self.salutation = self.customer.salutation

            if not self.birth_date:
                self.birth_date = self.customer.birth_date

            if not self.first_name:
                self.first_name = self.customer.user.first_name
                
            if not self.last_name:
                self.last_name = self.customer.user.last_name

            if not self.street:
                self.street = self.customer.street

            if not self.street_number:
                self.street_number = self.customer.street_number

            if not self.postalcode:
                self.postalcode = self.customer.postcode

            if not self.city:
                self.city = self.customer.city

            if not self.state:
                self.state = self.customer.state

            if not self.country:
                self.country = self.customer.country

            if not self.phone_number:
                self.phone_number = self.customer.phone

            if not self.email_address:
                self.email_address = self.customer.user.email

            if not self.health_insurance_company:
                self.health_insurance_company = self.customer.health_insurance_company

            if not self.health_insurance_contact_person:
                self.health_insurance_contact_person = self.customer.health_insurance_contact_person
        
        # Strip customer fields
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        self.street = self.street.strip()
        self.street_number = self.street_number.strip()
        self.postalcode = self.postalcode.strip()
        self.city = self.city.strip()

        if self.delivery_address_as_invoice:

            self.del_first_name = self.first_name.strip()
            self.del_last_name = self.last_name.strip()
            self.del_street = self.street.strip()
            self.del_street_number = self.street_number.strip()
            self.del_postalcode = self.postalcode.strip()
            self.del_city = self.city.strip()
            self.del_state = self.state
            self.del_country = self.country

        # Strip delivery fields
        self.del_first_name = self.del_first_name.strip()
        self.del_last_name = self.del_last_name.strip()
        self.del_street = self.del_street.strip()
        self.del_street_number = self.del_street_number.strip()
        self.del_postalcode = self.del_postalcode.strip()
        self.del_city = self.del_city.strip()

        # Deliverytype
        if self.delivery_type == 'pickup':
            self.delivery_costs = 0
        elif self.delivery_type:
            try:
                delivery_type = DeliveryTypes.objects.get(name=self.delivery_type)
                
                # Free delivery bevore 13. Mai 2024
                # if self.order_time.date() < timezone.datetime(2024, 5, 13).date():
                if self.order_time < timezone.datetime(2024, 5, 13, 15, 30, 0, tzinfo=timezone.utc):
                    self.delivery_costs = 0
                else:
                    if delivery_type.free_deliver_amount != 0 and self.subtotal >= delivery_type.free_deliver_amount:
                        self.delivery_costs = 0
                    else:
                        self.delivery_costs = delivery_type.price

                # Intern delivery costs
                if delivery_type:
                    self.intern_delivery_costs = delivery_type.intern_price

            except ObjectDoesNotExist:
                self.delivery_costs = 0

        # Paymenttype
        self.payment_fee = 2.5 if self.payment_type == 'payment_by_invoice' else 0

        # Get fix prices from PriceSettings
        price_settings = PriceSettings.objects.all().first()

        if price_settings:

            # Umsatzsteuer
            self.tax_amount = round(self.subtotal * price_settings.tax_rate, 2)

        self.subtotal_brutto = round(self.subtotal + self.tax_amount, 2)
        self.total = round(self.subtotal + self.tax_amount + self.delivery_costs + self.payment_fee - self.discount + self.reminder_fee, 2)

        if self.order_time.date() < timezone.datetime(2024, 4, 1).date():
            self.total = round(self.total + self.btm_fee, 2)

        # Kassenpatient Zuzahlungsbefreit
        if self.customer_type in ['insurance_patient']:
            self.co_payment = 0

        if self.customer_type in ['insurance_patient_with_supplement', 'insurance_patient']:
            self.insurance_participation = self.total - (self.co_payment + self.delivery_costs)

            # Zu Zahlender Betrag
            self.amount_payable = round(self.co_payment + self.delivery_costs, 2)

        else:
            self.co_payment = 0
            self.insurance_participation = 0

            # Zu Zahlender Betrag
            self.amount_payable = self.total

        if self.ordered:

            if self.customer and not self.__original_ordered:

                self.customer.birth_date = self.birth_date
                self.customer.salutation = self.salutation
                self.customer.user.first_name = self.first_name.strip()
                self.customer.user.last_name = self.last_name.strip()
                self.customer.street = self.street.strip()
                self.customer.street_number = self.street_number.strip()
                self.customer.postcode = self.postalcode.strip()
                self.customer.city = self.city.strip()
                self.customer.state = self.state
                self.customer.country = self.country
                self.customer.phone = self.phone_number
                self.customer.health_insurance_company = self.health_insurance_company
                self.customer.health_insurance_contact_person = self.health_insurance_contact_person

                self.customer.save()
                self.customer.user.save()

            # if self.payment_status == 'received' and self.recipe_status in ['received', 'checked'] and self.status in ['ordered', 'open']:
            #     self.status = 'process'

            if self.delivery_type == 'pickup' and self.payment_status != 'received' and self.payment_type == 'payment_at_pickup':
                self.payment_status = 'at_pickup'

            ### Bestellnummer ####
            if not self.number:

                date = timezone.now()
                year = date.strftime('%y')

                pharmacy_id = self.pharmacy.pharmacy_ext_id if self.pharmacy.pharmacy_ext_id else 000

                order_numbers = list(Orders.objects
                                    .filter(ordered=True, order_time__year=date.year, pharmacy=self.pharmacy)
                                    .exclude(number='')
                                    .values_list('number', flat=True)
                                    .order_by('number')
                                    )

                if len(order_numbers) != 0:
                    last_number = order_numbers[-1]
                    number = str(int(last_number) + 1)
                else:
                    number = str(year) + str(pharmacy_id) + '100001'

                self.number = number

        # Update delivery date
        if self.status == 'delivered' and not self.delivered_on:
            self.delivered_on = timezone.now()

        # Update order_time when orderd
        if self.ordered and not self.__original_ordered:
            self.order_time = timezone.now()

        # Cannot change back to started, open or ordered
        if self.status in ['started', 'open', 'ordered', 'in_review'] and self.__original_status not in ['started', 'open', 'ordered', 'in_review']:
            self.status = self.__original_status

        # Change online recipe status if recipe status is received or checked
        if self.recipe_status in ['received', 'checked'] and self.online_recipe_status == 'open':
            self.online_recipe_status = 'checked'

        self.__original_ordered = self.ordered

        # Relevant fields for credit score check
        if self.pk:

            current_data = {field: getattr(self, field) for field in self._original_data.keys()}
            changes = {field: (self._original_data[field], current_data[field]) for field in current_data if self._original_data[field] != current_data[field]}
            
            # If changes in relevant fields are detected, set credit_check to False
            if changes:
                self.credit_check = False

        super(Orders, self).save(*args, **kwargs)

        # Relevant fields for credit score check
        for field in self._original_data.keys():
            self._original_data[field] = getattr(self, field)

    def __str__(self):
        return f'{self.id} - {self.first_name} {self.last_name} ({self.order_time.strftime("%d.%m.%Y")})'

    @property
    def total_product_amount(self):
        """ Get total product amount """

        order_articles = OrderProducts.objects.filter(order=self, product__form='flower').aggregate(total_amount=Sum('amount'))
            
        return order_articles['total_amount'] if order_articles['total_amount'] else 0

def recipe_upload(instance, filename):
    """ Uploaden eines Banners """

    upload_to = 'orders/' + str(instance.order.id) + '/recipes/'

    ext = filename.split('.')[-1]
    
    try:
        this = OrderRecipes.objects.get(id=instance.id)
        if this.file != "":
            path = this.file.path
            os.remove(path)
            
        filename = '{}.{}'.format(str(uuid.uuid4()), ext)
    except Exception:
        filename = '{}.{}'.format(str(uuid.uuid4()), ext)

    return os.path.join(upload_to, filename)

class OrderRecipes(models.Model):
    """ Rezepte """

    class Meta:
        """ Meta """
        verbose_name = 'Rezept'
        verbose_name_plural = 'Rezepte'

    order = models.ForeignKey(Orders, verbose_name='Bestellungen', on_delete=models.CASCADE)
    file = models.FileField(verbose_name='Rezept', upload_to=recipe_upload, blank=True)
    number = models.CharField(verbose_name='Rezeptnummer', max_length=255, blank=True)
    e_recipe = models.BooleanField(verbose_name='E-Rezept', default=False)

    # Auszustellender Arzt
    doctor_first_name = models.CharField(verbose_name='Arzt Vorname', max_length=255, blank=True)
    doctor_last_name = models.CharField(verbose_name='Arzt Nachname', max_length=255, blank=True)
    doctor_phone = models.CharField(verbose_name='Arzt Telefon', max_length=255, blank=True)
    city_of_signature = models.CharField(verbose_name='Ort der Unterschrift', max_length=255, blank=True)
    date_of_signature = models.DateField(verbose_name='Datum der Unterschrift', blank=True, null=True)

    def save(self, *args, **kwargs):
        """ Save """

        if self.e_recipe:
            self.number = 'E-Rezept'

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'Bestellid: { self.order.id }. Rezeptnr.: { self.number }'

@receiver(post_delete, sender=OrderRecipes)
#pylint: disable=unused-argument
def delete_recipe_file(sender, instance, **kwargs):
    """ Delete recipe file """
    try:
        os.remove(instance.file.path)
    except OSError:
        pass

class OrderProducts(models.Model):
    """ Bestellprodukte """

    class Meta:
        """ Meta """
        verbose_name = 'Bestellprodukt'
        verbose_name_plural = 'Bestellprodukte'

    product = models.ForeignKey(Products, verbose_name='Produkt', on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Orders, related_name='Bestellung', on_delete=models.CASCADE)

    amount = models.PositiveIntegerField(verbose_name='Menge', default=0)
    purchase_price = models.FloatField(verbose_name='Einkaufspreis', default=0, null=True)
    price_surcharge = models.FloatField(verbose_name='Aufschlag', default=0, null=True)
    price_per_unit = models.FloatField(verbose_name='Preis pro Einheit (Netto)', default=0, null=True)
    price_net = models.FloatField(verbose_name='Produktpreis (Netto)', default=0, null=True)
    price = models.FloatField(verbose_name='Produktpreis (Brutto)', default=0, null=True)
    discount = models.FloatField(verbose_name='Rabatt', default=0, null=True)

    # Fixzuschlag
    fixed_supplement = models.FloatField(verbose_name='Fixzuschlag', default=0)

    # Festzuschlag verarbeitung
    fixed_supplement_prepared = models.FloatField(verbose_name='Festzuschlag auf Zubereitung', default=0)
    recipe_supplement = models.FloatField(verbose_name='Rezeptzuschlag Zubereitung', default=0)

    # AEK Verpackung
    aek_package = models.FloatField(verbose_name='APEK Verpackung', default=2)
    surcharge_packing = models.FloatField(verbose_name='Zuschlag von auf Packmittel', default=2)

    # Anteil Dronabinol
    prescribed_proportion_cannabis_extract = models.FloatField(verbose_name='Verschriebener Anteil Dronabinol mg/ml', default=50)
    proportion_cannabis_extract = models.FloatField(verbose_name='Anteil Dronabinol mg/g', default=50)

    # Summe
    total = models.FloatField(verbose_name='Verkaufspreis (Brutto)', default=0, null=True)

    prepared = models.BooleanField(verbose_name='Zerkleinert')
    is_requested = models.BooleanField(verbose_name='Angefragtes Produkt', default=False)
    requested_product = models.ForeignKey(ProductRequest, verbose_name='Angefragtes Produkt', on_delete=models.SET_NULL, null=True, blank=True)

    # Für den Lagerbestand
    calculated_in_stock = models.BooleanField(verbose_name='Berechnet im Lagerbestand', default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_product = self.product if self.pk else None

    def save(self, *args, **kwargs):
        """ Save """

        price_settings = PriceSettings.objects.all().first()

        if self.order and self.product:
            try:
                product_prices = ProductPrices.objects.get(product=self.product, pharmacy=self.order.pharmacy)
            except ObjectDoesNotExist:
                product_prices = None

        if price_settings:

            ###### If flower ######
            if self.product.form == 'flower':

                ##### Verändert #####
                if self.prepared:
                    self.aek_package = round(price_settings.aek_package_prepared if price_settings.aek_package_prepared else self.aek_package, 2)
                ##### Unverändert #####
                else:
                    self.aek_package = round(price_settings.aek_package if price_settings.aek_package else self.aek_package, 2)

            elif self.product.form == 'extract':

                ##### Verändert #####
                if self.prepared:
                    self.aek_package = round(price_settings.triglycerides_price + price_settings.bottle_price + price_settings.dosing_pipette + price_settings.screw_mount, 2)

                ##### Unverändert #####
                else:
                    self.aek_package = round(price_settings.bottle_price + price_settings.dosing_pipette + price_settings.screw_mount, 2)

        if product_prices:

            ###### Kassenpatient ######
            if self.order.customer_type in ['insurance_patient_with_supplement', 'insurance_patient']:
                
                if not self.price and self.product != self.__original_product:
                    self.purchase_price = product_prices.purchase_price
                    self.price_surcharge = product_prices.price_surcharge
                    self.price_per_unit = product_prices.pirce_per_unit
                    self.price = product_prices.selling_price

                ##### If flower #####
                if self.product.form == 'flower':

                    amount_cannabis = self.amount
                    
                    #### Verändert ####
                    if self.prepared:

                        # Festzuschlag Zubereitung
                        self.fixed_supplement_prepared = 8.35
                        self.recipe_supplement = 6.00

                        # Fixzuschlag
                        tiers = [(15, 8.56), (30, 3.70), (float('inf'), 2.60)]
                        self.fixed_supplement = round(calculate_fixed_supplement(self.amount, tiers), 2)

                        # AEP Verpackung
                        self.surcharge_packing = round(self.aek_package * 0.9, 2)

                    #### Unverändert ####
                    else:
                        
                        # Fixzuschlag
                        tiers = [(15, 9.52), (30, 3.70), (float('inf'), 2.60)]
                        self.fixed_supplement = round(calculate_fixed_supplement(self.amount, tiers), 2)

                        # AEP Verpackung
                        self.surcharge_packing = round(self.aek_package * 1, 2)

                ##### If extract #####
                elif self.product.form == 'extract':

                    #### Verändert ####
                    if self.prepared:

                        # Festzuschlag Zubereitung
                        self.fixed_supplement_prepared = 8.35
                        self.recipe_supplement = 3.50

                        # Berechnung der benötigten Menge an Dronabinol = mg
                        amount_needed = self.prescribed_proportion_cannabis_extract * self.amount

                        # Anteil Cannabisextrakt in der bestellten Menge anhand der Dichte = g
                        amount_cannabis = amount_needed / self.proportion_cannabis_extract

                        # Umrechnung der Masse in Volumen = ml
                        volume_required = round(amount_cannabis * self.product.rel_density, 2)
                        
                        # Zuschlag = AEK * Anteil Cannabisextrakt
                        surcharge = self.price_surcharge * volume_required

                        # Wenn 90% vom Zuschlag den max. Zuschlag von 80€ überschreitet
                        if (surcharge * 0.9) > 80:

                            # Anteilige Menge = Menge - (Max. Zuschlag / Einkaufspreis)
                            proportionate_amount = amount_cannabis - (80 / (self.price_surcharge * 0.9))

                            # Anteiliger VK = Anteilige Menge * Apotheke EK * Prozentualer Anteil von 8,4%
                            proportionate_surcharge = proportionate_amount * self.price_surcharge * 0.03

                            self.fixed_supplement = round(80 + proportionate_surcharge, 2)

                        # Zuschlag unter 80€
                        else:
                            self.fixed_supplement = round(surcharge * 0.9, 2)

                        # Packmittel
                        self.surcharge_packing = round(self.aek_package * 0.9, 2)

                    #### Unverändert ####
                    else:

                        # Amount
                        amount_cannabis = self.amount

                        # Maximaler EK 4,85 €/ml
                        purchase_price = self.price_per_unit if self.price_per_unit <= 4.85 else 4.85

                        # Zuschlag = EK * Menge
                        surcharge = purchase_price * self.amount

                        # Wenn Zuchlag den max. Zuschlag von 80€ überschreitet
                        if surcharge > 80:

                            # Anteilige Menge = Menge - (Max. Zuschlag / Einkaufspreis)
                            proportionate_amount = self.amount - (80 / purchase_price)

                            # Anteiliger VK = Anteilige Menge * Apotheken EK * Prozentualer Anteil von 8,4 %
                            proportionate_surcharge = proportionate_amount * self.price_per_unit * 0.084

                            self.fixed_supplement = round(80 + proportionate_surcharge, 2)

                        # Zuschlag unter 80€
                        else:
                            self.fixed_supplement = round(surcharge, 2)

                        # Packmittel
                        self.surcharge_packing = self.aek_package * 1


                ##### Berechnung der Summe #####
                # Total = (Menge * VK Preis) + Fixzuschlag + AEK Packung + Zuschlag Packmittel
                self.total = round((amount_cannabis * self.price_per_unit) + self.fixed_supplement + self.aek_package + self.surcharge_packing + self.fixed_supplement_prepared + self.recipe_supplement, 2)


            ###### Selbstzahler #####
            if self.order.customer_type in ['self_payer']:

                if not self.price and self.product != self.__original_product:
                    self.purchase_price = product_prices.purchase_price
                    self.price_surcharge = product_prices.price_surcharge
                    self.price_per_unit = product_prices.pirce_per_unit
                    self.price_net = product_prices.self_payer_selling_price
                    self.price = product_prices.self_payer_selling_price_brutto

                ##### If flowser #####
                if self.product.form == 'flower':

                    # Fixzuschlag nach Angabe pro Produkt Zuschlag vom EK-Preis
                    self.fixed_supplement = round(self.amount * self.purchase_price * self.price_surcharge, 2)

                    #### Verändert ####
                    if self.prepared:
                        
                        # Festzuschlag Zubereitung
                        self.fixed_supplement_prepared = 8.35
                        self.recipe_supplement = 6.00

                        # AEP Verpackung
                        self.surcharge_packing = round(self.aek_package * 0.9, 2)

                    #### Unverändert ####
                    else:

                        # AEP Verpackung
                        self.surcharge_packing = self.aek_package * 1

                ##### Extrakt #####
                if self.product.form == 'extract':

                    # Fixzuschlag nach Angabe pro Produkt Zuschlag vom EK-Preis
                    self.fixed_supplement = round(self.amount * self.price_surcharge * self.price_surcharge, 2)

                    #### Verändert ####
                    if self.prepared:

                        # Festzuschlag Zubereitung
                        self.fixed_supplement_prepared = 8.35
                        self.recipe_supplement = 3.50

                        # AEP Verpackung
                        self.surcharge_packing = round(self.aek_package * 0.9, 2)

                    #### Unverändert ####
                    else:

                        # AEP Verpackung
                        self.surcharge_packing = self.aek_package * 1

                # Berechnung der Summe
                if not self.prepared:
                    # Total = (Menge * AEK Preis)
                    self.total = round((self.amount * self.price) , 2)
                else:
                    # Total = (Menge * AEK Preis) + Festzuschlag Zubereitung + AEP Verpackung
                    self.total = round((self.amount * self.price) + self.fixed_supplement_prepared + self.recipe_supplement, 2)
        
        return super(OrderProducts, self).save(*args, **kwargs)

    def __str__(self):
        return f'Bestellung: {str(self.order.id)} Produkt: {self.product.name if self.product else ""} Preis: {self.total}'

@receiver(post_save, sender=OrderProducts)
@receiver(post_delete, sender=OrderProducts)
#pylint: disable=unused-argument
def update_orderarticles(sender, instance, **kwargs):
    """ Calculate total after update """
    order_articles = OrderProducts.objects.filter(order=instance.order).aggregate(total_price=Sum('total'))
    total_price = order_articles['total_price'] if order_articles['total_price'] else 0

    # Subtotal price
    instance.order.subtotal = round(total_price / (1 + PriceSettings.objects.first().tax_rate), 2)

    # Zuzahlung Kassenpatient
    # Get fix prices from PriceSettings
    price_settings = PriceSettings.objects.all().first()

    co_payment = 0

    if instance.order.customer_type in ['insurance_patient_with_supplement']:

        for order_article in OrderProducts.objects.filter(order=instance.order):

            article_total = order_article.total * (1 + price_settings.tax_rate)

            if article_total <= 50:
                co_payment += 5
            elif 50 <= article_total <= 100:
                co_payment += round(article_total * 0.1, 2)
            else:
                co_payment += 10

    instance.order.co_payment = co_payment

    instance.order.save()

class PackageManufacturers(models.Model):
    """Verpackungshersteller"""

    class Meta:
        verbose_name = 'Verpackungshersteller'
        verbose_name_plural = 'Verpackungshersteller'

    name = models.CharField(verbose_name='Herstellername', max_length=255)

    def __str__(self):
        return self.name
    
class Packages(models.Model):
    """ Verpackungen """

    class Meta:
        """ Meta """
        verbose_name = 'Verpackung'
        verbose_name_plural = 'Verpackungen'

    name = models.CharField(verbose_name='Bezeichnung', max_length=255)
    batch_number = models.CharField(verbose_name='Chargennummer', max_length=255, unique=True)
    manufacturer = models.ForeignKey(PackageManufacturers, verbose_name='Packungshersteller', on_delete=models.CASCADE)
    size = models.CharField(verbose_name='Packungsgröße', choices=PackageSizeChoices, max_length=10, default=0)
    amount = models.PositiveIntegerField(verbose_name='Menge', default=0)
    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.pharmacy}: {self.name} - {self.size} - {self.batch_number} - {self.pharmacy}'

class StockProducts(models.Model):
    """ Lagerbestand """

    class Meta:
        """ Meta """
        verbose_name = 'Lagerbestand'
        verbose_name_plural = 'Lagerbestände'

    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, verbose_name='Produkt', on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name='Menge', default=0)
    status = models.CharField(verbose_name='Status', max_length=255, choices=StockStatusChoices, default='3')
    amount_status = models.CharField(verbose_name='Mengenstatus', max_length=255, choices=StockAmountStatusChoices, default='2')
    batch_number = models.CharField(verbose_name='Chargennummer', max_length=255, blank=True)
    verification_number = models.CharField(verbose_name='Prüfnummer', max_length=255, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        """ Define save """

        if self.amount == 0 and self.status in ['2', '3']:
            self.status = '0'
            self.amount_status = '0'

        if self.amount > 0 and self.amount < 100:
            self.amount_status = '1'

        if self.amount >= 100:
            self.amount_status = '2'

        if self.amount > 0 and self.status == '0':
            self.status = '3'

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{ self.pharmacy.name }: {self.product.name} / {self.batch_number} - {self.amount}'
    
class PackedOrderedProducts(models.Model):
    """ Verpackte Bestellprodukte """

    class Meta:
        """ Meta """
        verbose_name = 'Verpackte Bestellprodukt'
        verbose_name_plural = 'Verpackte Bestellprodukte'

    order_product = models.ForeignKey(OrderProducts, verbose_name='Bestellprodukt', on_delete=models.CASCADE)
    package = models.ForeignKey(Packages, verbose_name='Verpackung', on_delete=models.CASCADE)
    stock_product = models.ForeignKey(StockProducts, verbose_name='Lagerprodukt', on_delete=models.CASCADE)
    fill_amount = models.PositiveIntegerField(verbose_name='Menge', default=0)
    packer_name = models.ForeignKey(PharmacyEmployees, verbose_name='Verpacker', on_delete=models.SET_NULL, null=True, related_name='packer_name')
    supervisor_name = models.ForeignKey(PharmacyEmployees, verbose_name='Supervisor', on_delete=models.SET_NULL, null=True, related_name='supervisor_name')
    calculated_in_stock = models.BooleanField(verbose_name='Berechnet im Lagerbestand', default=False)

    def __str__(self):
        return f'{self.order_product.order.pharmacy.name} {self.order_product.order.id} - {self.order_product.product.name} ({self.stock_product.batch_number}) - {self.fill_amount} - {self.package.batch_number}' 
    
class FillProtocols(models.Model):
    """ Abfüllprotokolle """

    class Meta:
        """ Meta """
        verbose_name = 'Abfüllprotokoll'
        verbose_name_plural = 'Abfüllprotokolle'

    order = models.ForeignKey(Orders, verbose_name='Bestellung', on_delete=models.CASCADE)
    order_product = models.ForeignKey(OrderProducts, verbose_name='Bestellprodukt', on_delete=models.SET_NULL, null=True)
    external_id = models.CharField(verbose_name='Protokollnummer', max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.order.pharmacy.name} - {self.external_id}'
    
    def save(self, *args, **kwargs):
        """ Define save """

        if not self.external_id:

            # Get first two characters of standard filling protocol id
            standard_protcol_id = StandardFillingProtocolIds.objects.filter(pharmacy=self.order.pharmacy).order_by('-date').first()
            short = standard_protcol_id.protocol_id[:2]

            today = timezone.now().strftime('%y%m%d')
            last_protocol = FillProtocols.objects.filter(
                external_id__startswith=f'{short}{today}',
                order__pharmacy=self.order.pharmacy
            ).order_by('external_id').last()
            
            if last_protocol:
                last_number = int(last_protocol.external_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.external_id = f'{short}{today}-{new_number:04d}'
        
        super().save(*args, **kwargs)

class StockProductsLogger(models.Model):
    """ Lagerbestandsprotokolle """

    class Meta:
        """ Meta """
        verbose_name = 'Lagerbestandsprotokoll'
        verbose_name_plural = 'Lagerbestandsprotokolle'

    stock_product = models.ForeignKey(StockProducts, verbose_name='Lagerprodukt', on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name='Menge', default=0)
    action = models.CharField(verbose_name='Aktion', max_length=255, choices=StockActionChoices, default='add')
    reason = models.CharField(verbose_name='Grund', max_length=255)
    user = models.CharField(verbose_name='Benutzer', max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.stock_product.pharmacy.name} - {self.stock_product.product.name} - {self.amount}'

class PackagesLogger(models.Model):
    """ Verpackungsprotokolle """

    class Meta:
        """ Meta """
        verbose_name = 'Verpackungsprotokoll'
        verbose_name_plural = 'Verpackungsprotokolle'

    package = models.ForeignKey(Packages, verbose_name='Verpackung', on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name='Menge', default=0)
    action = models.CharField(verbose_name='Aktion', max_length=255, choices=StockActionChoices, default='add')
    reason = models.CharField(verbose_name='Grund', max_length=255)
    user = models.CharField(verbose_name='Benutzer', max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.package.pharmacy.name} - {self.package.name} - {self.amount}'

@receiver(post_save, sender=PackedOrderedProducts)
#pylint: disable=unused-argument
def update_stock_after_packed_order_product_save(sender, instance, **kwargs):
    """ Update stock after packed order product is saved """

    stock_product = instance.stock_product

    if not instance.calculated_in_stock:

        if instance.fill_amount > 0:

            if instance.fill_amount > stock_product.amount:
                stock_product.amount = 0
            else:
                stock_product.amount -= instance.fill_amount

            stock_product.save()

            package = instance.package

            if package.amount > 0:
                package.amount -= 1

            package.save()

            # Log stock product
            StockProductsLogger.objects.create(
                stock_product=stock_product,
                amount=instance.fill_amount,
                action='remove',
                reason=f'Produkt { instance.order_product.product.name } der Bestellung { instance.order_product.order.number } verpackt',
                user='System'
            )

            # Log package
            PackagesLogger.objects.create(
                package=package,
                amount=1,
                action='remove',
                reason=f'Produkt { instance.order_product.product.name } der Bestellung { instance.order_product.order.number } verpackt',
                user='System'
            )

            instance.calculated_in_stock = True
            instance.save(update_fields=['calculated_in_stock'])

@receiver(post_delete, sender=PackedOrderedProducts)
#pylint: disable=unused-argument
def update_stock_after_packed_order_product_delete(sender, instance, **kwargs):
    """ Update stock after packed order product is deleted """

    stock_product = instance.stock_product

    if instance.calculated_in_stock:

        if instance.fill_amount > 0:

            stock_product.amount += instance.fill_amount
            stock_product.save()

            package = instance.package
            package.amount += 1
            package.save()

            # Log stock product
            StockProductsLogger.objects.create(
                stock_product=stock_product,
                amount=instance.fill_amount,
                action='add',
                reason=f'Verpacktes Produkt { instance.order_product.product.name } der Bestellung { instance.order_product.order.number } gelöscht',
                user='System'
            )

            # Log package
            PackagesLogger.objects.create(
                package=package,
                amount=1,
                action='add',
                reason=f'Verpacktes Produkt { instance.order_product.product.name } der Bestellung { instance.order_product.order.number } gelöscht',
                user='System'
            )

def identification_file_upload(instance, filename):
    """ Uploaden eines Ausweisdokuments """

    upload_to = 'orders/' + str(instance.order.id) + '/identificationFiles/'

    ext = filename.split('.')[-1]
    
    try:
        this = IdentificationFiles.objects.get(id=instance.id)
        if this.file != "":
            path = this.file.path
            os.remove(path)
            
        filename = '{}-{}-{}.{}'.format(instance.order.id, instance.order.last_name, instance.id_number, ext)
    except Exception:
        filename = '{}-{}-{}.{}'.format(instance.order.id, instance.order.last_name, instance.id_number, ext)

    return os.path.join(upload_to, filename)

class IdentificationFiles(models.Model):
    """ Ausweisdokumente für Bestellungen auf Rechnung """

    class Meta:
        """ Meta """
        verbose_name = "Ausweisdokument"
        verbose_name_plural = "Ausweisdokumente"

    order = models.ForeignKey(Orders, verbose_name='Ausweisdokumente', on_delete=models.CASCADE)
    file = models.FileField(verbose_name='Ausweisdokument 1', upload_to=identification_file_upload, blank=True)
    id_number = models.CharField(verbose_name='Ausweisnummer', max_length=255, blank=True)

    def is_image(self):
        """Prüft, ob die Datei ein Bild ist."""
        if self.file:
            return self.file.name.lower().endswith(('.png', '.jpg', '.jpeg'))
        return False

    def is_pdf(self):
        """Prüft, ob die Datei eine PDF ist."""
        if self.file:
            return self.file.name.lower().endswith('.pdf')
        return False

    def get_file_ending(self):
        """Gibt die Dateiendung zurück."""
        if self.file:
            return self.file.name.lower().split('.')[-1]
        return False
    
    def get_mime_type(self):
        """Gibt den MIME-Typ der Datei zurück."""
        mime_type, _ = mimetypes.guess_type(self.file.name)
        return mime_type

    def __str__(self):
        return f'Bestellid: {self.order.id}'

def confirmation_upload(instance, filename):
    """ Uploaden eines Banners """

    upload_to = 'orders/' + str(instance.order.id) + '/confirmation/'

    ext = filename.split('.')[-1]
    
    try:
        this = OrderRecipes.objects.get(id=instance.id)
        if this.file != "":
            path = this.file.path
            os.remove(path)
            
        filename = '{}.{}'.format('Confirmation', ext)
    except Exception:
        filename = '{}.{}'.format('Confirmation', ext)

    return os.path.join(upload_to, filename)

class OrderInsuranceConfirmation(models.Model):
    """ Konsteübernahme """

    class Meta:
        """ Meta """
        verbose_name = 'Konsteübernahme'
        verbose_name_plural = 'Konsteübernahme'

    order = models.ForeignKey(Orders, verbose_name='Bestellungen', on_delete=models.CASCADE)
    file = models.FileField(verbose_name='Rezept', upload_to=confirmation_upload, blank=True)

    def __str__(self):
        return f'Bestellid: { self.order.id }'

######################## Invoices ########################
class Invoices(models.Model):
    """ Rechnung """

    class Meta:
        """ Metainformationen"""
        verbose_name = 'Rechnung'
        verbose_name_plural = 'Rechnungen'

    main_settings = models.ForeignKey(MainSettings, verbose_name='Hauptsettings', on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customers, verbose_name='Kunde', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Orders, verbose_name='Bestellung', on_delete=models.SET_NULL, null=True, blank=True)

    # Rechnungsdetails
    invoice_number = models.CharField(verbose_name='Rechnungsnummer', max_length=255, blank=True)
    date = models.DateField(verbose_name='Datum', default=timezone.now)
    status = models.CharField(verbose_name='Status', max_length=255, choices=InvoiceStatus, blank=True, default='open')
    canceled = models.BooleanField(verbose_name='Storniert', default=False)
    cancellation_invoice = models.BooleanField(verbose_name='Stornorechnung', default=False)
    payment_type = models.CharField(verbose_name="Zahlmethode", max_length=255, choices=PaymentTypeChoices, blank=True)
    send_to_customer = models.BooleanField(verbose_name='An Kunden gesendet', default=False)
    pro_forma_invoice = models.BooleanField(verbose_name='Proformarechnung', default=False)

    # Kundendetails
    recipe_number = models.CharField(verbose_name='Rezeptnummer', max_length=255, blank=True)
    customer_type = models.CharField(verbose_name='Patiententyp', max_length=255, choices=CustomerTypeChoices, blank=True)
    customer_number = models.CharField(verbose_name='Kundenummer', max_length=255, blank=True)
    company_name = models.CharField(verbose_name='Firmenname', max_length=255, blank=True)
    first_name = models.CharField(verbose_name='Vorname', max_length=255, blank=True)
    last_name = models.CharField(verbose_name='Nachname', max_length=255, blank=True)
    street = models.CharField(verbose_name='Straße', max_length=255, blank=True)
    street_number = models.CharField(verbose_name='Hausnummer', max_length=255, blank=True)
    postalcode = models.CharField(verbose_name='Postleitzahl', max_length=255, blank=True)
    city = models.CharField(verbose_name='Stadt', max_length=255, blank=True)

    # Firmendetails
    own_company_name = models.CharField(verbose_name='Firmenname', max_length=255, blank=True)
    own_street = models.CharField(verbose_name='Straße', max_length=255, blank=True)
    own_street_number = models.CharField(verbose_name='Hausnummer', max_length=255, blank=True)
    own_postalcode = models.CharField(verbose_name='Postleitzahl', max_length=255, blank=True)
    own_city = models.CharField(verbose_name='Stadt', max_length=255, blank=True)

    # Beträge
    tax_rate = models.FloatField(verbose_name='Steuerrate', default=0.19)
    subtotal = models.FloatField(verbose_name='Netto', default=0, blank=True)
    tax_amount = models.FloatField(verbose_name='Steuern', default=0, blank=True)
    discount = models.FloatField(verbose_name='Rabatt', default=0, blank=True)
    payment_fee = models.FloatField(verbose_name='Bearbeitungsgebühr Bezahlmethode', default=0, blank=True)
    delivery_costs = models.FloatField(verbose_name='Lieferkosten', default=0, blank=True)
    btm_fee = models.FloatField(verbose_name='BTM Gebühr', default=0, blank=True)
    reminder_fee = models.FloatField(verbose_name='Mahngebühr', default=0, blank=True)
    total = models.FloatField(verbose_name='Brutto', default=0, blank=True)
    co_payment = models.FloatField(verbose_name='Zuzahlung (Kunde)', default=0)
    insurance_participation = models.FloatField(verbose_name='Versicherungsbeteiligung', default=0)
    already_paid = models.FloatField(verbose_name='Bereits bezahlt', default=0)
    amount_payable = models.FloatField(verbose_name='Zu zahlender Betrag', default=0)

    def save(self, *args, **kwargs):
        """ Save definieren """

        ##### Hauptdetails #####
        price_settings = PriceSettings.objects.first()

        if not self.cancellation_invoice and self.order:

            # Set own company details if not set
            if not self.own_company_name:
                self.own_company_name = self.order.pharmacy.invoice_name
                self.own_street = self.order.pharmacy.invoice_street
                self.own_street_number = self.order.pharmacy.invoice_street_number
                self.own_postalcode = self.order.pharmacy.invoice_postalcode
                self.own_city = self.order.pharmacy.invoice_city

            #### Kundendetails #####
            if self.order.customer:
                self.customer = self.order.customer
                self.customer_number = self.customer.id

            self.recipe_number = ", ".join([recipe.number for recipe in OrderRecipes.objects.filter(order=self.order)])
            self.customer_type = self.order.customer_type
            self.payment_type = self.order.payment_type
            self.first_name = self.order.first_name
            self.last_name = self.order.last_name
            self.street = self.order.street
            self.street_number = self.order.street_number
            self.postalcode = self.order.postalcode
            self.city = self.order.city

        ######## Beträge #######
        if not self.total:
            self.tax_rate = price_settings.tax_rate
            self.delivery_costs = self.order.delivery_costs
            self.discount = self.order.discount
            self.subtotal = self.order.subtotal
            self.tax_amount = self.order.tax_amount
            self.total = self.order.total
            self.payment_fee = self.order.payment_fee
            # BTM fee before new law
            self.btm_fee = self.order.btm_fee if self.order.order_time.date() < timezone.datetime(2024, 4, 1).date() else 0
            self.reminder_fee = self.order.reminder_fee
            self.co_payment = self.order.co_payment
            self.insurance_participation = self.order.insurance_participation
            self.amount_payable = self.order.amount_payable

        if self.canceled:
            self.status = 'canceled'
        elif self.status == 'canceled':
            self.canceled = True

        ### Rechnungsnummer ####
        if not 'RE' in self.invoice_number and not self.cancellation_invoice:

            date = timezone.now()
            year = date.strftime('%y')

            pharmacy_id = self.order.pharmacy.pharmacy_ext_id if self.order.pharmacy.pharmacy_ext_id else 000

            invoice_numbers = list(Invoices.objects
                                   .filter(cancellation_invoice=False, date__year=date.year, order__pharmacy=self.order.pharmacy)
                                   .values_list('invoice_number', flat=True)
                                   .order_by('invoice_number')
                                )

            if len(invoice_numbers) != 0:
                last_number = invoice_numbers[-1]
                only_number = int(last_number.split('RE')[-1])
                only_number += 1
                number = 'RE' + str(only_number)

            else:
                number = f'RE1{year}{pharmacy_id}100001'

            self.invoice_number = number

        # Stornorechnung
        elif not 'SRE' in self.invoice_number and self.cancellation_invoice:

            date = timezone.now()
            year = date.strftime('%y')

            pharmacy_id = self.order.pharmacy.pharmacy_ext_id if self.order.pharmacy.pharmacy_ext_id else 000

            invoice_numbers = list(Invoices.objects
                                   .filter(cancellation_invoice=True, order__pharmacy=self.order.pharmacy)
                                   .values_list('invoice_number', flat=True)
                                   .order_by('invoice_number')
                                   )

            if len(invoice_numbers) != 0:
                last_number = invoice_numbers[-1]
                only_number = int(last_number.split('RE')[-1])
                only_number += 1
                number = 'SRE' + str(only_number)

            else:
                number = f'SRE1{year}{pharmacy_id}100001'

            self.invoice_number = number

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.id}. {self.invoice_number} - {self.get_status_display()}'

class InvoiceItems(models.Model):
    """ Rechnungselemente """

    class Meta:
        """ Meta """
        verbose_name = 'Rechnungselement'
        verbose_name_plural = 'Rechnungselemente'

    invoice = models.ForeignKey(Invoices, verbose_name='Rechnung', on_delete=models.CASCADE)

    product_number = models.CharField(verbose_name='Produktnummer', max_length=255)
    product = models.CharField(verbose_name='Produktbezeichnung', max_length=255)
    form = models.CharField(verbose_name='Abgabeform', max_length=255, choices=CannabisFormChoices, blank=True)
    amount = models.CharField(verbose_name='Menge', max_length=255, blank=True)
    price = models.FloatField(verbose_name='Preis', default=0)
    discount = models.FloatField(verbose_name='Rabatt', default=0)
    total = models.FloatField(verbose_name='Summe', default=0)

    def __str__(self):
        return f'{self.invoice.invoice_number} - {self.product}'

@receiver(post_save, sender=Invoices)
#pylint: disable=unused-argument
def create_invoiceitems(sender, instance, created, **kwargs):
    """ Calculate total after update """
    
    if created:

        if not instance.cancellation_invoice:
            order_products = OrderProducts.objects.filter(order=instance.order)

            for order_product in order_products:
                InvoiceItems.objects.create(
                    invoice=instance,
                    product_number=order_product.product.number,
                    product=order_product.product.name,
                    form=order_product.product.form,
                    amount=str(order_product.amount) + ' g' if order_product.product.form == 'flower' else str(order_product.amount) + ' ml',
                    price=order_product.price,
                    discount=order_product.discount,
                    total=order_product.total
                )

@receiver(post_save, sender=Orders)
#pylint: disable=unused-argument
def create_invoice(sender, instance, **kwargs):
    """ Calculate total after update """
    
    if instance.ordered:
        if instance.online_recipe_status == 'checked' or \
            instance.payment_type in ['paypal', 'applepay', 'cc', 'prepayment']:

            try:
                invoice, created = Invoices.objects.get_or_create(order=instance, cancellation_invoice=False, canceled=False)
            except MultipleObjectsReturned:
                Invoices.objects.filter(order=instance, cancellation_invoice=False, canceled=False).delete()
                invoice = Invoices.objects.filter(order=instance, cancellation_invoice=False, canceled=False).last()

            if instance.payment_status == 'received':
                invoice.pro_forma_invoice = False
                invoice.status = 'paid'
                invoice.save()

            elif instance.payment_type == 'prepayment':
                invoice.pro_forma_invoice = True
                invoice.save()

            elif instance.payment_type == 'payment_by_invoice':
                invoice.pro_forma_invoice = True
                invoice.save()

    if instance.status == 'cancelled':

        try:
            invoice = Invoices.objects.get(order=instance, cancellation_invoice=False, canceled=False)
            invoice.canceled = True
            invoice.save()
        except ObjectDoesNotExist:
            pass

######################## Inhalt ########################
def effects_banner_image_upload(instance, filename):
    """ Uploaden eines Banners """

    upload_to = 'effects/banner/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = CannabisEffects.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)
            
        filename = '{}.{}'.format('banner_image' + now, ext)
    except Exception:
        filename = '{}.{}'.format('banner_image' + now, ext)

    return os.path.join(upload_to, filename)

def effects_image_upload(instance, filename):
    """ Uploaden eines Bilder """

    upload_to = 'effects/images/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]

    try:
        this = CannabisEffects.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)

        filename = f'banner_imgae{ now }.{ext}'
    except Exception:
        filename = f'banner_image{ now }.{ext}'

    return os.path.join(upload_to, filename)

class CannabisEffects(models.Model):
    """ Wirkungsweisen """

    class Meta:
        """ Meta """
        verbose_name = '(Template) Wirkungsweise'
        verbose_name_plural = '(Template) Wirkungsweisen'

    position = models.PositiveIntegerField(verbose_name='Position', default=1)
    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True, null=True)
    title = models.CharField(verbose_name='Titel', max_length=255, blank=True, null=True)
    teaser = models.TextField(verbose_name='Teaser Text', max_length=65535, blank=True, null=True)
    content = models.TextField(verbose_name='Inhalt als HTML', max_length=65535, blank=True, null=True)

    terpene_effects = models.ForeignKey(TerpeneEffects, verbose_name='Zugehörige Terpenen Effekte', on_delete=models.SET_NULL, null=True, blank=True)

    banner_image = models.ImageField(verbose_name='Banner Bild', upload_to=effects_banner_image_upload, blank=True, null=True)
    image = models.ImageField(verbose_name='Bild', upload_to=effects_image_upload, blank=True)

    source = models.TextField(verbose_name='Quelle', max_length=65535, blank=True, null=True)

    meta_title = models.CharField(verbose_name='Meta:Titel', max_length=255, blank=True, null=True)
    meta_description = models.TextField(verbose_name='Meta:Beschreibung', max_length=65535, blank=True, null=True)

    color = models.CharField(verbose_name='Farbschema', max_length=255, blank=True, null=True, default='#899a71')
    main_page = models.BooleanField(verbose_name='Hauptseite', default=False)

    active = models.BooleanField(verbose_name='Aktiv', default=True)

    url_name = models.CharField(verbose_name='Url Bezeichnung', max_length=255, blank=True, null=True)
    meta_title = models.CharField(verbose_name='Meta:Titel', max_length=255, blank=True)
    meta_description = models.TextField(verbose_name='Meta:Beschreibung', max_length=65535, blank=True)

    active = models.BooleanField(verbose_name='Aktiv', default=True)

    def save(self, *args, **kwargs):
        """ Define save """

        if self.url_name == '' or not self.url_name:
            url_name = re.sub(r'[^a-zA-Z]', '-', self.title)
            url_name = re.sub(r'-+', '-', url_name)
            self.url_name = url_name.lower()

        try:
            CannabisEffects.objects.get(position=self.position)
        except MultipleObjectsReturned:
            nums = list(CannabisEffects.objects.all().values_list('position' ,flat=True))
            self.position = find_position(nums)
        except ObjectDoesNotExist:
            pass

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.position}. {self.title}'

@receiver(post_delete, sender=CannabisEffects)
#pylint: disable=unused-argument
def delete_effect_images(sender, instance, **kwargs):
    """ Delete effect images """
    try:
        if instance.banner_image:
            os.remove(instance.banner_image.path)
    except OSError:
        pass

def indications_banner_image_upload(instance, filename):
    """ Uploaden eines Banners """

    upload_to = 'indications/banner/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = CannabisIndications.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)
            
        filename = '{}.{}'.format('banner_image' + now, ext)
    except Exception:
        filename = '{}.{}'.format('banner_image' + now, ext)

    return os.path.join(upload_to, filename)

def indications_image_upload(instance, filename):
    """ Uploaden eines Banners """

    upload_to = 'indications/image/'

    now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0]
    ext = filename.split('.')[-1]
    
    try:
        this = CannabisIndications.objects.get(id=instance.id)
        if this.logo != "":
            path = this.logo.path
            os.remove(path)
            
        filename = '{}.{}'.format('image' + now, ext)
    except Exception:
        filename = '{}.{}'.format('image' + now, ext)

    return os.path.join(upload_to, filename)

class CannabisIndications(models.Model):
    """ Indikationen """

    class Meta:
        """ Meta """
        verbose_name = '(Template) Indikationen'
        verbose_name_plural = '(Template) Indikationen'
        ordering = ['position']

    position = models.PositiveIntegerField(verbose_name='Position', default=1)
    name = models.CharField(verbose_name='Bezeichnung', max_length=255, blank=True)
    title = models.CharField(verbose_name='Titel', max_length=255, blank=True)
    teaser = models.TextField(verbose_name='Teaser Text', max_length=65535, blank=True)
    teaser_source = models.TextField(verbose_name='Quelle zum Teaser', max_length=65535, blank=True)
    content = models.TextField(verbose_name='Inhalt als HTML', max_length=65535, blank=True)

    indication = models.ForeignKey(Indications, verbose_name='Zugehörige Indication', on_delete=models.SET_NULL, null=True, blank=True)

    banner_image = models.ImageField(verbose_name='Banner Bild', upload_to=indications_banner_image_upload, blank=True)
    image = models.ImageField(verbose_name='Bild', upload_to=indications_image_upload, blank=True)

    source = models.TextField(verbose_name='Quelle', max_length=65535, blank=True)

    color = models.CharField(verbose_name='Farbschema', max_length=255, blank=True, null=True, default='#899a71')

    url_name = models.CharField(verbose_name='URL Bezeichnung', max_length=255, blank=True, null=True)
    meta_title = models.CharField(verbose_name='Meta:Titel', max_length=255, blank=True)
    meta_description = models.TextField(verbose_name='Meta:Beschreibung', max_length=65535, blank=True)

    active = models.BooleanField(verbose_name='Aktiv', default=True)

    def save(self, *args, **kwargs):
        """ define save """

        if self.url_name == '' or not self.url_name:
            url_name = re.sub(r'[^a-zA-Z]', '-', self.title)
            url_name = re.sub(r'-+', '-', url_name)
            self.url_name = url_name.lower()

        try:
            CannabisIndications.objects.get(position=self.position)
        except MultipleObjectsReturned:
            nums = list(CannabisIndications.objects.all().values_list('position' ,flat=True))
            self.position = find_position(nums)
        except ObjectDoesNotExist:
            pass

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.position}. {self.title}'

@receiver(post_delete, sender=CannabisIndications)
#pylint: disable=unused-argument
def delete_indication_images(sender, instance, **kwargs):
    """ Delete effect images """
    try:
        if instance.banner_image:
            os.remove(instance.banner_image.path)
    except OSError:
        pass

    try:
        if instance.image:
            os.remove(instance.image.path)
    except OSError:
        pass

######################## Inhalt ########################
class UserPremissions(models.Model):
    """ Nutzerrechte für den Adminbereich """

    class Meta:
        """ Meta """
        verbose_name = 'Nutzerrecht'
        verbose_name_plural = 'Nutzerrechte'

    user = models.ForeignKey(User, verbose_name='Benutzer', on_delete=models.CASCADE)
    view = models.CharField(verbose_name='Rechte', max_length=255, choices=DashboardViewsChoices)
    pharmacy = models.ForeignKey(Pharmacies, verbose_name='Apotheke', on_delete=models.CASCADE)

    read_premission = models.BooleanField(verbose_name='Lesen', default=True)
    write_premission = models.BooleanField(verbose_name='Schreiben', default=False)

    def save(self, *args, **kwargs):

        if self.write_premission:
            self.read_premission = True

        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.user.get_full_name()} - View: {self.get_view_display()} - Lesen: {self.read_premission}, Schreiben: {self.write_premission}'

class Logger(models.Model):
    """ Logger: Speichert Aktivitäten der Nutzer """

    class Meta:
        """ Meta """
        verbose_name = 'Logger'
        verbose_name_plural = 'Logger'

    user = models.CharField(verbose_name='User', max_length=255, default='System')
    category = models.CharField(verbose_name='Kategorie', max_length=255, choices=LoggerChoices, default='info')
    reference = models.CharField(verbose_name='Referenz', max_length=255, null=True)
    message = models.TextField(verbose_name='Message', max_length=65535, blank=True)
    stack_trace = models.TextField(verbose_name='Stack Trace', max_length=65535, blank=True)
    date_time = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f'{self.reference} | {self.message} | {self.date_time.strftime("%d.%m.%Y - %H:%M Uhr")}'

class StaffUser(models.Model):
    """ Mitarbeiter """

    class Meta:
        """ Meta """
        verbose_name = 'Mitarbeiter'
        verbose_name_plural = 'Mitarbeiter'

    user = models.OneToOneField(User, verbose_name='Benutzer', on_delete=models.CASCADE)
    selected_pharmacy = models.ForeignKey(Pharmacies, verbose_name='Letzte ausgewählte Apothejsontheke', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username
