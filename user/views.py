from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
# from rest_framework import status
from .models import user_data
# from django.contrib.auth.hashers import make_password
from datetime import datetime,timedelta
from django.core.mail import send_mail
from.models import UserDeviceInfo
import jwt
import json
import random
import geocoder
import platform
import socket


# Create your views here.
my_key = "django-insecure-*bddvoqfnkzyoramz@eatx6clprl$6t5+n(0qu&5e&t(4_g-j*"


def get_user_info(ip):
    try:
        if ip in ("127.0.0.1", "::1", "localhost"):
            g = geocoder.ip('me')
        else:
            g = geocoder.ip(ip)                    
        location = g.city
        country = g.country
        isp = g.org

        system = platform.system()             
        machine = platform.machine()            
        device_name = socket.gethostname()     

        return {
            "ip_address": ip,
            "location": location,
            "country": country,
            "isp": isp,
            "system": system,
            "machine": machine,
            "device_name": device_name
        }

    except Exception as e:
        return {"error": str(e)}


class register(APIView):
    def get_client_ip(self,request):
        x= request.META.get('HTTP_X_FORWARDED_FOR')
        if x:
            ip = x.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip  
    
    def post(self,request):
        b = request.body
        a = json.loads(b)
        email = a.get("email")
        password = a.get("password")
        d =user_data.objects.all()
        em = [i.email for i in d]
        a = [str(random.randint(0,9)) for i in range(6)]
        b = "".join(a)

        payload_1={"email":email,"exp":datetime.now()+timedelta(hours=1)}
        token_1 = jwt.encode(payload_1,my_key,algorithm="HS256")
        otp_time = datetime.now()+timedelta(minutes=20)
        time = otp_time.timestamp()

        ip_address = self.get_client_ip(request)
        user_info = get_user_info(ip_address)
        print("User Info:", user_info)
        
        
        if email not in em:
            obj = user_data(email=email,
                            password=make_password(password),
                            user_otp=b,
                            is_verified=0,
                            expire_otp=time,
                            ip_address=ip_address)
            
            obj.save()
            self.send_html_email(email, b)
            UserDeviceInfo.objects.create(
            user=obj,
            ip_address=ip_address,
            location=user_info.get("location"),
            country=user_info.get("country"),
            isp= user_info.get("isp"),
            system = user_info.get("system"),
            machine = user_info.get("machine"),
            device_name=user_info.get("device_name"),
            )
            return Response({
            "message": "User Registered Successfully, Please Verify OTP",
            "token": token_1,  
            })
        
        
        else:
            user = user_data.objects.get(email=email)
            if user.is_verified == "0":   # not verified yet → send OTP again
                user.user_otp = b
                user.save()
                self.send_html_email(email,b)
                return Response({"message":"User already exists but not verified. OTP resent.","token":token_1})
            return Response({"message":"User Already Exists and Verified"})
        
    def send_html_email(self,email,b):
        subject = "Thank you for contacting us!"
        from_email = "hi@demomailtrap.co"
        to_email = email

        # Render HTML template with dynamic data
        html_content = render_to_string('pages/otp.html',{'otp':b})

        # Optional plain text fallback
        text_content = f"Hello {b},\n\n\n\nThank you!"

        # Create email
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
      

class VerifyRegister(APIView):
        
    def post(self,request):
        token = request.META.get("HTTP_AUTHORIZATION")
        data = json.loads(request.body)
    
        try:
            js_dec = jwt.decode(token,my_key,algorithms="HS256")
            email = js_dec.get("email")
            print(email)
        except:
            return Response ({"message":"Token Expired"})
        
        dat = user_data.objects.get(email=email)
        usr_otp = dat.user_otp
        exp = int(float(dat.expire_otp))
        otp_time = datetime.now()
        time = int(otp_time.timestamp())

        otp = data.get("otp")
        
        if time<exp:
        
            if usr_otp==otp==otp:
                dat.is_verified = 1
                dat.save()
                
                return Response({"message":"OTP Matched Successfully and user verified"})
            else:
                dat.is_verified = 0 
                dat.save()
                return Response({"message":"Incorrect OTP"})
        else:
            return Response({"message":"OTP Expired"})




        
class login(APIView):

    def post(self, request):
        data = json.loads(request.body)
        email = data.get("email")
        passwor = data.get("password")
        a1=authenticate(email=email,password=passwor)

        d1=user_data.objects.all()
        em = [i.email for i in d1]


        if email in em:
            if a1 is not None:
                a = "".join([str(random.randint(0, 9)) for i in range(6)])
                user = user_data.objects.get(email=email)
                user.user_otp = a
                user.save()

                send_mail(
                    subject="Login OTP",
                    message=f"Your OTP is {a}",
                    from_email="hi@demomailtrap.co",
                    recipient_list=[email],
                    fail_silently=False,
                )
                payload_1={"email":email,"exp":datetime.utcnow()+timedelta(minutes=15)}
                token_1 = jwt.encode(payload_1,my_key,algorithm="HS256")
                return Response({"message":"OTP sent to your email", "token": token_1})
            else:
                return Response ({"message":"Enter Correct Password"})
        else:
                return Response({"message":"email do not exist"})


