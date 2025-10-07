from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import EmailMultiAlternatives
from .models import user_data
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from datetime import datetime,timedelta
from django.core.mail import send_mail
from .models import UserDeviceInfo
import geocoder
import platform
import socket
import jwt
import json
import random
# Create your views here.

my_key="django-insecure-t=z$msw)4v02n7g7)u1*0jk+c5k0*du+4sk%k!r(i)j^m83tya"


def get_user_info(ip):
    try:
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
        print(email)
        password = a.get("password")
        d=user_data.objects.all()
        em = [i.email for i in d]
        a = [str(random.randint(0,9)) for i in range(6)]
        b = "".join(a)
                
        payload_1={"email":email,"exp":datetime.now()+timedelta(hours=1)}
        token_1 = jwt.encode(payload_1,my_key,algorithm="HS256")
        otp_time = datetime.now()+timedelta(minutes=5)
        time = otp_time.timestamp()
        #print( otp_time.timestamp())
        
        ip_address = self.get_client_ip(request)
        print("User ip_address:", ip_address)

        user_info = get_user_info(ip_address)
        print("User Info:", user_info)
        
        if email not in em:
            obj = user_data(email=email,
                            password=make_password(password),
                            user_otp=b,
                            usr_verify=0,
                            expire_otp=time,
                            )
            
            obj.save()
            self.send_html_email(email,b)
            UserDeviceInfo.objects.create(
            user=obj,
            ip_address=ip_address,
            location=user_info.get("location"),
            country=user_info.get("country"),
            isp=user_info.get("isp"),
            system=user_info.get("system"),
            machine=user_info.get("machine"),
            device_name=user_info.get("device_name")
        )
            return Response({"message":"User Registerd Successfully",
                             "token":token_1,
                             })
        
        else:
            user =user_data.objects.get(email=email)
            if user.usr_verify==0:   #not verified yet  ,send otp again
                user.user_otp=b
                user.save()
                self.send_html_email(email,b)
                return Response({"message":"User already exist but not verified. OTP resent ","token":token_1})
                
            return Response({"message":"User Already Exists"})
   
    def send_html_email(self,email,b):
        subject = "Thank you for contacting us!" 
        from_email = "hi@demomailtrap.co"
        to_email = email

        # Render HTML template with dynamic data
        html_content = render_to_string('pages/otp.html',{
            'otp':b
    })

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
        
            if usr_otp==otp:
                dat.usr_verify = 1
                dat.save()
                
                return Response({"message":"OTP Matched Successfully and user verified"})
            else:
                dat.usr_verify = 0 
                dat.save()
                return Response({"message":"Incorrect OTP"})
        else:
            return Response({"message":"OTP Expired"})
 
        
class login(APIView):
    
    def post(self, request):
        data = json.loads(request.body)
        email = data.get("email")
        passwor = data.get("password")
        a1=authenticate(email=email,password=passwor)
         
        d1=user_data.objects.all()
        em = [i.email for i in d1]   
        try:
            payload_1={"email":email,"exp":datetime.utcnow()+timedelta(hours=1)}
            token_1 = jwt.encode(payload_1,my_key,algorithm="HS256")
        except:
            return Response({"message":"Token Expired"})       
        
        if email in em :
            if a1 is not None:
                 return Response({"message":"login successfully ","token":token_1})
            else:
                 return Response({"message":"Enter Correct password"})
        else:
             return Response({"message":"email do not exists"})
 
class forgot(APIView):
    
    def post(self, request):
        
        data = json.loads(request.body)
        email = data.get("email")
        
        d1=user_data.objects.all()
        em = [i.email for i in d1]
         
        
        payload ={"email":email,"exp":datetime.utcnow()+timedelta(hours=1)}
        token = jwt.encode(payload,my_key,algorithm="HS256")
        otp_time = datetime.now()+timedelta(minutes=5)
        time = otp_time.timestamp()
    
        obj = user_data.objects.get(email=email)

        obj.expire_otp = time
        obj.usr_verify = 0
        obj.save()

        
    
        if email in em :
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
        html_content = render_to_string('pages/forgot.html',{
            'otp':b
    })

        # Optional plain text fallback
        text_content = f"Hello {b},\n\n\n\nThank you!"

        # Create email
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()  
        
      



class Verify_forgot(APIView):
        
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
        
            if usr_otp==otp:
                dat.usr_verify = 1
                dat.save()
                
                return Response({"message":"OTP Matched Successfully and user verified"})
            else:
                dat.usr_verify = 0 
                dat.save()
                return Response({"message":"Incorrect OTP"})
        else:
            return Response({"message":"OTP Expired"})
        

# class ContactView(APIView):
#     def post(self, request):
#         data = request.data  # DRF automatically parses JSON
#         name = data.get("name")
#         phone = data.get("phone")
#         email = data.get("email")
#         message = data.get("message")
#         course = data.get("course")

#         try:
#             send_mail(
#                 subject="New contact form submission",
#                 message=f"Name: {name}\nPhone: {phone}\nEmail: {email}\nMessage: {message}\nCourse: {course}",
#                 from_email="hi@demomailtrap.co",
#                 recipient_list=[email],  # admin ya testing email
#                 fail_silently=False,
#             )
#             return Response({"message": "Email Sent Successfullyt"})
#         except Exception as e:
#             return Response({"error": str(e)},status=500)
        
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
        self.send_html_email(name,email,message)
        return Response({"message": "Email sent successfully!"})        

    def send_html_email(self,name,email,message):
        subject = "Thank you for contacting us!"
        from_email = "hi@demomailtrap.co"
        to_email = email

        # Render HTML template with dynamic data
        html_content = render_to_string('pages/email_template.html',{
            'name':name,
            'message':message
    })

        # Optional plain text fallback
        text_content = f"Hello {name},\n\n{message}\n\nThank you!"

        # Create email
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()  
    
class Seekho(APIView):
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
    def get (self,request):
        token = request.META.get("HTTP_AUTHORIZATION")
        jt_b = jwt.decode(token,my_key,algorithms="HS256")
        em=jt_b.get("email")
        usr = user_data.objects.get(email=em)
        usr_id = usr.id
        info = UserDeviceInfo.objects.filter(user_id=usr_id)
        for i in info:
            return Response({"data":[{
                "location":i.location,
                "device_name":i.device_name,
                "Internet Service":i.isp,
                "country":i.country,
                "system":i.system,
                "machine":i.machine,
                "created":i.created_at}]})