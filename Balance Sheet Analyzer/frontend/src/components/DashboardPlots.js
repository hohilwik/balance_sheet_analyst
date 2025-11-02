import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarStack
} from 'recharts';

const DashboardPlots = () => {
  const [plotData, setPlotData] = useState({
    assetsLiabilities: null,
    profitability: null,
    expenses: null,
    cashFlow: null,
    ratios: null,
    leverage: null
  });
  const [loading, setLoading] = useState({
    assetsLiabilities: true,
    profitability: true,
    expenses: true,
    cashFlow: true,
    ratios: true,
    leverage: true
  });
  const [errors, setErrors] = useState({});

  // Color palettes for consistent styling
  const colorPalette = {
    primary: ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'],
    assets: ['#4CAF50', '#8BC34A', '#FF9800', '#F44336'],
    profitability: ['#2196F3', '#4CAF50', '#FF5722'],
    expenses: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'],
    cashFlow: ['#00C49F', '#0088FE', '#FFBB28', '#FF8042'],
    ratios: ['#8884D8', '#82CA9D', '#FF8042', '#0088FE'],
    leverage: ['#FF6B6B', '#4ECDC4', '#45B7D1']
  };

  useEffect(() => {
    fetchAllPlotData();
  }, []);

  const fetchPlotData = async (plotName) => {
    try {
      const response = await axios.get(`http://localhost:5000/api/user/plot/${plotName}`);
      
      if (response.data && Array.isArray(response.data.data)) {
        return response.data.data;
      } else {
        throw new Error('Invalid data format');
      }
    } catch (error) {
      console.warn(`Failed to fetch ${plotName} data, using dummy data:`, error);
      setErrors(prev => ({ ...prev, [plotName]: 'Using sample data' }));
      return generateDummyData(plotName);
    }
  };

  const fetchAllPlotData = async () => {
    try {
      const plotNames = ['assets_liabilities', 'profitability', 'expenses', 'cash_flow', 'ratios', 'leverage'];
      
      const promises = plotNames.map(async (plotName) => {
        const data = await fetchPlotData(plotName);
        return { plotName, data };
      });

      const results = await Promise.all(promises);
      
      const newPlotData = {};
      const newLoading = { ...loading };
      
      results.forEach(({ plotName, data }) => {
        newPlotData[plotName] = data;
        newLoading[plotName] = false;
      });
      
      setPlotData(newPlotData);
      setLoading(newLoading);
    } catch (error) {
      console.error('Error fetching plot data:', error);
    }
  };

  // Generate comprehensive dummy data for each plot type
  const generateDummyData = (plotType) => {
    const timePeriods = ['2020', '2021', '2022', '2023', '2024'];
    
    switch (plotType) {
      case 'assets_liabilities':
        return timePeriods.map(period => ({
          period,
          currentAssets: Math.floor(Math.random() * 5000) + 1000,
          nonCurrentAssets: Math.floor(Math.random() * 8000) + 2000,
          shortTermLiabilities: Math.floor(Math.random() * 3000) + 500,
          longTermLiabilities: Math.floor(Math.random() * 4000) + 1000,
          totalAssets: function() { return this.currentAssets + this.nonCurrentAssets; },
          totalLiabilities: function() { return this.shortTermLiabilities + this.longTermLiabilities; }
        }));

      case 'profitability':
        return timePeriods.map(period => ({
          period,
          totalRevenue: Math.floor(Math.random() * 15000) + 5000,
          grossProfit: Math.floor(Math.random() * 8000) + 2000,
          netProfit: Math.floor(Math.random() * 3000) + 500,
          operatingProfit: Math.floor(Math.random() * 5000) + 1000
        }));

      case 'expenses':
        const expenseCategories = ['Salaries', 'Marketing', 'R&D', 'Operations', 'Administration', 'Taxes'];
        return timePeriods.map(period => {
          const expenses = {};
          let total = 0;
          expenseCategories.forEach(category => {
            expenses[category] = Math.floor(Math.random() * 2000) + 500;
            total += expenses[category];
          });
          return { period, ...expenses, total };
        });

      case 'cash_flow':
        const cashFlowCategories = ['Operating', 'Investing', 'Financing', 'Free Cash Flow'];
        return timePeriods.map(period => {
          const cashFlows = {};
          cashFlowCategories.forEach(category => {
            cashFlows[category] = Math.floor(Math.random() * 4000) - 1000; // Can be negative
          });
          return { period, ...cashFlows };
        });

      case 'ratios':
        return timePeriods.map(period => ({
          period,
          pbditMargin: (Math.random() * 0.4 + 0.1).toFixed(3), // 10% to 50%
          pbtMargin: (Math.random() * 0.3 + 0.05).toFixed(3), // 5% to 35%
          netMargin: (Math.random() * 0.25 + 0.02).toFixed(3), // 2% to 27%
          returnOnAssets: (Math.random() * 0.2 + 0.05).toFixed(3) // 5% to 25%
        }));

      case 'leverage':
        return timePeriods.map(period => ({
          period,
          currentRatio: (Math.random() * 2 + 0.5).toFixed(2), // 0.5 to 2.5
          quickRatio: (Math.random() * 1.5 + 0.3).toFixed(2), // 0.3 to 1.8
          debtToEquity: (Math.random() * 2 + 0.1).toFixed(2) // 0.1 to 2.1
        }));

      default:
        return [];
    }
  };

  // Dynamic key extractors for flexible data handling
  const getDynamicKeys = (data, excludeKeys = ['period', 'total']) => {
    if (!data || data.length === 0) return [];
    const sample = data[0];
    return Object.keys(sample).filter(key => !excludeKeys.includes(key));
  };

  // Render individual plots with loading states
  const renderPlot = (plotKey, title, chartComponent, height = 300) => {
    const data = plotData[plotKey];
    const isLoading = loading[plotKey];
    const hasError = errors[plotKey];

    if (isLoading) {
      return (
        <div className="plot-card">
          <h3>{title}</h3>
          <div className="plot-loading">
            <div className="loading-spinner"></div>
            <p>Loading {title} data...</p>
          </div>
        </div>
      );
    }

    return (
      <div className="plot-card">
        <div className="plot-header">
          <h3>{title}</h3>
          {hasError && <span className="data-warning">Sample Data</span>}
        </div>
        {chartComponent}
      </div>
    );
  };

  // Plot 1: Stacked bar chart for assets and liabilities
  const renderAssetsLiabilitiesChart = () => {
    const data = plotData.assets_liabilities || [];
    const keys = ['currentAssets', 'nonCurrentAssets', 'shortTermLiabilities', 'longTermLiabilities'];
    
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={(value) => new Intl.NumberFormat('en-US').format(value)} />
          <Legend />
          <Bar dataKey="currentAssets" stackId="assets" fill={colorPalette.assets[0]} name="Current Assets" />
          <Bar dataKey="nonCurrentAssets" stackId="assets" fill={colorPalette.assets[1]} name="Non-Current Assets" />
          <Bar dataKey="shortTermLiabilities" stackId="liabilities" fill={colorPalette.assets[2]} name="Short Term Liabilities" />
          <Bar dataKey="longTermLiabilities" stackId="liabilities" fill={colorPalette.assets[3]} name="Long Term Liabilities" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  // Plot 2: Trend line chart for profitability
  const renderProfitabilityChart = () => {
    const data = plotData.profitability || [];
    
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={(value) => new Intl.NumberFormat('en-US').format(value)} />
          <Legend />
          <Line type="monotone" dataKey="totalRevenue" stroke={colorPalette.profitability[0]} strokeWidth={2} name="Total Revenue" />
          <Line type="monotone" dataKey="grossProfit" stroke={colorPalette.profitability[1]} strokeWidth={2} name="Gross Profit" />
          <Line type="monotone" dataKey="netProfit" stroke={colorPalette.profitability[2]} strokeWidth={2} name="Net Profit" />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  // Plot 3: Stacked area chart of expenses (dynamic)
  const renderExpensesChart = () => {
    const data = plotData.expenses || [];
    const expenseKeys = getDynamicKeys(data, ['period', 'total']);
    
    return (
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={(value) => new Intl.NumberFormat('en-US').format(value)} />
          <Legend />
          {expenseKeys.map((key, index) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stackId="1"
              stroke={colorPalette.expenses[index % colorPalette.expenses.length]}
              fill={colorPalette.expenses[index % colorPalette.expenses.length]}
              name={key}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  // Plot 4: Stacked area chart of cash flow (dynamic)
  const renderCashFlowChart = () => {
    const data = plotData.cash_flow || [];
    const cashFlowKeys = getDynamicKeys(data, ['period']);
    
    return (
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={(value) => new Intl.NumberFormat('en-US').format(value)} />
          <Legend />
          {cashFlowKeys.map((key, index) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stackId="1"
              stroke={colorPalette.cashFlow[index % colorPalette.cashFlow.length]}
              fill={colorPalette.cashFlow[index % colorPalette.cashFlow.length]}
              name={key}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  // Plot 5: Trend line of fundamental ratios
  const renderRatiosChart = () => {
    const data = plotData.ratios || [];
    
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={(value) => `${(value * 100).toFixed(1)}%`} />
          <Legend />
          <Line type="monotone" dataKey="pbditMargin" stroke={colorPalette.ratios[0]} strokeWidth={2} name="PBDIT Margin" />
          <Line type="monotone" dataKey="pbtMargin" stroke={colorPalette.ratios[1]} strokeWidth={2} name="PBT Margin" />
          <Line type="monotone" dataKey="netMargin" stroke={colorPalette.ratios[2]} strokeWidth={2} name="Net Margin" />
          <Line type="monotone" dataKey="returnOnAssets" stroke={colorPalette.ratios[3]} strokeWidth={2} name="Return on Assets" />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  // Plot 6: Trend line of leverage metrics
  const renderLeverageChart = () => {
    const data = plotData.leverage || [];
    
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="currentRatio" stroke={colorPalette.leverage[0]} strokeWidth={2} name="Current Ratio" />
          <Line type="monotone" dataKey="quickRatio" stroke={colorPalette.leverage[1]} strokeWidth={2} name="Quick Ratio" />
          <Line type="monotone" dataKey="debtToEquity" stroke={colorPalette.leverage[2]} strokeWidth={2} name="Debt/Equity" />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="dashboard-plots">
      <div className="plots-header">
        <h2>Financial Analytics Dashboard</h2>
        <button onClick={fetchAllPlotData} className="refresh-plots-btn">
          Refresh Data
        </button>
      </div>
      
      <div className="plots-grid">
        {renderPlot(
          'assets_liabilities',
          'Assets & Liabilities Overview',
          renderAssetsLiabilitiesChart()
        )}
        
        {renderPlot(
          'profitability',
          'Profitability Trends',
          renderProfitabilityChart()
        )}
        
        {renderPlot(
          'expenses',
          'Expense Breakdown',
          renderExpensesChart()
        )}
        
        {renderPlot(
          'cash_flow',
          'Cash Flow Analysis',
          renderCashFlowChart()
        )}
        
        {renderPlot(
          'ratios',
          'Financial Ratios',
          renderRatiosChart()
        )}
        
        {renderPlot(
          'leverage',
          'Leverage Metrics',
          renderLeverageChart()
        )}
      </div>
    </div>
  );
};

export default DashboardPlots;