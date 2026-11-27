import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly
import plotly.express as px
import plotly.graph_objects as go

# GreenSupply Business Performance Dashboard

# PAGE CONFIGURATION
st.set_page_config(
    page_title="GreenSupply Business Performance Dashboard",
    page_icon="🌱",
    layout="wide"
)

# CUSTOM CSS
st.markdown("""
<style>
    .main {
        background-color: #FFFFFF;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .dashboard-title {
        font-size: 30px;
        font-weight: 700;
        color: #1729A5;
        text-align: center;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 650;
        color: #1729A5;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .kpi-card {
        background-color: #F5F7FC;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #E1E6F0;
        text-align: center;
    }

    .kpi-label {
        font-size: 14px;
        color: #555555;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 25px;
        font-weight: 700;
        color: #1729A5;
    }
</style>
""", unsafe_allow_html=True)

# DASHBOARD HEADING
st.markdown(
    '<div class="dashboard-title">'
    'GreenSupply Business Performance Dashboard'
    '</div>',
    unsafe_allow_html=True
)





# LOAD DATASETS
project_folder = os.path.dirname(os.path.abspath(__file__))
data_folder = project_folder

orders = pd.read_csv(
    os.path.join(data_folder, "BA-Cleaned Data set(Cleaned Orders).csv"),
    encoding="cp1252"
)

inventory = pd.read_csv(
    os.path.join(data_folder, "BA-Cleaned Data set(Cleaned_WH_Monthly_Inventory).csv"),
    encoding="cp1252"
)

kpis = pd.read_csv(
    os.path.join(data_folder, "BA-Cleaned Data set(KPI Calculations).csv"),
    encoding="cp1252"
)


# CLEAN DATA
orders.columns = orders.columns.str.strip()
inventory.columns = inventory.columns.str.strip()
kpis.columns = kpis.columns.str.strip()

# Convert financial columns
financial_columns = [
    'Unit Price (€)', 'Revenue (€)', 'Unit Cost (€)', 'COGS (€)',
    'Holding Cost (€)', 'Shipping Cost (€)', 'Profit Adjusted (€)',
    'Value of Returns'
]

for col in financial_columns:
    orders[col] = pd.to_numeric(
        orders[col].astype(str)
        .str.replace('€', '', regex=False)
        .str.replace(',', '', regex=False)
        .str.strip(),
        errors='coerce'
    )

# Convert date columns
date_columns = [
    'Order Date', 'Shipment Date',
    'Promised Delivery Date', 'Actual Delivery Date'
]

for col in date_columns:
    orders[col] = pd.to_datetime(
        orders[col], format='%m/%d/%Y', errors='coerce'
    )

inventory['YearMonth'] = pd.to_datetime(
    inventory['YearMonth'], format='%m/%d/%Y', errors='coerce'
)

# Convert numeric columns
numeric_columns = [
    'Sales Quantity', 'Returned Quantity', 'Shipping Delay',
    'Delivery variance', 'On Time Delivery', 'Year',
    'Monthly Sales Qty'
]

for col in numeric_columns:
    orders[col] = pd.to_numeric(orders[col], errors='coerce')



# SIDEBAR FILTERS
with st.sidebar:
    st.title("Dashboard Filters")

    st.subheader("Year")
    selected_years = st.multiselect(
        "Select Year",
        options=sorted(orders['Year'].dropna().unique()),
        default=sorted(orders['Year'].dropna().unique())
    )

    st.subheader("Product Category")
    selected_categories = st.multiselect(
        "Select Product Category",
        options=sorted(orders['Product Category'].dropna().unique()),
        default=sorted(orders['Product Category'].dropna().unique())
    )

    st.subheader("Warehouse")
    selected_warehouses = st.multiselect(
        "Select Warehouse",
        options=sorted(orders['Warehouse'].dropna().unique()),
        default=sorted(orders['Warehouse'].dropna().unique())
    )


# APPLY FILTERS
filtered_orders = orders[
    orders['Year'].isin(selected_years)
    & orders['Product Category'].isin(selected_categories)
    & orders['Warehouse'].isin(selected_warehouses)
].copy()


