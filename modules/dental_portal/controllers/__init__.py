from . import main
# merged portal controllers; dental_portal_booking_main defines
# DentalBookingController, which dental_booking_slots_main subclasses,
# so it is imported first.
from . import dental_portal_v2_main
from . import dental_portal_booking_main
from . import dental_booking_slots_main
