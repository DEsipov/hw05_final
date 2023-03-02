from django.utils import timezone


def year(request):
    date_dt = timezone.now().year
    return {'year': date_dt}
