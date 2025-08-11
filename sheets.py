################# Setting up environment and fetching data from Google Sheets #################
import streamlit as st
import pandas as pd
import numpy
import bcrypt
import re
import gspread
from streamlit_gsheets import GSheetsConnection
st.set_page_config(
            page_title="Sheets",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
hash_password = st.secrets["app_credentials"]["hashed_password"]
def check_credentials(password):
    entered_password_bytes = password.encode('utf-8')
    correct_password_hash_bytes = hash_password.encode('utf-8')
    return bcrypt.checkpw(entered_password_bytes, correct_password_hash_bytes)
# --- Initialize session state ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_error' not in st.session_state:
    st.session_state.login_error = False
#st.session_state.logged_in=True #DELETE THIS WHEN COMMITING!!!!!!!!!!!!!!!
###############################Show login form if not logged in##########################################
if not st.session_state.logged_in:
    st.title("Login")

    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if check_credentials(password):
                st.session_state.logged_in = True
                st.session_state.login_error = False
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.session_state.login_error = True
                st.error("Invalid  password.")
                st.rerun()

    if st.session_state.login_error:
        st.warning("Please try again.")
################################Show main interface if logged in##########################################
else:
    with st.spinner("Connecting to Google Sheets..."):  #connect to Gsheets and fetch data
        #scope = [ 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive' ]      
        #service_account_info = st.secrets["gcp_service_account"]
        #client = gspread.service_account_from_dict(dict(service_account_info))
        from pathlib import Path
       # conn = st.connection("ffpe_gsheets", type=GSheetsConnection)        
        client = gspread.service_account(filename=Path('.streamlit/ravits-lab-paraffin-blocks-e254d6aa1b19.json')) # type: ignore
        sheet = client.open("Ravits Lab Paraffin Blocks Inventory")
        sheet_guide = sheet.get_worksheet(0)
        sheet_summary=sheet.get_worksheet(1)
        sheet_detail= sheet.get_worksheet(2)
        sheet_code=sheet.get_worksheet(3)
    ################################## Initializing global funcs and  pre-processing data  ############################################
    
    @st.dialog('Message',width='large')
    def Msg():
        st.markdown('''
                    Welcome to the FFPE portal. All the block information is up-to-date as of writing.
                    Although all block info has been inputed (and should be updated if used properly), not all functions of the portal have been implemented.
                    
                    Here's a overview of what you **CAN** do:
                    1. Look up information about any block.
                    2. Criteria mode: Narrow down your searches by filtering with diagnosis (Control/fALS/sALS), or anatomical region(s).
                    3. Case No. mode: Narrow down your search by filter for specific cases.
                    4. Filter for active blocks (block that is being used for a specific purpose, and is not in its default location)
                    
                    Here's what you **CANNOT** do, but I hope to implement these in the future:
                    1. Change any information about a block. Please go to the spreadsheet and change it there.
                    2. See additional information: secondary dx, genetics, pt demographics et c. Please use the MAIN DB spreadsheet. 
                    
                    ### 2025-08-10 AM

                    ''')
        st.session_state.msg=True

    if 'msg' not in st.session_state:
        Msg() 
    @st.fragment
    def mainDF_styles(df):
        def conditional_cell_colors(row):   #color cells based on block color and status
            styles=['']*len(row)
            text_color='color: #000'
            background_color=''
            if row['Block color'].lower() == "red":
                background_color = 'background-color: #da0000'
                text_color='color: #fff'
            elif row['Block color'].lower() == 'orange':
                background_color = 'background-color: #ff9966'
            elif row['Block color'].lower() == 'gold':
                background_color = 'background-color: #fbc315'
            elif row['Block color'].lower() == 'yellow':
                background_color = 'background-color: #faf28a'
            elif row['Block color'].lower() == 'green':
                background_color = 'background-color: #99d3a1'
            elif row['Block color'].lower() == "teal":
                background_color = 'background-color: #53ada3'
            elif row['Block color'].lower() == "blue":
                background_color = 'background-color: #afcae7'
            elif row['Block color'].lower() == "purple":
                background_color = 'background-color: #e78dd5'
            elif row['Block color'].lower() == "pink":
                background_color = 'background-color: #f6cad9'
            elif row['Block color'].lower() == "gray":
                background_color = 'background-color: #bdbdbd'
            elif row['Block color'].lower() == "white":
                background_color = 'background-color: #FFFFFF'
            styles[list(row.index).index('Block label')]=f"{background_color}; {text_color}"
            background_color=''
            if row['Block status'].lower()=="uncut":
                text_color='color: #808080'
            elif row['Block status'].lower()=='cut':
                text_color='color: #009900'
            elif row['Block status'].lower()=='low':
                text_color='color: #fa9b0f'
            elif row['Block status'].lower()=='used up':
                text_color='color: #da0000'
            styles[list(row.index).index('Block status')]=f"{background_color}; {text_color}"
            return styles
        output=df.style.set_properties(**{'width':'10 px'},subset=['Region code'])   
        output=df.style.apply(conditional_cell_colors,axis=1)
        return output
        
    @st.fragment
    def case_info_card_display(row):    #for the case info block in the search by case page
        st.write(f"**Pt. {row.Case}**")
        st.write(f"**Primary Dx**: {row.Diagnosis}")
        st.write("Genetics:")
        st.write("Clinical Subtype:")
        st.write("Onset:")

    @st.fragment
    def make_code_dict():     # Function to generate a dict from sheet_codes to be used later.
        list=sheet_code.get_values('A2:B73')
        codes_list=[]
        for item in list:
            label_temp=item[1]
            item_temp=[item[0][:2],item[0][2:4],label_temp]
            codes_list.append(item_temp)
        #df=pd.DataFrame(codes_list,None,['Region','Code','Label'],)
        #output=df.to_dict(orient='index')           # the dict is formatted as: {1:{Region:'CR', Code:'00', Label:''}, 2:{}....}
        output={
            i:{'Region': sublist[0], 'Code': sublist[1], 'Label': sublist[2]}
            for i,sublist in enumerate(codes_list,1)
        }
        return(output)
    
    @st.fragment
    def df_style(df):
        return(st.dataframe(
                    df,
                    column_order=[
                        'Active','Diagnosis', 'Case No.','Region code','Block label', 'Location', 'Block status','Notes'
                    ],
                    height=1000,
                    hide_index=True,
                    #on_select="rerun",
                    #selection_mode='multi-row',
                ))
    # preparing all data from the Google Sheets document
    full_list_of_lists = sheet_detail.get_all_values() #get all values from 'block details' sheet, remove header row ([0])
    mainDataDF = pd.DataFrame(full_list_of_lists[1:], columns=full_list_of_lists[0],index=None) #manually assign header values from Gsheet
    #print(mainDataDF)
    diagnosis_index=[row[:2] for row in sheet_summary.get_all_values()[3:]]  # get diagnosis information from 'summary' sheet and Extract only the first two columns
    diagnosis_df = pd.DataFrame(diagnosis_index, columns=['Case', 'Diagnosis']) # Convert the list of lists to a DataFrame
    mainDataDF = pd.merge(mainDataDF, diagnosis_df, left_on='Case No.', right_on='Case', how='left') #merge the diagnosis information with the main data
    mainDataDF.drop(columns=['Case'], inplace=True) #remove duplicate 'Case' column
    mainDataDF.dropna(axis=0,subset='Diagnosis',inplace=True,) #remove rows with no Case No.
    mainDataDF['Active']=mainDataDF['Active']=='TRUE'
    activeBlocks = mainDataDF[mainDataDF['Active']==True]  
    regions_dict=make_code_dict()

    ########################################### Actual interface begins here ####################################################

    
    colL,colR = st.columns([5, 1])
    with colL:
        st.markdown('''# Ravits Lab FFPE Blocks Inventory''')
    with colR:
        st.markdown(''':blue-badge[Last Updated:2025-08-11] ''')
    st.divider()    
    c1,c2,c3,c4=st.columns([4,1, 1, 1])
    c1.markdown('''
        Web application for accessing the paraffin blocks inventory. All data here is pulled from the Google Sheets document.    
        Please use the filter set below to crearte a list of blocks to include in an experiment.

        ''')
    c2.metric(label="Total Blocks", value=len(mainDataDF), help="Total number of FFPE blocks in the inventory.",border=True)
    c3.metric(label="Total Cases", value=len(mainDataDF['Case No.'].unique()), help="Number of cases that have blocks the inventory.",border=True)
    c4.metric(label="Active Blocks", value=len(activeBlocks), help="Number of blocks that are removed from the inventory to be used in an experiment.",border=True)
    c4.link_button(":material/link: Link to Spreadsheet",'https://docs.google.com/spreadsheets/d/18WNJFahK-IlF8yqIsYkL-yoB1Wyc4cO5uKeDngAkkXs/edit',type='primary')
    @st.fragment
    def criteria_filter_main():     #Wrapping all functions used in this module under the @frag
        @st.fragment
        def diagnosis_filter(arg: list):
            pattern = []
            for item in arg:
                pattern.append(rf'{item}')
            regex = '|'.join(pattern)
            # Return a boolean Series for filtering
            return mainDataDF['Diagnosis'].astype(str).str.contains(regex, case=False, regex=True,na=False)
        @st.fragment    
        def region_filter_code(arg:str):    #Filtedring regoins, to be used with direct code input
            if arg=='':
                return(True) #return all blocks if not specified
            else:                
                #input preprocess
                split=re.split(r'\,',arg)
                region=split[0]
                range1=split[1]
                if len(split)>2:
                    range2=split[2]
                else:
                    range2=''
                #originally take arg as (region: str, range1, range2). Need to add a pre-process because I don't want to put in 3 st.empty s for selecting menu type, so the input is now through one single string.
                # filtering the main df based on given parameters, should return df
                match_list=[]    #An empty list that will be filled with codes to match
                output=pd.DataFrame
                if range2=='': #not a range filter, only filtering for a specific subcategory (child node)
                    match_range=[int(range1)]
                    #match_list=[f'{region}{range1}']    #only one code to match
                else:
                    range1=int(range1)  #convert to ints for generating mathematical range
                    range2=int(range2)+1  #+1 to account for excluding upper lim
                    match_range=range(range1,range2)        #a list of ints between range1 and range 2                      
                for entry in match_range:   #format the ints to be 2 digit str type
                    if entry==0:        #0 cannot undergo the log test, so singling it out here
                        code='00'
                    else:               # nonzero numbers can be tested with log for length
                        size_test=numpy.floor(numpy.log10(abs(entry)))+1    #returns 1 if (1-9), 2 if (10-99)
                        if size_test==1:    
                            code=f'0{entry}'    # add a padding zero to single digits  
                        else:    
                            code=str(entry)     # don't do anything to double digits, just convert to str
                    match_list.append(f'{region}{code}')    # cocatenate the letter code with the formatted number code to form the whole code, add it to the list
                #print(match_range) For debugging
                #print(match_list)
                output=mainDataDF['Region code'].isin(match_list)   #create a logic statement that can be used to filter selected categories
                return(output)       # return the the filter logic statement (to be combined with other filters)
        @st.fragment
        def region_filter_menu(dict,selection:list):        #Filtering regions, to be used with the multiselect menu
            #take the list of dict indices, look up the corresponding keys for each index under dict, then return the df entries that match the selected keys
            match_list=[]
            if selection==[]:
                return(True)     # return all blocks if not specified
            else:
                for item in selection:
                    index_it=int(item)
                    full_code=f'{dict[index_it]['Region']}{dict[index_it]['Code']}'
                    match_list.append(full_code)
                output=mainDataDF['Region code'].isin(match_list)
                return(output)    
        @st.fragment
        def menu_option_formatter(key): #Format the codes dict to display labels in the menu
            code_name=regions_dict[key]
            return(f'[{code_name['Region']}{code_name['Code']}] {code_name['Label']}')    
        
        diagnosis_list=["Control", "sALS", "fALS"]
        
        CritC1, CritC2 = st.columns([1, 3])
        with CritC1:
            st.markdown(''' ### Filters ''')
            #display the input fields, and generate filters for each category based on the input                
            with st.form(key="filter_lookup_input",width='content'):
            # Diagnosis filter
                diag_list= st.multiselect(
                "Diagnosis",
                options=diagnosis_list,
                default=diagnosis_list,  # Default to all options selected
                )  
                region_menu_container=st.empty()

            # Select with anatomical region filter menu to use  
                region_menu_type=st.radio(
                    "Region Selection Method",
                    ['Multiselect menu','Region code (Dev)'],
                    captions=['Use a dropdown menu to click all the regions you want to select','Look up a numerical code range under ONE letter code.'],
                    help='',
                    horizontal=True                
                ) 
                #multiselect menu                               
                if region_menu_type=='Multiselect menu':
                    region_selected=[]
                    region_selected=region_menu_container.multiselect(
                        "Anatomical Regions",
                        regions_dict,
                        format_func=menu_option_formatter,
                        help='Select all the anatomical regions you are interested in. Leaving it empty to include all regions. '
                        )
                #code menu
                elif region_menu_type=='Region code (Dev)':
                    with region_menu_container:
                        #region=st.pills('Region letter code',['CR','SS','LS','BS','CL','SC','MI'])
                        code_selected=st.text_input('Region code',value='',help='Separate each element by comma. Format: \"CR,00\" if looking for single region. \"CR, 00, 99\" if looking for a range.')             
                active_toggle=st.checkbox("Show only active blocks")
                filters_submit=st.form_submit_button('Search',type='primary')
                
            with st.expander("Region code reference chart",expanded=False):
                st.dataframe(pd.DataFrame.from_dict(regions_dict,orient='index'),hide_index=True)    
        if filters_submit:  #create the final filter used to query the DF once the form is submitted
            if region_menu_type=='Multiselect menu':
                filter_combined = diagnosis_filter(diag_list) & region_filter_menu(regions_dict,region_selected) # Combine filters
            else:
                filter_combined= diagnosis_filter(diag_list) & region_filter_code(code_selected)
            if active_toggle==True:
                filter_combined=filter_combined & mainDataDF['Active']==True
        with CritC2:
            st.markdown(''' ### Blocks List ''')
            df_container=st.empty()
            df_container.write('''Enter a search critera...''')    
            if filters_submit:
                filtered_data = mainDataDF[filter_combined]        
                if len(filtered_data) == 0:
                    st.markdown(f":red-badge[No blocks found for the selected filters.]")
                else:
                    st.markdown(f":green-badge[Found {len(filtered_data)} blocks.]")
                    filtered_data_style =mainDF_styles(filtered_data)
                    with st.spinner(text="Loading...",show_time=True):
                        with df_container:
                            df_style(filtered_data_style)
                    #st.download_button(
                    #    "Download List",
                    #    data=filtered_data.to_csv(index=False).encode('utf-8'),
                    #    on_click="ignore",
                    #    key="dl_1")   

    @st.fragment
    def case_filter_main():        #Wrapping all functions used in this module under the @frag
        caseC1, caseC2 = st.columns([1, 3])   
        with caseC1: 
            st.markdown(''' ### Case Input''')
            with st.form(key="case_no_lookup_input"):
                caseNo_list=st.multiselect(
                    "Case Numbers",
                    options=diagnosis_df['Case'].unique(),
                    default=None
                )
                active_toggle=st.checkbox("Show only active blocks")
                filters_submit=st.form_submit_button('Search',type='primary')
                with st.expander("Region code reference chart",expanded=False):
                    st.dataframe(pd.DataFrame.from_dict(regions_dict,orient='index'),hide_index=True)    

        if filters_submit:
            if caseNo_list:
                st.markdown('''### Case Info''')
                for _, row in diagnosis_df[diagnosis_df['Case'].isin(caseNo_list)].iterrows():
                     with st.container(border=True):
                        case_info_card_display(row)

            else:
                    st.markdown(":red-badge[Please select at least one case .]")    
        
        with caseC2:
            st.markdown(''' ### Blocks List ''')
            DLButton_Container = st.empty()
            df_container=st.empty()
            df_container.write('''Enter a search critera...''')
            if filters_submit:
                filter=mainDataDF['Case No.'].isin(caseNo_list)    
                if active_toggle==True:
                    filter=filter & mainDataDF['Active']==True    
                filtered_data = mainDataDF[filter]
                if len(filtered_data) == 0:
                    st.markdown(f":red-badge[No blocks found for Case No. {caseNo_list}]")
                else:
                    st.markdown(f":green-badge[Found {len(filtered_data)} blocks for Case No. {caseNo_list}]")
                    filtered_data_style = mainDF_styles(filtered_data)
                    with st.spinner(text="Loading...",show_time=True):
                        with df_container:
                            df_style(filtered_data_style)
            #DLButton_Container.download_button(
            #    "Download List",
            #    data=filtered_data.to_csv(index=False).encode('utf-8'),
            #    on_click="ignore",
            #    key="dl_2")

    criterial_filter_tab, case_filter_tab =st.tabs(["Search by Criteria", "Look Up Cases"])

    with criterial_filter_tab:
        criteria_filter_main()
    with case_filter_tab:
        case_filter_main()

st.divider()
st.write("Please contact Alex Meng s7meng@health.ucsd.edu for any questions.")