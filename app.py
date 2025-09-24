import streamlit as st
import pandas as pd
from simple_salesforce import Salesforce
import requests
import io
from io import StringIO
from datetime import datetime
from datetime import date
import folium
from streamlit_folium import st_folium
from folium.features import DivIcon
import PIL
from PIL import Image
from PIL import ImageDraw


APP_TITLE = "IBERIA ACCOUNTS"

@st.cache_data
def display_map(df):
    zoom_var = 6
    
    #lat_center = (df['Lat'].max() + df['Lat'].min())/2
    #lon_center = (df['Lon'].max() + df['Lon'].min())/2

    m = folium.Map(location=[40.43206557785185, -3.7118551338892396], tiles='OpenStreetMap', zoom_start = zoom_var)

    for i, row in df.iterrows():
        lat = df.at[i, 'Lat']
        lon = df.at[i, 'Lon']
        segment = df.at[i, 'Account Segment']
        name = df.at[i, 'Account Name']
        brick = df.at[i, 'Brick Description']
        city = df.at[i, 'Primary City']
        street = df.at[i, 'Primary Street']
        date = df.at[i, 'Last Visit']
        id = df.at[i, 'Account ID']
        visited = df.at[i, 'Visited']
        rate = df.at[i, 'Call Rate']
        size = df.at[i, 'Call Target']
        meters = df.at[i, 'Meters Placed']
        orders = df.at[i, '# Orders']
        last_order = df.at[i, 'Last Order']
        days_vo_visits = df.at[i, 'Days vo Visits']

        if segment == 'Hunter':
            color = 'lightblue'
        elif segment == 'Farmer':
            color = 'lightgreen'
        elif segment == 'Refocus':
            color = 'pink'
        else:
            color = 'beige'
        
        if visited == 'Yes':
            visited_color = 'darkgreen'
        else:
            visited_color = 'darkred'

        html = '''
                <b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <em style="color:gray;font-family:verdana;font-size:80%;">Coverage: </em><b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <em style="color:gray;font-family:verdana;font-size:80%;">Last visited date: </em><b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <em style="color:gray;font-family:verdana;font-size:80%;">Days vo Visits: </em><b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <em style="color:gray;font-family:verdana;font-size:80%;">Meters Placed YTD: </em><b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <em style="color:gray;font-family:verdana;font-size:80%;"># Orders: </em><b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <em style="color:gray;font-family:verdana;font-size:80%;">Last Order: </em><b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
                <em style="color:gray;font-family:verdana;font-size:80%;">ID: </em><b style="color:gray;font-family:verdana;font-size:80%;">{}</b><br>
            '''.format(name, segment, rate, date, days_vo_visits, meters, orders, last_order, brick, city, street, id)

        iframe = folium.IFrame(html,
                            width=300,
                            height=180)

        popup = folium.Popup(iframe,
                            max_width=300)

        
        folium.CircleMarker(location=[lat,lon],
                            popup=popup,
                            color=visited_color,
                            fill=True,
                            fill_color=color,
                            fill_opacity=1,
                            radius=size*2).add_to(m)
    
    return m