# KPI CALCULATIONS
def calculate_kpis(df):

    total_revenue = df['Revenue (€)'].sum()
    total_profit = df['Profit Adjusted (€)'].sum()
    total_cogs = df['COGS (€)'].sum()

    total_sales = df['Sales Quantity'].sum()
    total_returns = df['Returned Quantity'].sum()

    profit_margin = total_profit / total_revenue * 100 if total_revenue else 0
    return_rate = total_returns / total_sales * 100 if total_sales else 0
    on_time_delivery = df['On Time Delivery'].mean() * 100
    cogs_percentage = total_cogs / total_revenue * 100 if total_revenue else 0

    return {
        "Total Sales Revenue": total_revenue,
        "Net Profit": total_profit,
        "Overall Profit Margin": profit_margin,
        "Product Return Rate": return_rate,
        "On-Time Delivery": on_time_delivery,
        "COGS % of Revenue": cogs_percentage
    }


# DISPLAY SIX KPI CARDS
kpis_values = calculate_kpis(filtered_orders)

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

kpi_cards = [
    (kpi1, "Total Sales Revenue", f"€{kpis_values['Total Sales Revenue']:,.2f}"),
    (kpi2, "Net Profit", f"€{kpis_values['Net Profit']:,.2f}"),
    (kpi3, "Overall Profit Margin", f"{kpis_values['Overall Profit Margin']:.2f}%"),
    (kpi4, "Product Return Rate", f"{kpis_values['Product Return Rate']:.2f}%"),
    (kpi5, "On-Time Delivery", f"{kpis_values['On-Time Delivery']:.2f}%"),
    (kpi6, "COGS % of Revenue", f"{kpis_values['COGS % of Revenue']:.2f}%")
]

for column, label, value in kpi_cards:
    with column:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# RETURN RATE BY WAREHOUSE
warehouse_returns = (
    filtered_orders.groupby('Warehouse')
    .agg({
        'Sales Quantity': 'sum',
        'Returned Quantity': 'sum'
    })
    .reset_index()
)

warehouse_returns['Return Rate'] = (
    warehouse_returns['Returned Quantity']
    / warehouse_returns['Sales Quantity'] * 100
)

warehouse_returns = warehouse_returns.sort_values(
    'Return Rate', ascending=False
)

fig1 = px.bar(
    warehouse_returns,
    x='Warehouse',
    y='Return Rate',
    text=warehouse_returns['Return Rate'].map(lambda x: f'{x:.2f}%'),
    color_discrete_sequence=['#1729A5'],
    title='Return Rate<br><sup>by Warehouse</sup>'
)

fig1.update_traces(textposition='outside')

fig1.update_layout(
    yaxis=dict(
        title='Return Rate',
        ticksuffix='%',
        range=[0, 7]
    ),
    xaxis_title='Warehouse',
    showlegend=False,
    height=400
)

st.plotly_chart(fig1, use_container_width=True)


# GRAPH 2: ITEM RETURN REASONS
return_reasons = (
    filtered_orders[filtered_orders['Returned Quantity'] > 0]
    .groupby('Return Reason')['Returned Quantity']
    .sum()
    .reset_index()
)

return_reasons = return_reasons.sort_values(
    'Returned Quantity', ascending=False
)

total_returns = return_reasons['Returned Quantity'].sum()

fig2 = px.pie(
    return_reasons,
    names='Return Reason',
    values='Returned Quantity',
    hole=0.55,
    title='Item Return Reasons'
)

fig2.update_traces(
    textinfo='percent',
    hovertemplate='%{label}<br>Returned Quantity: %{value}<br>Share: %{percent}<extra></extra>'
)

fig2.add_annotation(
    text=f'{total_returns:,.0f}<br>Returns',
    x=0.5,
    y=0.5,
    showarrow=False,
    font=dict(size=18, color='#1729A5')
)

fig2.update_layout(height=450)

st.plotly_chart(fig2, use_container_width=True)


