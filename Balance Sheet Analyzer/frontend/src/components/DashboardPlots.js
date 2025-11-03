import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const DashboardPlots = () => {
  const [plotData, setPlotData] = useState({
    assetsLiabilities: null,
    profitability: null,
    expenses: null,
    cashFlow: null,
    margins: null,
    leverage: null
  });
  const [loading, setLoading] = useState({
    assetsLiabilities: true,
    profitability: true,
    expenses: true,
    cashFlow: true,
    margins: true,
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
    margins: ['#8884D8', '#82CA9D', '#FF8042', '#0088FE', '#FF6B6B'],
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
      const plotNames = ['01_plot_AandL', '02_plot_revPL', '03_plot_expenses', '04_plot_cashflow', '05_plot_margins', '06_plot_leverage'];
      
      const promises = plotNames.map(async (plotName) => {
        const data = await fetchPlotData(plotName);
        return { plotName, data };
      });

      const results = await Promise.all(promises);
      
      const newPlotData = {};
      const newLoading = { ...loading };
      
      results.forEach(({ plotName, data }) => {
        // Map the file names to our internal state keys
        let stateKey;
        switch(plotName) {
          case '01_plot_AandL':
            stateKey = 'assetsLiabilities';
            break;
          case '02_plot_revPL':
            stateKey = 'profitability';
            break;
          case '03_plot_expenses':
            stateKey = 'expenses';
            break;
          case '04_plot_cashflow':
            stateKey = 'cashFlow';
            break;
          case '05_plot_margins':
            stateKey = 'margins';
            break;
          case '06_plot_leverage':
            stateKey = 'leverage';
            break;
          default:
            stateKey = plotName;
        }
        newPlotData[stateKey] = data;
        newLoading[stateKey] = false;
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
      case '01_plot_AandL':
        return timePeriods.map(period => ({
          period,
          'Total Current Assets': Math.floor(Math.random() * 5000) + 1000,
          'Total Non-Current Assets': Math.floor(Math.random() * 8000) + 2000,
          'Total Current Liabilities': Math.floor(Math.random() * 3000) + 500,
          'Total Non-Current Liabilities': Math.floor(Math.random() * 4000) + 1000
        }));

      case '02_plot_revPL':
        return timePeriods.map(period => ({
          period,
          'Total Revenue': Math.floor(Math.random() * 15000) + 5000,
          'Profit/Loss before Tax': Math.floor(Math.random() * 3000) - 500, // Can be negative
          'Profit/Loss for the period': Math.floor(Math.random() * 2500) - 300 // Can be negative
        }));

      case '03_plot_expenses':
        // Dynamic expenses based on actual CSV structure
        const expenseCategories = ['Employee Benefits', 'Depreciation', 'Finance Costs', 'Other Expenses', 'Total Tax Expenses', 'Exceptional Items'];
        return timePeriods.map(period => {
          const expenses = {};
          expenseCategories.forEach(category => {
            expenses[category] = Math.floor(Math.random() * 2000) + 500;
          });
          return { period, ...expenses };
        });

      case '04_plot_cashflow':
        // Dynamic cash flow categories based on filtered CSV
        const cashFlowCategories = ['Cash Flow from Operating Activities', 'Cash Flow from Investing Activities', 'Cash Flow from Financing Activities', 'Net Increase in Cash and Cash Equivalents'];
        return timePeriods.map(period => {
          const cashFlows = {};
          cashFlowCategories.forEach(category => {
            cashFlows[category] = Math.floor(Math.random() * 4000) - 1000; // Can be negative
          });
          return { period, ...cashFlows };
        });

      case '05_plot_margins':
        return timePeriods.map(period => ({
          period,
          'PBDIT Margin (%)': (Math.random() * 40 + 10).toFixed(2), // 10% to 50%
          'PBT Margin (%)': (Math.random() * 30 + 5).toFixed(2), // 5% to 35%
          'Net Profit Margin (%)': (Math.random() * 25 + 2).toFixed(2), // 2% to 27%
          'Return on Capital Employed (%)': (Math.random() * 25 + 5).toFixed(2), // 5% to 30%
          'Return on Assets (%)': (Math.random() * 20 + 5).toFixed(2) // 5% to 25%
        }));

      case '06_plot_leverage':
        return timePeriods.map(period => ({
          period,
          'Current Ratio (X)': (Math.random() * 2 + 0.5).toFixed(2), // 0.5 to 2.5
          'Quick Ratio (X)': (Math.random() * 1.5 + 0.3).toFixed(2), // 0.3 to 1.8
          'Total Debt/Equity (X)': (Math.random() * 2 + 0.1).toFixed(2) // 0.1 to 2.1
        }));

      default:
        return [];
    }
  };

  // Dynamic key extractors for flexible data handling
  const getDynamicKeys = (data, excludeKeys = ['period']) => {
    if (!data || data.length === 0) return [];
    const sample = data[0];
    return Object.keys(sample).filter(key => !excludeKeys.includes(key));
  };

  // Format currency values in tooltips
  const formatCurrency = (value) => {
    if (typeof value !== 'number') return value;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format percentage values in tooltips
  const formatPercentage = (value) => {
    if (typeof value !== 'number') return value;
    return `${value}%`;
  };

  // Render individual plots with loading states
  const renderPlot = (plotKey, title, chartComponent, height = 500) => {
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
    const data = plotData.assetsLiabilities || [];
    
    return (
      <ResponsiveContainer width="100%" height={500}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={formatCurrency} />
          <Legend />
          <Bar dataKey="Total Current Assets" stackId="assets" fill={colorPalette.assets[0]} name="Current Assets" />
          <Bar dataKey="Total Non-Current Assets" stackId="assets" fill={colorPalette.assets[1]} name="Non-Current Assets" />
          <Bar dataKey="Total Current Liabilities" stackId="liabilities" fill={colorPalette.assets[2]} name="Current Liabilities" />
          <Bar dataKey="Total Non-Current Liabilities" stackId="liabilities" fill={colorPalette.assets[3]} name="Non-Current Liabilities" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  // Plot 2: Trend line chart for profitability
  const renderProfitabilityChart = () => {
    const data = plotData.profitability || [];
    
    return (
      <ResponsiveContainer width="100%" height={500}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={formatCurrency} />
          <Legend />
          <Line type="monotone" dataKey="Total Revenue" stroke={colorPalette.profitability[0]} strokeWidth={2} name="Total Revenue" />
          <Line type="monotone" dataKey="Profit/Loss before Tax" stroke={colorPalette.profitability[1]} strokeWidth={2} name="Profit before Tax" />
          <Line type="monotone" dataKey="Profit/Loss for the period" stroke={colorPalette.profitability[2]} strokeWidth={2} name="Net Profit/Loss" />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  // Plot 3: Stacked area chart of expenses (dynamic)
  const renderExpensesChart = () => {
    const data = plotData.expenses || [];
    const expenseKeys = getDynamicKeys(data, ['period']);
    
    return (
      <ResponsiveContainer width="100%" height={500}>
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={formatCurrency} />
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
    const data = plotData.cashFlow || [];
    const cashFlowKeys = getDynamicKeys(data, ['period']);
    
    return (
      <ResponsiveContainer width="100%" height={500}>
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={formatCurrency} />
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

  // Plot 5: Trend line of margin ratios
  const renderMarginsChart = () => {
    const data = plotData.margins || [];
    
    return (
      <ResponsiveContainer width="100%" height={500}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={formatPercentage} />
          <Legend />
          <Line type="monotone" dataKey="PBDIT Margin (%)" stroke={colorPalette.margins[0]} strokeWidth={2} name="EBDIT Margin" />
          <Line type="monotone" dataKey="PBT Margin (%)" stroke={colorPalette.margins[1]} strokeWidth={2} name="EBT Margin" />
          <Line type="monotone" dataKey="Net Profit Margin (%)" stroke={colorPalette.margins[2]} strokeWidth={2} name="Net Profit Margin" />
          <Line type="monotone" dataKey="Return on Capital Employed (%)" stroke={colorPalette.margins[3]} strokeWidth={2} name="ROCE" />
          <Line type="monotone" dataKey="Return on Assets (%)" stroke={colorPalette.margins[4]} strokeWidth={2} name="ROA" />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  // Plot 6: Trend line of leverage metrics
  const renderLeverageChart = () => {
    const data = plotData.leverage || [];
    
    return (
      <ResponsiveContainer width="100%" height={500}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="Current Ratio (X)" stroke={colorPalette.leverage[0]} strokeWidth={2} name="Current Ratio" />
          <Line type="monotone" dataKey="Quick Ratio (X)" stroke={colorPalette.leverage[1]} strokeWidth={2} name="Quick Ratio" />
          <Line type="monotone" dataKey="Total Debt/Equity (X)" stroke={colorPalette.leverage[2]} strokeWidth={2} name="Debt/Equity" />
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
          'assetsLiabilities',
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
          'cashFlow',
          'Cash Flow Analysis',
          renderCashFlowChart()
        )}
        
        {renderPlot(
          'margins',
          'Margin & Return Ratios',
          renderMarginsChart()
        )}
        
        {renderPlot(
          'leverage',
          'Leverage & Liquidity Ratios',
          renderLeverageChart()
        )}
      </div>
    </div>
  );
};

export default DashboardPlots;