@st.cache_data(show_spinner="Downloading accounts from SFDC...")
def get_data(Rep_name):
    sf = Salesforce(
        username='nmatyash@lifescan.com', 
        password='KLbq57fa31!',
        security_token='')

    sf_org = 'https://jjds-sunrise.my.salesforce.com/'
    report_id_accounts = '00OQv00000Cg06LMAR'
    report_id_visits = '00OQv00000CcQLyMAN'
    report_id_meters_placed = '00OQv00000Cdgq5MAB'
    
    export_params = '?isdtp=p1&export=1&enc=UTF-8&xf=csv'

    sf_report_url_accounts = sf_org + report_id_accounts + export_params
    response_accounts = requests.get(sf_report_url_accounts, headers=sf.headers, cookies={'sid': sf.session_id})
    report_accounts = response_accounts.content.decode('utf-8')
    All_Accounts = pd.read_csv(StringIO(report_accounts))
    All_Accounts = All_Accounts[All_Accounts['Account ID'].map(lambda x: str(x)[0]) == '0']
    All_Accounts = All_Accounts.rename(columns={
        'Owner' : 'Account Owner',
        'Target Call Frequency / Cycle (Account)': 'Call Target'})

    sf_report_url_visits = sf_org + report_id_visits + export_params
    response_visits = requests.get(sf_report_url_visits, headers=sf.headers, cookies={'sid': sf.session_id})
    report_visits = response_visits.content.decode('utf-8')
    visits = pd.read_csv(StringIO(report_visits))
    visits = visits[visits['Account ID'].map(lambda x: str(x)[0]) == '0']

    sf_report_url_meters_placed = sf_org + report_id_meters_placed + export_params
    response_meters_placed = requests.get(sf_report_url_meters_placed, headers=sf.headers, cookies={'sid': sf.session_id})
    report_meters_placed = response_meters_placed.content.decode('utf-8')
    meters_placed = pd.read_csv(StringIO(report_meters_placed))
    meters_placed = meters_placed[meters_placed['Account ID'].map(lambda x: str(x)[0]) == '0']
    meters_placed = meters_placed.rename(columns={'Items Dropped': 'Quantity'})


    visits = visits[visits['Assigned'] == Rep_name]
    visits['Date'] = visits['Date'].map(lambda x: pd.to_datetime(x, format='%d/%m/%Y'))
    visits_count = visits.groupby('Account ID').agg({'Date': 'nunique'}).reset_index()
    visits_count = visits_count.rename(columns={'Date': '# Visits'})
    visits_last = visits.groupby('Account ID').agg({'Date': 'max'}).reset_index()
    visits_last = visits_last.rename(columns={'Date': 'Last Visit'})

    All_Accounts = All_Accounts[All_Accounts['Account Owner'] == Rep_name].reset_index()
    All_Accounts = All_Accounts.merge(visits_count[['Account ID','# Visits']], on = 'Account ID', how = 'left') 
    All_Accounts['# Visits'] = All_Accounts['# Visits'].fillna(0)
    All_Accounts = All_Accounts.merge(visits_last[['Account ID','Last Visit']], on = 'Account ID', how = 'left') 
    All_Accounts['Last Visit new'] = All_Accounts['Last Visit'].map(lambda x: pd.to_datetime(x))
    All_Accounts['Last Visit new'] = All_Accounts['Last Visit new'].dt.date
    All_Accounts['Last Visit new'] = All_Accounts['Last Visit new'].fillna(0)
    today = date.today()
    All_Accounts['Days vo Visits'] = All_Accounts['Last Visit new'].map(lambda x: (today - pd.to_datetime(x).date()).days)
    All_Accounts['Call Rate'] = All_Accounts['# Visits'].map(lambda x: str(int(x))) + "/" + All_Accounts['Call Target'].map(lambda x: str(int(x)))
    All_Accounts['Coverage'] = All_Accounts['# Visits'] / All_Accounts['Call Target']
    All_Accounts['Visited'] = All_Accounts['# Visits'].map(lambda x: "Yes" if x > 0 else "No")

    meters_placed['Date'] = meters_placed['Date'].map(lambda x: pd.to_datetime(x, format='%d/%m/%Y'))
    orders_count = meters_placed.groupby('Account ID').agg({'Visit Product Id': 'nunique'}).reset_index()
    orders_count = orders_count.rename(columns={'Visit Product Id': '# Orders'})
    orders_last = meters_placed.groupby('Account ID').agg({'Date': 'max'}).reset_index()
    orders_last = orders_last.rename(columns={'Date': 'Last Order'})
    meters_pivot = meters_placed.groupby('Account ID').agg({'Quantity': 'sum'}).reset_index()
    meters_pivot['Quantity'] = meters_pivot['Quantity'].astype('int')

    All_Accounts = All_Accounts.merge(meters_pivot[['Account ID','Quantity']], on = 'Account ID', how = 'left')
    All_Accounts['Quantity'] = All_Accounts['Quantity'].fillna(0)
    All_Accounts = All_Accounts.rename(columns={'Quantity': 'Meters Placed'})
    All_Accounts['Meters Placed'] = All_Accounts['Meters Placed'].astype('int')
    All_Accounts = All_Accounts.merge(orders_count[['Account ID','# Orders']], on = 'Account ID', how = 'left') 
    All_Accounts['# Orders'] = All_Accounts['# Orders'].fillna(0)
    All_Accounts['# Orders'] = All_Accounts['# Orders'].astype(int)
    All_Accounts = All_Accounts.merge(orders_last[['Account ID','Last Order']], on = 'Account ID', how = 'left')

    data = All_Accounts.reset_index(drop=True)
    data['Lat'] = data['Lat'].fillna(0)
    data['Lon'] = data['Lon'].fillna(0)
    data['Last Visit'] = data['Last Visit'].map(lambda x: str(x.date()).replace("/", "-"))
    data['Last Order'] = data['Last Order'].map(lambda x: str(x.date()).replace("/", "-"))
    data['Last Visit'] = data['Last Visit'].replace('NaT', '')
    data['Last Order'] = data['Last Order'].replace('NaT', '')
    data = data[['Account ID', 'Account Owner', 'Account Name',
       'Account Type', 'Account Segment', 'Brick Code', 'Brick Description',
       'Primary State/Province', 'Primary City', 'Primary Street',
       'Call Target', 'Lat', 'Lon', '# Visits', 'Last Visit',
       'Days vo Visits', 'Call Rate', 'Coverage', 'Visited', 'Meters Placed',
       '# Orders', 'Last Order']]
    
    return data


