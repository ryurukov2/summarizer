import json
import os
from time import sleep

import requests
from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

from summarizer.auth_app.utils import get_or_create_account

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')


@csrf_exempt
def google_logout(request):
    try:
        logout(request)
        print('logging out')
        if request.method == 'GET':
            return HttpResponseRedirect(reverse('home'))
        elif request.method == 'POST':
            return JsonResponse({'result': 'success'}, status=200)
    except Exception as e:
        print(f'logout Ex: {e}')
        if request.method == 'GET':
            return HttpResponseRedirect(reverse('home'))
        elif request.method == 'POST':
            return JsonResponse({'result': 'failed to logout'}, status=418)



def render_login(request):
    # print(f'from render_login {request.user.is_authenticated}')
    context = {'google_client_id': GOOGLE_CLIENT_ID,
               'login_handle_redirect': GOOGLE_REDIRECT_URI}
    return render(request, 'auth_app/login.html', context)


def validate_google_token(token):
    idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
    try:
        if idinfo["aud"] == GOOGLE_CLIENT_ID:
            account = get_or_create_account(idinfo['sub'], idinfo['email'])
            return account
    except Exception as ex:
        print(f'exception - {ex}')
        raise ValueError


@csrf_exempt
def google_login(request):
    # login process through web page redirect URL handler, working for log in with google
    if request.method == 'GET':
        # print(f'GET ')
        return HttpResponseRedirect(reverse('login'))
    elif request.method == 'POST':
        # print(f'POST ')
        try:
            # check CSRF from google
            csrf_token_cookie = request.COOKIES.get('g_csrf_token')
            print(f'hi, {csrf_token_cookie}')
            if not csrf_token_cookie:
                raise Exception('No CSRF token in Cookie.')
            csrf_token_body = request.POST.get('g_csrf_token')
            if not csrf_token_body:
                raise Exception('No CSRF token in post body.')
            if csrf_token_cookie != csrf_token_body:
                raise Exception('Failed to verify double submit cookie.')
        except Exception as e:
            print(e)
            return HttpResponseRedirect(reverse('login'))

        try:
            token = request.POST.get('credential')
            # verify ID token received
            try:
                account = validate_google_token(token)
                login(request, account)
                response = HttpResponseRedirect(reverse('home'))
            except ValueError as er:
                stre = 'Token used too early'
                err = str(er)
                if stre in err:
                    print(err)
                    sleep(1)
                    try:
                        account = validate_google_token(token)
                        login(request, account)
                        response = HttpResponseRedirect(reverse('home'))
                    except ValueError as e:
                        print(e)
                        print('failed twice')
                        response = HttpResponseRedirect(reverse('login'))
                else:
                    response = HttpResponseRedirect(reverse('login'))

            return response
        except ValueError as e:
            print(e)

    # return response
    return render(request, 'auth_app/login-fail.html')



def render_index(request):
    return render(request, 'auth_app/index.html')


@csrf_exempt
def google_login_api(request):
    # logic to get email
    if request.method == 'POST':
        print(f'POST ')
        data = json.loads(request.body)
        id_token_ext = data.get('token')
        headers = {
            'Authorization': f'Bearer {id_token_ext}',
            'Content-Type': 'application/json',
        }
        params = {}
        # url = 'https://www.googleapis.com/oauth2/v3/certs'
        # url = 'https://www.googleapis.com/oauth2/v3/tokeninfo'
        # url = 'https://openidconnect.googleapis.com/v1/userinfo'
        url = 'https://www.googleapis.com/userinfo/v2/me'
        response = requests.get(url, headers=headers)
        if response:
            # print(f'RESPONSE FROM GOOGLE - {response.__dict__}')
            data = json.loads(response.content)
            # print(f'data = {data}')
            if data['id'] and data['email']:
                account = get_or_create_account(data['id'], data['email'])
                login(request, account)
                return JsonResponse({'response': 'success'}, status=200)
            else:
                print('no sub')

        else:
            print('no res')
    else:
        print(request.method)

    return JsonResponse({'response': 'no success'}, status=400)
