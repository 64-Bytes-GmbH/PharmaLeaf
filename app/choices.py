""" Choices lists """

DaysChoices = [
    ('0', 'Montag'),
    ('1', 'Dienstag'),
    ('2', 'Mittwoch'),
    ('3', 'Donnerstag'),
    ('4', 'Freitag'),
    ('5', 'Samstag'),
    ('6', 'Sonntag'),
]

TreatmentChoices = [
    ('unirradiated', 'unbestrahlt'),
    ('irradiated', 'bestrahlt')
]

ProductStatusChoices = [
    ('3', 'Sofort verfügbar'),
    ('2', 'Verfügbar'),
    ('1', 'Auf Anfrage'),
    ('0', 'Nicht verfügbar'),
]

StockStatusChoices = [
    ('3', 'Auf Lager'),
    ('2', 'Verfügbar, Bestellt'),
    ('1', 'Bestellt'),
    ('0', 'Nicht verfügbar'),
]

StockAmountStatusChoices = [
    ('3', 'Auf Lager'),
    ('2', 'Wenige verfügbar'),
    ('0', 'Nicht verfügbar'),
]

PackageSizeChoices = [
    ('10', '10g'),
    ('15', '15g'),
    ('20', '20g'),
    ('25', '25g'),
    ('30', '30g'),
    ('50', '50g'),
    ('60', '60g'),
]

ProductOrderStatus = [
    ('ordered', 'Bestellt'),
    ('complete', 'Erledigt'),
    ('cancelled', 'Storniert'),
]

PriorityChoices = [
    (4, '(4) Am höchsten'),
    (3, '(3) Hoch'),
    (2, '(2) Mittel'),
    (1, '(1) Niedrg'),
    (0, '(0) Keine'),
]

CannabisFormChoices = [
    ('flower', 'Blüte'),
    ('extract', 'Extrakt'),
]

OrderDetailStatusChoices = [
    ('in_review', 'In Überprüfung'),
    ('processed', 'Bearbeitet'),
    ('checked', 'Überprüft'),
    ('missing_details', 'Fehlende Daten'),
]

RecipeStatusChoices = [
    ('not_received', 'Nicht erhalten'),
    ('received', 'Erhalten'),
    ('checked', 'Überprüft'),
    ('incorrect', 'Fehlerhaft'),
]

OnlineRecipeStatusChoices = [
    ('open', 'Ausstehend'),
    ('checked', 'Überprüft'),
    ('incorrect', 'Fehlerhaft'),
]

OrderStatusChoices = [
    ('cancelled', 'Storniert', True),
    ('open', 'Offen', False),
    ('in_review', 'In Überprüfung', False),
    ('started', 'Angelegt', False),
    ('ordered', 'Bestellt', False),
    ('product_changed', 'Produktänderung', True),
    ('process', 'In Bearbeitung', True),
    ('process_waiting', 'In Bearbeitung (ausstehend)', True),
    ('queries', 'Rückfragen', True),
    ('clarified', 'Geklärt', True),
    ('payment_change', 'Differenzzahlung', True),
    ('ready_to_ship', 'Versandbereit', False),
    ('ready_for_pickup', 'Abholbereit', True),
    ('shipped', 'Versandt', False),
    ('acceptance_refused', 'Annahme verweigert', False),
    ('delivery_not_possible', 'Zustellung nicht möglich', False),
    ('picked_up', 'Abgeholt', True),
    ('delivered', 'Geliefert', False),
]

PaymentStatusChoices = [
    ('pending', 'Ausstehend', True),
    ('invoice_reminder', 'Zahlungserinnerung', False),
    ('last_reminder', 'Mahnung', False),
    ('overdue', 'Überfällig', False),
    ('debt_collection', 'Inkasso', True),
    ('at_pickup', 'Bei Abholung', True),
    ('received', 'Bezahlt', True),
]

CustomerTypeChoices = [
    ('self_payer', 'Selbstzahler'),
    ('insurance_patient_with_supplement', 'Kassenpatient (mit Zuschlag)'),
    ('insurance_patient', 'Kassenpatient (Zuzahlungsbefreit)'),
]

SalutationChoices = [
    ('other', 'Divers'),
    ('female', 'Frau'),
    ('male', 'Herr'),
]

CountryChoices = [
    ('DE', 'Deutschland'),
]

InvoiceStatus = [
    ('open', 'Offen'),
    ('paid', 'Bezahlt'),
    ('draft', 'Entwurf'),
    ('canceled', 'Storniert'),
    ('part_canceled', 'Teilstorno'),
    ('refund', 'Rückerstattung'),
]