def main():
    #Page settings
    st.set_page_config(layout='wide')
    st.title(APP_TITLE)
    
    FSR = pd.read_excel("./FSR.xlsx", sheet_name="FSR")
    placeholder = st.empty()
    placeholder.header('Choose Field Sales Rep Name')
    
    uploaded_name = st.selectbox("FSR Name", FSR.sort_values(by = 'FSR', ignore_index=True)['FSR'].to_list(), index=None, placeholder="Choose your Name...")
    if uploaded_name is None:
        st.stop()
    else:
        placeholder.empty()
        if "Rep_name" not in st.session_state:
            st.session_state.Rep_name = uploaded_name
        else:
            st.session_state.Rep_name = uploaded_name
        df = get_data(st.session_state.Rep_name)


        
    
    #Display filters
    cola, colb = st.columns([0.9, 0.1])
    with cola:
        col1, col2, col3 = st.columns(3, vertical_alignment="center")
        with col1:
            account_type_list = df['Account Type'].map(lambda x: str(x)).unique()
            for i, n in enumerate(account_type_list):
                if n == "nan":
                    account_type_list[i] = "-"
            account_type_list.sort()
            account_type = st.multiselect('Account Type', account_type_list)

        with col2:
            account_segment_list = df['Account Segment'].map(lambda x: str(x)).unique()
            for i, n in enumerate(account_segment_list):
                if n == "nan":
                    account_segment_list[i] = "-"
            account_segment_list.sort()
            account_segment = st.multiselect('Account Segment', account_segment_list)
        
        with col3:
            st.write('')
            if st.button("🔄 Refresh data", use_container_width=True):
                get_data.clear()
                df = get_data(st.session_state.Rep_name)
        
        col4, col5, col6= st.columns(3)
        with col4:
            start_coverage, end_coverage = st.select_slider(
                "Select a range of coverage",
                options=['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'],
                value=('0%', '100%'))
        
        with col5:
            target = st.slider("Call Target", int(df['Call Target'].min()), int(df['Call Target'].max()), (int(df['Call Target'].min()), int(df['Call Target'].max())))
        
        with col6:
            underserved = st.select_slider(
                "Underserved more than ... days",
                options=[0, 30, 60, 90])

    if account_type == []:
        account_type_filter = account_type_list
    else:
        account_type_filter = account_type
    if account_segment == []:
        account_segment_filter = account_segment_list
    else:
        account_segment_filter = account_segment
    
    df_filtered = df[(df['Account Type'].isin(account_type_filter))
                     &(df['Account Segment'].isin(account_segment_filter))
                     &(df['Coverage'] >= int(start_coverage[:-1]) / 100)
                     &(df['Coverage'] <= int(end_coverage[:-1]) / 100)
                     &(df['Call Target'] >= target[0])
                     &(df['Call Target'] <= target[1])
                     &(df['Days vo Visits'] > underserved)]
    df_filtered = df_filtered[['Account ID', 'Account Owner', 'Account Name', 'Account Type', 'Account Segment', 
       'Call Target', '# Visits', 'Call Rate', 'Last Visit',
       'Days vo Visits',  'Coverage', 'Visited',
       'Meters Placed', '# Orders', 'Last Order',
       'Brick Code', 'Brick Description', 'Primary State/Province', 'Primary City', 'Primary Street', 'Lat', 'Lon']]
    
    #Display success graph
    indicatorcolor = '#217346'
    indicatorcolor_false = '#FF0000'
    hollowcolor = '#E2E2E2'
    size = 30

    textvariable = int((df_filtered[df_filtered['# Visits']>0]['Account ID'].nunique()/df_filtered['Account ID'].nunique())*100 if df_filtered['Account ID'].nunique()>0 else 0)
    arcvariable = (df_filtered[df_filtered['# Visits']>0]['Account ID'].nunique()/df_filtered['Account ID'].nunique())*220 if df_filtered['Account ID'].nunique()>0 else 0
    if textvariable >=100:
        text_x = 380
        angle = 380
    else:
        text_x = 410
        angle = int(float(arcvariable)) + 160

    im = PIL.Image.new('RGBA', (1000,1000))
    draw = PIL.ImageDraw.Draw(im)
    draw.arc((0,0,990,990),160,380,hollowcolor,100)
    draw.arc((0,0,990,990),160,angle,indicatorcolor,100)
    draw.text((text_x, 450), f"{textvariable}%", fill='#217346', align ="center", font_size=100)
    draw.text((300, 600), "Coverage", fill='#217346', align ="center", font_size=100)
    new_size = (200, 200)
    resized_im = im.resize(new_size)
    
    with colb:
        st.image(resized_im, use_container_width="auto")

    #Display map
    fol_map = display_map(df_filtered)
    st_folium(fol_map, width=1000, height=850)
    
    #Download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_filtered.to_excel(writer, sheet_name='Sheet1', index=False)
    st.download_button(label='📥 Download Current Account List',
                                data=buffer,
                                file_name= 'Accounts.xlsx',
                                mime='application/vnd.ms-excel')
    
    #Display dataframe
    data_frame = df_filtered[['Account ID', 'Account Owner', 'Account Name', 'Account Type', 'Account Segment', 
       'Call Target', '# Visits', 'Call Rate', 'Last Visit',
       'Days vo Visits',  'Coverage', 'Visited',
       'Meters Placed', '# Orders', 'Last Order',
       'Brick Code', 'Brick Description', 'Primary State/Province', 'Primary City', 'Primary Street']]
    st.dataframe(data_frame,
                column_config={
                'Coverage': st.column_config.NumberColumn(
                     "Coverage",
                     help="The percentage value",
                     format="%.0f%%")},
                hide_index=True)



if __name__ == "__main__":
    main()
