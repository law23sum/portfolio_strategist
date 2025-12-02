import json
import logging

import numpy as np
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone
from pathlib import Path

logger = logging.getLogger(__name__)

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
    """Analyze a stock symbol - web view"""
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
@csrf_exempt
@require_http_methods(["POST"])
def analyze_stock_api(request):
    """API endpoint for analyzing a stock symbol - for mobile apps"""
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', '').upper().strip()
        forecast_days = int(data.get('forecast_days', 365))
        equation_type = data.get('equation_type', 'Geometric Brownian Motion External Macroeconomic Factors')
        
        if not symbol:
            return JsonResponse({'error': 'Stock symbol is required'}, status=400)
        
        service = StockAnalysisService()
        result = service.analyze_stock(symbol, forecast_days, equation_type)
        
        if not result:
            return JsonResponse({'error': f'Unable to fetch data for {symbol}'}, status=400)
        
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
            equation_type=equation_type,
        )
        
        return JsonResponse({
            'success': True,
            'analysis_id': analysis.pk,
            'symbol': symbol,
            'stock_data': result['stock_data'],
            'ratios_table': result['ratios_table'],
            'ai_assessment': result['ai_assessment'],
            'forecast_data': result['forecast_data'],
            'news_html': result['news_html'],
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


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
@csrf_exempt
@require_http_methods(["POST"])
def investment_forecast_api(request):
    """
    API endpoint for investment forecasting using Financia logic.
    
    CSRF exempt to support both web (session auth) and mobile (token auth) clients.
    Authentication is still enforced via @login_required decorator.
    """
    try:
        import json
        from .lib.investment_utils import (
            get_current_price,
            calculate_purchase_plan,
            summarize_forecast,
        )
        from .lib.stock_statistics import (
            calculate_statistics,
            calculate_eta_theta,
            calculate_factor_betas,
            calculate_interest_rate_beta,
            calculate_market_beta,
            calculate_volatility_beta,
        )
    except ImportError:
        return JsonResponse(
            {'error': 'Stock analysis library not available. The lib directory is missing.'},
            status=503,
        )

    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', '').upper().strip()
        investment_amount = data.get('investment_amount')
        share_quantity = data.get('share_quantity')
        forecast_days = int(data.get('forecast_days', 10950))
        equation_type = data.get(
            'equation_type', 'Geometric Brownian Motion External Macroeconomic Factors'
        )
        biweekly_contribution = float(data.get('biweekly_contribution', 0) or 0)

        if not symbol:
            return JsonResponse({'error': 'Stock symbol is required'}, status=400)

        service = StockAnalysisService()

        history_df = service.stock_app.fetch_stock_history(symbol, period="2y", interval="1d")
        if history_df.empty:
            history_df = service.stock_app.fetch_stock_history(symbol, period="1y", interval="1d")
        if history_df.empty:
            return JsonResponse({'error': f'Unable to fetch historical data for {symbol}'}, status=400)

        current_price = get_current_price(history_df)
        if not current_price:
            return JsonResponse({'error': 'Unable to determine current price'}, status=400)

        plan = calculate_purchase_plan(
            current_price=current_price,
            investment_amount=float(investment_amount) if investment_amount else None,
            share_quantity=float(share_quantity) if share_quantity else None,
        )
        if plan['shares'] <= 0:
            return JsonResponse({'error': 'Calculated share quantity is zero. Adjust your inputs.'}, status=400)

        stock_data = service.stock_app.fetch_stock_data(symbol)
        ratios_table = service.stock_app.analyze_stock(stock_data) if stock_data else pd.DataFrame()

        mu_daily, sigma_daily, closing_prices, _ = calculate_statistics(history_df)

        mean_reversion_params = {"eta": 0.0, "theta": float(current_price)}
        external_factors = {
            "market_beta": 0.0,
            "factor_betas": {},
            "interest_rate_beta": 0.0,
            "volatility_beta": 0.0,
        }

        def _load_series(sym):
            df = service.stock_app.fetch_stock_history(sym, period="1y", interval="1d")
            if df.empty:
                return pd.DataFrame()
            series = df[['Date', 'Close']].copy()
            series['Date'] = pd.to_datetime(series['Date'])
            series.rename(columns={'Close': f'{sym}_Close'}, inplace=True)
            return series

        try:
            stock_series = history_df[['Date', 'Close']].copy()
            stock_series['Date'] = pd.to_datetime(stock_series['Date'])
            stock_series.rename(columns={'Close': f'{symbol}_Close'}, inplace=True)

            market_series = _load_series('^GSPC')
            vix_series = _load_series('^VIX')
            tnx_series = _load_series('^TNX')

            merged = stock_series
            for extra in (market_series, vix_series, tnx_series):
                if extra.empty:
                    merged = pd.DataFrame()
                    break
                merged = merged.merge(extra, on='Date', how='inner')

            if not merged.empty:
                stock_data_vals = merged[f'{symbol}_Close'].to_numpy(dtype=float)
                market_data_vals = merged['^GSPC_Close'].to_numpy(dtype=float)
                vix_data_vals = merged['^VIX_Close'].to_numpy(dtype=float)
                tnx_data_vals = merged['^TNX_Close'].to_numpy(dtype=float)

                stock_returns = np.diff(stock_data_vals) / stock_data_vals[:-1]
                market_returns = np.diff(market_data_vals) / market_data_vals[:-1]
                vix_changes = np.diff(vix_data_vals) / vix_data_vals[:-1]
                interest_rate_changes = np.diff(tnx_data_vals) / tnx_data_vals[:-1]

                min_len = min(
                    len(stock_returns), len(market_returns), len(vix_changes), len(interest_rate_changes)
                )
                if min_len > 10:
                    stock_returns = stock_returns[:min_len]
                    market_returns = market_returns[:min_len]
                    vix_changes = vix_changes[:min_len]
                    interest_rate_changes = interest_rate_changes[:min_len]

                    factor_returns = pd.DataFrame(
                        {
                            "SMB": np.random.normal(0, 0.01, min_len),
                            "HML": np.random.normal(0, 0.01, min_len),
                            "MOM": np.random.normal(0, 0.01, min_len),
                        }
                    )

                    eta, theta = calculate_eta_theta(stock_data_vals[:min_len])
                    beta_m = calculate_market_beta(stock_returns, market_returns)
                    factor_betas = calculate_factor_betas(stock_returns, factor_returns)
                    beta_r = calculate_interest_rate_beta(stock_returns, interest_rate_changes)
                    beta_v = calculate_volatility_beta(stock_returns, vix_changes)

                    mean_reversion_params = {
                        "eta": float(eta) if np.isfinite(eta) else 0.0,
                        "theta": float(theta) if np.isfinite(theta) else float(current_price),
                    }
                    external_factors = {
                        "market_beta": float(beta_m) if np.isfinite(beta_m) else 0.0,
                        "factor_betas": {
                            k: float(v) if np.isfinite(v) else 0.0 for k, v in factor_betas.items()
                        } if isinstance(factor_betas, dict) else {},
                        "interest_rate_beta": float(beta_r) if np.isfinite(beta_r) else 0.0,
                        "volatility_beta": float(beta_v) if np.isfinite(beta_v) else 0.0,
                    }
        except Exception as exc:
            print(f"External factor calculation failed: {exc}")

        forecast_result = service.stock_app.forecast_prices_advanced(
            history_df,
            symbol,
            ratios_table,
            "1d",
            equation_type=equation_type,
            forecast_days=forecast_days,
            return_raw_series=True,
        )

        if isinstance(forecast_result, tuple):
            forecast_df, t_forecast, forecast_prices = forecast_result
        else:
            forecast_df = forecast_result
            t_forecast = np.arange(len(forecast_df))
            forecast_prices = forecast_df['Forecasted_Close'].to_numpy(dtype=float)

        if forecast_df is None or forecast_df.empty:
            num_points = min(forecast_days, 1000)
            t_forecast = np.linspace(0, forecast_days, num_points)
            dt = forecast_days / num_points if num_points > 1 else 1
            np.random.seed(42)
            W = np.cumsum(np.random.standard_normal(num_points) * np.sqrt(dt))
            forecast_prices = current_price * np.exp(
                (mu_daily - 0.5 * sigma_daily ** 2) * t_forecast + sigma_daily * W
            )
            forecast_df = pd.DataFrame(
                {
                    'Date': [pd.to_datetime(history_df['Date'].iloc[-1]) + pd.Timedelta(days=int(t)) for t in t_forecast],
                    'Forecasted_Close': forecast_prices,
                }
            )

        # Ensure t_forecast and forecast_prices are proper 1D arrays
        t_forecast = np.asarray(t_forecast, dtype=float)
        forecast_prices = np.asarray(forecast_prices, dtype=float)
        
        # Flatten to 1D if needed (handle 0-d arrays or multi-dimensional arrays)
        if t_forecast.ndim == 0:
            t_forecast = np.array([float(t_forecast)])
        elif t_forecast.ndim > 1:
            t_forecast = t_forecast.flatten()
        
        if forecast_prices.ndim == 0:
            forecast_prices = np.array([float(forecast_prices)])
        elif forecast_prices.ndim > 1:
            forecast_prices = forecast_prices.flatten()
        
        # Ensure arrays have at least one element
        if len(t_forecast) == 0 or len(forecast_prices) == 0:
            raise ValueError("Forecast arrays are empty; cannot generate summary.")
        
        # Ensure arrays have the same length
        min_len = min(len(t_forecast), len(forecast_prices))
        t_forecast = t_forecast[:min_len]
        forecast_prices = forecast_prices[:min_len]

        last_hist_date = pd.to_datetime(history_df['Date'].iloc[-1]) if 'Date' in history_df.columns else None
        extended_horizons = {
            "Biweekly": 14,
            "Monthly": 30,
            "Quarterly": 90,
            "Biyearly": 182,
            "Yearly": 365,
            "3 Years": 1095,
            "5 Years": 1825,
            "Decade": 3650,
            "Two Decades": 7300,
            "Three Decades": 10950,
        }

        summary = summarize_forecast(
            t_values=t_forecast,
            forecast_prices=forecast_prices,
            current_price=current_price,
            share_quantity=plan['shares'],
            total_cost=plan['total_cost'],
            last_hist_date=last_hist_date,
            horizons=extended_horizons,
        )

        forecast_data = []
        if isinstance(forecast_df, pd.DataFrame) and not forecast_df.empty:
            for _, row in forecast_df.iterrows():
                forecast_data.append(
                    {
                        'date': str(row.get('Date')),
                        'price': float(row.get('Forecasted_Close', 0) or 0),
                    }
                )
        else:
            for idx, (t_val, price) in enumerate(zip(t_forecast, forecast_prices)):
                forecast_data.append(
                    {
                        'date': str(last_hist_date + pd.Timedelta(days=int(t_val))) if last_hist_date else str(idx),
                        'price': float(price),
                    }
                )

        statistics = {
            'mu_daily': float(mu_daily) if np.isfinite(mu_daily) else 0.0,
            'sigma_daily': float(sigma_daily) if np.isfinite(sigma_daily) else 0.0,
        }

        formatted_summary = []
        for entry in summary:
            formatted_summary.append(
                {
                    'label': entry['label'],
                    'days': entry['days'],
                    'forecast_price': float(entry['forecast_price']),
                    'growth_pct': float(entry['growth_pct']) if entry['growth_pct'] is not None else None,
                    'investment_value': float(entry['investment_value']) if entry['investment_value'] is not None else None,
                    'profit_loss': float(entry['profit_loss']) if entry['profit_loss'] is not None else None,
                    'target_date': entry['target_date'].isoformat() if entry['target_date'] is not None else None,
                    'peak': entry['peak'],
                    'valley': entry['valley'],
                }
            )

        # Add comprehensive financia analysis data
        from .lib.analysis_utils import (
            calculate_risk_statistics,
            build_market_overview,
            generate_risk_insights,
            build_decision_support,
            build_forecast_error_rows,
        )
        from .lib.ai_analyzer import analyze_stock_with_news

        # Get ratios data
        ratios_data = []
        if not ratios_table.empty:
            ratios_data = ratios_table.to_dict('records')

        # Get risk statistics
        risk_metrics, benchmark_df = calculate_risk_statistics(history_df)
        risk_insights = generate_risk_insights(risk_metrics, symbol)

        # Get market overview
        market_overview = build_market_overview(history_df, symbol)

        # Get news and AI analysis
        news_html = service.stock_app.fetch_stock_news(symbol)
        ai_assessment = ""
        if not ratios_table.empty:
            try:
                ai_assessment = analyze_stock_with_news(ratios_table, news_html)
            except Exception as ai_exc:
                print(f"AI analysis failed: {ai_exc}")

        # Get decision support
        decision_support = build_decision_support(
            ratios_table,
            ai_assessment,
            history_df,
            risk_metrics=risk_metrics,
        )

        # Get forecast errors
        forecast_errors = build_forecast_error_rows(history_df, forecast_df)

        # Prepare historical data for charts
        historical_data = []
        if not history_df.empty:
            for _, row in history_df.iterrows():
                historical_data.append({
                    'date': str(row.get('Date', '')),
                    'open': float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None,
                    'high': float(row.get('High', 0)) if pd.notna(row.get('High')) else None,
                    'low': float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None,
                    'close': float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                    'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None,
                })

        # Prepare stock fundamentals
        key_metrics = {}
        if stock_data:
            key_metrics = {
                'sector': stock_data.get('sector', 'N/A'),
                'industry': stock_data.get('industry', 'N/A'),
                'marketCap': stock_data.get('Market Cap', None),
                'enterpriseValue': stock_data.get('Enterprise Value/EBITDA', None),
                'trailingPE': stock_data.get('PE Ratio (TTM)', None),
                'beta': stock_data.get('beta', None),
                'dividendYield': stock_data.get('Forward Annual Dividend Yield 4', None),
                '52WeekHigh': stock_data.get('fiftyTwoWeekHigh', None),
                '52WeekLow': stock_data.get('fiftyTwoWeekLow', None),
            }

        # Save forecast data to StockAnalysis for future use
        forecast_data_dict = {
            'forecast_data': forecast_data,
            'summary': formatted_summary,
            'statistics': statistics,
            'external_factors': external_factors,
            'mean_reversion_params': mean_reversion_params,
            'risk_metrics': {k: float(v) if np.isfinite(v) else None for k, v in risk_metrics.items()},
            'risk_insights': risk_insights,
            'market_overview': market_overview,
            'decision_support': decision_support,
            'forecast_errors': forecast_errors,
            'historical_data': historical_data,
            'purchase_plan': {
                'shares': float(plan['shares']),
                'total_cost': float(plan['total_cost']),
                'current_price': float(current_price),
            },
        }
        
        # Update or create StockAnalysis with forecast data
        try:
            stock_data_dict = stock_data if stock_data else {}
            ratios_dict = ratios_table.to_dict('records') if not ratios_table.empty else []
            
            StockAnalysis.objects.update_or_create(
                user=request.user,
                symbol=symbol,
                defaults={
                    'stock_data': stock_data_dict,
                    'ratios_table': ratios_dict,
                    'forecast_data': forecast_data_dict,
                    'forecast_days': forecast_days,
                    'equation_type': equation_type,
                    'forecast_errors': forecast_errors,
                    'risk_metrics': {k: float(v) if np.isfinite(v) else None for k, v in risk_metrics.items()},
                    'risk_insights': risk_insights,
                    'market_overview': market_overview,
                    'decision_support': decision_support,
                    'history_data': historical_data,
                }
            )
            logger.info(f"Saved forecast data to StockAnalysis for {symbol}")
        except Exception as save_error:
            logger.warning(f"Failed to save forecast data to StockAnalysis: {save_error}")
            # Continue even if save fails
        
        return JsonResponse(
            {
                'success': True,
                'symbol': symbol,
                'current_price': float(current_price),
                'purchase_plan': {
                    'shares': float(plan['shares']),
                    'total_cost': float(plan['total_cost']),
                },
                'forecast_data': forecast_data,
                'summary': formatted_summary,
                'equation_type': equation_type,
                'statistics': statistics,
                'external_factors': external_factors,
                'mean_reversion_params': mean_reversion_params,
                # Comprehensive financia data
                'ratios': ratios_data,
                'risk_metrics': {k: float(v) if np.isfinite(v) else None for k, v in risk_metrics.items()},
                'risk_insights': risk_insights,
                'market_overview': market_overview,
                'decision_support': decision_support,
                'forecast_errors': forecast_errors,
                'historical_data': historical_data,
                'key_metrics': key_metrics,
                'news_html': news_html,
                'ai_assessment': ai_assessment,
            }
        )

    except Exception as exc:
        import traceback
        return JsonResponse({'error': str(exc), 'traceback': traceback.format_exc()}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def get_stock_analysis_forecast(request):
    """
    API endpoint to fetch forecast data from StockAnalysis model.
    This allows Preview Forecast to use existing analysis/predictions data.
    
    CSRF exempt to support both web (session auth) and mobile (token auth) clients.
    Authentication is still enforced via @login_required decorator.
    """
    try:
        import json
        if request.method == 'POST':
            data = json.loads(request.body)
        else:
            data = request.GET
        
        symbol = data.get('symbol', '').upper().strip()
        if not symbol:
            return JsonResponse({'error': 'Stock symbol is required'}, status=400)
        
        # Get the most recent StockAnalysis for this symbol and user
        analysis = StockAnalysis.objects.filter(
            user=request.user,
            symbol=symbol
        ).order_by('-analysis_date').first()
        
        if not analysis or not analysis.forecast_data:
            return JsonResponse({
                'success': False,
                'error': f'No forecast data found for {symbol}. Please run analysis first.',
                'symbol': symbol
            }, status=404)
        
        forecast_data_dict = analysis.forecast_data
        
        # Get current price from stock_data if available, or from purchase_plan
        current_price = None
        if analysis.stock_data and isinstance(analysis.stock_data, dict):
            current_price = analysis.stock_data.get('currentPrice') or analysis.stock_data.get('regularMarketPrice')
        
        if not current_price and forecast_data_dict.get('purchase_plan'):
            current_price = forecast_data_dict.get('purchase_plan', {}).get('current_price')
        
        # Extract data in the format expected by the frontend
        purchase_plan = forecast_data_dict.get('purchase_plan', {})
        if current_price and not purchase_plan.get('current_price'):
            purchase_plan['current_price'] = current_price
        
        response_data = {
            'success': True,
            'symbol': symbol,
            'current_price': float(current_price) if current_price else None,
            'purchase_plan': purchase_plan,
            'forecast_data': forecast_data_dict.get('forecast_data', []),
            'summary': forecast_data_dict.get('summary', []),
            'equation_type': analysis.equation_type,
            'statistics': forecast_data_dict.get('statistics', {}),
            'external_factors': forecast_data_dict.get('external_factors', {}),
            'mean_reversion_params': forecast_data_dict.get('mean_reversion_params', {}),
            'ratios': analysis.ratios_table if isinstance(analysis.ratios_table, list) else [],
            'risk_metrics': forecast_data_dict.get('risk_metrics', {}),
            'risk_insights': forecast_data_dict.get('risk_insights', []),
            'market_overview': forecast_data_dict.get('market_overview', {}),
            'decision_support': forecast_data_dict.get('decision_support', {}),
            'forecast_errors': forecast_data_dict.get('forecast_errors', []),
            'historical_data': forecast_data_dict.get('historical_data', []),
            'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
        }
        
        return JsonResponse(response_data)
        
    except Exception as exc:
        import traceback
        logger.exception(f"Error fetching StockAnalysis forecast: {exc}")
        return JsonResponse({'error': str(exc), 'traceback': traceback.format_exc()}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def stock_details_api(request):
    """
    API endpoint to fetch comprehensive stock details from multiple sources:
    - Polygon.io (if API key available)
    - Alpha Vantage (if API key available)
    - Yahoo Finance (via web scraping)
    
    Data is aggregated, deduplicated, and merged intelligently.
    
    NOTE: Stock data is PUBLIC and shared across all users. Any authenticated user
    can access stock data for any symbol. StockWatchSnapshot stores public stock
    data that is accessible to all users.
    
    CSRF exempt to support both web (session auth) and mobile (token auth) clients.
    Authentication is still enforced via @login_required decorator.
    """
    try:
        import json
        if request.method == 'POST':
            data = json.loads(request.body)
        else:
            data = request.GET
        
        symbol = data.get('symbol', '').upper().strip()
        if not symbol:
            return JsonResponse({'error': 'Stock symbol is required'}, status=400)
        
        # PRIORITY 1: ALWAYS fetch Yahoo Finance scraping FIRST (web scraping via headless Chrome)
        # This ensures fresh data is always being populated from web scraping
        # When populating information, we wait for scraping to complete to get accurate current price
        from .tasks import scrape_yahoo_finance_comprehensive
        from .models import StockWatchSnapshot
        from datetime import timedelta
        
        # Check if we have recent snapshot to determine if we should force refresh
        snapshot = None
        force_refresh = True
        try:
            snapshot = StockWatchSnapshot.objects.filter(symbol=symbol).first()
            if snapshot and snapshot.fetched_at:
                age = timezone.now() - snapshot.fetched_at
                # Force refresh if data is older than 1 hour
                force_refresh = age > timedelta(hours=1)
        except Exception:
            pass
        
        # When populating information, we need fresh data, so run scraping synchronously
        # This ensures we get the correct current price from web scraping
        scraping_completed = False
        try:
            # Try to run synchronously first to get fresh data immediately
            # This is important for getting accurate current price when populating information
            logger.info(f"Running synchronous Yahoo Finance web scraping for {symbol} to get fresh current price (force_refresh={force_refresh})")
            result = scrape_yahoo_finance_comprehensive(symbol, force_refresh=force_refresh)
            scraping_completed = result.get('success', False)
            logger.info(f"Synchronous Yahoo Finance scraping completed for {symbol}: {scraping_completed}")
        except Exception as sync_error:
            # If synchronous fails, try async via Celery as fallback
            try:
                logger.warning(f"Synchronous scraping failed, trying async Celery task: {sync_error}")
                scrape_yahoo_finance_comprehensive.delay(symbol, force_refresh=force_refresh)
                logger.info(f"Triggered async comprehensive Yahoo Finance web scraping task for {symbol} (force_refresh={force_refresh})")
            except Exception as async_error:
                logger.error(f"Could not trigger Yahoo Finance scraping: {async_error}")
        
        # Refresh snapshot from database after scraping (may have been just updated)
        snapshot = None
        try:
            snapshot = StockWatchSnapshot.objects.filter(symbol=symbol).first()
            # If we just completed scraping, use the fresh data even if it's slightly old
            # Otherwise, check if snapshot is stale (older than 1 hour)
            if snapshot and snapshot.fetched_at:
                age = timezone.now() - snapshot.fetched_at
                if not scraping_completed and age > timedelta(hours=1):
                    snapshot = None  # Consider stale only if scraping didn't complete
        except Exception:
            pass
        
        # If we have a snapshot with price data, use it immediately
        if snapshot and snapshot.current_price and snapshot.payload:
            try:
                # Extract data from snapshot payload
                payload = snapshot.payload or {}
                yahoo_data = payload.get('yahoo_comprehensive', {})
                
                # Build response from snapshot
                summary = payload.get('summary', {})
                statistics = payload.get('statistics', {})
                
                # Get current price from snapshot - prioritize web-scraped price
                # Try multiple sources in order: snapshot.current_price (from web scraping) > summary.currentPrice > statistics
                current_price = None
                if snapshot.current_price:
                    try:
                        current_price = float(snapshot.current_price)
                    except (ValueError, TypeError):
                        pass
                
                # Fallback to summary if snapshot price is not available
                if not current_price or current_price <= 0:
                    price_candidates = [
                        summary.get('currentPrice'),
                        summary.get('regularMarketPrice'),
                        statistics.get('Current Price'),
                        statistics.get('Previous Close'),
                    ]
                    for candidate in price_candidates:
                        if candidate is not None:
                            try:
                                # Clean price string (remove $, commas, etc.)
                                if isinstance(candidate, str):
                                    candidate = candidate.replace('$', '').replace(',', '').strip()
                                current_price = float(candidate)
                                if current_price and current_price > 0:
                                    break
                            except (ValueError, TypeError):
                                continue
                
                # Build key metrics from snapshot
                key_metrics = {
                    'sector': summary.get('sector') or statistics.get('Sector', 'N/A'),
                    'industry': summary.get('industry') or statistics.get('Industry', 'N/A'),
                    'marketCap': summary.get('marketCap') or statistics.get('Market Cap'),
                    'currentPrice': current_price,
                    'beta': summary.get('beta') or statistics.get('Beta (5Y Monthly)'),
                    'peRatio': summary.get('peRatio') or statistics.get('Trailing P/E'),
                    'forwardPE': summary.get('forwardPE') or statistics.get('Forward P/E'),
                    'dividendYield': summary.get('dividendYield') or statistics.get('Dividend Yield'),
                    '52WeekHigh': summary.get('52WeekHigh') or statistics.get('52 Week High'),
                    '52WeekLow': summary.get('52WeekLow') or statistics.get('52 Week Low'),
                }
                
                # Prepare news from snapshot
                news_items = snapshot.news_items or []
                news_html_parts = []
                for item in news_items:
                    # Handle nested structure where data is inside 'summary' object
                    if item.get('summary') and isinstance(item.get('summary'), dict):
                        summary = item.get('summary', {})
                        title = summary.get('title') or item.get("title", "")
                        link = (
                            summary.get('canonicalUrl', {}).get('url') or
                            summary.get('clickThroughUrl', {}).get('url') or
                            summary.get('previewUrl') or
                            item.get("link", "") or
                            item.get("url", "")
                        )
                        publisher = (
                            summary.get('provider', {}).get('displayName') or
                            summary.get('provider', {}).get('name') or
                            item.get("publisher", "")
                        )
                        summary_text = summary.get('summary') or summary.get('description') or item.get("summary", "")
                    else:
                        # Handle flat structure (normalized format)
                        title = item.get("title", "")
                        link = item.get("link", "") or item.get("url", "")
                        publisher = item.get("publisher", "")
                        summary_text = item.get("summary", "")
                    
                    if title and link:
                        article_html = f'<article><h2>{title}</h2>'
                        if publisher:
                            article_html += f'<p><em>{publisher}</em></p>'
                        if summary_text:
                            article_html += f'<p>{summary_text}</p>'
                        article_html += f'<p><a href="{link}">Read more</a></p></article>'
                        news_html_parts.append(article_html)
                
                news_html = "\n".join(news_html_parts) if news_html_parts else ""
                
                # Fetch historical data for charts
                history_df = service.stock_app.fetch_stock_history(symbol, period="1y", interval="1d")
                historical_data = []
                if not history_df.empty:
                    for _, row in history_df.iterrows():
                        historical_data.append({
                            'date': str(row.get('Date', '')),
                            'open': float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None,
                            'high': float(row.get('High', 0)) if pd.notna(row.get('High')) else None,
                            'low': float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None,
                            'close': float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                            'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None,
                        })
                
                # Analyze ratios
                stock_data = payload.get('summary', {})
                ratios_table = service.stock_app.analyze_stock(stock_data)
                ratios_data = []
                if not ratios_table.empty:
                    ratios_data = ratios_table.to_dict('records')
                
                # Build comprehensive response from snapshot
                response_data = {
                    'success': True,
                    'symbol': symbol,
                    'stock_data': stock_data,
                    'key_metrics': key_metrics,
                    'historical_data': historical_data,
                    'ratios': ratios_data,
                    'news_html': news_html,
                    'sources_used': ['yahoo_finance_snapshot'],
                    'fetched_at': snapshot.fetched_at.isoformat() if snapshot.fetched_at else None,
                }
                
                # Add comprehensive Yahoo Finance data if available
                if yahoo_data:
                    response_data['yahoo_finance'] = {
                        'summary': yahoo_data.get('summary', summary),
                        'news': yahoo_data.get('news', news_items),
                        'chart_details': yahoo_data.get('chart_details', {}),
                        'statistics': yahoo_data.get('statistics', statistics),
                        'options': yahoo_data.get('options', {}),
                        'holders': yahoo_data.get('holders', {}),
                        'profile': yahoo_data.get('profile', {}),
                        'financials': yahoo_data.get('financials', {}),
                        'analysis': yahoo_data.get('analysis', {}),
                        'sustainability': yahoo_data.get('sustainability', {}),
                    }
                
                return JsonResponse(response_data)
            except Exception as snapshot_error:
                logger.warning(f"Error using snapshot data, falling back to API: {snapshot_error}")
                # Fall through to API-based fetching
        
        # Use data aggregator to fetch from all sources
        from .lib.data_aggregator import StockDataAggregator
        
        service = StockAnalysisService()
        aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)
        
        # Get comprehensive aggregated data
        try:
            comprehensive_data = aggregator.get_comprehensive_data(symbol)
        except Exception as agg_error:
            import traceback
            # Fallback to original method if aggregator fails
            print(f"Aggregator failed, falling back to single-source fetch: {agg_error}")
            traceback.print_exc()
            
            # Fallback to original method
            stock_data = service.stock_app.fetch_stock_data(symbol)
            if not stock_data:
                return JsonResponse({
                    'error': f'Unable to fetch stock data for {symbol}',
                    'suggestion': 'Please verify the stock symbol is correct and try again.'
                }, status=400)
            
            history_df = service.stock_app.fetch_stock_history(symbol, period="1y", interval="1d")
            news_html = service.stock_app.fetch_stock_news(symbol)
            ratios_table = service.stock_app.analyze_stock(stock_data)
            
            # Prepare response in old format
            historical_data = []
            if not history_df.empty:
                for _, row in history_df.iterrows():
                    historical_data.append({
                        'date': str(row.get('Date', '')),
                        'open': float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None,
                        'high': float(row.get('High', 0)) if pd.notna(row.get('High')) else None,
                        'low': float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None,
                        'close': float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                        'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None,
                    })
            
            ratios_data = []
            if not ratios_table.empty:
                ratios_data = ratios_table.to_dict('records')
            
            current_price = stock_data.get('currentPrice', None)
            if (current_price is None or current_price <= 0) and not history_df.empty:
                if 'Close' in history_df.columns:
                    close_prices = history_df['Close'].dropna()
                    if not close_prices.empty:
                        current_price = float(close_prices.iloc[-1])
            
            key_metrics = {
                'sector': stock_data.get('sector', 'N/A'),
                'industry': stock_data.get('industry', 'N/A'),
                'marketCap': stock_data.get('marketCap', None),
                'currentPrice': current_price,
            }
            
            return JsonResponse({
                'success': True,
                'symbol': symbol,
                'stock_data': stock_data,
                'key_metrics': key_metrics,
                'historical_data': historical_data,
                'ratios': ratios_data,
                'news_html': news_html,
                'sources_used': ['fallback'],
            })
        
        # Process aggregated data
        fundamentals = comprehensive_data.get('fundamentals', {})
        stock_history = comprehensive_data.get('stock_history', pd.DataFrame())
        
        # Fetch historical data for charts
        if stock_history.empty:
            history_df = service.stock_app.fetch_stock_history(symbol, period="1y", interval="1d")
            if history_df.empty:
                history_df = service.stock_app.fetch_stock_history(symbol, period="2y", interval="1d")
        else:
            history_df = stock_history
        
        # Analyze ratios using aggregated fundamentals
        ratios_table = service.stock_app.analyze_stock(fundamentals)
        
        # Prepare historical data for charts
        historical_data = []
        if not history_df.empty:
            for _, row in history_df.iterrows():
                historical_data.append({
                    'date': str(row.get('Date', '')),
                    'open': float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None,
                    'high': float(row.get('High', 0)) if pd.notna(row.get('High')) else None,
                    'low': float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None,
                    'close': float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                    'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None,
                })
        
        # Prepare ratios data
        ratios_data = []
        if not ratios_table.empty:
            ratios_data = ratios_table.to_dict('records')
        
        # Get current price - prioritize web-scraped snapshot data
        current_price = None
        
        # First, try to get price from snapshot (web-scraped data)
        try:
            snapshot = StockWatchSnapshot.objects.filter(symbol=symbol).first()
            if snapshot and snapshot.current_price:
                current_price = float(snapshot.current_price)
        except Exception:
            pass
        
        # Fallback to aggregated fundamentals if snapshot price not available
        if not current_price or current_price <= 0:
            current_price = fundamentals.get('currentPrice', None)
        
        # Fallback to historical data if still no price
        if (current_price is None or current_price <= 0) and not history_df.empty:
            try:
                from .lib.investment_utils import get_current_price
                current_price = get_current_price(history_df)
            except (ImportError, Exception):
                if 'Close' in history_df.columns:
                    close_prices = history_df['Close'].dropna()
                    if not close_prices.empty:
                        current_price = float(close_prices.iloc[-1])
        
        # Build key metrics from aggregated fundamentals
        key_metrics = {
            'sector': fundamentals.get('sector', 'N/A'),
            'industry': fundamentals.get('industry', 'N/A'),
            'marketCap': fundamentals.get('marketCap', None),
            'enterpriseValue': fundamentals.get('enterpriseValue', None),
            'trailingPE': fundamentals.get('trailingPE', None),
            'forwardPE': fundamentals.get('forwardPE', None),
            'beta': fundamentals.get('beta', None),
            'dividendYield': fundamentals.get('dividendYield', None),
            '52WeekHigh': fundamentals.get('52WeekHigh', None),
            '52WeekLow': fundamentals.get('52WeekLow', None),
            'currentPrice': current_price,
        }
        
        # Prepare news HTML from aggregated news
        news_items = comprehensive_data.get('news', [])
        news_html_parts = []
        for item in news_items:
            # Handle nested structure where data is inside 'summary' object
            if item.get('summary') and isinstance(item.get('summary'), dict):
                summary = item.get('summary', {})
                title = summary.get('title') or item.get("title", "")
                url = (
                    summary.get('canonicalUrl', {}).get('url') or
                    summary.get('clickThroughUrl', {}).get('url') or
                    summary.get('previewUrl') or
                    item.get("url", "") or
                    item.get("link", "")
                )
                publisher = (
                    summary.get('provider', {}).get('displayName') or
                    summary.get('provider', {}).get('name') or
                    item.get("publisher", item.get("source", ""))
                )
                description = summary.get('summary') or summary.get('description') or item.get("description", "")
            else:
                # Handle flat structure (normalized format)
                title = item.get("title", "")
                url = item.get("url", "") or item.get("link", "")
                publisher = item.get("publisher", item.get("source", ""))
                description = item.get("description", "") or item.get("summary", "")
            
            if title and url:
                article_html = f'<article><h2>{title}</h2>'
                if publisher:
                    article_html += f'<p><em>{publisher}</em></p>'
                if description:
                    article_html += f'<p>{description}</p>'
                article_html += f'<p><a href="{url}">Read more</a></p></article>'
                news_html_parts.append(article_html)
        
        news_html = "\n".join(news_html_parts) if news_html_parts else ""
        
        # Get Yahoo Finance data
        yahoo_finance = comprehensive_data.get('yahoo_finance', {})
        
        # Build response with aggregated data
        response_data = {
            'success': True,
            'symbol': symbol,
            'stock_data': fundamentals,  # Use aggregated fundamentals
            'key_metrics': key_metrics,
            'historical_data': historical_data,
            'ratios': ratios_data,
            'news_html': news_html,
            'sources_used': comprehensive_data.get('sources_used', []),
        }
        
        # Add Yahoo Finance comprehensive data if available
        if yahoo_finance:
            response_data['yahoo_finance'] = {
                'summary': yahoo_finance.get('summary', {}),
                'news': yahoo_finance.get('news', []),
                'chart_details': yahoo_finance.get('chart_details', {}),
                'statistics': yahoo_finance.get('statistics', {}),
                'options': yahoo_finance.get('options', {}),
                'holders': yahoo_finance.get('holders', {}),
                'profile': yahoo_finance.get('profile', {}),
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
