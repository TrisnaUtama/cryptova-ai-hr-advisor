import bson
from django.contrib.auth.mixins import LoginRequiredMixin

def generate_id():
    return str(bson.ObjectId())

class LoginCheckMixin(LoginRequiredMixin):
    login_url = "/"