class VerifyLogin(APIView):

    def post(self, request):
        token = request.META.get("HTTP_AUTHORIZATION")
        data = json.loads(request.body)

        try:
            js_dec = jwt.decode(token, my_key, algorithms="HS256")
        except jwt.ExpiredSignatureError:
            return Response({"message": "OTP expired"})
        
        email = js_dec.get("email")
        otp = data.get("otp")


        try:
            user = user_data.objects.get(email=email)
        except user_data.DoesNotExist:
            return Response({"message": "Invalid user"})

        if user.user_otp == otp:
            final_payload = {"email": email, "exp": datetime.utcnow() + timedelta(hours=1)}
            final_token = jwt.encode(final_payload, my_key, algorithm="HS256")

            return Response({"message": "Login successful", "token": final_token})
        else:
            return Response({"message": "Incorrect OTP"})



class forget(APIView):
    
    def post(self,request):

        data = json.loads(request.body)
        email = data.get("email")

        d1= user_data.objects.all()
        em= [i.email for i in d1]

        payload = {"email":email, "exp":datetime.utcnow()+timedelta(hours=1)}
        token = jwt.encode(payload,my_key,algorithm="HS256")
        otp_time = datetime.now()+timedelta(minutes=15)
        time = otp_time.timestamp()

        obj = user_data.objects.get(email=email)

        obj.expire_otp = time
        obj.is_verified = 0
        obj.save()

        if email in em:
            a = [str(random.randint(0,9)) for i in range(6)]
            b = "".join(a)
            self.send_html_email(email,b)
            obj.user_otp = b   #  Save OTP here
            obj.save()

            return Response({"message":"otp send successfully","token":token})
        else:
            return Response({"message":"email not valid"})

    def patch(self, request):
    
        token = request.META.get('HTTP_AUTHORIZATION') # to get the token safely 
        user_ = user_data.objects.all()
        em = [i.email for i in user_]
        js_dec = jwt.decode(token,my_key,algorithms="HS256")
        email = js_dec.get("email")
        
        data = json.loads(request.body)
        new = data.get("new_password")
        conf = data.get("old_password")
        if email in em:
            obj = user_data.objects.get(email=email)
            obj.password=make_password(new)
            obj.save()
            return Response({"message":"Password has beend changed"}) 

    def send_html_email(self,email,b):
        subject = "Thank you for contacting us!"
        from_email = "hi@demomailtrap.co"
        to_email = email

        # Render HTML template with dynamic data
        html_content = render_to_string('pages/otp.html', {
            "otp" : b
        })

        # Optional plain text fallback
        text_content = f"Hello {b},\n\n\n\nThank you!"

        # Create email
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
       
        
        

        
class Verify_forget(APIView):
        
    def post(self,request):
        token = request.META.get("HTTP_AUTHORIZATION")
        data = json.loads(request.body)
    
        try:
            js_dec = jwt.decode(token,my_key,algorithms="HS256")
            email = js_dec.get("email")
            print(email)
        except:
            return Response ({"message":"Token Expired"})
        
        dat = user_data.objects.get(email=email)
        usr_otp = dat.user_otp
        exp = int(float(dat.expire_otp))
        otp_time = datetime.now()
        time = int(otp_time.timestamp())

        otp = data.get("otp")
        
        if time<exp:
        
            if usr_otp==otp==otp:
                dat.is_verified = 1
                dat.save()
                
                return Response({"message":"OTP Matched Successfully and user verified"})
            else:
                dat.is_verified = 0 
                dat.save()
                return Response({"message":"Incorrect OTP"})
        else:
            return Response({"message":"OTP Expired"})


class ContactView(APIView):
    def post(self, request):
        # Get data from API request
        name = request.data.get('name')
        print(name)
        email = request.data.get('email')
        print(email)
        message = request.data.get('message')
        print(message)
        # Send email
        self.send_html_email(name, email,message)
        return Response({"message": "Email sent successfully!"})        

    def send_html_email(self, name, email, message):
        subject = "Thank you for contacting us!"
        from_email = "hi@demomailtrap.co"
        to_email = email

        # Render HTML template with dynamic data
        html_content = render_to_string('pages/email_template.html', {
            'name': name,
            'message': message
        })

        # Optional plain text fallback
        text_content = f"Hello {name},\n\n{message}\n\nThank you!"

        # Create email
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

class recieve(APIView):

    def get(self,request):
        token = request.META.get("HTTP_AUTHORIZATION")
        jt_b = jwt.decode(token,my_key,algorithms="HS256")
        em = jt_b.get("email")
        obj = user_data.objects.get(email=em)
        passw = obj.password
        email = obj.email
        otp_ = obj.user_otp        
        return Response({"data": [{"email":email,"password":passw,"otp":otp_}]})

class user_info(APIView):
    def get(self,request):
        token = request.META.get("HTTP_AUTHORIZATION")
        jt_b = jwt.decode(token,my_key,algorithms="HS256")
        em = jt_b.get("email")
        usr = user_data.objects.get(email=em)
        usr_id = usr.id
        info = UserDeviceInfo.objects.filter(user_data=usr_id)
        for i in info:
            return Response({"data":[{
                "location": i.location,
                "device_name": i.device_name,
                "Internet Services":i.isp,

                "system": i.system,
                "machine": i.machine,
                "created": i. created_at}]})