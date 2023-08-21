import asyncio
from datetime import datetime, time

from asgiref.sync import async_to_sync, sync_to_async
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import os
import openai
from dotenv import load_dotenv

from summarizer.auth_app.models import Account
from summarizer.auth_app.utils import get_or_create_account, login_required_api

load_dotenv()


@sync_to_async
def _increment_usage(account_id):
    with transaction.atomic():
        account = Account.objects.select_for_update().get(google_account_id=account_id)
        account.daily_usage += 1
        account.save()


async def increment_daily_usage(account_id):
    await _increment_usage(account_id)


def check_if_reset_needed(account):
    current_utc_time = timezone.now()
    # Create a new datetime object for today's date with 00:00 UTC time
    today_midnight_utc = datetime.combine(current_utc_time.date(), time(), tzinfo=timezone.utc)
    if account.usage_reset_date.date() < today_midnight_utc.date():
        account.reset_usage()



def check_usage(google_account_id):
    account = get_or_create_account(google_account_id)
    check_if_reset_needed(account)
    return account.daily_usage


# api endpoint
@login_required_api
@csrf_exempt
def check_daily_usage(request):
    if request.method == 'POST':
        if not check_valid_request(request):
            return JsonResponse(
                {'response_data': 'The API endpoint can only be accessed through the browser extension currently.'},
                status=401)
        # data = json.loads(request.body)
        # account_id = data.get('account_id')
        try:
            print('try 1')
            currentuser = request.user
            print(f'curr user = {currentuser.email}')
            print(f'curr user = {currentuser.google_account_id}')
            if currentuser.is_authenticated:
                print('is auth')
                daily_usage = check_usage(currentuser.google_account_id)
                print(f'daily usage = {daily_usage}')
                return JsonResponse({'response_data': daily_usage})
            else:
                return JsonResponse({'error': 'Authentication required'}, status=401)
        except Exception as e:
            print(f'CDU exc {e}')

    return JsonResponse({'response_data': 'Invalid request method'}, status=400)


def check_valid_request(request):
    # return True
    try:
        header = request.headers._store["origin"][1]
        if header == "chrome-extension://aciffogbicloiocdoenecgebekfpnlmg" or header == "chrome-extension://jgpidkgebcfjgekngiofilefemlmmcia":
            # print(header)
            return True
        return False
    except KeyError:
        return False


@sync_to_async
def check_moderation(prompt):
    is_flagged = openai.Moderation.create(
        input=prompt,
    )
    is_flagged_data = json.loads(str(is_flagged))
    if is_flagged_data['results'][0]['flagged']:
        return True
    return False


async def make_advanced_submission(input_text, account_id):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    tokens_for_prompt = len(input_text) / 4
    tokens_total = 4000 - int(tokens_for_prompt)

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "Your only goal is to provide a factually accurate summary of the text entered by the 'user'."},
            {"role": "user", "content": f"{input_text}"}
        ],
        temperature=0,
    )

    result = completion["choices"][0]["message"]["content"]
    await increment_daily_usage(account_id)
    await increment_daily_usage(account_id)
    # result = 'Great success using the advanced model'
    # print(f'Result message = {result}')


    return {'response_data': result}


async def make_submission(prompt, account_id):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    tokens_for_prompt = len(prompt) / 4

    tokens_total = 2000 - int(tokens_for_prompt)
    print(f'Prompt tokens calc = {tokens_for_prompt}. Tokens for completion max = {tokens_total}')
    print(f'prompt - {prompt}')
    completion = openai.Completion.create(
        model="text-babbage-001",
        prompt=prompt,
        max_tokens=tokens_total,
        temperature=0,
        user=account_id
    )
    result = completion["choices"][0]["text"]
    await increment_daily_usage(account_id)
    # result = "Old model yuckies"
    #
    # print(result)
    return {'response_data': result}

@csrf_exempt
@login_required_api
@async_to_sync
async def submit_text_adv(request):
    if request.method == 'POST':
        MAX_INPUT_CHARS = 6200
        MIN_INPUT_CHARS = 10
        data = json.loads(request.body)
        input_text = data.get('input_text')
        account_id = request.user.google_account_id
        # print(f'acc id = {account_id}')
        # header = request.headers._store["origin"][1]
        # print(header)
        if not check_valid_request(request):
            return JsonResponse(
                {'response_data': 'The API endpoint can only be accessed through the browser extension currently.'},
                status=401)
        if len(input_text) < MIN_INPUT_CHARS:
            return JsonResponse(
                {
                    'response_data': 'The inputted text is too short. Please enter a longer text (article, paragraph, etc). The text should be between 500 and 12000 characters, or approximately 100 and 2300 words due to limitations of the model being used currently.'},
                status=411)
        elif len(input_text) > MAX_INPUT_CHARS:
            return JsonResponse({
                'response_data': 'The inputted text is too long. Please enter a shorter text (article, paragraph, etc). The text should be between 500 and 12000 characters, or approximately 200 and 2300 words due to limitations of the model being used currently.'},
                status=411)
        check_usage_async = sync_to_async(check_usage)
        d_u = await check_usage_async(int(account_id))
        print(d_u)
        if int(d_u) < 20:
            if await check_moderation(input_text):
                return JsonResponse({

                    'response_data': 'The inputted text violates some of OpenAI\'s Terms and Conditions. Apologize for the inconvenience caused.'},
                    status=405)
            response_data = await make_advanced_submission(input_text, account_id)
            return JsonResponse(response_data)
        else:
            return JsonResponse({'response_data': 'Free daily usage exceeded. Usage limits reset at 00:00UTC.'},
                                status=403)

    return JsonResponse({'response_data': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required_api
@async_to_sync
async def submit_text(request):
    if request.method == 'POST':
        MAX_INPUT_CHARS = 6200
        MIN_INPUT_CHARS = 10
        data = json.loads(request.body)
        input_text = data.get('input_text')
        account_id = request.user.google_account_id
        print(account_id)
        # header = request.headers._store["origin"][1]
        # print(header)
        if not check_valid_request(request):
            return JsonResponse(
                {'response_data': 'The API endpoint can only be accessed through the browser extension currently.'},
                status=401)
        if len(input_text) < MIN_INPUT_CHARS:
            return JsonResponse(
                {
                    'response_data': 'The inputted text is too short. Please enter a longer text (article, paragraph, etc). The text should be between 500 and 6200 characters, or approximately 100 and 1150 words due to limitations of the model being used currently.'},
                status=411)
        elif len(input_text) > MAX_INPUT_CHARS:
            return JsonResponse({
                'response_data': 'The inputted text is too long. Please enter a shorter text (article, paragraph, etc). The text should be between 500 and 6300 characters, or approximately 200 and 1200 words due to limitations of the model being used currently.'},
                status=411)
        check_usage_async = sync_to_async(check_usage)
        d_u = await check_usage_async(int(account_id))
        print(d_u)
        if int(d_u) < 20:
            prompt = f'"""\n{input_text}\n"""\n Provide a short, accurate summary of the text above. \n'
            if await check_moderation(prompt):
                return JsonResponse({

                    'response_data': 'The inputted text violates some of OpenAI\'s Terms and Conditions. Apologize for the inconvenience caused.'},
                    status=405)
            response_data = await make_submission(prompt, account_id)
            # response_data = await make_advanced_submission(input_text, account_id)
            return JsonResponse(response_data)
        else:
            return JsonResponse({'response_data': 'Free daily usage exceeded. Usage limits reset at 00:00UTC.'},
                                status=403)

    return JsonResponse({'response_data': 'Invalid request method'}, status=400)
