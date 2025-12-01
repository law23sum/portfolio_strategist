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

