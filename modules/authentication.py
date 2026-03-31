from fastapi import APIRouter, HTTPException, status
from schemas.authentication import signup, signin, forgot_password, reset_password
from db import auth_collection, pending_auth_collection
import hashlib
from datetime import datetime, timedelta
import random
import os
import aiosmtplib
from email.message import EmailMessage
import bcrypt


auth = APIRouter()


def hash_password(password: str):
    # Hash password using bcrypt directly
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str):
    # Verify password using bcrypt directly
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
# 🔢 OTP Generator
def generate_otp():
    return str(random.randint(1000, 9999))


# 📩 Async Email Sender
async def send_email_otp(to_email: str, otp: str):
    message = EmailMessage()
    message["From"] = "santoshxr53@gmail.com"
    message["To"] = to_email
    message["Subject"] = "Your OTP Verification Code"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #333;
                margin: 0;
                font-size: 28px;
            }}
            .otp-box {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin: 30px 0;
            }}
            .otp-box p {{
                color: #ffffff;
                font-size: 14px;
                margin: 0 0 10px 0;
            }}
            .otp-code {{
                background-color: rgba(255,255,255,0.2);
                color: #ffffff;
                font-size: 36px;
                font-weight: bold;
                letter-spacing: 8px;
                padding: 15px;
                border-radius: 6px;
                font-family: 'Courier New', monospace;
            }}
            .content {{
                color: #555;
                font-size: 16px;
                line-height: 1.6;
                margin: 20px 0;
            }}
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 12px;
                margin: 20px 0;
                border-radius: 4px;
                color: #856404;
            }}
            .footer {{
                text-align: center;
                color: #999;
                font-size: 12px;
                margin-top: 30px;
                border-top: 1px solid #eee;
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Email Verification</h1>
            </div>
            
            <p class="content">Hello,</p>
            
            <p class="content">Thank you for signing up! Please use the OTP code below to verify your email address.</p>
            
            <div class="otp-box">
                <p>Your One-Time Password</p>
                <div class="otp-code">{otp}</div>
                <p>Valid for 5 minutes</p>
            </div>
            
            <div class="warning">
                ⚠️ <strong>Important:</strong> Never share this OTP with anyone. We will never ask for this code via email or message.
            </div>
            
            <p class="content">
                If you didn't create this account, please ignore this email.
            </p>
            
            <div class="footer">
                <p>© 2026 Healther. All rights reserved.</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    message.add_alternative(html_content, subtype='html')

    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=os.getenv("GMAIL_USERNAME"),
            password=os.getenv("GMAIL_APP_PASSWORD")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )


# 🚀 SIGNUP
@auth.post('/sign-up')
async def signup_user(data: signup):
    try:
        # 🔍 Check if user already exists (verified or pending)
        existing_user = await auth_collection.find_one({"email_id": data.email_id})
        pending_user = await pending_auth_collection.find_one({"email_id": data.email_id})
        
        if existing_user or pending_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists with this email"
            )

        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=5)

        hashed_password = hash_password(data.password)

        # ➕ Insert into PENDING collection (not verified yet)
        result = await pending_auth_collection.insert_one({
            "name": data.name,
            "email_id": data.email_id,
            "mobile_number": data.mobile_number,
            "password": hashed_password,
            "otp": otp,
            "otp_expiry": expiry
        })

        # 📩 Send OTP Email
        await send_email_otp(data.email_id, otp)

        return {
            "message": "OTP sent successfully to email",
            "temp_id": str(result.inserted_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔐 VERIFY OTP
@auth.post('/verify-otp')
async def verify_otp(email: str, otp: str):
    try:
        # 🔍 Find in PENDING collection
        user = await pending_auth_collection.find_one({"email_id": email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found or already verified")

        # ⏳ Check expiry
        if datetime.utcnow() > user.get("otp_expiry"):
            raise HTTPException(status_code=400, detail="OTP expired")

        # ❌ Check OTP
        if user.get("otp") != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # ✅ Move to verified users with verified=true
        user_data = {
            "name": user["name"],
            "email_id": user["email_id"],
            "mobile_number": user["mobile_number"],
            "password": user["password"],
            "verified": True,
            "created_at": datetime.utcnow()
        }
        
        result = await auth_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        
        # 📝 Update document with userId field
        await auth_collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"userId": user_id}}
        )

        # 🗑️ Delete from pending collection
        await pending_auth_collection.delete_one({"_id": user["_id"]})

        return {
            "message": "User verified successfully",
            "userId": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔄 RESEND OTP
@auth.post('/resend-otp')
async def resend_otp(email: str):
    try:
        # 🔍 Find in PENDING collection
        user = await pending_auth_collection.find_one({"email_id": email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found or already verified")

        # ❌ Prevent resend if still valid
        if datetime.utcnow() < user.get("otp_expiry"):
            raise HTTPException(
                status_code=400,
                detail="OTP still valid. Try again later"
            )

        new_otp = generate_otp()
        new_expiry = datetime.utcnow() + timedelta(minutes=5)

        await pending_auth_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "otp": new_otp,
                    "otp_expiry": new_expiry
                }
            }
        )

        # 📩 Send new OTP
        await send_email_otp(email, new_otp)

        return {
            "message": "New OTP sent successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔑 SIGNIN
@auth.post('/sign-in')
async def signin_user(data: signin):
    try:
        # 🔍 Check if user exists and is verified
        user = await auth_collection.find_one({"email_id": data.email_id})

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # ✅ Verify password
        if not verify_password(data.password, user.get("password")):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # ✅ Check if user is verified
        if not user.get("verified"):
            raise HTTPException(
                status_code=403,
                detail="User not verified. Please verify your email first"
            )

        return {
            "message": "Sign in successful",
            "userId": user.get("userId"),
            "name": user.get("name"),
            "email_id": user.get("email_id")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔓 FORGOT PASSWORD
@auth.post('/forgot-password')
async def forgot_password_endpoint(data: forgot_password):
    try:
        # 🔍 Check if user exists and is verified
        user = await auth_collection.find_one({"email_id": data.email_id})

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if not user.get("verified"):
            raise HTTPException(
                status_code=403,
                detail="User not verified. Please verify your email first"
            )

        # Generate OTP for password reset
        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=10)

        # Store password reset request in auth_collection
        await auth_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_otp": otp,
                    "reset_otp_expiry": expiry
                }
            }
        )

        # 📩 Send OTP Email for password reset
        message = EmailMessage()
        message["From"] = "santoshxr53@gmail.com"
        message["To"] = data.email_id
        message["Subject"] = "Password Reset OTP"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    padding: 40px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #333;
                    margin: 0;
                    font-size: 28px;
                }}
                .otp-box {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .otp-box p {{
                    color: #ffffff;
                    font-size: 14px;
                    margin: 0 0 10px 0;
                }}
                .otp-code {{
                    background-color: rgba(255,255,255,0.2);
                    color: #ffffff;
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    padding: 15px;
                    border-radius: 6px;
                    font-family: 'Courier New', monospace;
                }}
                .content {{
                    color: #555;
                    font-size: 16px;
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #f8d7da;
                    border-left: 4px solid #f5576c;
                    padding: 12px;
                    margin: 20px 0;
                    border-radius: 4px;
                    color: #721c24;
                }}
                .footer {{
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                    margin-top: 30px;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Password Reset</h1>
                </div>
                
                <p class="content">Hello,</p>
                
                <p class="content">We received a request to reset your password. Please use the OTP code below to proceed with resetting your password.</p>
                
                <div class="otp-box">
                    <p>Your Password Reset Code</p>
                    <div class="otp-code">{otp}</div>
                    <p>Valid for 10 minutes</p>
                </div>
                
                <div class="warning">
                    ⚠️ <strong>Important:</strong> Never share this OTP with anyone. We will never ask for this code via email or message.
                </div>
                
                <p class="content">
                    If you didn't request a password reset, please ignore this email and your account will remain secure.
                </p>
                
                <div class="footer">
                    <p>© 2026 Healther. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message.add_alternative(html_content, subtype='html')

        try:
            await aiosmtplib.send(
                message,
                hostname="smtp.gmail.com",
                port=587,
                start_tls=True,
                username=os.getenv("GMAIL_USERNAME"),
                password=os.getenv("GMAIL_APP_PASSWORD")
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {str(e)}"
            )

        return {
            "message": "Password reset OTP sent to email",
            "email_id": data.email_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔑 RESET PASSWORD
@auth.post('/reset-password')
async def reset_password_endpoint(data: reset_password):
    try:
        # 🔍 Find user
        user = await auth_collection.find_one({"email_id": data.email_id})

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # ⏳ Check if OTP is set
        reset_otp = user.get("reset_otp")
        reset_otp_expiry = user.get("reset_otp_expiry")

        if not reset_otp:
            raise HTTPException(
                status_code=400,
                detail="No password reset request found. Request a new OTP"
            )

        # ⏳ Check expiry
        if datetime.utcnow() > reset_otp_expiry:
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Request a new OTP"
            )

        # ❌ Check OTP
        if user.get("reset_otp") != data.otp:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP"
            )

        # ✅ Hash new password and update
        hashed_password = hash_password(data.new_password)

        await auth_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password": hashed_password
                },
                "$unset": {
                    "reset_otp": "",
                    "reset_otp_expiry": ""
                }
            }
        )

        return {
            "message": "Password reset successfully",
            "email_id": data.email_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