PaymentTypeChoices = [
    ('payment_at_pickup', 'Zahlung bei Abholung'),
    ('prepayment', 'Vorkasse'),
    # ('online_payment', 'Online Zahlung'),
    # ('payment_by_invoice', 'Kauf auf Rechnung'),
    # ('paypal', 'PayPal'),
    # ('cc', 'Kreditkarte'),
    # ('applepay', 'ApplePay'),
]

DeliveryTypeChoices = [
    ('pickup', 'Abholung'),
    ('dhl_standard', 'DHL Standard'),
    # ('dhl_express', 'DHL Express'),
    # ('go_express', 'GO! Express')
]

UnitChoices = [
    ('g', 'g'),
    ('units', 'Einheiten'),
]

StateChoices = [
    ('BW', 'Baden-Württemberg'),
    ('BY', 'Bayern'),
    ('BE', 'Berlin'),
    ('BB', 'Brandenburg'),
    ('HB', 'Bremen'),
    ('HH', 'Hamburg'),
    ('HE', 'Hessen'),
    ('MV', 'Mecklenburg-Vorpommern'),
    ('NI', 'Niedersachsen'),
    ('NW', 'Nordrhein-Westfalen'),
    ('RP', 'Rheinland-Pfalz'),
    ('SL', 'Saarland'),
    ('SN', 'Sachsen'),
    ('ST', 'Sachsen-Anhalt'),
    ('SH', 'Schleswig-Holstein'),
    ('TH', 'Thüringen'),
]

