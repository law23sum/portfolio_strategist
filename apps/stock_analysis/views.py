import json
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings
from pathlib import Path

from .models import StockAnalysis, InvestmentPlan, PersonalLoanAnalysis
from .services import StockAnalysisService
from .forms import StockAnalysisForm, InvestmentPlanForm, PersonalLoanForm


@login_required
def stock_analysis_home(request):
    """Main stock analysis page"""
    analyses = StockAnalysis.objects.filter(user=request.user)[:10]
    return render(request, 'stock_analysis/home.html', {
        'analyses': analyses,
        'active_tab': 'stock_analysis',
    })


@login_required
@require_http_methods(["GET", "POST"])
def analyze_stock(request):
    """Analyze a stock symbol"""
    if request.method == 'POST':
        form = StockAnalysisForm(request.POST)
        if form.is_valid():
            symbol = form.cleaned_data['symbol'].upper()
            forecast_days = form.cleaned_data.get('forecast_days', 365)
            equation_type = form.cleaned_data.get('equation_type')
            
            service = StockAnalysisService()
            result = service.analyze_stock(symbol, forecast_days, equation_type)
            
            if result:
                # Save analysis
                analysis = StockAnalysis.objects.create(
                    user=request.user,
                    symbol=symbol,
                    stock_data=result['stock_data'],
                    ratios_table=result['ratios_table'],
                    ai_assessment=result['ai_assessment'],
                    forecast_data=result['forecast_data'],
                    news_html=result['news_html'],
                    forecast_days=forecast_days,
                    equation_type=equation_type or 'Geometric Brownian Motion External Macroeconomic Factors',
                )
                
                return redirect('stock_analysis:results', pk=analysis.pk)
            else:
                form.add_error('symbol', 'Unable to fetch data for this symbol. Please try again.')
    
    else:
        form = StockAnalysisForm()
    
    return render(request, 'stock_analysis/analyze.html', {
        'form': form,
        'active_tab': 'stock_analysis',
    })


@login_required
def analysis_results(request, pk):
    """View analysis results"""
    analysis = get_object_or_404(StockAnalysis, pk=pk, user=request.user)
    
    # Convert JSON back to DataFrames for display
    ratios_df = pd.DataFrame(analysis.ratios_table) if analysis.ratios_table else pd.DataFrame()
    forecast_df = pd.DataFrame(analysis.forecast_data) if analysis.forecast_data else pd.DataFrame()
    
    return render(request, 'stock_analysis/results.html', {
        'analysis': analysis,
        'ratios_df': ratios_df,
        'forecast_df': forecast_df,
        'active_tab': 'stock_analysis',
    })


@login_required
@require_http_methods(["GET", "POST"])
def investment_planner(request, analysis_pk):
    """Investment planner and alerts page"""
    analysis = get_object_or_404(StockAnalysis, pk=analysis_pk, user=request.user)
    
    if request.method == 'POST':
        form = InvestmentPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.stock_analysis = analysis
            plan.save()
            return redirect('stock_analysis:planner', analysis_pk=analysis_pk)
    else:
        form = InvestmentPlanForm()
    
    # Get current price from forecast data
    current_price = None
    if analysis.forecast_data:
        forecast_df = pd.DataFrame(analysis.forecast_data)
        if not forecast_df.empty:
            current_price = float(forecast_df.iloc[0].get('Forecasted_Close', 0))
    
    plans = InvestmentPlan.objects.filter(user=request.user, stock_analysis=analysis)
    
    return render(request, 'stock_analysis/planner.html', {
        'analysis': analysis,
        'form': form,
        'plans': plans,
        'current_price': current_price,
        'active_tab': 'stock_analysis',
    })


