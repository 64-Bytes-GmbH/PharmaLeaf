""" All middleware classes are stored in this file. """

from django.utils.deprecation import MiddlewareMixin
from .models import UserPremissions, StaffUser

class SelectFirstPharmacyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and request.user.is_staff:

            try:
                staff_user = StaffUser.objects.get(user=request.user)

                if not staff_user.selected_pharmacy:
            
                    first_pharmacy = UserPremissions.objects.filter(user=request.user).order_by('pharmacy__name').first()

                    if first_pharmacy:
                        staff_user.selected_pharmacy = first_pharmacy.pharmacy
                        staff_user.save()
            
            except StaffUser.DoesNotExist:
                pass