HealthInsuranceChoices = [
    ('Andere', 'Andere'),
    ('AOK Baden-Württemberg', 'AOK Baden-Württemberg'),
    ('AOK Bayern', 'AOK Bayern'),
    ('AOK Bremen/Bremerhaven', 'AOK Bremen/Bremerhaven'),
    ('AOK Hessen', 'AOK Hessen'),
    ('AOK Niedersachsen', 'AOK Niedersachsen'),
    ('AOK Nordost', 'AOK Nordost'),
    ('AOK Nordwest', 'AOK Nordwest'),
    ('AOK Plus', 'AOK Plus'),
    ('AOK Rheinland/Hamburg', 'AOK Rheinland/Hamburg'),
    ('AOK Rheinland-Pfalz/Saarland', 'AOK Rheinland-Pfalz/Saarland'),
    ('AOK Sachsen-Anhalt', 'AOK Sachsen-Anhalt'),
    ('Audi BKK', 'Audi BKK'),
    ('Bahn-BKK', 'Bahn-BKK'),
    ('Barmer Ersatzkasse', 'Barmer Ersatzkasse'),
    ('Bergische Krankenkasse', 'Bergische Krankenkasse'),
    ('Bertelsmann BKK', 'Bertelsmann BKK'),
    ('Betriebskrankenkasse BPW Bergische Achsen KG - betriebsbezogen', 'Betriebskrankenkasse BPW Bergische Achsen KG - betriebsbezogen'),
    ('Betriebskrankenkasse der BMW AG - betriebsbezogen', 'Betriebskrankenkasse der BMW AG - betriebsbezogen'),
    ('Betriebskrankenkasse der G. M. Pfaff AG', 'Betriebskrankenkasse der G. M. Pfaff AG'),
    ('Betriebskrankenkasse Firmus', 'Betriebskrankenkasse Firmus'),
    ('Betriebskrankenkasse Groz-Beckert - betriebsbezogen', 'Betriebskrankenkasse Groz-Beckert - betriebsbezogen'),
    ('Betriebskrankenkasse Mahle - betriebsbezogen', 'Betriebskrankenkasse Mahle - betriebsbezogen'),
    ('Betriebskrankenkasse Miele - betriebsbezogen', 'Betriebskrankenkasse Miele - betriebsbezogen'),
    ('Betriebskrankenkasse Mobil', 'Betriebskrankenkasse Mobil'),
    ('Betriebskrankenkasse Schwarzwald-Baar-Heuberg', 'Betriebskrankenkasse Schwarzwald-Baar-Heuberg'),
    ('Betriebskrankenkasse Vereinigte Deutsche Nickel-Werke', 'Betriebskrankenkasse Vereinigte Deutsche Nickel-Werke'),
    ('Betriebskrankenkasse WMF Württembergische Metallwarenfabrik AG', 'Betriebskrankenkasse WMF Württembergische Metallwarenfabrik AG'),
    ('BKK Akzo Nobel Bayern', 'BKK Akzo Nobel Bayern'),
    ('BKK B. Braun Aesculap - betriebsbezogen', 'BKK B. Braun Aesculap - betriebsbezogen'),
    ('BKK Deutsche Bank AG - betriebsbezogen', 'BKK Deutsche Bank AG - betriebsbezogen'),
    ('BKK Diakonie', 'BKK Diakonie'),
    ('BKK Dürkopp Adler', 'BKK Dürkopp Adler'),
    ('BKK Euregio', 'BKK Euregio'),
    ('BKK evm - betriebsbezogen', 'BKK evm - betriebsbezogen'),
    ('BKK EWE - betriebsbezogen', 'BKK EWE - betriebsbezogen'),
    ('BKK exklusiv', 'BKK exklusiv'),
    ('BKK Faber-Castell & Partner', 'BKK Faber-Castell & Partner'),
    ('BKK Freudenberg', 'BKK Freudenberg'),
    ('BKK Gildemeister Seidensticker', 'BKK Gildemeister Seidensticker'),
    ('BKK Herkules', 'BKK Herkules'),
    ('BKK Linde', 'BKK Linde'),
    ('BKK Melitta HMR', 'BKK Melitta HMR'),
    ('BKK MTU - betriebsbezogen', 'BKK MTU - betriebsbezogen'),
    ('BKK Pfalz', 'BKK Pfalz'),
    ('BKK Provita', 'BKK Provita'),
    ('BKK Public', 'BKK Public'),
    ('BKK PwC - betriebsbezogen', 'BKK PwC - betriebsbezogen'),
    ('BKK Rieker Ricosta Weisser - betriebsbezogen', 'BKK Rieker Ricosta Weisser - betriebsbezogen'),
    ('BKK Salzgitter - betriebsbezogen', 'BKK Salzgitter - betriebsbezogen'),
    ('BKK Scheufelen', 'BKK Scheufelen'),
    ('BKK Technoform', 'BKK Technoform'),
    ('BKK Textilgruppe Hof', 'BKK Textilgruppe Hof'),
    ('BKK VBU', 'BKK VBU'),
    ('BKK Verbundplus', 'BKK Verbundplus'),
    ('BKK Voralb Heller Index Leuze - betriebsbezogen', 'BKK Voralb Heller Index Leuze - betriebsbezogen'),
    ('BKK Werra-Meissner', 'BKK Werra-Meissner'),
    ('BKK Wirtschaft & Finanzen', 'BKK Wirtschaft & Finanzen'),
    ('BKK Würth - betriebsbezogen', 'BKK Würth - betriebsbezogen'),
    ('BKK ZF & Partner', 'BKK ZF & Partner'),
    ('BKK24', 'BKK24'),
    ('Bosch BKK', 'Bosch BKK'),
    ('Bundesinnungskrankenkasse Gesundheit', 'Bundesinnungskrankenkasse Gesundheit'),
    ('Continentale Betriebskrankenkasse', 'Continentale Betriebskrankenkasse'),
    ('DAK-Gesundheit', 'DAK-Gesundheit'),
    ('Debeka BKK', 'Debeka BKK'),
    ('Energie-Betriebskrankenkasse', 'Energie-Betriebskrankenkasse'),
    ('Ernst & Young BKK - betriebsbezogen', 'Ernst & Young BKK - betriebsbezogen'),
    ('Handelskrankenkasse', 'Handelskrankenkasse'),
    ('Heimat Krankenkasse', 'Heimat Krankenkasse'),
    ('HEK - Hanseatische Krankenkasse', 'HEK - Hanseatische Krankenkasse'),
    ('IKK - Die Innovationskasse', 'IKK - Die Innovationskasse'),
    ('IKK classic', 'IKK classic'),
    ('IKK gesund plus', 'IKK gesund plus'),
    ('IKK Südwest', 'IKK Südwest'),
    ('Innungskrankenkasse Brandenburg und Berlin', 'Innungskrankenkasse Brandenburg und Berlin'),
    ('Karl Mayer Betriebskrankenkasse - betriebsbezogen', 'Karl Mayer Betriebskrankenkasse - betriebsbezogen'),
    ('Kaufmännische Krankenkasse', 'Kaufmännische Krankenkasse'),
    ('Knappschaft', 'Knappschaft'),
    ('Koenig & Bauer BKK - betriebsbezogen', 'Koenig & Bauer BKK - betriebsbezogen'),
    ('Krones Betriebskrankenkasse - betriebsbezogen', 'Krones Betriebskrankenkasse - betriebsbezogen'),
    ('Landwirtschaftliche Krankenkasse', 'Landwirtschaftliche Krankenkasse'),
    ('Mercedes-Benz Betriebskrankenkasse - betriebsbezogen', 'Mercedes-Benz Betriebskrankenkasse - betriebsbezogen'),
    ('Merck BKK - betriebsbezogen', 'Merck BKK - betriebsbezogen'),
    ('MHplus Betriebskrankenkasse', 'MHplus Betriebskrankenkasse'),
    ('Novitas BKK', 'Novitas BKK'),
    ('Pronova BKK', 'Pronova BKK'),
    ('R+V Betriebskrankenkasse', 'R+V Betriebskrankenkasse'),
    ('Salus BKK', 'Salus BKK'),
    ('Securvita BKK', 'Securvita BKK'),
    ('Siemens-Betriebskrankenkasse', 'Siemens-Betriebskrankenkasse'),
    ('SKD BKK', 'SKD BKK'),
    ('Südzucker BKK - betriebsbezogen', 'Südzucker BKK - betriebsbezogen'),
    ('Techniker Krankenkasse', 'Techniker Krankenkasse'),
    ('TUI BKK', 'TUI BKK'),
    ('Viactiv BKK', 'Viactiv BKK'),
    ('Vivida BKK', 'Vivida BKK'),
    ('Andere', 'Andere'),
]