@login_required
def download_pdf(request, pk):
    """Download PDF report"""
    analysis = get_object_or_404(StockAnalysis, pk=pk, user=request.user)
    
    service = StockAnalysisService()
    output_dir = Path(settings.MEDIA_ROOT) / 'stock_reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'{analysis.symbol}_{analysis.pk}.pdf'
    
    service.generate_pdf_report(
        analysis.symbol,
        analysis.stock_data,
        analysis.ratios_table,
        analysis.ai_assessment,
        str(output_path)
    )
    
    with open(output_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{analysis.symbol}_report.pdf"'
        return response


@login_required
@require_http_methods(["GET", "POST"])
def personal_loan_analysis(request):
    """Personal loan analysis page"""
    if request.method == 'POST':
        form = PersonalLoanForm(request.POST, request.FILES)
        if form.is_valid():
            loan_analysis = form.save(commit=False)
            loan_analysis.user = request.user
            
            # Process CSV
            df = pd.read_csv(loan_analysis.csv_file)
            
            # Calculate individual amounts
            individual_amounts = df.sort_values('Direction').to_dict('records')
            
            # Calculate total amounts by direction
            total_amounts = df.groupby('Direction')['Amount'].sum().to_dict()
            
            loan_analysis.individual_amounts = individual_amounts
            loan_analysis.total_amounts = total_amounts
            loan_analysis.save()
            
            return redirect('stock_analysis:loan_results', pk=loan_analysis.pk)
    else:
        form = PersonalLoanForm()
    
    analyses = PersonalLoanAnalysis.objects.filter(user=request.user)[:10]
    
    return render(request, 'stock_analysis/personal_loan.html', {
        'form': form,
        'analyses': analyses,
        'active_tab': 'stock_analysis',
    })


@login_required
def loan_results(request, pk):
    """View loan analysis results"""
    analysis = get_object_or_404(PersonalLoanAnalysis, pk=pk, user=request.user)
    
    individual_df = pd.DataFrame(analysis.individual_amounts)
    total_df = pd.DataFrame(list(analysis.total_amounts.items()), columns=['Direction', 'Total'])
    
    return render(request, 'stock_analysis/loan_results.html', {
        'analysis': analysis,
        'individual_df': individual_df,
        'total_df': total_df,
        'active_tab': 'stock_analysis',
    })


@login_required
@require_http_methods(["POST"])
def investment_forecast_api(request):
    """
    API endpoint for investment forecasting using full financia logic.
    Returns forecast data for the investment and retirement planner.
    """
    try:
        import json
        from .lib.investment_utils import (
            get_current_price, calculate_purchase_plan, summarize_forecast, HORIZON_WINDOWS
        )
        
        data = json.loads(request.body)
        symbol = data.get('symbol', '').upper().strip()
        investment_amount = data.get('investment_amount')
        share_quantity = data.get('share_quantity')
        forecast_days = int(data.get('forecast_days', 365))
        equation_type = data.get('equation_type', 'Geometric Brownian Motion External Macroeconomic Factors')
        
        if not symbol:
            return JsonResponse({'error': 'Stock symbol is required'}, status=400)
        
        # Use StockAnalysisService to get full financia analysis
        service = StockAnalysisService()
        
        # Fetch historical data
        history_df = service.stock_app.fetch_stock_history(symbol, period="1y", interval="1d")
        if history_df.empty:
            return JsonResponse({'error': f'Unable to fetch historical data for {symbol}'}, status=400)
        
        # Get current price
        current_price = get_current_price(history_df)
        if not current_price:
            return JsonResponse({'error': 'Unable to determine current price'}, status=400)
        
        # Calculate purchase plan
        try:
            plan = calculate_purchase_plan(
                current_price=current_price,
                investment_amount=float(investment_amount) if investment_amount else None,
                share_quantity=float(share_quantity) if share_quantity else None
            )
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        if plan['shares'] <= 0:
            return JsonResponse({'error': 'Calculated share quantity is zero. Adjust your inputs.'}, status=400)
        
        # Get ratios for advanced forecasting
        stock_data = service.stock_app.fetch_stock_data(symbol)
        ratios_table = service.stock_app.analyze_stock(stock_data) if stock_data else pd.DataFrame()
        
        # Generate forecast using full financia logic
        forecast_result = service.stock_app.forecast_prices_advanced(
            history_df,
            symbol,
            ratios_table,
            "1d",
            equation_type=equation_type,
            forecast_days=forecast_days,
            return_raw_series=True
        )
        
        if isinstance(forecast_result, tuple):
            forecast_df, t_forecast, forecast_prices = forecast_result
        else:
            forecast_df = forecast_result
            if forecast_df.empty:
                return JsonResponse({'error': 'Forecast generation failed'}, status=400)
            t_forecast = forecast_df.index.values if hasattr(forecast_df.index, 'values') else range(len(forecast_df))
            forecast_prices = forecast_df['Forecasted_Close'].values if 'Forecasted_Close' in forecast_df.columns else forecast_df.iloc[:, 0].values
        
        # Get last historical date
        last_hist_date = pd.to_datetime(history_df['Date'].iloc[-1]) if 'Date' in history_df.columns else None
        
        # Summarize forecast for all horizons
        import numpy as np
        summary = summarize_forecast(
            t_values=np.asarray(t_forecast, dtype=float),
            forecast_prices=np.asarray(forecast_prices, dtype=float),
            current_price=current_price,
            share_quantity=plan['shares'],
            total_cost=plan['total_cost'],
            last_hist_date=last_hist_date,
            horizons=HORIZON_WINDOWS
        )
        
        # Convert forecast data to list format
        forecast_data = []
        if isinstance(forecast_df, pd.DataFrame) and not forecast_df.empty:
            for idx, row in forecast_df.iterrows():
                forecast_data.append({
                    'date': str(row.get('Date', idx)) if 'Date' in row else str(idx),
                    'price': float(row.get('Forecasted_Close', row.iloc[0])),
                    'day': int(idx) if isinstance(idx, (int, float)) else 0
                })
        else:
            # Fallback: create from t_forecast and forecast_prices
            for i, (t, price) in enumerate(zip(t_forecast, forecast_prices)):
                forecast_data.append({
                    'date': str(last_hist_date + pd.Timedelta(days=int(t))) if last_hist_date else str(i),
                    'price': float(price),
                    'day': int(t)
                })
        
        # Format summary for JSON response
        formatted_summary = []
        for entry in summary:
            formatted_summary.append({
                'label': entry['label'],
                'days': entry['days'],
                'forecast_price': float(entry['forecast_price']),
                'growth_pct': float(entry['growth_pct']) if entry['growth_pct'] is not None else None,
                'investment_value': float(entry['investment_value']) if entry['investment_value'] is not None else None,
                'profit_loss': float(entry['profit_loss']) if entry['profit_loss'] is not None else None,
                'target_date': str(entry['target_date']) if entry['target_date'] is not None else None,
                'peak': {
                    'price': float(entry['peak']['price']),
                    'day': float(entry['peak']['day']),
                    'date': str(entry['peak']['date']) if entry['peak']['date'] is not None else None,
                },
                'valley': {
                    'price': float(entry['valley']['price']),
                    'day': float(entry['valley']['day']),
                    'date': str(entry['valley']['date']) if entry['valley']['date'] is not None else None,
                }
            })
        
        return JsonResponse({
            'success': True,
            'current_price': float(current_price),
            'purchase_plan': {
                'shares': float(plan['shares']),
                'total_cost': float(plan['total_cost'])
            },
            'forecast_data': forecast_data,
            'summary': formatted_summary,
            'equation_type': equation_type,
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

