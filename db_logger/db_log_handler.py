""" Logger handler """
import logging
import traceback

db_default_formatter = logging.Formatter()

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        """ Add log to db """

        from .models import Logger
        from .utils import send_error_mail


        # Traceback extrahieren, um den Dateipfad und die Zeilennummer zu erhalten
        tb = traceback.format_exception(None, record.exc_info[1], record.exc_info[2])
        file_path = tb[-1].split(',')[0] if record.exc_info and len(tb) > 1 else 'Unbekannt'

        if record.exc_info:
            trace = db_default_formatter.formatException(record.exc_info)

        msg = self.format(record)

        kwargs = {
            'message': file_path,
            'stack_trace': trace,
            'reference': msg,
            'category': record.levelname.lower()
        }

        log_item = Logger.objects.create(**kwargs)

        if record.levelname.lower() in ['error', 'fatal']:
            send_error_mail(log_item)

    def format(self, record):
        """ Format error tracer """
        if self.formatter:
            fmt = self.formatter
        else:
            fmt = db_default_formatter

        if type(fmt) == logging.Formatter:
            record.message = record.getMessage()

            if fmt.usesTime():
                record.asctime = fmt.formatTime(record, fmt.datefmt)

            # ignore exception traceback and stack info

            return fmt.formatMessage(record)
        else:
            return fmt.format(record)
