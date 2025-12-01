"""
API views for Investment & Savings assessments
"""
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal

from apps.records.models import StocksAssessment, SavingsAssessment, CDAssessment, BondAssessment, LinkedAccount


@login_required
@require_http_methods(["POST"])
def save_stocks_assessment(request):
    """Save stocks assessment"""
    try:
        data = json.loads(request.body)
        
        symbol = data.get('symbol', '').upper().strip()
        if not symbol:
            return JsonResponse({'error': 'Stock symbol is required'}, status=400)
        
        linked_account_id = data.get('linked_account_id')
        linked_account = None
        if linked_account_id:
            linked_account = LinkedAccount.objects.filter(
                id=linked_account_id,
                user=request.user
            ).first()
        
        assessment, created = StocksAssessment.objects.update_or_create(
            user=request.user,
            symbol=symbol,
            defaults={
                'linked_account': linked_account,
                'investment_amount': Decimal(str(data.get('investment_amount', 0))) if data.get('investment_amount') else None,
                'share_quantity': Decimal(str(data.get('share_quantity', 0))) if data.get('share_quantity') else None,
                'current_price': Decimal(str(data.get('current_price', 0))),
                'forecast_data': data.get('forecast_data', {}),
                'notes': data.get('notes', ''),
            }
        )
        
        return JsonResponse({
            'success': True,
            'created': created,
            'id': assessment.id,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_savings_assessment(request):
    """Save savings assessment"""
    try:
        data = json.loads(request.body)
        
        linked_account_id = data.get('linked_account_id')
        linked_account = None
        if linked_account_id:
            linked_account = LinkedAccount.objects.filter(
                id=linked_account_id,
                user=request.user
            ).first()
        
        account_name = data.get('account_name', 'Savings Account')
        assessment_id = data.get('id')
        
        if assessment_id:
            try:
                assessment = SavingsAssessment.objects.get(id=assessment_id, user=request.user)
                created = False
            except SavingsAssessment.DoesNotExist:
                assessment = SavingsAssessment(user=request.user)
                created = True
        else:
            assessment = SavingsAssessment(user=request.user)
            created = True
        
        assessment.linked_account = linked_account
        assessment.account_name = account_name
        assessment.initial_deposit = Decimal(str(data.get('initial_deposit', 0)))
        assessment.annual_interest_rate = Decimal(str(data.get('annual_interest_rate', 0)))
        # Handle both biweekly and monthly contributions
        biweekly_contrib = data.get('biweekly_contribution')
        if biweekly_contrib is not None:
            assessment.monthly_contribution = Decimal(str(biweekly_contrib)) * Decimal('26') / Decimal('12')  # Convert biweekly to monthly
        else:
            assessment.monthly_contribution = Decimal(str(data.get('monthly_contribution', 0)))
        assessment.compounding_frequency = int(data.get('compounding_frequency', 12))
        forecast_data = data.get('forecast_data', {})
        # Store biweekly contribution in forecast_data for reference
        if biweekly_contrib is not None:
            forecast_data['biweekly_contribution'] = float(biweekly_contrib)
        assessment.forecast_data = forecast_data
        assessment.notes = data.get('notes', '')
        assessment.save()
        
        return JsonResponse({
            'success': True,
            'created': created,
            'id': assessment.id,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_cd_assessment(request):
    """Save CD assessment"""
    try:
        data = json.loads(request.body)
        
        linked_account_id = data.get('linked_account_id')
        linked_account = None
        if linked_account_id:
            linked_account = LinkedAccount.objects.filter(
                id=linked_account_id,
                user=request.user
            ).first()
        
        assessment_id = data.get('id')
        if assessment_id:
            try:
                assessment = CDAssessment.objects.get(id=assessment_id, user=request.user)
                created = False
            except CDAssessment.DoesNotExist:
                assessment = CDAssessment(user=request.user)
                created = True
        else:
            assessment = CDAssessment(user=request.user)
            created = True
        
        assessment.linked_account = linked_account
        assessment.account_name = data.get('account_name', 'CD Account')
        assessment.amount = Decimal(str(data.get('amount', 0)))
        assessment.annual_interest_rate = Decimal(str(data.get('annual_interest_rate', 0)))
        assessment.term_months = int(data.get('term_months', 36))  # Default to 36 months (3 years)
        assessment.compounding_frequency = int(data.get('compounding_frequency', 12))
        forecast_data = data.get('forecast_data', {})
        # Store biweekly contribution in forecast_data for reference
        biweekly_contrib = data.get('biweekly_contribution')
        if biweekly_contrib is not None:
            forecast_data['biweekly_contribution'] = float(biweekly_contrib)
        assessment.forecast_data = forecast_data
        assessment.notes = data.get('notes', '')
        assessment.save()
        
        return JsonResponse({
            'success': True,
            'created': created,
            'id': assessment.id,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_bond_assessment(request):
    """Save bond assessment"""
    try:
        data = json.loads(request.body)
        
        linked_account_id = data.get('linked_account_id')
        linked_account = None
        if linked_account_id:
            linked_account = LinkedAccount.objects.filter(
                id=linked_account_id,
                user=request.user
            ).first()
        
        assessment_id = data.get('id')
        if assessment_id:
            try:
                assessment = BondAssessment.objects.get(id=assessment_id, user=request.user)
                created = False
            except BondAssessment.DoesNotExist:
                assessment = BondAssessment(user=request.user)
                created = True
        else:
            assessment = BondAssessment(user=request.user)
            created = True
        
        assessment.linked_account = linked_account
        assessment.account_name = data.get('account_name', 'Bond Investment')
        assessment.face_value = Decimal(str(data.get('face_value', 0)))
        assessment.coupon_rate = Decimal(str(data.get('coupon_rate', 0)))
        assessment.purchase_price = Decimal(str(data.get('purchase_price', 0)))
        assessment.years_to_maturity = Decimal(str(data.get('years_to_maturity', 0)))
        assessment.payment_frequency = int(data.get('payment_frequency', 2))
        forecast_data = data.get('forecast_data', {})
        # Store biweekly contribution in forecast_data for reference
        biweekly_contrib = data.get('biweekly_contribution')
        if biweekly_contrib is not None:
            forecast_data['biweekly_contribution'] = float(biweekly_contrib)
        assessment.forecast_data = forecast_data
        assessment.notes = data.get('notes', '')
        assessment.save()
        
        return JsonResponse({
            'success': True,
            'created': created,
            'id': assessment.id,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

