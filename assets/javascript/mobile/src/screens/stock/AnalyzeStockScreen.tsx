import React, {useMemo, useRef, useState} from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  LayoutChangeEvent,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService, {StockDetailsResponse} from '../../services/api';

const ACTION_SECTIONS = [
  {key: 'detailed', label: 'Detailed Reports', icon: 'description'},
  {key: 'analysis', label: 'Analysis / Predictions', icon: 'analytics'},
  {key: 'market', label: 'Market Overview', icon: 'public'},
  {key: 'risk', label: 'Risk Dashboard', icon: 'shield'},
  {key: 'decision', label: 'Decision Support', icon: 'lightbulb-outline'},
  {key: 'planner', label: 'Planner Alerts', icon: 'notifications'},
];

type NormalizedRatio = {
  displayName: string;
  value?: number;
  performance?: string;
};

const normalizeRatios = (ratios?: Array<Record<string, any>>): NormalizedRatio[] => {
  if (!ratios || ratios.length === 0) {
    return [];
  }

  return ratios.map(ratio => {
    const normalized: Record<string, any> = {};
    Object.entries(ratio).forEach(([key, value]) => {
      const normalizedKey = key.replace(/\s+/g, '_').replace(/-+/g, '_').toLowerCase();
      normalized[normalizedKey] = value;
      normalized[key] = value;
    });

    const name =
      normalized['ratio_name'] ||
      normalized['ratio'] ||
      normalized['name'] ||
      normalized['ratio_name'] ||
      normalized['ratio name'] ||
      Object.values(ratio)[0];

    const value =
      normalized['ratio_value'] ??
      normalized['value'] ??
      normalized['ratio value'];

    return {
      displayName: typeof name === 'string' ? name : 'Metric',
      value: typeof value === 'number' ? value : Number(value) || undefined,
      performance: normalized['performance'] || normalized['perf'] || normalized['performance'],
    };
  });
};

const formatCurrency = (value?: number | null) => {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return '—';
  }
  try {
    return `$${Intl.NumberFormat('en-US', {notation: 'compact', maximumFractionDigits: 1}).format(Number(value))}`;
  } catch (error) {
    return `$${Number(value).toFixed(2)}`;
  }
};

const formatNumber = (value?: number | string | null) => {
  if (value === null || value === undefined) {
    return '—';
  }
  const num = typeof value === 'number' ? value : Number(value);
  if (isNaN(num)) {
    return String(value);
  }
  return Intl.NumberFormat('en-US', {maximumFractionDigits: 2}).format(num);
};

const getNewsItems = (details: StockDetailsResponse | null) => {
  if (!details) return [];
  const yahooNews = details.yahoo_finance?.news || [];
  if (yahooNews.length) return yahooNews;
  return [];
};

