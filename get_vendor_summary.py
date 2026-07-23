import duckdb
import logging
import pandas as pd
from execution_db import load_raw_data


logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a",
    force=True
)

def create_vendor_summary(con):
    '''this function will merge the different to get the overall vendor summary and adding new columns in the resultant data'''
    vendor_sales_summary = con.execute("""WITH FreightSummary AS (
     SELECT
         VendorNumber,
         SUM(Freight) AS FreightCost
     FROM vendor_invoice
     GROUP BY VendorNumber
    ),

    PurchaseSummary AS (
        SELECT
            p.VendorName,
            p.VendorNumber,
            p.Brand,
            p.Description,
            p.PurchasePrice,
            pp.Price AS ActualPrice,
            pp.Volume,
            SUM(p.Quantity) AS TotalPurchaseQuantity,
            SUM(p.Dollars) AS TotalPurchaseDollars
        FROM purchases p
        JOIN purchase_prices pp
            ON p.Brand = pp.Brand
            WHERE p.PurchasePrice > 0
            GROUP BY p.VendorName, p.VendorNumber,p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
    ),
    SalesSummary AS (
        SELECT
            VendorNo,
            Brand,
            SUM(SalesQuantity) AS TotalSalesQuantity,
            SUM(SalesDollars) AS TotalSalesDollars,
            SUM(SalesPrice) AS TotalSalesPrice,
            SUM(ExciseTax) AS TotalExciseTax
        FROM sales
        GROUP BY VendorNo, Brand
    )

    SELECT
        ps.VendorName,
        ps.VendorNumber,
        ps.Brand,
        ps.Description,
        ps.PurchasePrice,
        ps.ActualPrice,
        ps.Volume,
        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,
        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,
        fs.FreightCost
    FROM PurchaseSummary ps
    LEFT JOIN SalesSummary ss
        ON ps.VendorNumber = ss.VendorNo
        AND ps.Brand = ss.Brand
    LEFT JOIN FreightSummary fs
        ON ps.VendorNumber = fs.VendorNumber
    ORDER BY ps.TotalPurchaseDollars DESC""").fetchdf()   
    
    return vendor_sales_summary

def clean_data(df):
    '''this function will clean the data'''
    # changing datatype to float
    df['Volume'] = df['Volume'].astype('float')

    #filling missing values with 0
    df.fillna(0,inplace = True)

    # removing spaces from categorical columns
    df['VendorName'] = df['VendorName'].str.strip()
    df['Description'] = df['Description'].str.strip()

    #creatinf new columns for better analysis
    vendor_sales_summary['GrossProfit']= vendor_sales_summary['TotalSalesDollars']- vendor_sales_summary['TotalPurchaseDollars']
    vendor_sales_summary['ProfitMargin'] =vendor_sales_summary['GrossProfit'] / vendor_sales_summary['TotalSalesDollars']*100
    vendor_sales_summary['StockTurnover'] = vendor_sales_summary['TotalSalesQuantity'] / vendor_sales_summary['TotalPurchaseQuantity']
    vendor_sales_summary['SalesPurchaseRatio'] = vendor_sales_summary['TotalSalesDollars'] / vendor_sales_summary['TotalPurchaseDollars']

     return df

if __name__== '__main__':
    #creating database connection
    con = duckdb.connect("inventory.duckdb")

    logging.info('Creating Vendor Summary Table......')
    summary_df = create_vendor_summary(con)
    logging. info(summary_df.head())
    
    logging. info('Cleaning Data....')
    clean_df = clean_data(summary_df)
    logging. info(clean_df.head())
    logging.info('Ingesting data.....')
    con.register("temp_df", vendor_sales_summary)
    con.execute("""
    CREATE OR REPLACE TABLE vendor_sales_summary AS
    SELECT * FROM temp_df
    """)
    
    logging.info('Completed')

     


















