import json

import numpy as np
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
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
@require_http_methods(["POST"])
def investment_forecast_api(request):
    """API endpoint for investment forecasting using Financia logic."""
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
            t_values=np.asarray(t_forecast, dtype=float),
            forecast_prices=np.asarray(forecast_prices, dtype=float),
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
@require_http_methods(["GET", "POST"])
def stock_details_api(request):
    """
    API endpoint to fetch comprehensive stock details from yfinance including:
    - Stock info (fundamentals)
    - Historical price data (for charts)
    - Financial ratios
    - News
    - Volume data
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
        
        service = StockAnalysisService()
        
        # Fetch stock data (fundamentals)
        stock_data = service.stock_app.fetch_stock_data(symbol)
        if not stock_data:
            return JsonResponse({'error': f'Unable to fetch stock data for {symbol}'}, status=400)
        
        # Fetch historical data for charts
        history_df = service.stock_app.fetch_stock_history(symbol, period="1y", interval="1d")
        if history_df.empty:
            # Try longer period
            history_df = service.stock_app.fetch_stock_history(symbol, period="2y", interval="1d")
        
        # Fetch news
        news_html = service.stock_app.fetch_stock_news(symbol)
        
        # Analyze ratios
        ratios_table = service.stock_app.analyze_stock(stock_data)
        
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
        
        # Extract key metrics from stock_data
        key_metrics = {
            'sector': stock_data.get('sector', 'N/A'),
            'industry': stock_data.get('industry', 'N/A'),
            'marketCap': stock_data.get('marketCap', None),
            'enterpriseValue': stock_data.get('enterpriseValue', None),
            'trailingPE': stock_data.get('trailingPE', None),
            'forwardPE': stock_data.get('forwardPE', None),
            'beta': stock_data.get('beta', None),
            'dividendYield': stock_data.get('dividendYield', None),
            '52WeekHigh': stock_data.get('fiftyTwoWeekHigh', None),
            '52WeekLow': stock_data.get('fiftyTwoWeekLow', None),
            'currentPrice': stock_data.get('currentPrice', None),
            'targetHighPrice': stock_data.get('targetHighPrice', None),
            'targetLowPrice': stock_data.get('targetLowPrice', None),
            'targetMeanPrice': stock_data.get('targetMeanPrice', None),
            'recommendationMean': stock_data.get('recommendationMean', None),
            'recommendationKey': stock_data.get('recommendationKey', None),
        }
        
        return JsonResponse({
            'success': True,
            'symbol': symbol,
            'stock_data': stock_data,
            'key_metrics': key_metrics,
            'historical_data': historical_data,
            'ratios': ratios_data,
            'news_html': news_html,
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