# GRAPH 3: COGS SHARE AND PROFIT MARGINS BY PRODUCT CATEGORY
category_performance = (
    filtered_orders.groupby('Product Category')
    .agg({
        'Revenue (€)': 'sum',
        'COGS (€)': 'sum',
        'Profit Adjusted (€)': 'sum'
    })
    .reset_index()
)

category_performance['Overall Profit Margin'] = (
    category_performance['Profit Adjusted (€)']
    / category_performance['Revenue (€)'] * 100
)

category_performance['COGS % of Revenue'] = (
    category_performance['COGS (€)']
    / category_performance['Revenue (€)'] * 100
)

category_melted = category_performance.melt(
    id_vars='Product Category',
    value_vars=['COGS % of Revenue', 'Overall Profit Margin'],
    var_name='Financial Measure',
    value_name='Percentage'
)

fig3 = px.bar(
    category_melted,
    x='Percentage',
    y='Product Category',
    color='Financial Measure',
    barmode='group',
    orientation='h',
    text=category_melted['Percentage'].map(lambda x: f'{x:.2f}%'),
    title='COGS Share and Profit Margins<br><sup>by Product Category</sup>',
    color_discrete_map={
        'COGS % of Revenue': '#1729A5',
        'Overall Profit Margin': '#E96B36'
    }
)

fig3.update_traces(textposition='outside')

fig3.update_layout(
    xaxis_title='Percentage',
    yaxis_title='Product Category',
    xaxis_ticksuffix='%',
    height=400,
    legend_title_text=''
)

st.plotly_chart(fig3, use_container_width=True)




# GRAPH 4: PRODUCT RETURNS BY CATEGORY
product_returns = (
    filtered_orders.groupby('Product Category')
    .agg({
        'Sales Quantity': 'sum',
        'Returned Quantity': 'sum'
    })
    .reset_index()
)

product_returns['Return Rate'] = (
    product_returns['Returned Quantity']
    / product_returns['Sales Quantity'] * 100
)

# Sort in descending order
product_returns = product_returns.sort_values(
    'Return Rate',
    ascending=False
)

fig4 = px.bar(
    product_returns,
    x='Return Rate',
    y='Product Category',
    orientation='h',
    text=product_returns['Return Rate'].map(lambda x: f'{x:.2f}%'),
    color_discrete_sequence=['#E96B36'],
    title='Product Returns<br><sup>by Category</sup>'
)

fig4.update_traces(textposition='outside')

fig4.update_layout(
    xaxis_title='Return Rate',
    yaxis_title='Product Category',
    xaxis_ticksuffix='%',
    yaxis=dict(categoryorder='total ascending'),
    height=400,
    showlegend=False
)

st.plotly_chart(fig4, use_container_width=True)


# GRAPH 5: PROFIT PERFORMANCE BY CUSTOMER SEGMENT
segment_profit = (
    filtered_orders.groupby('Customer Segment')
    .agg({'Profit Adjusted (€)': 'sum'})
    .reset_index()
)

# Sort descending: highest profit first
segment_profit = segment_profit.sort_values(
    'Profit Adjusted (€)',
    ascending=False
)

fig5 = px.bar(
    segment_profit,
    x='Customer Segment',
    y='Profit Adjusted (€)',
    text=segment_profit['Profit Adjusted (€)'].map(
        lambda x: f'€{x:,.0f}'
    ),
    color_discrete_sequence=['#F4A6C1'],
    title='Profit Performance<br><sup>by Customer Segment</sup>'
)

fig5.update_traces(textposition='outside')

fig5.update_layout(
    xaxis_title='Customer Segment',
    yaxis_title='Net Profit (€)',
    height=400,
    showlegend=False
)

st.plotly_chart(fig5, use_container_width=True)


# GRAPH 6: ON-TIME DELIVERY RATE BY ORDER PRIORITY
priority_delivery = (
    filtered_orders.groupby('Order Priority')
    .agg({'On Time Delivery': 'mean'})
    .reset_index()
)

priority_delivery['On-Time Delivery Rate'] = (
    priority_delivery['On Time Delivery'] * 100
)

# Sort descending: highest delivery rate first
priority_delivery = priority_delivery.sort_values(
    'On-Time Delivery Rate',
    ascending=False
)

