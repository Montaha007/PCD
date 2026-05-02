import os, sys, traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mysite.settings')
import django
django.setup()
from lifestyle.models import LifestyleLog
from ai.services import predict_lifestyle

try:
    obj = LifestyleLog.objects.get(pk=1)
    print('Found LifestyleLog id=1')
    res = predict_lifestyle(obj)
    print('Prediction result:', res)
except Exception as e:
    print('Exception:', type(e), str(e))
    traceback.print_exc()