DashboardViewsChoices = [
    ('dashboard', 'Dashboard'),
    ('dashboard_orders', 'Bestellungen'),
    ('dashboard_order_products', 'Bestellprodukte'),
    ('dashboard_review_orders', 'Bestelleingang'),
    ('dashboard_imports', 'Imports'),
    ('dashboard_terpene_all', 'Terpene'),
    ('dashboard_products_all', 'Produkte'),
    ('dashboard_customers', 'Kunden'),
    ('dashboard_product_requests', 'Produktanfragen'),
    ('dashboard_products_stock', 'Lagerbestand Produkte'),
    ('dashboard_packages_stock', 'Lagerbestand Packungen'),
    ('dashboard_users', 'Benutzerverwaltung'),
    ('dashboard_settings', 'Einstellungen'),
]

ViewsChoices = [
    ('for_all', 'Generelle Metadaten'),
    ('home', 'Startseite'),
    ('imprint', 'Impressum'),
    ('policy', 'Datenschutz'),
    ('agb', 'AGB'),
    ('about_us', 'Über uns'),
    ('cookie_info', 'Cookie-Informationen'),
    ('shipping_and_retoures', 'Versand & Retouren'),
    ('payment', 'Zahlungsmethoden'),
    ('livestock', 'Livebestand'),
    ('cannabisproducts', 'Cannabisprodukte'),
    ('product', 'Einzelne Produkte'),
    ('content_medicalcannabis_index', 'Medizinisches Cannabis'),
    ('content_medicalcannabis_entourage_effect', 'Entourage Effekt'),
    ('content_medicalcannabis_entourage_effect_terpenetable', 'Terpenentabelle'),
    ('content_medicalcannabis_entourage_effect_cannabinoidtable', 'Cannabinoidtabelle'),
    ('content_medicalcannabis_entourage_effect_flavonoidetable', 'Flavonidetabelle'),
    ('content_medicalcannabis_effects', 'Wirkungsweisen'),
    ('content_medicalcannabis_indications', 'Indikationen'),
    ('advisor', 'Ratgeber medizinisches Cannabis'),
    ('advisor_faqs', 'FAQs'),
    ('advisor_lexicon', 'Cannabis Lexikon'),
    ('advisor_blog', 'Cannabis Blog'),
    ('advisor_blog_template', 'Cannabis Blog Unterseiten'),
]

ProductRequestChoices = [
    ('open', 'offen'),
    ('in_review', 'In Bearbeitung'),
    ('approved', 'Freigegeben'),
    ('rejected', 'Abgelehnt'),
    ('expired', 'Abgelaufen'),
]

LoggerChoices = [
    ('info', 'INFO'),
    ('warning', 'WARNING'),
    ('error', 'ERROR'),
    ('debug', 'DEBUG'),
    ('notset', 'NotSet'),
    ('fatal', 'FATAL'),
    ('task', 'TASK')
]

ProductRequestRejectChoices = [
    ('currently_not_available', 'Derzeit nicht lieferbar'),
    ('sold_out', 'Ausverkauft'),
]

EmailRecipientCategories = [
    ('new_order', 'Neue Bestellungen'),
    ('contact_request', 'Kontaktanfragen'),
    ('product_request', 'Produktanfragen'),
    ('error_message', 'Fehlermeldungen'),
    ('payment_reminder', 'Zahlungserinnerung'),
    ('new_recipe_order', 'Neue Rezeptbestellungen'),
]

EmailTypes = [
    ('new_order', 'Neue Bestellung'),
    ('contact_request', 'Kontaktanfrage'),
    ('product_request', 'Produktanfrage'),
    ('error_message', 'Fehlermeldung'),
    ('payment_reminder', 'Zahlungserinnerung'),
    ('new_recipe_order', 'Neue Rezeptbestellung'),
    ('order_shipped', 'Bestellung versandt'),
    ('activate_staff_user', 'Mitarbeiter aktivieren'),
]

StockActionChoices = [
    ('add', 'Hinzufügen'),
    ('remove', 'Entfernen'),
    ('created', 'Erstellt'),
    ('updated', 'Aktualisiert'),
    ('deleted', 'Gelöscht'),
]