fig6 = px.bar(
    priority_delivery,
    x='On-Time Delivery Rate',
    y='Order Priority',
    orientation='h',
    text=priority_delivery['On-Time Delivery Rate'].map(
        lambda x: f'{x:.2f}%'
    ),
    color_discrete_sequence=['#D94350'],
    title='On-Time Delivery Rate<br><sup>by Order Priority</sup>'
)

fig6.update_traces(textposition='outside')

fig6.update_layout(
    xaxis_title='On-Time Delivery Rate',
    yaxis_title='Order Priority',
    xaxis_ticksuffix='%',
    yaxis=dict(categoryorder='total ascending'),
    height=400,
    showlegend=False
)

st.plotly_chart(fig6, use_container_width=True)




# GRAPH 7: MONTHLY DELIVERY DELAY VS MONTHLY SALES

# Create month columns from Order Date
filtered_orders['Order Date'] = pd.to_datetime(
    filtered_orders['Order Date'],
    errors='coerce'
)

filtered_orders['Month_Number'] = filtered_orders['Order Date'].dt.month
filtered_orders['Month_Label'] = filtered_orders['Order Date'].dt.strftime('%b')

monthly_delivery_sales = (
    filtered_orders.groupby(['Month_Number', 'Month_Label'])
    .agg({
        'Delivery variance': 'sum',
        'Monthly Sales Qty': 'sum'
    })
    .reset_index()
)

monthly_delivery_sales = monthly_delivery_sales.sort_values(
    'Month_Number'
)

monthly_delivery_sales = monthly_delivery_sales.rename(
    columns={'Delivery variance': 'Delivery Delays'}
)

fig7 = go.Figure()

# Delivery variance line
fig7.add_trace(go.Scatter(
    x=monthly_delivery_sales['Month_Label'],
    y=monthly_delivery_sales['Delivery Delays'],
    name='Delivery Delays',
    mode='lines+markers',
    line=dict(color='#168BFF', shape='spline', smoothing=1.3, width=3),
    fill='tozeroy',
    fillcolor='rgba(22,139,255,0.12)',
    yaxis='y'
))

# Monthly sales line
fig7.add_trace(go.Scatter(
    x=monthly_delivery_sales['Month_Label'],
    y=monthly_delivery_sales['Monthly Sales Qty'],
    name='Monthly Sales',
    mode='lines+markers',
    line=dict(color='#1729A5', shape='spline', smoothing=1.3, width=3),
    fill='tozeroy',
    fillcolor='rgba(23,41,165,0.08)',
    yaxis='y2'
))

fig7.update_layout(
    title='Monthly Delivery Delay vs Monthly Sales',
    xaxis_title='Month',
    yaxis=dict(
        title='Delivery Variance',
        range=[350, 550],
        dtick=50
    ),
    yaxis2=dict(
        title='Monthly Sales Quantity',
        overlaying='y',
        side='right',
        range=[0, 35000],
        tickvals=[10000, 20000, 30000],
        ticktext=['10K', '20K', '30K']
    ),
    height=450,
    legend=dict(orientation='h', y=-0.2)
)

st.plotly_chart(fig7, use_container_width=True)


# GRAPH 8: TOTAL REVENUE AND TOTAL COGS BY YEAR

yearly_financials = (
    filtered_orders.groupby('Year')
    .agg({
        'Revenue (€)': 'sum',
        'COGS (€)': 'sum'
    })
    .reset_index()
)

yearly_financials = yearly_financials.sort_values(
    'Year',
    ascending=True
)

fig8 = px.bar(
    yearly_financials,
    x='Year',
    y=['Revenue (€)', 'COGS (€)'],
    barmode='group',
    title='Total Revenue and Total COGS<br><sup>by Year</sup>',
    color_discrete_map={
        'Revenue (€)': '#800080',
        'COGS (€)': '#E344A8'
    },
    text_auto='.2s'
)

fig8.update_layout(
    xaxis_title='Year',
    yaxis_title='Amount (€)',
    height=400,
    bargap=0.25,
    legend_title_text=''
)

st.plotly_chart(fig8, use_container_width=True)