export default function AnalyzeStockScreen({navigation}: any) {
  const [symbol, setSymbol] = useState('');
  const [forecastDays, setForecastDays] = useState('365');
  const [equationType, setEquationType] = useState(
    'Geometric Brownian Motion External Macroeconomic Factors',
  );
  const [analyzing, setAnalyzing] = useState(false);
  const [fetchingDetails, setFetchingDetails] = useState(false);
  const [stockDetails, setStockDetails] = useState<StockDetailsResponse | null>(null);
  const [detailsError, setDetailsError] = useState<string | null>(null);

  const scrollRef = useRef<ScrollView>(null);
  const sectionPositions = useRef<Record<string, number>>({});

  const equationTypes = [
    'Geometric Brownian Motion',
    'Geometric Brownian Motion with Mean Reversion',
    'Geometric Brownian Motion External Macroeconomic Factors',
  ];

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      Alert.alert('Error', 'Please enter a stock symbol');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await apiService.analyzeStock(
        symbol.toUpperCase(),
        parseInt(forecastDays, 10),
        equationType,
      );

      if (response.error) {
        Alert.alert('Analysis Failed', response.error);
      } else if (response.data) {
        navigation.navigate('AnalysisResults', {analysisId: response.data.id || 1, data: response.data});
      }
    } catch (error: any) {
      Alert.alert('Analysis Failed', error.message || 'Failed to analyze stock');
    } finally {
      setAnalyzing(false);
    }
  };

  const handlePopulateInformation = async () => {
    if (!symbol.trim()) {
      Alert.alert('Error', 'Please enter a stock symbol');
      return;
    }

    setFetchingDetails(true);
    setDetailsError(null);
    try {
      const response = await apiService.getStockDetails(symbol.trim().toUpperCase());
      if (response.data) {
        setStockDetails(response.data);
      } else {
        setDetailsError(response.error || 'Unable to fetch stock information');
      }
    } catch (error: any) {
      setDetailsError(error.message || 'Unable to fetch stock information');
    } finally {
      setFetchingDetails(false);
    }
  };

  const scrollToSection = (key: string) => {
    const scrollView = scrollRef.current;
    const position = sectionPositions.current[key];
    if (scrollView && typeof position === 'number') {
      scrollView.scrollTo({y: Math.max(position - 80, 0), animated: true});
    }
  };

  const handleSectionLayout = (key: string, event: LayoutChangeEvent) => {
    sectionPositions.current[key] = event.nativeEvent.layout.y;
  };

  const normalizedRatios = useMemo(() => normalizeRatios(stockDetails?.ratios), [stockDetails]);
  const newsItems = useMemo(() => getNewsItems(stockDetails), [stockDetails]);
  const fundamentals = stockDetails?.stock_data || {};
  const keyMetrics = stockDetails?.key_metrics || {};
  const yahooFinance = stockDetails?.yahoo_finance || {};

  const summaryCards = useMemo(
    () => [
      {label: 'Current Price', value: formatCurrency(keyMetrics.currentPrice || fundamentals.currentPrice)},
      {label: 'Market Cap', value: formatCurrency(keyMetrics.marketCap || fundamentals.marketCap)},
      {label: 'Sector', value: (keyMetrics.sector || fundamentals.sector || '—') as string},
      {label: 'Industry', value: (keyMetrics.industry || fundamentals.industry || '—') as string},
      {label: 'Beta', value: formatNumber(keyMetrics.beta || fundamentals.beta)},
      {label: 'Dividend Yield', value: keyMetrics.dividendYield ? `${(keyMetrics.dividendYield * 100).toFixed(2)}%` : '—'},
      {
        label: '52W Range',
        value: `${formatCurrency(keyMetrics['52WeekLow'] || fundamentals['52WeekLow'])} – ${formatCurrency(
          keyMetrics['52WeekHigh'] || fundamentals['52WeekHigh'],
        )}`,
      },
    ],
    [keyMetrics, fundamentals],
  );

  const renderSummarySection = () => (
    <View
      style={styles.section}
      onLayout={event => handleSectionLayout('detailed', event)}
    >
      <Text style={styles.sectionTitle}>Detailed Snapshot</Text>
      <View style={styles.cardGrid}>
        {summaryCards.map(card => (
          <View key={card.label} style={styles.statCard}>
            <Text style={styles.statLabel}>{card.label}</Text>
            <Text style={styles.statValue}>{card.value}</Text>
          </View>
        ))}
      </View>
    </View>
  );

  const renderAnalysisSection = () => (
    <View
      style={styles.section}
      onLayout={event => handleSectionLayout('analysis', event)}
    >
      <Text style={styles.sectionTitle}>Analysis Highlights</Text>
      {normalizedRatios.length ? (
        normalizedRatios.slice(0, 6).map(ratio => (
          <View key={ratio.displayName} style={styles.listRow}>
            <View>
              <Text style={styles.listTitle}>{ratio.displayName}</Text>
              <Text style={styles.listSubtitle}>{ratio.performance || '—'}</Text>
            </View>
            <Text style={styles.listValue}>{ratio.value ? ratio.value.toFixed(3) : '—'}</Text>
          </View>
        ))
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No ratio data available</Text>
        </View>
      )}
    </View>
  );

  const renderMarketSection = () => (
    <View
      style={styles.section}
      onLayout={event => handleSectionLayout('market', event)}
    >
      <Text style={styles.sectionTitle}>Market Overview</Text>
      <View style={styles.listRow}>
        <View>
          <Text style={styles.listTitle}>Trailing P/E</Text>
          <Text style={styles.listSubtitle}>Relative valuation</Text>
        </View>
        <Text style={styles.listValue}>{formatNumber(keyMetrics.trailingPE || fundamentals.trailingPE)}</Text>
      </View>
      <View style={styles.listRow}>
        <View>
          <Text style={styles.listTitle}>Forward P/E</Text>
          <Text style={styles.listSubtitle}>Next 12 months</Text>
        </View>
        <Text style={styles.listValue}>{formatNumber(keyMetrics.forwardPE || fundamentals.forwardPE)}</Text>
      </View>
      <View style={styles.listRow}>
        <View>
          <Text style={styles.listTitle}>Free Cash Flow</Text>
          <Text style={styles.listSubtitle}>Liquidity runway</Text>
        </View>
        <Text style={styles.listValue}>{formatCurrency(fundamentals.freeCashflow)}</Text>
      </View>
    </View>
  );

  const renderRiskSection = () => (
    <View
      style={styles.section}
      onLayout={event => handleSectionLayout('risk', event)}
    >
      <Text style={styles.sectionTitle}>Risk Dashboard</Text>
      <View style={styles.listRow}>
        <View>
          <Text style={styles.listTitle}>Beta</Text>
          <Text style={styles.listSubtitle}>Volatility vs market</Text>
        </View>
        <Text style={styles.listValue}>{formatNumber(keyMetrics.beta || fundamentals.beta)}</Text>
      </View>
      <View style={styles.listRow}>
        <View>
          <Text style={styles.listTitle}>Debt / Equity</Text>
          <Text style={styles.listSubtitle}>Balance sheet leverage</Text>
        </View>
        <Text style={styles.listValue}>{formatNumber(fundamentals.debtToEquity)}</Text>
      </View>
      <View style={styles.listRow}>
        <View>
          <Text style={styles.listTitle}>Operating Margin</Text>
          <Text style={styles.listSubtitle}>Cost efficiency</Text>
        </View>
        <Text style={styles.listValue}>
          {fundamentals.operatingMargins ? `${(fundamentals.operatingMargins * 100).toFixed(2)}%` : '—'}
        </Text>
      </View>
    </View>
  );

  const renderDecisionSection = () => (
    <View
      style={styles.section}
      onLayout={event => handleSectionLayout('decision', event)}
    >
      <Text style={styles.sectionTitle}>Decision Support</Text>
      {newsItems.length ? (
        newsItems.slice(0, 5).map((item, index) => (
          <TouchableOpacity
            key={item.url || `${item.title}-${index}`}
            style={styles.newsCard}
            onPress={() => item.url && Linking.openURL(item.url)}
          >
            <Text style={styles.newsTitle}>{item.title}</Text>
            <Text style={styles.newsMeta}>{item.publisher || item.source || '—'}</Text>
            <Text style={styles.newsLink}>Read article →</Text>
          </TouchableOpacity>
        ))
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No recent news</Text>
        </View>
      )}
    </View>
  );

  const renderPlannerSection = () => (
    <View
      style={styles.section}
      onLayout={event => handleSectionLayout('planner', event)}
    >
      <Text style={styles.sectionTitle}>Investment Planner Signals</Text>
      <View style={styles.listRow}>
        <View>
          <Text style={styles.listTitle}>Options Data</Text>
          <Text style={styles.listSubtitle}>Open interest & expirations</Text>
        </View>
        <Text style={styles.listValue}>
          {yahooFinance.options ? Object.keys(yahooFinance.options).length : 'N/A'}
        </Text>
      </View>
      <View style={styles.listRow}>
        <View>
          <Text style={styles.listTitle}>Holders Records</Text>
          <Text style={styles.listSubtitle}>Institutional ownership snapshots</Text>
        </View>
        <Text style={styles.listValue}>
          {yahooFinance.holders ? Object.keys(yahooFinance.holders).length : 'N/A'}
        </Text>
      </View>
    </View>
  );

  const renderDetailsSections = () => (
    <>
      {renderSummarySection()}
      {renderAnalysisSection()}
      {renderMarketSection()}
      {renderRiskSection()}
      {renderDecisionSection()}
      {renderPlannerSection()}
    </>
  );

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      keyboardShouldPersistTaps="handled"
      ref={scrollRef}
    >
      <View style={styles.content}>
        <Text style={styles.title}>Stocks Assessment</Text>
        <Text style={styles.subtitle}>Populate the latest data and run desktop-grade analysis on-the-go.</Text>

        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.primaryButton, fetchingDetails && styles.buttonDisabled]}
            onPress={handlePopulateInformation}
            disabled={fetchingDetails}
          >
            {fetchingDetails ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Icon name="download" size={18} color="#fff" style={styles.buttonIcon} />
                <Text style={styles.primaryButtonText}>Populate Information</Text>
              </>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.secondaryButton, analyzing && styles.buttonDisabled]}
            onPress={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? (
              <ActivityIndicator color="#0A84FF" />
            ) : (
              <Text style={styles.secondaryButtonText}>Analyze Stock</Text>
            )}
          </TouchableOpacity>
        </View>

        <View style={styles.form}>
          <Text style={styles.label}>Stock Symbol</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., AAPL, NVDA, MSFT"
            value={symbol}
            onChangeText={setSymbol}
            autoCapitalize="characters"
            editable={!analyzing && !fetchingDetails}
          />

          <Text style={styles.label}>Forecast Days (1-1825)</Text>
          <TextInput
            style={styles.input}
            placeholder="365"
            value={forecastDays}
            onChangeText={setForecastDays}
            keyboardType="number-pad"
            editable={!analyzing}
          />

          <Text style={styles.label}>Analysis Model</Text>
          <View style={styles.pickerContainer}>
            {equationTypes.map(type => (
              <TouchableOpacity
                key={type}
                style={[styles.pickerOption, equationType === type && styles.pickerOptionSelected]}
                onPress={() => setEquationType(type)}
                disabled={analyzing}
              >
                <Text
                  style={[styles.pickerOptionText, equationType === type && styles.pickerOptionTextSelected]}
                >
                  {type}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {detailsError ? (
          <View style={styles.errorCard}>
            <Icon name="error-outline" size={20} color="#B00020" />
            <Text style={styles.errorText}>{detailsError}</Text>
          </View>
        ) : null}

        {stockDetails ? (
          <>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.actionChips}>
              {ACTION_SECTIONS.map(action => (
                <TouchableOpacity
                  key={action.key}
                  style={styles.actionChip}
                  onPress={() => scrollToSection(action.key)}
                >
                  <Icon name={action.icon} size={18} color="#0A84FF" />
                  <Text style={styles.actionChipText}>{action.label}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            {renderDetailsSections()}
          </>
        ) : (
          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>What you'll unlock:</Text>
            <Text style={styles.infoText}>• Latest price, market cap and ratio snapshots</Text>
            <Text style={styles.infoText}>• Cross-provider validation (Polygon, Alpha, Yahoo)</Text>
            <Text style={styles.infoText}>• News, options activity and holders context</Text>
            <Text style={styles.infoText}>• One tap navigation to desktop-caliber workflows</Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    paddingBottom: 24,
  },
  content: {
    padding: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111',
  },
  subtitle: {
    fontSize: 15,
    color: '#555',
    marginTop: 4,
    marginBottom: 16,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  primaryButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0A84FF',
    paddingVertical: 14,
    borderRadius: 12,
    marginRight: 12,
  },
  secondaryButton: {
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#0A84FF',
  },
  buttonIcon: {
    marginRight: 8,
  },
  primaryButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  secondaryButtonText: {
    color: '#0A84FF',
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  form: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  pickerContainer: {
    marginTop: 8,
  },
  pickerOption: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  pickerOptionSelected: {
    borderColor: '#0A84FF',
    backgroundColor: '#E9F3FF',
  },
  pickerOptionText: {
    color: '#333',
  },
  pickerOptionTextSelected: {
    color: '#0A84FF',
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  infoText: {
    color: '#555',
    marginBottom: 4,
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FCE8E6',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
  },
  errorText: {
    color: '#B00020',
    marginLeft: 8,
    flex: 1,
  },
  actionChips: {
    marginTop: 8,
    marginBottom: 12,
  },
  actionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#0A84FF',
  },
  actionChipText: {
    color: '#0A84FF',
    marginLeft: 6,
    fontWeight: '600',
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    color: '#111',
  },
  cardGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
  },
  statCard: {
    width: '50%',
    paddingHorizontal: 6,
    marginBottom: 12,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
  },
  listRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  listTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#222',
  },
  listSubtitle: {
    fontSize: 12,
    color: '#666',
  },
  listValue: {
    fontSize: 15,
    fontWeight: '600',
    color: '#0A84FF',
  },
  newsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  newsTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
    marginBottom: 4,
  },
  newsMeta: {
    color: '#666',
    marginBottom: 6,
  },
  newsLink: {
    color: '#0A84FF',
    fontWeight: '600',
  },
  emptyCard: {
    backgroundColor: '#fff',
    padding: 18,
    borderRadius: 12,
  },
  emptyText: {
    color: '#666',
    textAlign: 'center',
  },
});
